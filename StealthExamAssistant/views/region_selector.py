import platform
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QRect, Signal, QPoint, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QCursor, QGuiApplication

# 平台检测
PLATFORM = platform.system()

if PLATFORM == "Darwin":
    try:
        import objc
        MACOS_OBJC_AVAILABLE = True
    except ImportError:
        MACOS_OBJC_AVAILABLE = False
elif PLATFORM == "Windows":
    import ctypes

class RegionSelector(QWidget):
    """全屏半透明遮罩，用于框选监控区域"""
    
    region_selected = Signal(dict)  # 信号：区域选择完成
    selection_cancelled = Signal()  # 信号：选择取消
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 窗口设置：全屏、无边框、置顶
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus  # 不抢焦点
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        
        # 获取全屏尺寸
        screen = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        # 选择状态
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.is_selecting = False
        self.selected_rect = QRect()
        
        # 延迟设置置顶（等待窗口创建完成）
        QTimer.singleShot(100, self._force_stay_on_top)
        
    def _force_stay_on_top(self):
        """强制窗口置顶（macOS 终极置顶）"""
        if PLATFORM == "Darwin" and MACOS_OBJC_AVAILABLE:
            try:
                ns_view = objc.objc_object(c_void_p=self.winId().__int__())
                ns_window = ns_view.window()
                if ns_window:
                    # 使用系统级最高遮罩层 (2000)
                    ns_window.setLevel_(2000)
                    # 设置集合行为：在所有空间和全屏应用上显示
                    # 1 = NSWindowCollectionBehaviorCanJoinAllSpaces
                    # 16 = NSWindowCollectionBehaviorFullScreenAuxiliary
                    ns_window.setCollectionBehavior_(1 | 16)
                    print("[RegionSelector] macOS 终极置顶已启用 (Level 2000)")
            except Exception as e:
                print(f"[RegionSelector] macOS 置顶设置失败: {e}")
        elif PLATFORM == "Windows":
            try:
                hwnd = int(self.winId())
                # HWND_TOPMOST = -1
                ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002)
                print("[RegionSelector] Windows 置顶已启用")
            except Exception as e:
                print(f"[RegionSelector] Windows 置顶设置失败: {e}")
                
    def showEvent(self, event):
        """窗口显示时确保置顶"""
        super().showEvent(event)
        self._ensure_stay_on_top()
        
    def _ensure_stay_on_top(self):
        """确保窗口置顶"""
        if PLATFORM == "Darwin" and MACOS_OBJC_AVAILABLE:
            try:
                ns_view = objc.objc_object(c_void_p=self.winId().__int__())
                ns_window = ns_view.window()
                if ns_window:
                    ns_window.setLevel_(2000)
                    ns_window.setCollectionBehavior_(1 | 16)
            except Exception as e:
                print(f"[RegionSelector] 置顶确认失败: {e}")
        elif PLATFORM == "Windows":
            try:
                hwnd = int(self.winId())
                ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002)
            except Exception as e:
                print(f"[RegionSelector] 置顶确认失败: {e}")
        
    def paintEvent(self, event):
        """绘制半透明遮罩和选择框"""
        painter = QPainter(self)
        
        # 绘制半透明背景
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        
        if self.is_selecting or not self.selected_rect.isNull():
            # 清除选择区域（透明）
            if not self.selected_rect.isNull():
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                painter.fillRect(self.selected_rect, Qt.GlobalColor.transparent)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            
            # 绘制选择框边框
            pen = QPen(QColor(0, 150, 136), 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawRect(self.selected_rect)
            
            # 绘制尺寸提示
            if not self.selected_rect.isNull():
                size_text = f"{self.selected_rect.width()} x {self.selected_rect.height()}"
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(
                    self.selected_rect.bottomLeft() + QPoint(5, 20),
                    size_text
                )
                
        # 绘制提示文字
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "拖拽鼠标框选题目区域 | 按 ESC 取消"
        )
        
        painter.end()
        
    def mousePressEvent(self, event):
        """鼠标按下：开始选择"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.is_selecting = True
            self.selected_rect = QRect()
            self.update()
            
    def mouseMoveEvent(self, event):
        """鼠标移动：更新选择框"""
        if self.is_selecting:
            self.end_point = event.pos()
            self.selected_rect = QRect(self.start_point, self.end_point).normalized()
            self.update()
            
    def mouseReleaseEvent(self, event):
        """鼠标释放：完成选择"""
        if event.button() == Qt.MouseButton.LeftButton and self.is_selecting:
            self.is_selecting = False
            self.end_point = event.pos()
            self.selected_rect = QRect(self.start_point, self.end_point).normalized()
            
            # 最小尺寸检查
            if self.selected_rect.width() > 50 and self.selected_rect.height() > 50:
                # 发送选择结果
                region = {
                    "x": self.selected_rect.x(),
                    "y": self.selected_rect.y(),
                    "width": self.selected_rect.width(),
                    "height": self.selected_rect.height()
                }
                self.region_selected.emit(region)
                self.close()
            else:
                # 选择区域太小，重置
                self.selected_rect = QRect()
                self.update()
                
    def keyPressEvent(self, event):
        """按键处理"""
        if event.key() == Qt.Key.Key_Escape:
            self.selection_cancelled.emit()
            self.close()
        super().keyPressEvent(event)
