import os
import numpy as np
import cv2
import mss
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QGuiApplication


class VisionService(QObject):
    """视觉服务：单次截屏触发（已废弃自动轮询）"""
    
    # 信号定义
    question_detected = Signal(np.ndarray)  # 检测到新题目，发送图像帧
    status_changed = Signal(str)  # 状态变化信号
    error_occurred = Signal(str)  # 错误信号
    capture_started = Signal()  # 截图开始信号（用于隐藏覆盖层）
    capture_finished = Signal()  # 截图结束信号（用于显示覆盖层）
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.region = None  # 监控区域 {x, y, width, height}
        self.is_monitoring = False  # 监控状态标记
        
        # Retina 缩放因子
        self.device_pixel_ratio = self._get_device_pixel_ratio()
        print(f"[Vision] 设备像素比: {self.device_pixel_ratio}")
        
        # 调试图像保存目录
        self.debug_dir = "./debug"
        os.makedirs(self.debug_dir, exist_ok=True)
        
    def _get_device_pixel_ratio(self):
        """获取设备像素比（Retina 缩放因子）"""
        try:
            screen = QGuiApplication.primaryScreen()
            if screen:
                ratio = screen.devicePixelRatio()
                return ratio
        except Exception as e:
            print(f"[Vision] 获取设备像素比失败: {e}")
        return 1.0
        
    def set_region(self, region):
        """设置监控区域"""
        self.region = region
        print(f"[Vision] 区域已设置: x={region['x']}, y={region['y']}, w={region['width']}, h={region['height']}")
        self.status_changed.emit("区域已设置，按 Ctrl+Shift+A 识题")
        
    def start_monitoring(self):
        """开始监控（标记状态）"""
        if self.region is None:
            self.error_occurred.emit("请先选择监控区域")
            return
        self.is_monitoring = True
        print("[Vision] 已就绪，等待快捷键触发")
        self.status_changed.emit("就绪 (按 Ctrl+Shift+A 识题)")
        
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        print("[Vision] 已停止")
        self.status_changed.emit("已停止")
        
    def capture_and_recognize(self):
        """单次截屏并触发识别（快捷键触发）"""
        if self.region is None:
            self.error_occurred.emit("请先选择监控区域")
            return
            
        if not self.is_monitoring:
            self.error_occurred.emit("请先启动监控")
            return
            
        print("\n[Vision] 快捷键触发，开始截屏识别...")
        self.status_changed.emit("正在截屏识别...")
        
        try:
            # 发送截图开始信号（隐藏覆盖层）
            self.capture_started.emit()
            
            # 使用 mss 截屏
            with mss.mss() as sct:
                # 直接使用逻辑坐标
                monitor = {
                    "top": self.region["y"],
                    "left": self.region["x"],
                    "width": self.region["width"],
                    "height": self.region["height"]
                }
                
                # 截取屏幕
                screenshot = sct.grab(monitor)
                
                # 转换为 numpy 数组
                frame = np.array(screenshot)
                
                # 转换为 BGR 格式（OpenCV 标准）
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
            # 发送截图结束信号（显示覆盖层）
            self.capture_finished.emit()
            
            # 保存调试图像
            debug_path = os.path.join(self.debug_dir, "latest_capture.png")
            cv2.imwrite(debug_path, frame)
            print(f"[Vision] 截图已保存: {debug_path} (尺寸: {frame.shape[1]}x{frame.shape[0]})")
            
            # 触发识别管线
            self.question_detected.emit(frame)
            self.status_changed.emit("正在识别...")
            
        except Exception as e:
            print(f"[Vision] 截屏失败: {e}")
            self.error_occurred.emit(f"截屏失败: {str(e)}")
            self.capture_finished.emit()  # 确保覆盖层恢复
