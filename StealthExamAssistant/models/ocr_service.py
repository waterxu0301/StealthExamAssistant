import numpy as np
import cv2
from PySide6.QtCore import QThread, Signal

class OCRService(QThread):
    """OCR 文本提取服务"""
    
    ocr_result = Signal(str)  # OCR 结果信号
    ocr_error = Signal(str)  # 错误信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ocr_engine = None
        self.image = None
        self._initialize_ocr()
        
    def _initialize_ocr(self):
        """初始化 RapidOCR 引擎"""
        try:
            from rapidocr_onnxruntime import RapidOCR
            self.ocr_engine = RapidOCR()
            print("[OCR] RapidOCR 初始化成功")
        except ImportError:
            print("[OCR] 警告: rapidocr_onnxruntime 未安装")
            self.ocr_engine = None
        except Exception as e:
            print(f"[OCR] 初始化失败: {e}")
            self.ocr_engine = None
            
    def process_image(self, image):
        """处理图像进行 OCR"""
        if self.ocr_engine is None:
            self.ocr_error.emit("OCR 引擎未初始化")
            return
            
        self.image = image
        self.start()
        
    def run(self):
        """执行 OCR 识别"""
        if self.image is None or self.ocr_engine is None:
            print("[OCR] 引擎未初始化或图像为空")
            return
            
        try:
            h, w = self.image.shape[:2]
            print(f"[OCR] 开始识别，图像尺寸: {w}x{h}")
            
            # 直接使用原始图像进行 OCR（不预处理）
            result, elapse = self.ocr_engine(self.image)
            
            if result is None or len(result) == 0:
                print("[OCR] 未识别到文字")
                self.ocr_result.emit("")
                return
                
            # 提取文本
            texts = []
            for line in result:
                if line and len(line) >= 2:
                    text = line[1]  # 文本内容
                    confidence = float(line[2])  # 置信度（转换为浮点数）
                    print(f"[OCR] 识别: '{text[:50]}' (置信度: {confidence:.2f})")
                    if confidence > 0.3:
                        texts.append(text)
            
            # 合并文本
            full_text = "\n".join(texts)
            
            if full_text.strip():
                print(f"[OCR] 识别成功，共 {len(texts)} 行文字")
                self.ocr_result.emit(full_text)
            else:
                print("[OCR] 无有效文字")
                self.ocr_result.emit("")
                
        except Exception as e:
            print(f"[OCR] 识别错误: {e}")
            import traceback
            traceback.print_exc()
            self.ocr_error.emit(f"OCR 识别错误: {str(e)}")
            
    def is_available(self):
        """检查 OCR 是否可用"""
        return self.ocr_engine is not None