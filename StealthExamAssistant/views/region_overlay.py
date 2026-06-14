import platform
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QPen, QColor

PLATFORM = platform.system()

if PLATFORM == "Darwin":
    try:
        import objc
    except ImportError:
        objc = None

class RegionOverlay(QWidget):
    """区域覆盖窗口：显示虚线框标识监控区域"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.region = None
        
        # 窗口设置：全屏、无边框、透明、穿透鼠标
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput  # 鼠标穿透
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # 全屏显示
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
    def set_region(self, region):
        """设置显示区域"""
        self.region = region
        self.update()
        
    def clear_region(self):
        """清除显示区域"""
        self.region = None
        self.update()
        
    def paintEvent(self, event):
        """绘制虚线框"""
        if self.region is None:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 创建矩形区域
        rect = QRect(
            self.region["x"],
            self.region["y"],
            self.region["width"],
            self.region["height"]
        )
        
        # 绘制虚线边框
        pen = QPen(QColor(0, 188, 212, 200), 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawRect(rect)
        
        # 绘制半透明填充
        painter.fillRect(rect, QColor(0, 188, 212, 20))
        
        painter.end()
        
    def showEvent(self, event):
        """窗口显示时设置置顶"""
        super().showEvent(event)
        self._setup_stay_on_top()
        
    def _setup_stay_on_top(self):
        """设置窗口置顶"""
        if PLATFORM == "Darwin" and objc:
            try:
                ns_view = objc.objc_object(c_void_p=self.winId().__int__())
                ns_window = ns_view.window()
                if ns_window:
                    # 使用较高的窗口级别但不过高
                    ns_window.setLevel_(100)  # NSScreenSaverWindowLevel
                    # 设置集合行为
                    ns_window.setCollectionBehavior_(1 | 16)
                    print("[Overlay] macOS 置顶已启用")
            except Exception as e:
                print(f"[Overlay] macOS 置顶设置失败: {e}")