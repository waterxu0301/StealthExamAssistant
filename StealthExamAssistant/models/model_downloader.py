import os
import hashlib
from pathlib import Path
from PySide6.QtCore import QThread, Signal

class ModelDownloadThread(QThread):
    """模型下载线程：带进度条和详细状态"""
    
    # 信号
    progress_updated = Signal(int, str)  # (百分比, 状态文本)
    file_downloading = Signal(str)  # 当前下载的文件名
    download_complete = Signal(bool, str)  # (是否成功, 消息)
    
    # bge-micro-v2 模型文件配置
    MODEL_FILES = {
        "model.onnx": {
            "url": "https://huggingface.co/seeklhy/bge-micro-v2/resolve/main/onnx/model.onnx",
            "mirror_url": "https://hf-mirror.com/seeklhy/bge-micro-v2/resolve/main/onnx/model.onnx",
            "size": 33_000_000,  # 约 33MB
        },
        "tokenizer.json": {
            "url": "https://huggingface.co/seeklhy/bge-micro-v2/resolve/main/tokenizer.json",
            "mirror_url": "https://hf-mirror.com/seeklhy/bge-micro-v2/resolve/main/tokenizer.json",
            "size": 2_000_000,  # 约 2MB
        },
        "config.json": {
            "url": "https://huggingface.co/seeklhy/bge-micro-v2/resolve/main/config.json",
            "mirror_url": "https://hf-mirror.com/seeklhy/bge-micro-v2/resolve/main/config.json",
            "size": 1_000,  # 约 1KB
        }
    }
    
    def __init__(self, model_path="./models/bge-micro-v2", parent=None):
        super().__init__(parent)
        self.model_path = Path(model_path)
        self.is_cancelled = False
        
    def run(self):
        """执行下载"""
        try:
            import httpx
            
            # 设置 HuggingFace 镜像
            os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
            
            # 创建目录
            self.model_path.mkdir(parents=True, exist_ok=True)
            
            # 计算总大小
            total_size = sum(f["size"] for f in self.MODEL_FILES.values())
            downloaded_size = 0
            
            # 下载每个文件
            for filename, file_info in self.MODEL_FILES.items():
                if self.is_cancelled:
                    self.download_complete.emit(False, "下载已取消")
                    return
                    
                filepath = self.model_path / filename
                
                # 检查文件是否已存在且完整
                if filepath.exists() and filepath.stat().st_size > 0:
                    file_size = filepath.stat().st_size
                    downloaded_size += file_size
                    progress = int(downloaded_size * 100 / total_size)
                    self.progress_updated.emit(progress, f"文件已存在: {filename}")
                    continue
                    
                # 下载文件
                self.file_downloading.emit(filename)
                success = self._download_file(filename, file_info, filepath)
                
                if not success:
                    self.download_complete.emit(False, f"下载失败: {filename}")
                    return
                    
                # 更新进度
                file_size = filepath.stat().st_size if filepath.exists() else 0
                downloaded_size += file_size
                progress = int(downloaded_size * 100 / total_size)
                self.progress_updated.emit(progress, f"下载完成: {filename}")
                
            # 验证文件完整性
            self.progress_updated.emit(100, "验证文件完整性...")
            
            if self._verify_files():
                self.download_complete.emit(True, "模型下载完成！")
            else:
                self.download_complete.emit(False, "文件验证失败，请重试")
                
        except ImportError:
            self.download_complete.emit(False, "缺少 httpx 依赖")
        except Exception as e:
            self.download_complete.emit(False, f"下载异常: {str(e)}")
            
    def _download_file(self, filename, file_info, filepath):
        """下载单个文件"""
        import httpx
        
        # 尝试主 URL，失败则使用镜像
        urls = [file_info["url"], file_info["mirror_url"]]
        
        for url in urls:
            try:
                self.progress_updated.emit(-1, f"正在下载 {filename}...")
                
                with httpx.Client(timeout=120.0, follow_redirects=True) as client:
                    with client.stream("GET", url) as response:
                        response.raise_for_status()
                        
                        total_size = int(response.headers.get("content-length", 0))
                        downloaded = 0
                        
                        with open(filepath, 'wb') as f:
                            for chunk in response.iter_bytes(chunk_size=8192):
                                if self.is_cancelled:
                                    filepath.unlink(missing_ok=True)
                                    return False
                                    
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                # 更新进度
                                if total_size > 0:
                                    percent = int(downloaded * 100 / total_size)
                                    self.progress_updated.emit(
                                        percent, 
                                        f"下载 {filename}: {percent}%"
                                    )
                                    
                return True
                
            except Exception as e:
                print(f"下载失败 ({url}): {e}")
                continue
                
        return False
        
    def _verify_files(self):
        """验证文件完整性"""
        required_files = ["model.onnx", "tokenizer.json"]
        
        for filename in required_files:
            filepath = self.model_path / filename
            
            if not filepath.exists():
                print(f"文件不存在: {filename}")
                return False
                
            if filepath.stat().st_size == 0:
                print(f"文件为空: {filename}")
                return False
                
        return True
        
    def cancel(self):
        """取消下载"""
        self.is_cancelled = True