import numpy as np
import httpx
from PySide6.QtCore import QObject, Signal

class EmbeddingService(QObject):
    """向量检索服务：使用 Ollama 本地 Embedding（0 Token）"""
    
    # 信号
    error_occurred = Signal(str)
    status_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 从配置加载
        from config.settings import EMBEDDING_MODE, EMBEDDING_API_KEY, EMBEDDING_API_BASE_URL, EMBEDDING_MODEL_NAME
        
        self.mode = EMBEDDING_MODE  # local or cloud
        self.api_key = EMBEDDING_API_KEY
        self.api_base = EMBEDDING_API_BASE_URL
        self.model_name = EMBEDDING_MODEL_NAME
        
        self._last_error = None
        
    def is_configured(self):
        """检查是否已配置"""
        return bool(self.api_base and self.model_name)
        
    def is_available(self):
        """检查服务是否可用（已配置且可连接）"""
        return self.is_configured()
        
    def get_mode(self):
        """获取当前模式"""
        return self.mode
        
    def set_mode(self, mode):
        """设置模式"""
        self.mode = mode
        
    def get_status_text(self):
        """获取状态文本"""
        if not self.is_configured():
            return "未配置"
            
        if self.mode == "local":
            return f"本地 Ollama ({self.model_name})"
        else:
            return f"云端 API ({self.model_name})"
            
    def get_last_error(self):
        """获取最后一次错误"""
        return self._last_error
        
    def test_connection(self):
        """测试 Ollama 连接"""
        if not self.is_configured():
            return False, "未配置 Embedding API"
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            url = f"{self.api_base}/embeddings"
            payload = {
                "model": self.model_name,
                "input": ["测试连接"]
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
            data = response.json()
            
            if data.get("data"):
                vector_dim = len(data["data"][0]["embedding"])
                return True, f"连接成功！向量维度: {vector_dim}"
            else:
                return False, "返回数据格式错误"
                
        except httpx.ConnectError:
            return False, "Ollama 服务未启动，请在终端执行: ollama serve"
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return False, f"模型未找到，请在终端执行: ollama pull {self.model_name}"
            return False, f"HTTP 错误: {e.response.status_code}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"
            
    def encode_text(self, text):
        """将单个文本转换为向量"""
        if not self.is_configured():
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            url = f"{self.api_base}/embeddings"
            payload = {
                "model": self.model_name,
                "input": [text]
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
            data = response.json()
            
            if data.get("data"):
                vector = np.array(data["data"][0]["embedding"], dtype=np.float32)
                # 归一化
                norm = np.linalg.norm(vector)
                if norm > 0:
                    vector = vector / norm
                self._last_error = None
                return vector
                
            return None
            
        except httpx.ConnectError:
            self._last_error = "Ollama 服务未启动"
            print(f"[WARN] Embedding 失败: Ollama 服务未启动，请在终端执行: ollama serve")
            return None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                self._last_error = f"模型未找到: {self.model_name}"
                print(f"[WARN] Embedding 失败: 模型未找到，请在终端执行: ollama pull {self.model_name}")
            else:
                self._last_error = f"HTTP 错误: {e.response.status_code}"
                print(f"[WARN] Embedding 失败: HTTP {e.response.status_code}")
            return None
        except Exception as e:
            self._last_error = str(e)
            print(f"[WARN] Embedding 失败: {e}")
            return None
            
    def encode_batch(self, texts):
        """批量向量化"""
        if not self.is_configured():
            return []
            
        results = []
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            url = f"{self.api_base}/embeddings"
            payload = {
                "model": self.model_name,
                "input": texts
            }
            
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
            data = response.json()
            
            for i, item in enumerate(data.get("data", [])):
                vector = np.array(item["embedding"], dtype=np.float32)
                norm = np.linalg.norm(vector)
                if norm > 0:
                    vector = vector / norm
                results.append((i, vector))
                
            self._last_error = None
            return results
            
        except httpx.ConnectError:
            self._last_error = "Ollama 服务未启动"
            print(f"[WARN] 批量 Embedding 失败: Ollama 服务未启动")
            return []
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                self._last_error = f"模型未找到: {self.model_name}"
                print(f"[WARN] 批量 Embedding 失败: 模型未找到，请执行: ollama pull {self.model_name}")
            else:
                self._last_error = f"HTTP 错误: {e.response.status_code}"
            return []
        except Exception as e:
            self._last_error = str(e)
            print(f"[WARN] 批量 Embedding 失败: {e}")
            return []
            
    def search_similar_question(self, text, db_service, threshold=0.88, project=None):
        """搜索相似题目"""
        if not self.is_configured():
            return None
            
        try:
            query_embedding = self.encode_text(text)
            
            if query_embedding is None:
                return None
                
            questions = db_service.get_all_questions_with_vectors(project)
            
            if not questions:
                return None
                
            best_match = None
            best_score = 0
            
            for q in questions:
                if q["vector"] is None:
                    continue
                    
                score = np.dot(query_embedding, q["vector"])
                
                if score > best_score and score >= threshold:
                    best_score = score
                    best_match = {
                        "id": q["id"],
                        "question": q["question"],
                        "options": q["options"],
                        "answer": q["answer"],
                        "source": q["source"],
                        "project": q["project"],
                        "score": float(score)
                    }
                    
            return best_match
            
        except Exception as e:
            self.error_occurred.emit(f"向量检索失败: {str(e)}")
            return None
            
    def get_model_info(self):
        """获取模型信息"""
        return {
            "mode": self.mode,
            "is_configured": self.is_configured(),
            "api_base": self.api_base,
            "model_name": self.model_name,
            "status": self.get_status_text(),
            "last_error": self._last_error
        }