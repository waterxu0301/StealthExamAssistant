import json
import httpx
from PySide6.QtCore import QObject, Signal, QThread

class LLMWorker(QThread):
    """LLM 推理工作线程"""
    
    result_ready = Signal(dict)  # 结果信号
    error_occurred = Signal(str)  # 错误信号
    
    def __init__(self, api_key, api_base, model_name, question_text, image_base64=None, is_review=False):
        super().__init__()
        self.api_key = api_key
        self.api_base = api_base
        self.model_name = model_name
        self.question_text = question_text
        self.image_base64 = image_base64
        self.is_review = is_review
        
    def run(self):
        """执行 LLM 推理"""
        try:
            headers = {
                "api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            if self.is_review:
                messages = self._build_review_messages()
            else:
                messages = self._build_question_messages()
            
            url = f"{self.api_base}/chat/completions"
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "max_completion_tokens": 1024
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            result = self._parse_response(content)
            self.result_ready.emit(result)
            
        except httpx.TimeoutException:
            self.error_occurred.emit("请求超时，请检查网络连接")
        except httpx.HTTPStatusError as e:
            self.error_occurred.emit(f"HTTP 错误: {e.response.status_code}")
        except Exception as e:
            self.error_occurred.emit(f"LLM 推理失败: {str(e)}")
            
    def _build_question_messages(self):
        """构建题目分析消息"""
        messages = [
            {
                "role": "system",
                "content": """你是一个考试答题助手。用户会给你题目内容，你需要：
1. 分析题目
2. 给出建议答案
3. 简要说明推理过程

请以 JSON 格式回复：
{
    "answer": "建议答案（如选择题选项字母）",
    "reasoning": "简要推理过程"
}"""
            }
        ]
        
        if self.image_base64:
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{self.image_base64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": f"请分析这道题目并给出答案：\n{self.question_text}"
                    }
                ]
            })
        else:
            messages.append({
                "role": "user",
                "content": f"请分析这道题目并给出答案：\n{self.question_text}"
            })
            
        return messages
        
    def _build_review_messages(self):
        """构建复盘清洗消息（支持文本和图片）"""
        system_prompt = """你是一个考试题目清洗助手。用户会给你题目内容（文本或图片），你需要：

1. 从内容中识别并提取出规范的题目结构
2. 清洗并规范化文本
3. 识别出题干、选项、答案

请以严格的 JSON 格式回复，不要添加任何其他内容：
{
    "question": "清洗后的完整题干",
    "options": "规范化后的选项（如 A. xxx B. xxx C. xxx D. xxx）",
    "answer": "正确答案（如 B 或 AB）"
}

注意：
- 如果是图片，请仔细识别图片中的所有文字内容
- 如果没有明确的选项，options 可以为空字符串
- 如果没有明确的答案，answer 可以为空字符串
- 保持题目原意，不要修改题目内容
- 去除多余的空格、换行、特殊字符
- 如果图片中有多个题目，只提取第一个"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # 构建用户消息
        if self.image_base64:
            # 图片模式：使用 VLM 接口
            content = []
            
            if self.question_text:
                content.append({
                    "type": "text",
                    "text": f"请清洗以下题目内容：\n\n{self.question_text}"
                })
            
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{self.image_base64}"
                }
            })
            
            if not self.question_text:
                content.append({
                    "type": "text",
                    "text": "请识别图片中的题目内容并清洗提取。"
                })
            
            messages.append({"role": "user", "content": content})
        else:
            # 纯文本模式
            messages.append({
                "role": "user",
                "content": f"请清洗以下题目内容：\n\n{self.question_text}"
            })
        
        return messages
        
    def _parse_response(self, content):
        """解析 LLM 响应"""
        try:
            result = json.loads(content)
            return {
                "question": result.get("question", ""),
                "options": result.get("options", ""),
                "answer": result.get("answer", ""),
                "reasoning": result.get("reasoning", ""),
                "source": "llm"
            }
        except json.JSONDecodeError:
            import re
            
            json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    return {
                        "question": result.get("question", ""),
                        "options": result.get("options", ""),
                        "answer": result.get("answer", ""),
                        "reasoning": result.get("reasoning", ""),
                        "source": "llm"
                    }
                except:
                    pass
            
            return {
                "question": content[:100] if not self.is_review else "",
                "options": "",
                "answer": content[:50] if not self.is_review else "",
                "reasoning": content,
                "source": "llm"
            }


class LLMService(QObject):
    """大模型推理服务"""
    
    # 信号
    result_ready = Signal(dict)  # 结果信号
    review_result_ready = Signal(dict)  # 复盘结果信号
    error_occurred = Signal(str)  # 错误信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        from config.settings import LLM_API_KEY, LLM_API_BASE_URL, LLM_MODEL_NAME
        
        self.api_key = LLM_API_KEY
        self.api_base = LLM_API_BASE_URL
        self.model_name = LLM_MODEL_NAME
        
        self.worker = None
        
        if not self.api_key:
            print("警告: LLM_API_KEY 未配置")
            
    def is_configured(self):
        """检查是否已配置"""
        return bool(self.api_key and self.api_base)
        
    def get_status_text(self):
        """获取状态文本"""
        if not self.is_configured():
            return "未配置"
        return f"已配置 ({self.model_name})"
        
    def test_connection(self):
        """测试云端 API 连接"""
        if not self.is_configured():
            return False, "未配置 LLM API"
            
        try:
            headers = {
                "api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            url = f"{self.api_base}/chat/completions"
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": "Hi"}
                ],
                "max_tokens": 10
            }
            
            with httpx.Client(timeout=15.0) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
            data = response.json()
            
            if data.get("choices"):
                reply = data["choices"][0]["message"]["content"][:50]
                return True, f"连接成功！模型回复: {reply}..."
            else:
                return False, "返回数据格式错误"
                
        except httpx.ConnectError:
            return False, "无法连接到 API 服务器，请检查网络"
        except httpx.TimeoutException:
            return False, "连接超时，请检查网络或 API 地址"
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return False, "API Key 无效，请检查配置"
            elif e.response.status_code == 404:
                return False, f"模型未找到: {self.model_name}"
            return False, f"HTTP 错误: {e.response.status_code}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"
        
    def analyze_question(self, question_text, image_base64=None):
        """分析题目并返回答案"""
        if not self.is_configured():
            self.error_occurred.emit("LLM 服务未配置")
            return
            
        self.worker = LLMWorker(
            self.api_key,
            self.api_base,
            self.model_name,
            question_text,
            image_base64,
            is_review=False
        )
        
        self.worker.result_ready.connect(self.result_ready)
        self.worker.error_occurred.connect(self.error_occurred)
        self.worker.start()
        
    def analyze_question_for_review(self, question_text, project="默认项目", image_base64=None):
        """分析题目用于复盘清洗（支持图片）"""
        if not self.is_configured():
            self.error_occurred.emit("LLM 服务未配置")
            return
            
        self.worker = LLMWorker(
            self.api_key,
            self.api_base,
            self.model_name,
            question_text,
            image_base64,
            is_review=True
        )
        
        # 包装结果以包含项目信息
        def on_result(result):
            result["project"] = project
            self.review_result_ready.emit(result)
            
        self.worker.result_ready.connect(on_result)
        self.worker.error_occurred.connect(self.error_occurred)
        self.worker.start()
        
    def analyze_question_sync(self, question_text, image_base64=None):
        """同步分析题目（用于测试）"""
        if not self.is_configured():
            return {"error": "LLM 服务未配置"}
            
        try:
            headers = {
                "api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            messages = [
                {
                    "role": "system",
                    "content": """你是一个考试答题助手。用户会给你题目内容，你需要：
1. 分析题目
2. 给出建议答案
3. 简要说明推理过程

请以 JSON 格式回复：
{
    "answer": "建议答案（如选择题选项字母）",
    "reasoning": "简要推理过程"
}"""
                },
                {
                    "role": "user",
                    "content": f"请分析这道题目并给出答案：\n{question_text}"
                }
            ]
            
            url = f"{self.api_base}/chat/completions"
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "max_completion_tokens": 1024
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            return self._parse_response_sync(content)
            
        except Exception as e:
            return {"error": str(e)}
            
    def _parse_response_sync(self, content):
        """解析 LLM 响应"""
        try:
            result = json.loads(content)
            return {
                "answer": result.get("answer", ""),
                "reasoning": result.get("reasoning", ""),
                "source": "llm"
            }
        except json.JSONDecodeError:
            import re
            
            json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    return {
                        "answer": result.get("answer", ""),
                        "reasoning": result.get("reasoning", ""),
                        "source": "llm"
                    }
                except:
                    pass
            
            return {
                "answer": content[:100],
                "reasoning": content,
                "source": "llm"
            }