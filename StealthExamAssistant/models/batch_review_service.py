import json
import httpx
from PySide6.QtCore import QObject, Signal, QThread

class BatchReviewWorker(QThread):
    """批量复盘工作线程"""
    
    progress_updated = Signal(int, str)  # (进度百分比, 状态文本)
    result_ready = Signal(list)  # 清洗后的题目列表
    error_occurred = Signal(str)
    
    def __init__(self, api_key, api_base, model_name, raw_text, project, image_base64=None):
        super().__init__()
        self.api_key = api_key
        self.api_base = api_base
        self.model_name = model_name
        self.raw_text = raw_text
        self.project = project
        self.image_base64 = image_base64
        
    def run(self):
        """执行批量清洗"""
        try:
            self.progress_updated.emit(10, "正在调用 AI 清洗...")
            
            # 调用 LLM 清洗
            questions = self._clean_with_llm()
            
            if not questions:
                self.error_occurred.emit("AI 清洗失败，未提取到题目")
                return
                
            self.progress_updated.emit(50, f"成功提取 {len(questions)} 道题目")
            
            # 返回结果
            self.progress_updated.emit(100, "清洗完成")
            self.result_ready.emit(questions)
            
        except Exception as e:
            self.error_occurred.emit(f"批量清洗失败: {str(e)}")
            
    def _clean_with_llm(self):
        """使用 LLM 清洗文本或图片"""
        try:
            headers = {
                "api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            system_prompt = """你是一个考试题目清洗助手。用户会给你题目内容（文本或图片），你需要：

1. 从内容中识别并提取出所有题目
2. 清洗并规范化每道题目的文本
3. 识别出每道题的题干、选项、答案

请以严格的 JSON 数组格式回复，不要添加任何其他内容：
[
    {
        "question": "清洗后的完整题干",
        "options": "规范化后的选项（如 A. xxx B. xxx C. xxx D. xxx）",
        "answer": "正确答案（如 B 或 AB）"
    },
    ...
]

注意：
- 如果是图片，请仔细识别图片中的所有文字内容
- 如果题目没有明确的选项，options 可以为空字符串
- 如果题目没有明确的答案，answer 可以为空字符串
- 保持题目原意，不要修改题目内容
- 去除多余的空格、换行、特殊字符
- 确保返回的是有效的 JSON 数组"""
            
            # 构建用户消息
            if self.image_base64:
                # 图片模式
                content = []
                
                if self.raw_text:
                    content.append({
                        "type": "text",
                        "text": f"请清洗以下题目内容：\n\n{self.raw_text}"
                    })
                
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{self.image_base64}"
                    }
                })
                
                if not self.raw_text:
                    content.append({
                        "type": "text",
                        "text": "请识别图片中的题目内容并清洗提取。"
                    })
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ]
            else:
                # 纯文本模式
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"请清洗以下题目内容：\n\n{self.raw_text}"}
                ]
            
            url = f"{self.api_base}/chat/completions"
            payload = {
                "model": self.model_name,
                "messages": messages,
                "max_completion_tokens": 4096
            }
            
            with httpx.Client(timeout=120.0) as client:
                response = client.post(url, json=payload, headers=headers)
                
                if response.status_code != 200:
                    # 如果是图片模式且失败，尝试降级到纯文本模式
                    if self.image_base64 and self.raw_text:
                        print("[WARN] 图片模式失败，尝试纯文本模式...")
                        messages = [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"请清洗以下题目内容：\n\n{self.raw_text}"}
                        ]
                        payload["messages"] = messages
                        response = client.post(url, json=payload, headers=headers)
                        
                response.raise_for_status()
                
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            # 解析 JSON
            return self._parse_json_response(content)
            
        except Exception as e:
            print(f"LLM 清洗失败: {e}")
            import traceback
            traceback.print_exc()
            return []
            
    def _parse_json_response(self, content):
        """解析 JSON 响应"""
        try:
            # 尝试直接解析
            result = json.loads(content)
            if isinstance(result, list):
                return result
            return [result]
        except json.JSONDecodeError:
            pass
            
        # 尝试提取 JSON 数组
        import re
        json_match = re.search(r'\[[\s\S]*\]', content)
        if json_match:
            try:
                result = json.loads(json_match.group())
                if isinstance(result, list):
                    return result
            except:
                pass
                
        # 尝试提取多个 JSON 对象
        json_objects = re.findall(r'\{[^}]+\}', content)
        if json_objects:
            results = []
            for obj_str in json_objects:
                try:
                    obj = json.loads(obj_str)
                    if "question" in obj:
                        results.append(obj)
                except:
                    continue
            return results
            
        return []


class BatchReviewService(QObject):
    """批量复盘服务"""
    
    # 信号
    progress_updated = Signal(int, str)  # (进度百分比, 状态文本)
    review_complete = Signal(int, int)  # (成功数量, 总数量)
    error_occurred = Signal(str)
    
    def __init__(self, db_service, embedding_service, parent=None):
        super().__init__(parent)
        self.db_service = db_service
        self.embedding_service = embedding_service
        
        # 从配置加载
        from config.settings import LLM_API_KEY, LLM_API_BASE_URL, LLM_MODEL_NAME
        
        self.api_key = LLM_API_KEY
        self.api_base = LLM_API_BASE_URL
        self.model_name = LLM_MODEL_NAME
        
        self.worker = None
        
    def start_review(self, raw_text, project="默认项目", image_base64=None):
        """开始批量复盘（支持图片）"""
        if not self.api_key:
            self.error_occurred.emit("LLM 服务未配置")
            return
            
        self.worker = BatchReviewWorker(
            self.api_key, self.api_base, self.model_name,
            raw_text, project, image_base64
        )
        self.worker.progress_updated.connect(self.progress_updated)
        self.worker.result_ready.connect(lambda questions: self._save_questions(questions, project))
        self.worker.error_occurred.connect(self.error_occurred)
        self.worker.start()
        
    def _save_questions(self, questions, project):
        """保存题目到数据库"""
        self.progress_updated.emit(60, "正在生成向量...")
        
        success_count = 0
        total_count = len(questions)
        
        # 批量生成向量
        texts = [q.get("question", "") for q in questions]
        vectors = self.embedding_service.encode_batch(texts) if self.embedding_service.is_configured() else []
        
        # 构建向量映射
        vector_map = {}
        for q_id, vector in vectors:
            vector_map[q_id] = vector
        
        # 保存到数据库
        for i, q in enumerate(questions):
            try:
                question = q.get("question", "").strip()
                options = q.get("options", "").strip()
                answer = q.get("answer", "").strip()
                
                if not question:
                    continue
                    
                # 获取向量
                vector_data = vector_map.get(i)
                
                # 插入数据库
                result = self.db_service.insert_question(
                    question=question,
                    options=options,
                    answer=answer,
                    source="batch_review",
                    project=project,
                    vector_data=vector_data
                )
                
                if result:
                    success_count += 1
                    
                # 更新进度
                progress = 60 + int(40 * (i + 1) / total_count)
                self.progress_updated.emit(progress, f"正在入库: {i + 1}/{total_count}")
                
            except Exception as e:
                print(f"保存题目失败: {e}")
                continue
                
        self.progress_updated.emit(100, f"完成：成功入库 {success_count}/{total_count} 道题目")
        self.review_complete.emit(success_count, total_count)