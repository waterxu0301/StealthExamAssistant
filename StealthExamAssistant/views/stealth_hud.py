import sys
import platform
import numpy as np
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QApplication, QSizePolicy,
                               QMessageBox, QSlider)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, Slot, Signal, QTimer
from PySide6.QtGui import QColor, QPainter, QBrush, QPen

# Platform-specific imports with strict validation
PLATFORM = platform.system()

if PLATFORM == "Windows":
    import ctypes
elif PLATFORM == "Darwin":
    try:
        import objc
        from Cocoa import NSWindow, NSApplication
        from AppKit import NSWindowSharingNone
        MACOS_OBJC_AVAILABLE = True
    except ImportError as e:
        MACOS_OBJC_AVAILABLE = False
        print(f"[FATAL] pyobjc not installed! macOS anti-capture will NOT work.")

from views.region_selector import RegionSelector
from views.region_overlay import RegionOverlay
from models.vision_service import VisionService
from models.ocr_service import OCRService
from models.database_service import DatabaseService
from models.embedding_service import EmbeddingService
from models.llm_service import LLMService
from controllers.search_controller import SearchController


class StealthHUD(QWidget):
    """隐形 HUD：极简悬浮窗，只显示最终结果"""
    
    # 信号
    return_to_main = Signal()  # 返回主程序
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("HUD")
        self.setFixedSize(320, 240)  # 增加高度以容纳题目显示
        
        # 加载配置
        from config.settings import HUD_OPACITY
        self.default_opacity = HUD_OPACITY
        
        # 检查 macOS 防录屏依赖
        if PLATFORM == "Darwin" and not MACOS_OBJC_AVAILABLE:
            QMessageBox.critical(
                None,
                "致命错误：缺少 pyobjc",
                "macOS 防录屏功能需要 pyobjc 库！\n\n"
                "请在终端运行以下命令安装：\n\n"
                "pip install pyobjc pyobjc-framework-Cocoa\n\n"
                "安装后重新启动程序。"
            )
            sys.exit(1)
        
        # 状态变量
        self.is_monitoring = False
        self.is_locked = False  # 锁定模式
        
        # 区域覆盖窗口
        self.region_overlay = RegionOverlay()
        
        # 初始化服务
        self._init_services()
        
        # 窗口标志设置
        self._setup_window_flags()
        
        # UI 初始化
        self._setup_ui()
        
        # 防录屏设置
        self._setup_anti_capture()
        
        # 连接信号
        self._connect_signals()
        
        # 区域选择器
        self.region = None
        self.region_selector = None
        
    def _init_services(self):
        """初始化服务"""
        self.db_service = DatabaseService("./data/exam_data.db", self)
        self.embedding_service = EmbeddingService(self)
        self.llm_service = LLMService(self)
        
        self.search_controller = SearchController(
            self.db_service,
            self.embedding_service,
            self.llm_service,
            self
        )
        
        self.ocr_service = OCRService(self)
        self.vision_service = VisionService(self)
        
    def _setup_window_flags(self):
        """配置窗口标志：防录屏 + 防焦点抢占 + 强制置顶"""
        flags = (
            Qt.WindowType.WindowStaysOnTopHint |  # 强制置顶
            Qt.WindowType.FramelessWindowHint |   # 无边框
            Qt.WindowType.Tool |                  # 任务栏隐藏
            Qt.WindowType.WindowDoesNotAcceptFocus  # 彻底切断焦点抢占
        )
        
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # macOS 特殊属性
        if PLATFORM == "Darwin":
            self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow)
        
        # 强制置顶（macOS 特殊处理）
        if PLATFORM == "Darwin":
            QTimer.singleShot(100, self._force_stay_on_top)
            
    def _force_stay_on_top(self):
        """强制窗口置顶（macOS）"""
        try:
            ns_view = objc.objc_object(c_void_p=self.winId().__int__())
            ns_window = ns_view.window()
            if ns_window:
                # 使用系统级最高遮罩层 (2000)
                # 这个级别足够高，可以覆盖所有应用包括全屏应用
                ns_window.setLevel_(2000)
                
                # 设置集合行为：在所有空间和全屏应用上显示
                # 1 = NSWindowCollectionBehaviorCanJoinAllSpaces
                # 16 = NSWindowCollectionBehaviorFullScreenAuxiliary
                ns_window.setCollectionBehavior_(1 | 16)
                
                print("[HUD] macOS 置顶已启用 (Level 2000 + AllSpaces)")
        except Exception as e:
            print(f"[HUD] macOS 置顶设置失败: {e}")
        
    def _setup_ui(self):
        """设置极简 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # 标题栏（可拖拽）
        title_bar = QFrame()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(24)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(8, 0, 8, 0)
        
        # 状态指示灯
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color: #F44336; font-size: 10px;")  # 红色 = 未监控
        title_bar_layout.addWidget(self.status_dot)
        
        title_label = QLabel("HUD")
        title_label.setStyleSheet("color: #aaaaaa; font-size: 10px;")
        title_bar_layout.addWidget(title_label)
        
        title_bar_layout.addStretch()
        
        # 返回主程序按钮
        return_btn = QPushButton("⌂")
        return_btn.setFixedSize(20, 20)
        return_btn.setObjectName("returnButton")
        return_btn.setToolTip("返回主程序")
        return_btn.clicked.connect(self._return_to_main)
        title_bar_layout.addWidget(return_btn)
        
        # 框选按钮
        select_btn = QPushButton("□")
        select_btn.setFixedSize(20, 20)
        select_btn.setObjectName("selectButton")
        select_btn.setToolTip("框选区域")
        select_btn.clicked.connect(self._start_region_selection)
        title_bar_layout.addWidget(select_btn)
        
        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setObjectName("closeButton")
        close_btn.clicked.connect(self.close)
        title_bar_layout.addWidget(close_btn)
        
        layout.addWidget(title_bar)
        
        # 题目识别结果显示区域
        question_frame = QFrame()
        question_frame.setObjectName("questionFrame")
        question_layout = QVBoxLayout(question_frame)
        question_layout.setContentsMargins(12, 6, 12, 6)
        question_layout.setSpacing(2)
        
        # 题目标签
        question_header = QLabel("题目:")
        question_header.setStyleSheet("color: #888888; font-size: 10px;")
        question_layout.addWidget(question_header)
        
        # 题目内容（简略显示）
        self.question_label = QLabel("等待识别...")
        self.question_label.setObjectName("questionLabel")
        self.question_label.setWordWrap(True)
        self.question_label.setMaximumHeight(60)  # 限制高度
        self.question_label.setStyleSheet("color: #E0E0E0; font-size: 11px;")
        question_layout.addWidget(self.question_label)
        
        layout.addWidget(question_frame)
        
        # 答案显示区域
        self.answer_frame = QFrame()
        self.answer_frame.setObjectName("answerFrame")
        answer_layout = QVBoxLayout(self.answer_frame)
        answer_layout.setContentsMargins(12, 6, 12, 6)
        answer_layout.setSpacing(4)
        
        # 来源标签
        self.source_label = QLabel("")
        self.source_label.setObjectName("sourceLabel")
        answer_layout.addWidget(self.source_label)
        
        # 答案标签
        self.answer_label = QLabel("等待识别...")
        self.answer_label.setObjectName("answerLabel")
        self.answer_label.setWordWrap(True)
        answer_layout.addWidget(self.answer_label)
        
        layout.addWidget(self.answer_frame)
        
        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        layout.addWidget(self.status_label)
        
        # 透明度滑块
        opacity_layout = QHBoxLayout()
        opacity_layout.setContentsMargins(0, 0, 0, 0)
        opacity_layout.setSpacing(4)
        
        opacity_label = QLabel("透明度:")
        opacity_label.setStyleSheet("color: #888888; font-size: 10px;")
        opacity_layout.addWidget(opacity_label)
        
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.setValue(int(self.default_opacity * 100))
        self.opacity_slider.setFixedHeight(16)
        self.opacity_slider.valueChanged.connect(self._set_opacity)
        opacity_layout.addWidget(self.opacity_slider)
        
        layout.addLayout(opacity_layout)
        
        # 设置默认透明度
        self.setWindowOpacity(self.default_opacity)
        
    def _set_opacity(self, value):
        """设置透明度"""
        opacity = value / 100.0
        self.setWindowOpacity(opacity)
        
    def _setup_anti_capture(self):
        """设置防录屏 - 必须成功，否则致命错误"""
        if PLATFORM == "Windows":
            self._setup_windows_anti_capture()
        elif PLATFORM == "Darwin":
            self._setup_macos_anti_capture()
            
    def _setup_windows_anti_capture(self):
        """Windows 防录屏"""
        try:
            hwnd = int(self.winId())
            WDA_EXCLUDEFROMCAPTURE = 0x00000011
            result = ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
            if result:
                print("[OK] Windows 防录屏已启用")
            else:
                print("[WARN] Windows 防录屏设置返回失败")
        except Exception as e:
            print(f"[ERROR] Windows 防录屏设置失败: {e}")
            
    def _setup_macos_anti_capture(self):
        """macOS 防录屏 - 使用 NSWindowSharingNone"""
        try:
            # winId() 返回的是 NSView，需要获取其所属的 NSWindow
            ns_view = objc.objc_object(c_void_p=self.winId().__int__())
            
            # 通过 NSView 的 window() 方法获取 NSWindow
            ns_window = ns_view.window()
            
            if ns_window is None:
                print("[ERROR] 无法获取 NSWindow")
                return
            
            # 设置 sharingType 为 NSWindowSharingNone (0)
            # 这会阻止窗口内容被截图/录屏捕获
            ns_window.setSharingType_(0)  # NSWindowSharingNone = 0
            
            # 验证设置
            current_type = ns_window.sharingType()
            if current_type == 0:
                print("[OK] macOS 防录屏已启用 (NSWindowSharingNone)")
            else:
                print(f"[WARN] macOS 防录屏设置异常，当前值: {current_type}")
                
        except Exception as e:
            print(f"[FATAL] macOS 防录屏设置失败: {e}")
            QMessageBox.critical(
                self,
                "防录屏失败",
                f"macOS 防录屏设置失败！\n\n"
                f"错误: {e}\n\n"
                f"请确保已安装 pyobjc：\n"
                f"pip install pyobjc pyobjc-framework-Cocoa"
            )
            
    def _connect_signals(self):
        """连接信号"""
        # VisionService 信号
        self.vision_service.question_detected.connect(self._on_question_detected)
        self.vision_service.status_changed.connect(self._on_status_changed)
        self.vision_service.capture_started.connect(self._on_capture_started)
        self.vision_service.capture_finished.connect(self._on_capture_finished)
        
        # OCRService 信号
        self.ocr_service.ocr_result.connect(self._on_ocr_result)
        self.ocr_service.ocr_error.connect(self._on_ocr_error)
        
        # SearchController 信号
        self.search_controller.answer_found.connect(self._on_answer_found)
        self.search_controller.search_complete.connect(self._on_search_complete)
        self.search_controller.error_occurred.connect(self._on_error)
        
    @Slot()
    def _on_capture_started(self):
        """截图开始时隐藏覆盖层"""
        if hasattr(self, 'region_overlay') and self.region_overlay.isVisible():
            self.region_overlay.hide()
            
    @Slot()
    def _on_capture_finished(self):
        """截图结束时显示覆盖层"""
        if hasattr(self, 'region_overlay') and self.region and self.is_monitoring:
            self.region_overlay.show()
        
    def _start_region_selection(self):
        """开始区域选择"""
        if self.is_monitoring:
            return  # 监控中不允许重新选择区域
            
        self.hide()
        self.region_overlay.hide()  # 隐藏区域覆盖框
        self.region_selector = RegionSelector()
        self.region_selector.region_selected.connect(self._on_region_selected)
        self.region_selector.selection_cancelled.connect(self._on_selection_cancelled)
        self.region_selector.show()
        
    @Slot()
    def _on_selection_cancelled(self):
        """区域选择取消"""
        self.show()
        
    def _return_to_main(self):
        """返回主程序"""
        if self.is_monitoring:
            self.stop_monitoring()
        self.hide()
        self.region_overlay.hide()  # 隐藏区域覆盖框
        self.return_to_main.emit()
        
    def start_monitoring(self):
        """开始监控（标记状态）"""
        if self.region is None:
            self.status_label.setText("请先框选区域")
            return
            
        self.is_monitoring = True
        self.is_locked = True  # 锁定窗口
        self.vision_service.start_monitoring()
        
        # 更新状态
        self.status_dot.setStyleSheet("color: #4CAF50; font-size: 10px;")
        self.status_label.setText("● 就绪 (按 Ctrl+Shift+A 识题)")
        self.status_label.setStyleSheet("color: #4CAF50;")
        
        # 启用鼠标穿透
        self._enable_mouse_passthrough()
        
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        self.is_locked = False
        self.vision_service.stop_monitoring()
        
        # 更新状态
        self.status_dot.setStyleSheet("color: #F44336; font-size: 10px;")
        self.status_label.setText("● 已停止")
        self.status_label.setStyleSheet("color: #F44336;")
        
        # 禁用鼠标穿透
        self._disable_mouse_passthrough()
        
    def toggle_monitoring(self):
        """切换监控状态"""
        if self.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()
            
    def _enable_mouse_passthrough(self):
        """启用鼠标穿透"""
        if PLATFORM == "Windows":
            try:
                hwnd = int(self.winId())
                # 获取当前窗口样式
                style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE
                # 添加 WS_EX_TRANSPARENT 和 WS_EX_LAYERED
                style |= 0x20  # WS_EX_TRANSPARENT
                style |= 0x80000  # WS_EX_LAYERED
                ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)
                print("[OK] Windows 鼠标穿透已启用")
            except Exception as e:
                print(f"[WARN] Windows 鼠标穿透设置失败: {e}")
        elif PLATFORM == "Darwin":
            try:
                ns_view = objc.objc_object(c_void_p=self.winId().__int__())
                ns_window = ns_view.window()
                if ns_window:
                    # 设置窗口为不可点击
                    ns_window.setIgnoresMouseEvents_(True)
                    print("[OK] macOS 鼠标穿透已启用")
            except Exception as e:
                print(f"[WARN] macOS 鼠标穿透设置失败: {e}")
                
    def _disable_mouse_passthrough(self):
        """禁用鼠标穿透"""
        if PLATFORM == "Windows":
            try:
                hwnd = int(self.winId())
                style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
                style &= ~0x20  # 移除 WS_EX_TRANSPARENT
                ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)
                print("[OK] Windows 鼠标穿透已禁用")
            except Exception as e:
                print(f"[WARN] Windows 鼠标穿透设置失败: {e}")
        elif PLATFORM == "Darwin":
            try:
                ns_view = objc.objc_object(c_void_p=self.winId().__int__())
                ns_window = ns_view.window()
                if ns_window:
                    ns_window.setIgnoresMouseEvents_(False)
                    print("[OK] macOS 鼠标穿透已禁用")
            except Exception as e:
                print(f"[WARN] macOS 鼠标穿透设置失败: {e}")
                
    @Slot(dict)
    def _on_region_selected(self, region):
        """区域选择完成"""
        self.region = region
        self.vision_service.set_region(region)
        
        # 更新状态
        self.status_dot.setStyleSheet("color: #FF9800; font-size: 10px;")
        self.status_label.setText("● 区域已设置 - 按 Ctrl+Shift+M 开始监控")
        self.status_label.setStyleSheet("color: #FF9800;")
        self.source_label.setText("")
        self.answer_label.setText("等待识别...")
        self.show()
        
        # 显示区域覆盖框
        self.region_overlay.set_region(region)
        self.region_overlay.show()
        
        # 确保窗口置顶
        self._ensure_stay_on_top()
        
    def hide(self):
        """隐藏HUD时同时隐藏区域覆盖框"""
        super().hide()
        if hasattr(self, 'region_overlay'):
            self.region_overlay.hide()
        
    def showEvent(self, event):
        """窗口显示事件"""
        super().showEvent(event)
        # 确保窗口置顶
        self._ensure_stay_on_top()
        # 如果有区域设置，重新显示区域覆盖框
        if hasattr(self, 'region') and self.region and hasattr(self, 'region_overlay'):
            self.region_overlay.show()
        
    def _ensure_stay_on_top(self):
        """确保窗口置顶"""
        if PLATFORM == "Darwin":
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
                    
                    print("[HUD] 窗口置顶已确认 (Level 2000 + AllSpaces)")
            except Exception as e:
                print(f"[HUD] 窗口置顶设置失败: {e}")
        elif PLATFORM == "Windows":
            try:
                import ctypes
                hwnd = int(self.winId())
                # HWND_TOPMOST = -1
                ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002)
                print("[HUD] 窗口置顶已确认")
            except Exception as e:
                print(f"[HUD] 窗口置顶设置失败: {e}")
        
    @Slot(np.ndarray)
    def _on_question_detected(self, frame):
        """检测到新题目"""
        self.status_label.setText("● 检测到新题 - 正在识别...")
        self.status_label.setStyleSheet("color: #FF9800;")
        self.question_label.setText("正在识别...")
        self.answer_label.setText("...")
        self.source_label.setText("")
        self.ocr_service.process_image(frame)
        
    @Slot(str)
    def _on_ocr_result(self, text):
        """OCR 识别完成"""
        if not text or text.strip() == "":
            self.status_label.setText("● 就绪 - 未识别到文字")
            self.status_label.setStyleSheet("color: #4CAF50;")
            self.question_label.setText("未识别到文字")
            return
            
        # 显示题目内容（简略显示，截取前100字符）
        display_text = text.strip()[:100]
        if len(text.strip()) > 100:
            display_text += "..."
        self.question_label.setText(display_text)
        
        self.status_label.setText("● 正在检索答案...")
        self.status_label.setStyleSheet("color: #2196F3;")
        self.search_controller.search(text)
        
    @Slot(str)
    def _on_ocr_error(self, error):
        """OCR 错误"""
        self.status_label.setText("● OCR 识别失败")
        self.status_label.setStyleSheet("color: #F44336;")
        self.answer_label.setText(error[:50])
        
    @Slot(dict)
    def _on_answer_found(self, result):
        """找到答案"""
        source_label = result.get("source_label", "")
        answer = result.get("answer", "")
        
        self.source_label.setText(source_label)
        self.answer_label.setText(answer)
        self.answer_label.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold;")  # 白色字体，加粗
        self.status_label.setText("● 已找到答案")
        self.status_label.setStyleSheet("color: #4CAF50;")
        
        # 根据来源设置颜色
        if "极速" in source_label:
            self.source_label.setStyleSheet("color: #4CAF50;")
        elif "语义" in source_label:
            self.source_label.setStyleSheet("color: #2196F3;")
        elif "AI" in source_label:
            self.source_label.setStyleSheet("color: #FF9800;")
            
    @Slot()
    def _on_search_complete(self):
        """搜索完成"""
        if self.is_monitoring:
            self.status_label.setText("● 监控中 - 等待题目变化...")
            self.status_label.setStyleSheet("color: #4CAF50;")
            
    @Slot(str)
    def _on_error(self, error):
        """错误处理"""
        self.status_label.setText("● 错误")
        self.status_label.setStyleSheet("color: #F44336;")
        
    @Slot(str)
    def _on_status_changed(self, status):
        """状态变化"""
        if "画面变化" in status:
            self.status_label.setText("● 检测到画面变化...")
            self.status_label.setStyleSheet("color: #FF9800;")
        elif "新题目已稳定" in status:
            self.status_label.setText("● 新题目已稳定 - 正在识别...")
            self.status_label.setStyleSheet("color: #FF9800;")
            
    def paintEvent(self, event):
        """绘制窗口"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制阴影
        shadow_color = QColor(0, 0, 0, 60)
        painter.setBrush(QBrush(shadow_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect().adjusted(3, 3, -3, -3), 8, 8)
        
        # 绘制背景
        bg_color = QColor(30, 30, 30, 230)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -6, -6), 8, 8)
        
        painter.end()
        
    def mousePressEvent(self, event):
        """鼠标按下：拖拽窗口（仅在未锁定时）"""
        if self.is_locked:
            return  # 锁定模式下不允许拖拽
            
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """鼠标移动：拖拽窗口（仅在未锁定时）"""
        if self.is_locked:
            return
            
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
            
    def closeEvent(self, event):
        """关闭事件"""
        print("[HUD] 正在关闭...")
        if self.is_monitoring:
            self.stop_monitoring()
        self.region_overlay.close()  # 关闭区域覆盖框
        self.db_service.close()
        print("[HUD] 关闭完成")
        super().closeEvent(event)