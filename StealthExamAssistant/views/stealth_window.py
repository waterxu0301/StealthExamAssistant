import sys
import platform
import numpy as np
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QSlider, QFrame, QApplication,
                               QGroupBox, QScrollArea, QComboBox, QDialog,
                               QLineEdit, QMessageBox, QTabWidget)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, Slot
from PySide6.QtGui import QColor, QPainter, QBrush, QPen

# Platform-specific imports
if platform.system() == "Windows":
    import ctypes
elif platform.system() == "Darwin":
    try:
        import objc
    except ImportError:
        objc = None

from views.region_selector import RegionSelector
from views.answer_card import AnswerCard
from views.review_panel import ReviewPanel
from models.vision_service import VisionService
from models.ocr_service import OCRService
from models.database_service import DatabaseService
from models.embedding_service import EmbeddingService
from models.llm_service import LLMService
from models.project_service import ProjectService
from controllers.search_controller import SearchController

class StealthWindow(QWidget):
    """幽灵悬浮窗：集成区域监控、OCR、三级检索、项目管理、复盘录入"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stealth Exam Assistant")
        self.setMinimumSize(400, 600)
        self.setMaximumSize(500, 750)
        
        # 初始化服务
        self._init_services()
        
        # 窗口标志设置
        self.setup_window_flags()
        
        # UI 初始化
        self.setup_ui()
        
        # 应用 Material Design 样式
        self.apply_material_style()
        
        # 平台特定的防录屏设置
        self.setup_anti_capture()
        
        # 动画设置
        self.setup_animations()
        
        # 连接信号
        self.connect_signals()
        
        # 初始位置
        self.move_to_initial_position()
        
        # 加载项目列表
        self._load_projects()
        
    def _init_services(self):
        """初始化所有服务"""
        # 数据库服务
        self.db_service = DatabaseService("./data/exam_data.db", self)
        
        # 项目管理服务
        self.project_service = ProjectService("./data/exam_data.db", self)
        
        # Embedding 服务
        self.embedding_service = EmbeddingService("./models/bge-micro-v2", self)
        
        # LLM 服务
        self.llm_service = LLMService(self)
        
        # 搜索控制器
        self.search_controller = SearchController(
            self.db_service,
            self.embedding_service,
            self.llm_service,
            self
        )
        
        # OCR 服务
        self.ocr_service = OCRService(self)
        
        # Vision 服务
        self.vision_service = VisionService(self)
        
        # 区域选择器
        self.region = None
        self.region_selector = None
        
    def setup_window_flags(self):
        """配置窗口标志"""
        flags = (
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        
        if platform.system() == "Windows":
            flags |= Qt.WindowType.WindowDoesNotAcceptFocus
            
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
    def setup_ui(self):
        """设置用户界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)
        
        # 标题栏
        title_bar = self.create_title_bar()
        main_layout.addWidget(title_bar)
        
        # 项目选择栏
        project_bar = self.create_project_bar()
        main_layout.addWidget(project_bar)
        
        # 选项卡
        tab_widget = QTabWidget()
        tab_widget.setObjectName("mainTabs")
        
        # 监控选项卡
        monitor_tab = self.create_monitor_tab()
        tab_widget.addTab(monitor_tab, "监控")
        
        # 复盘选项卡
        review_tab = self.create_review_tab()
        tab_widget.addTab(review_tab, "复盘")
        
        main_layout.addWidget(tab_widget, 1)
        
        # 状态栏
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("statusLabel")
        status_layout.addWidget(self.status_label)
        
        # 服务状态指示
        self.service_status_label = QLabel()
        self.service_status_label.setObjectName("serviceStatus")
        self._update_service_status()
        status_layout.addWidget(self.service_status_label)
        
        main_layout.addLayout(status_layout)
        
        # 透明度控制
        transparency_layout = QHBoxLayout()
        transparency_label = QLabel("透明度:")
        self.transparency_slider = QSlider(Qt.Orientation.Horizontal)
        self.transparency_slider.setRange(30, 100)
        self.transparency_slider.setValue(90)
        self.transparency_slider.valueChanged.connect(self.set_opacity)
        transparency_layout.addWidget(transparency_label)
        transparency_layout.addWidget(self.transparency_slider)
        main_layout.addLayout(transparency_layout)
        
    def create_title_bar(self):
        """创建标题栏"""
        title_bar = QFrame()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(32)
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(8, 0, 8, 0)
        
        title_label = QLabel("Stealth Assistant")
        title_label.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        minimize_btn = QPushButton("─")
        minimize_btn.setFixedSize(24, 24)
        minimize_btn.setObjectName("minimizeButton")
        minimize_btn.clicked.connect(self.showMinimized)
        layout.addWidget(minimize_btn)
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setObjectName("closeButton")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        return title_bar
        
    def create_project_bar(self):
        """创建项目选择栏"""
        bar = QFrame()
        bar.setObjectName("projectBar")
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        project_label = QLabel("项目:")
        layout.addWidget(project_label)
        
        self.project_combo = QComboBox()
        self.project_combo.setObjectName("projectCombo")
        self.project_combo.currentTextChanged.connect(self._on_project_changed)
        layout.addWidget(self.project_combo, 1)
        
        new_project_btn = QPushButton("+")
        new_project_btn.setFixedSize(24, 24)
        new_project_btn.setObjectName("newProjectButton")
        new_project_btn.clicked.connect(self._show_new_project_dialog)
        layout.addWidget(new_project_btn)
        
        # 设置按钮
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(24, 24)
        settings_btn.setObjectName("settingsButton")
        settings_btn.setToolTip("设置")
        settings_btn.clicked.connect(self._show_settings_dialog)
        layout.addWidget(settings_btn)
        
        return bar
        
    def create_monitor_tab(self):
        """创建监控选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(8)
        
        # 区域选择组
        region_group = QGroupBox("监控区域")
        region_group.setObjectName("regionGroup")
        
        region_layout = QVBoxLayout(region_group)
        region_layout.setContentsMargins(8, 12, 8, 8)
        region_layout.setSpacing(8)
        
        self.region_info_label = QLabel("未选择区域")
        self.region_info_label.setObjectName("regionInfo")
        region_layout.addWidget(self.region_info_label)
        
        self.select_region_btn = QPushButton("选择题目区域")
        self.select_region_btn.setObjectName("selectRegionBtn")
        self.select_region_btn.clicked.connect(self.start_region_selection)
        region_layout.addWidget(self.select_region_btn)
        
        layout.addWidget(region_group)
        
        # 监控控制组
        monitor_group = QGroupBox("监控控制")
        monitor_group.setObjectName("monitorGroup")
        
        monitor_layout = QHBoxLayout(monitor_group)
        monitor_layout.setContentsMargins(8, 12, 8, 8)
        monitor_layout.setSpacing(8)
        
        self.monitor_btn = QPushButton("开始监控")
        self.monitor_btn.setObjectName("monitorButton")
        self.monitor_btn.setCheckable(True)
        self.monitor_btn.clicked.connect(self.toggle_monitoring)
        self.monitor_btn.setEnabled(False)
        monitor_layout.addWidget(self.monitor_btn)
        
        layout.addWidget(monitor_group)
        
        # Embedding 模型控制
        embedding_group = QGroupBox("语义模型")
        embedding_layout = QHBoxLayout(embedding_group)
        embedding_layout.setContentsMargins(8, 12, 8, 8)
        
        self.embedding_status_label = QLabel("未加载")
        embedding_layout.addWidget(self.embedding_status_label)
        
        self.download_model_btn = QPushButton("下载模型")
        self.download_model_btn.setObjectName("downloadButton")
        self.download_model_btn.clicked.connect(self._download_embedding_model)
        embedding_layout.addWidget(self.download_model_btn)
        
        layout.addWidget(embedding_group)
        
        # 答案卡片
        answer_scroll = QScrollArea()
        answer_scroll.setWidgetResizable(True)
        answer_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        answer_scroll.setObjectName("answerScroll")
        
        self.answer_card = AnswerCard()
        answer_scroll.setWidget(self.answer_card)
        
        layout.addWidget(answer_scroll, 1)
        
        return tab
        
    def create_review_tab(self):
        """创建复盘选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        
        self.review_panel = ReviewPanel()
        self.review_panel.question_submitted.connect(self._on_review_submitted)
        layout.addWidget(self.review_panel)
        
        return tab
        
    def _load_projects(self):
        """加载项目列表"""
        projects = self.project_service.get_project_names()
        self.project_combo.clear()
        self.project_combo.addItems(projects)
        
    def _on_project_changed(self, project_name):
        """项目切换"""
        if project_name:
            self.project_service.switch_project(project_name)
            self.review_panel.set_project(project_name)
            
    def _show_new_project_dialog(self):
        """显示新建项目对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("新建项目")
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout(dialog)
        
        name_label = QLabel("项目名称:")
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("例如：安全合规认证")
        layout.addWidget(name_label)
        layout.addWidget(name_edit)
        
        desc_label = QLabel("项目描述（可选）:")
        desc_edit = QLineEdit()
        desc_edit.setPlaceholderText("例如：2024年安全合规认证考试")
        layout.addWidget(desc_label)
        layout.addWidget(desc_edit)
        
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("创建")
        create_btn.setObjectName("createButton")
        create_btn.clicked.connect(lambda: self._create_project(
            name_edit.text(),
            desc_edit.text(),
            dialog
        ))
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
        
    def _create_project(self, name, description, dialog):
        """创建新项目"""
        if not name.strip():
            QMessageBox.warning(self, "错误", "项目名称不能为空")
            return
            
        success = self.project_service.create_project(name.strip(), description.strip())
        if success:
            self._load_projects()
            self.project_combo.setCurrentText(name.strip())
            dialog.accept()
        else:
            QMessageBox.warning(self, "错误", f"项目 '{name}' 已存在")
            
    def _show_settings_dialog(self):
        """显示设置对话框"""
        from views.settings_dialog import SettingsDialog
        
        dialog = SettingsDialog(
            embedding_service=self.embedding_service,
            parent=self
        )
        
        # 连接信号
        dialog.settings_saved.connect(self._on_settings_saved)
        
        dialog.exec()
        
    def _on_settings_saved(self):
        """设置保存后刷新服务状态"""
        self._update_service_status()
        
    def _download_embedding_model(self):
        """下载 Embedding 模型"""
        self.download_model_btn.setEnabled(False)
        self.embedding_status_label.setText("正在下载...")
        self.embedding_service.download_model()
        
    def _on_review_submitted(self, question, options, answer, project):
        """复盘提交处理"""
        # 如果只有原始文本，请求 AI 清洗
        if not options and not answer:
            self.status_label.setText("正在 AI 清洗...")
            self.llm_service.analyze_question_for_review(question, project)
        else:
            # 直接入库
            vector_data = None
            if self.embedding_service.is_available():
                vector_data = self.embedding_service.encode_text(question)
                
            success = self.db_service.insert_question(
                question=question,
                options=options,
                answer=answer,
                source="review",
                project=project,
                vector_data=vector_data
            )
            
            if success:
                self.review_panel.set_status("入库成功！")
                self.status_label.setText("题目已入库")
            else:
                self.review_panel.set_status("入库失败")
                self.status_label.setText("入库失败")
                
    def _update_service_status(self):
        """更新服务状态显示"""
        statuses = []
        
        if self.db_service.conn:
            statuses.append("✓ DB")
        else:
            statuses.append("✗ DB")
            
        if self.embedding_service.is_available():
            statuses.append("✓ 向量")
        else:
            statuses.append("○ 向量")
            
        if self.llm_service.is_configured():
            statuses.append("✓ LLM")
        else:
            statuses.append("✗ LLM")
            
        self.service_status_label.setText(" | ".join(statuses))
        
        # 更新 Embedding 状态
        if hasattr(self, 'embedding_status_label'):
            if self.embedding_service.is_available():
                self.embedding_status_label.setText("已加载")
                self.download_model_btn.setEnabled(False)
            else:
                info = self.embedding_service.get_model_info()
                if info["model_exists"] and info["tokenizer_exists"]:
                    self.embedding_status_label.setText("需要加载")
                else:
                    self.embedding_status_label.setText("未下载")
                self.download_model_btn.setEnabled(True)
                
    def apply_material_style(self):
        """应用 Material Design 样式"""
        try:
            from qt_material import apply_stylesheet
            apply_stylesheet(QApplication.instance(), theme='dark_teal.xml')
        except ImportError:
            self.setStyleSheet(self.get_material_stylesheet())
            
    def get_material_stylesheet(self):
        """返回 Material Design 样式表"""
        return """
        QWidget {
            background-color: rgba(30, 30, 30, 0.95);
            color: #ffffff;
            font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
            font-size: 12px;
        }
        
        #titleBar {
            background-color: rgba(0, 150, 136, 0.9);
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }
        
        #projectBar {
            background-color: rgba(50, 50, 50, 0.9);
            border-radius: 4px;
        }
        
        QGroupBox {
            background-color: rgba(40, 40, 40, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 12px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
            color: #009688;
        }
        
        QPushButton {
            background-color: rgba(0, 150, 136, 0.8);
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            color: white;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: rgba(0, 150, 136, 1.0);
        }
        
        QPushButton:pressed {
            background-color: rgba(0, 120, 106, 1.0);
        }
        
        QPushButton:checked {
            background-color: rgba(255, 87, 34, 0.9);
        }
        
        QPushButton:disabled {
            background-color: rgba(100, 100, 100, 0.5);
        }
        
        #minimizeButton, #closeButton, #newProjectButton, #settingsButton {
            background-color: transparent;
            border: none;
            border-radius: 12px;
            font-size: 14px;
            font-weight: bold;
        }
        
        #minimizeButton:hover, #closeButton:hover, #newProjectButton:hover, #settingsButton:hover {
            background-color: rgba(255, 255, 255, 0.2);
        }
        
        #closeButton:hover {
            background-color: rgba(255, 0, 0, 0.6);
        }
        
        #newProjectButton {
            color: #4CAF50;
        }
        
        #settingsButton {
            color: #FF9800;
        }
        
        #downloadButton {
            background-color: rgba(33, 150, 243, 0.8);
        }
        
        #downloadButton:hover {
            background-color: rgba(33, 150, 243, 1.0);
        }
        
        #createButton {
            background-color: rgba(76, 175, 80, 0.8);
        }
        
        #createButton:hover {
            background-color: rgba(76, 175, 80, 1.0);
        }
        
        QComboBox {
            background-color: rgba(50, 50, 50, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 4px;
            padding: 6px;
            color: #ffffff;
        }
        
        QComboBox::drop-down {
            border: none;
        }
        
        QComboBox QAbstractItemView {
            background-color: rgba(50, 50, 50, 0.95);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #ffffff;
        }
        
        QTabWidget::pane {
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }
        
        QTabBar::tab {
            background-color: rgba(40, 40, 40, 0.9);
            color: #aaaaaa;
            padding: 8px 16px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: rgba(0, 150, 136, 0.8);
            color: #ffffff;
        }
        
        QScrollArea {
            background-color: transparent;
            border: none;
        }
        
        QScrollArea QWidget {
            background-color: transparent;
        }
        
        QSlider::groove:horizontal {
            height: 4px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 2px;
        }
        
        QSlider::handle:horizontal {
            background: #009688;
            border: none;
            width: 16px;
            height: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }
        
        QSlider::sub-page:horizontal {
            background: #009688;
            border-radius: 2px;
        }
        
        QLabel {
            color: #ffffff;
        }
        
        #statusLabel {
            color: #aaaaaa;
            font-style: italic;
        }
        
        #serviceStatus {
            color: #888888;
            font-size: 10px;
        }
        
        #regionInfo {
            color: #ff9800;
        }
        """
        
    def setup_anti_capture(self):
        """设置防录屏"""
        if platform.system() == "Windows":
            self.setup_windows_anti_capture()
        elif platform.system() == "Darwin":
            self.setup_macos_anti_capture()
            
    def setup_windows_anti_capture(self):
        """Windows 防录屏"""
        try:
            hwnd = int(self.winId())
            WDA_EXCLUDEFROMCAPTURE = 0x00000011
            ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
        except Exception as e:
            print(f"Windows 防录屏设置失败: {e}")
            
    def setup_macos_anti_capture(self):
        """macOS 防录屏"""
        try:
            if objc is None:
                return
            # winId() 返回的是 NSView，需要获取其所属的 NSWindow
            ns_view = objc.objc_object(c_void_p=self.winId().__int__())
            ns_window = ns_view.window()
            
            if ns_window is None:
                print("[ERROR] 无法获取 NSWindow")
                return
                
            ns_window.setSharingType_(0)  # NSWindowSharingNone
            print("[OK] macOS 防录屏已启用")
        except Exception as e:
            print(f"macOS 防录屏设置失败: {e}")
            
    def setup_animations(self):
        """设置动画"""
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
    def connect_signals(self):
        """连接信号"""
        # VisionService 信号
        self.vision_service.question_detected.connect(self.on_question_detected)
        self.vision_service.status_changed.connect(self.on_status_changed)
        self.vision_service.error_occurred.connect(self.on_error_occurred)
        
        # OCRService 信号
        self.ocr_service.ocr_result.connect(self.on_ocr_result)
        self.ocr_service.ocr_error.connect(self.on_ocr_error)
        
        # SearchController 信号
        self.search_controller.answer_found.connect(self.on_answer_found)
        self.search_controller.search_complete.connect(self.on_search_complete)
        self.search_controller.error_occurred.connect(self.on_error_occurred)
        
        # EmbeddingService 信号
        self.embedding_service.model_loaded.connect(self._on_embedding_loaded)
        self.embedding_service.model_loading.connect(self._on_embedding_loading)
        self.embedding_service.error_occurred.connect(self.on_error_occurred)
        
        # LLMService 信号（用于复盘）
        self.llm_service.review_result_ready.connect(self._on_review_ai_result)
        
    def move_to_initial_position(self):
        """移动到初始位置"""
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 20, 20)
        
    def set_opacity(self, value):
        """设置透明度"""
        opacity = value / 100.0
        self.fade_animation.stop()
        self.fade_animation.setStartValue(self.windowOpacity())
        self.fade_animation.setEndValue(opacity)
        self.fade_animation.start()
        
    def start_region_selection(self):
        """开始区域选择"""
        self.hide()
        self.region_selector = RegionSelector()
        self.region_selector.region_selected.connect(self.on_region_selected)
        self.region_selector.show()
        
    @Slot(dict)
    def on_region_selected(self, region):
        """区域选择完成"""
        self.region = region
        self.region_info_label.setText(
            f"区域: ({region['x']}, {region['y']}) "
            f"大小: {region['width']}x{region['height']}"
        )
        self.monitor_btn.setEnabled(True)
        self.vision_service.set_region(region)
        self.show()
        
    def toggle_monitoring(self, checked):
        """切换监控状态"""
        if checked:
            self.vision_service.start_monitoring()
            self.monitor_btn.setText("停止监控")
            self.select_region_btn.setEnabled(False)
        else:
            self.vision_service.stop_monitoring()
            self.monitor_btn.setText("开始监控")
            self.select_region_btn.setEnabled(True)
            
    @Slot(np.ndarray)
    def on_question_detected(self, frame):
        """检测到新题目"""
        self.status_label.setText("正在识别...")
        self.answer_card.clear()
        self.ocr_service.process_image(frame)
        
    @Slot(str)
    def on_ocr_result(self, text):
        """OCR 识别完成"""
        self.status_label.setText("正在搜索答案...")
        
        # 获取当前项目
        current_project = self.project_service.get_current_project()
        
        # 触发三级检索
        self.search_controller.search(text, project=current_project)
        
    @Slot(str)
    def on_ocr_error(self, error):
        """OCR 错误"""
        self.status_label.setText(f"OCR 错误: {error}")
        
    @Slot(dict)
    def on_answer_found(self, result):
        """找到答案"""
        self.answer_card.set_answer(result)
        self.status_label.setText("答案已找到")
        
    @Slot()
    def on_search_complete(self):
        """搜索完成"""
        self._update_service_status()
        
    @Slot(str)
    def on_status_changed(self, status):
        """状态变化"""
        self.status_label.setText(status)
        
    @Slot(str)
    def on_error_occurred(self, error):
        """错误处理"""
        self.status_label.setText(f"错误: {error}")
        
    @Slot()
    def _on_embedding_loaded(self):
        """Embedding 模型加载完成"""
        self._update_service_status()
        self.status_label.setText("语义模型已加载")
        
    @Slot(str)
    def _on_embedding_loading(self, message):
        """Embedding 模型加载中"""
        self.embedding_status_label.setText(message)
        
    @Slot(dict)
    def _on_review_ai_result(self, result):
        """复盘 AI 清洗结果"""
        if "error" in result:
            self.review_panel.set_status(f"AI 清洗失败: {result['error']}")
        else:
            self.review_panel.set_ai_result(
                result.get("question", ""),
                result.get("options", ""),
                result.get("answer", "")
            )
            
    def paintEvent(self, event):
        """绘制窗口"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        shadow_color = QColor(0, 0, 0, 80)
        painter.setBrush(QBrush(shadow_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect().adjusted(4, 4, -4, -4), 8, 8)
        
        bg_color = QColor(30, 30, 30, 240)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -8, -8), 8, 8)
        
        painter.end()
        
    def mousePressEvent(self, event):
        """鼠标按下：拖拽窗口"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """鼠标移动：拖拽窗口"""
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
            
    def keyPressEvent(self, event):
        """按键处理"""
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        elif (event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier) and 
              event.key() == Qt.Key.Key_Space):
            if self.isVisible():
                self.hide()
            else:
                self.show()
        super().keyPressEvent(event)
        
    def closeEvent(self, event):
        """关闭事件"""
        self.vision_service.stop_monitoring()
        self.db_service.close()
        self.project_service.close()
        super().closeEvent(event)