import json
import httpx
from PySide6.QtCore import QObject, Signal, QThread

class MultimodalWorker(QThread):
    """多模态解析工作线程"""
    
    result_ready = Signal(dict)  # 结果信号
    error_occurred = Signal(str)  # 错误信号
    status_changed = Signal(str)  # 状态变化
    
    def __init__(self, text_content, image_base64, config):
        super().__init__()
        self.text_content = text_content
        self.image_base64 = image_base64
        self.config = config
        
    def run(self):
        """执行多模态解析"""
        try:
            if self.image_base64:
                # 图片模式：优先本地 Ollama，降级到云端
                result = self._parse_with_vlm()
            else:
                # 文本模式：使用 LLM 清洗
                result = self._parse_with_llm()
                
            self.result_ready.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(f"解析失败: {str(e)}")
            
    def _parse_with_vlm(self):
        """使用 VLM 解析图片"""
        # 优先尝试本地 Ollama 多模态模型
        if self.config.get('ollama_multimodal_enabled'):
            try:
                self.status_changed.emit("正在使用本地 Ollama 多模态模型...")
                return self._call_ollama_multimodal()
            except Exception as e:
                print(f"[WARN] 本地 Ollama 多模态失败: {e}")
                self.status_changed.emit("本地模型失败，降级到云端 VLM...")
        
        # 降级到云端 VLM
        if self.config.get('cloud_api_key'):
            self.status_changed.emit("正在使用云端 VLM...")
            return self._call_cloud_vlm()
            
        raise Exception("无可用的 VLM 服务")
        
    def _call_ollama_multimodal(self):
        """调用本地 Ollama 多模态模型"""
        ollama_base = self.config.get('ollama_base_url', 'http://127.0.0.1:11434')
        ollama_model = self.config.get('ollama_multimodal_model', 'llava:7b')
        
        # 构建提示词
        prompt = self._build_multimodal_prompt()
        
        # 调用 Ollama API
        url = f"{ollama_base}/api/generate"
        payload = {
            "model": ollama_model,
            "prompt": prompt,
            "images": [self.image_base64],
            "stream": False
        }
        
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            
        data = response.json()
        content = data.get("response", "")
        
        return self._parse_json_response(content)
        
    def _call_cloud_vlm(self):
        """调用云端 VLM"""
        api_key = self.config.get('cloud_api_key')
        api_base = self.config.get('cloud_api_base')
        model_name = self.config.get('cloud_model_name')
        
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }
        
        # 构建消息
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": self._build_multimodal_content()}
        ]
        
        url = f"{api_base}/chat/completions"
        payload = {
            "model": model_name,
            "messages": messages,
            "max_completion_tokens": 2048
        }
        
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        return self._parse_json_response(content)
        
    def _parse_with_llm(self):
        """使用 LLM 解析文本"""
        # 优先尝试本地 Ollama
        if self.config.get('ollama_enabled'):
            try:
                self.status_changed.emit("正在使用本地 Ollama...")
                return self._call_ollama_llm()
            except Exception as e:
                print(f"[WARN] 本地 Ollama 失败: {e}")
                self.status_changed.emit("本地模型失败，降级到云端 LLM...")
        
        # 降级到云端 LLM
        if self.config.get('cloud_api_key'):
            self.status_changed.emit("正在使用云端 LLM...")
            return self._call_cloud_llm()
            
        raise Exception("无可用的 LLM 服务")
        
    def _call_ollama_llm(self):
        """调用本地 Ollama LLM"""
        ollama_base = self.config.get('ollama_base_url', 'http://127.0.0.1:11434')
        ollama_model = self.config.get('ollama_llm_model', 'qwen2.5:7b')
        
        prompt = f"{self._get_system_prompt()}\n\n请清洗以下题目内容：\n\n{self.text_content}"
        
        url = f"{ollama_base}/api/generate"
        payload = {
            "model": ollama_model,
            "prompt": prompt,
            "stream": False
        }
        
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            
        data = response.json()
        content = data.get("response", "")
        
        return self._parse_json_response(content)
        
    def _call_cloud_llm(self):
        """调用云端 LLM"""
        api_key = self.config.get('cloud_api_key')
        api_base = self.config.get('cloud_api_base')
        model_name = self.config.get('cloud_model_name')
        
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }
        
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": f"请清洗以下题目内容：\n\n{self.text_content}"}
        ]
        
        url = f"{api_base}/chat/completions"
        payload = {
            "model": model_name,
            "messages": messages,
            "max_completion_tokens": 2048
        }
        
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        return self._parse_json_response(content)
        
    def _get_system_prompt(self):
        """获取系统提示词"""
        return """你是一个考试题目清洗助手。用户会给你题目内容（文本或图片），你需要：

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
        
    def _build_multimodal_prompt(self):
        """构建多模态提示词"""
        if self.text_content:
            return f"请识别图片中的题目内容，并结合以下文本进行清洗提取：\n\n{self.text_content}"
        else:
            return "请识别图片中的题目内容并清洗提取。"
            
    def _build_multimodal_content(self):
        """构建多模态内容"""
        content = []
        
        if self.text_content:
            content.append({
                "type": "text",
                "text": f"请清洗以下题目内容：\n\n{self.text_content}"
            })
        
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{self.image_base64}"
            }
        })
        
        if not self.text_content:
            content.append({
                "type": "text",
                "text": "请识别图片中的题目内容并清洗提取。"
            })
        
        return content
        
    def _parse_json_response(self, content):
        """解析 JSON 响应"""
        try:
            result = json.loads(content)
            if isinstance(result, list):
                return {"questions": result, "source": "ai"}
            return {"questions": [result], "source": "ai"}
        except json.JSONDecodeError:
            import re
            
            # 尝试提取 JSON 数组
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    return {"questions": result, "source": "ai"}
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
                if results:
                    return {"questions": results, "source": "ai"}
                    
            # 返回原始文本
            return {"questions": [], "raw_text": content, "source": "ai"}


class MultimodalService(QObject):
    """多模态服务：支持文本和图片的智能解析"""
    
    # 信号
    result_ready = Signal(dict)
    error_occurred = Signal(str)
    status_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 从配置加载
        from config.settings import (
            LLM_API_KEY, LLM_API_BASE_URL, LLM_MODEL_NAME,
            EMBEDDING_API_BASE_URL, EMBEDDING_MODEL_NAME
        )
        
        self.config = {
            # 云端配置
            'cloud_api_key': LLM_API_KEY,
            'cloud_api_base': LLM_API_BASE_URL,
            'cloud_model_name': LLM_MODEL_NAME,
            
            # 本地 Ollama 配置
            'ollama_base_url': EMBEDDING_API_BASE_URL.replace('/v1', ''),
            'ollama_enabled': True,
            
            # Ollama 多模态模型（需要用户自行安装）
            'ollama_multimodal_enabled': False,
            'ollama_multimodal_model': 'llava:7b',
            
            # Ollama 文本模型
            'ollama_llm_model': EMBEDDING_MODEL_NAME,
        }
        
        self.worker = None
        
        # 检测本地 Ollama 多模态模型
        self._detect_ollama_multimodal()
        
    def _detect_ollama_multimodal(self):
        """检测本地 Ollama 多模态模型"""
        try:
            import httpx
            
            ollama_base = self.config['ollama_base_url']
            url = f"{ollama_base}/api/tags"
            
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url)
                response.raise_for_status()
                
            data = response.json()
            models = [m['name'] for m in data.get('models', [])]
            
            # 检查多模态模型
            multimodal_models = ['llava', 'minicpm-v', 'moondream', 'bakllava']
            for model in models:
                for mm in multimodal_models:
                    if mm in model.lower():
                        self.config['ollama_multimodal_enabled'] = True
                        self.config['ollama_multimodal_model'] = model
                        print(f"[OK] 检测到本地多模态模型: {model}")
                        return
                        
            print("[INFO] 未检测到本地多模态模型，将使用云端 VLM")
            
        except Exception as e:
            print(f"[INFO] 检测 Ollama 多模态模型失败: {e}")
            
    def get_config(self):
        """获取配置"""
        return self.config.copy()
        
    def parse_file(self, text_content, image_base64):
        """解析文件"""
        self.worker = MultimodalWorker(text_content, image_base64, self.config)
        self.worker.result_ready.connect(self.result_ready)
        self.worker.error_occurred.connect(self.error_occurred)
        self.worker.status_changed.connect(self.status_changed)
        self.worker.start()
        
    def get_status(self):
        """获取服务状态"""
        status = {
            'cloud': bool(self.config.get('cloud_api_key')),
            'ollama': self.config.get('ollama_enabled', False),
            'ollama_multimodal': self.config.get('ollama_multimodal_enabled', False),
            'multimodal_model': self.config.get('ollama_multimodal_model', '未安装')
        }
        return status