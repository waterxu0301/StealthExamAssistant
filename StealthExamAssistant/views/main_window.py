from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QComboBox, QTextEdit, 
                               QTabWidget, QGroupBox, QProgressBar, QMessageBox,
                               QFrame, QApplication, QCheckBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap

from models.database_service import DatabaseService
from models.embedding_service import EmbeddingService
from models.llm_service import LLMService
from models.project_service import ProjectService
from models.batch_review_service import BatchReviewService
from views.settings_dialog import SettingsDialog

class MainWindow(QMainWindow):
    """主控台窗口：项目管理、设置、批量复盘"""
    
    # 信号
    launch_hud = Signal()  # 启动隐形 HUD
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stealth Exam Assistant - 主控台")
        self.setMinimumSize(600, 500)
        self.setMaximumSize(800, 700)
        
        # 初始化服务
        self._init_services()
        
        # 热键管理器（稍后设置）
        self.hotkey_manager = None
        
        # 设置 UI
        self._setup_ui()
        
        # 应用样式
        self._apply_style()
        
        # 加载项目列表
        self._load_projects()
        
    def set_hotkey_manager(self, hotkey_manager):
        """设置热键管理器（用于配置热更新）"""
        self.hotkey_manager = hotkey_manager
        
    def _init_services(self):
        """初始化服务"""
        self.db_service = DatabaseService("./data/exam_data.db", self)
        self.project_service = ProjectService("./data/exam_data.db", self)
        self.embedding_service = EmbeddingService(self)
        self.llm_service = LLMService(self)
        self.batch_review_service = BatchReviewService(
            self.db_service, self.embedding_service, self
        )
        
        # 连接信号
        self.batch_review_service.progress_updated.connect(self._on_review_progress)
        self.batch_review_service.review_complete.connect(self._on_review_complete)
        self.batch_review_service.error_occurred.connect(self._on_review_error)
        
    def _setup_ui(self):
        """设置 UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        
        # 标题
        title_layout = QHBoxLayout()
        title_label = QLabel("Stealth Exam Assistant")
        title_label.setObjectName("appTitle")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # 设置按钮
        settings_btn = QPushButton("⚙ 设置")
        settings_btn.setObjectName("settingsButton")
        settings_btn.clicked.connect(self._show_settings)
        title_layout.addWidget(settings_btn)
        
        main_layout.addLayout(title_layout)
        
        # 项目选择栏
        project_bar = self._create_project_bar()
        main_layout.addWidget(project_bar)
        
        # 选项卡
        tab_widget = QTabWidget()
        tab_widget.setObjectName("mainTabs")
        
        # Tab 1: 启动 HUD
        launch_tab = self._create_launch_tab()
        tab_widget.addTab(launch_tab, "启动辅助")
        
        # Tab 2: 批量复盘
        review_tab = self._create_review_tab()
        tab_widget.addTab(review_tab, "批量复盘")
        
        main_layout.addWidget(tab_widget, 1)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
        
    def _create_project_bar(self):
        """创建项目选择栏"""
        bar = QFrame()
        bar.setObjectName("projectBar")
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        project_label = QLabel("当前项目:")
        project_label.setObjectName("projectLabel")
        layout.addWidget(project_label)
        
        self.project_combo = QComboBox()
        self.project_combo.setObjectName("projectCombo")
        self.project_combo.currentTextChanged.connect(self._on_project_changed)
        layout.addWidget(self.project_combo, 1)
        
        new_project_btn = QPushButton("+ 新建项目")
        new_project_btn.setObjectName("newProjectButton")
        new_project_btn.clicked.connect(self._show_new_project_dialog)
        layout.addWidget(new_project_btn)
        
        return bar
        
    def _create_launch_tab(self):
        """创建启动 HUD 选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 说明文字
        desc_label = QLabel(
            "点击下方按钮启动隐形辅助 HUD。\n"
            "HUD 将以极简悬浮窗形式显示，支持防录屏和防焦点抢占。"
        )
        desc_label.setObjectName("descLabel")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # 服务状态
        status_group = QGroupBox("服务状态")
        status_layout = QVBoxLayout(status_group)
        
        self.service_status_label = QLabel()
        self.service_status_label.setObjectName("serviceStatus")
        self._update_service_status()
        status_layout.addWidget(self.service_status_label)
        
        layout.addWidget(status_group)
        
        # 启动按钮
        launch_btn = QPushButton("🚀 启动辅助 HUD")
        launch_btn.setObjectName("launchButton")
        launch_btn.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        launch_btn.setMinimumHeight(60)
        launch_btn.clicked.connect(self._launch_hud)
        layout.addWidget(launch_btn)
        
        layout.addStretch()
        
        return tab
        
    def _create_review_tab(self):
        """创建批量复盘选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # 说明
        desc_label = QLabel("粘贴题目文本/图片，或导入文件，AI 将自动清洗并入库：")
        desc_label.setObjectName("descLabel")
        layout.addWidget(desc_label)
        
        # 文件导入提示
        file_info = QLabel("支持格式：txt, pdf, doc, docx, xls, xlsx, png, jpg, jpeg, bmp, gif, webp")
        file_info.setObjectName("fileInfo")
        file_info.setWordWrap(True)
        layout.addWidget(file_info)
        
        # OCR 预处理选项
        ocr_option_layout = QHBoxLayout()
        self.use_ocr_checkbox = QCheckBox("图片使用 OCR 预处理（节省 Token，适合清晰文字）")
        self.use_ocr_checkbox.setChecked(False)
        self.use_ocr_checkbox.setToolTip(
            "勾选：先用本地 OCR 提取文字，再发送给大模型（节省 80-90% Token）\n"
            "不勾选：直接发送图片给大模型 VLM 识别（适合复杂题目、手写、图表）"
        )
        ocr_option_layout.addWidget(self.use_ocr_checkbox)
        ocr_option_layout.addStretch()
        layout.addLayout(ocr_option_layout)
        
        # 图片预览区域
        self.review_image_preview = QLabel()
        self.review_image_preview.setObjectName("imagePreview")
        self.review_image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.review_image_preview.setMinimumHeight(80)
        self.review_image_preview.setMaximumHeight(150)
        self.review_image_preview.setVisible(False)
        layout.addWidget(self.review_image_preview)
        
        # 文本输入
        self.review_text_edit = QTextEdit()
        self.review_text_edit.setObjectName("reviewTextEdit")
        self.review_text_edit.setPlaceholderText(
            "在此粘贴题目内容...\n\n"
            "支持格式：\n"
            "- 纯文本题目\n"
            "- 带选项的选择题\n"
            "- 粘贴图片（Ctrl+V）\n"
            "- 导入文件（txt/pdf/doc/图片）\n"
            "- 任意格式，AI 会自动清洗"
        )
        layout.addWidget(self.review_text_edit, 1)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        paste_btn = QPushButton("📋 粘贴文本")
        paste_btn.clicked.connect(self._paste_from_clipboard)
        button_layout.addWidget(paste_btn)
        
        paste_image_btn = QPushButton("🖼️ 粘贴图片")
        paste_image_btn.clicked.connect(self._paste_image_to_review)
        button_layout.addWidget(paste_image_btn)
        
        import_file_btn = QPushButton("📄 导入文件")
        import_file_btn.setObjectName("importFileButton")
        import_file_btn.clicked.connect(self._import_file_to_review)
        button_layout.addWidget(import_file_btn)
        
        upload_btn = QPushButton("📁 上传图片")
        upload_btn.clicked.connect(self._upload_image_to_review)
        button_layout.addWidget(upload_btn)
        
        clear_btn = QPushButton("🗑 清空")
        clear_btn.clicked.connect(self._clear_review_input)
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        
        self.review_btn = QPushButton("🚀 开始清洗入库")
        self.review_btn.setObjectName("reviewButton")
        self.review_btn.clicked.connect(self._start_review)
        button_layout.addWidget(self.review_btn)
        
        layout.addLayout(button_layout)
        
        # 进度条
        self.review_progress_bar = QProgressBar()
        self.review_progress_bar.setRange(0, 100)
        self.review_progress_bar.setValue(0)
        self.review_progress_bar.setVisible(False)
        layout.addWidget(self.review_progress_bar)
        
        # 状态文本
        self.review_status_label = QLabel("")
        self.review_status_label.setObjectName("reviewStatus")
        layout.addWidget(self.review_status_label)
        
        # 初始化图片数据
        self.review_image_base64 = None
        
        return tab
        
    def _apply_style(self):
        """应用样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            
            #appTitle {
                color: #009688;
                font-size: 20px;
                font-weight: bold;
            }
            
            #projectBar {
                background-color: #2d2d2d;
                border-radius: 8px;
            }
            
            #projectLabel {
                color: #cccccc;
                font-weight: bold;
            }
            
            QGroupBox {
                background-color: #2d2d2d;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
                color: #ffffff;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #009688;
            }
            
            QLabel {
                color: #cccccc;
            }
            
            #descLabel {
                color: #aaaaaa;
                font-size: 13px;
            }
            
            #serviceStatus {
                color: #4CAF50;
                font-size: 12px;
            }
            
            #reviewStatus {
                color: #FF9800;
                font-style: italic;
            }
            
            #imagePreview {
                background-color: rgba(50, 50, 50, 0.9);
                border: 2px dashed rgba(0, 150, 136, 0.5);
                border-radius: 8px;
                padding: 8px;
            }
            
            QComboBox {
                background-color: #3d3d3d;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                padding: 8px;
                color: #ffffff;
                font-size: 13px;
            }
            
            QComboBox::drop-down {
                border: none;
            }
            
            QComboBox QAbstractItemView {
                background-color: #3d3d3d;
                border: 1px solid rgba(255, 255, 255, 0.2);
                color: #ffffff;
            }
            
            QTextEdit {
                background-color: #2d2d2d;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 12px;
                color: #ffffff;
                font-size: 13px;
                font-family: 'Consolas', 'Monaco', monospace;
            }
            
            QPushButton {
                background-color: rgba(0, 150, 136, 0.8);
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                color: white;
                font-weight: bold;
                font-size: 13px;
            }
            
            QPushButton:hover {
                background-color: rgba(0, 150, 136, 1.0);
            }
            
            QPushButton:pressed {
                background-color: rgba(0, 120, 106, 1.0);
            }
            
            QPushButton:disabled {
                background-color: rgba(100, 100, 100, 0.5);
            }
            
            #settingsButton {
                background-color: rgba(100, 100, 100, 0.5);
                font-size: 12px;
                padding: 8px 16px;
            }
            
            #settingsButton:hover {
                background-color: rgba(100, 100, 100, 0.8);
            }
            
            #newProjectButton {
                background-color: rgba(76, 175, 80, 0.8);
            }
            
            #newProjectButton:hover {
                background-color: rgba(76, 175, 80, 1.0);
            }
            
            #launchButton {
                background-color: rgba(76, 175, 80, 0.9);
                font-size: 18px;
                min-height: 60px;
            }
            
            #launchButton:hover {
                background-color: rgba(76, 175, 80, 1.0);
            }
            
            #reviewButton {
                background-color: rgba(255, 152, 0, 0.8);
            }
            
            #reviewButton:hover {
                background-color: rgba(255, 152, 0, 1.0);
            }
            
            #importFileButton {
                background-color: rgba(156, 39, 176, 0.8);
            }
            
            #importFileButton:hover {
                background-color: rgba(156, 39, 176, 1.0);
            }
            
            #fileInfo {
                color: #888888;
                font-size: 11px;
                padding: 4px 8px;
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 4px;
            }
            
            QTabWidget::pane {
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                background-color: #2d2d2d;
            }
            
            QTabBar::tab {
                background-color: #1e1e1e;
                color: #aaaaaa;
                padding: 10px 20px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            
            QTabBar::tab:selected {
                background-color: #2d2d2d;
                color: #ffffff;
            }
            
            QProgressBar {
                background-color: #3d3d3d;
                border: none;
                border-radius: 4px;
                text-align: center;
                color: #ffffff;
                height: 24px;
            }
            
            QProgressBar::chunk {
                background-color: #009688;
                border-radius: 4px;
            }
            
            QStatusBar {
                background-color: #1e1e1e;
                color: #aaaaaa;
            }
        """)
        
    def _load_projects(self):
        """加载项目列表"""
        projects = self.project_service.get_project_names()
        self.project_combo.clear()
        self.project_combo.addItems(projects)
        
    def _on_project_changed(self, project_name):
        """项目切换"""
        if project_name:
            self.project_service.switch_project(project_name)
            
    def _show_new_project_dialog(self):
        """显示新建项目对话框"""
        from PySide6.QtWidgets import QDialog, QLineEdit
        
        dialog = QDialog(self)
        dialog.setWindowTitle("新建项目")
        dialog.setMinimumWidth(350)
        
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
        create_btn.clicked.connect(lambda: self._create_project(
            name_edit.text(), desc_edit.text(), dialog
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
            
    def _show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(
            embedding_service=self.embedding_service,
            llm_service=self.llm_service,
            hotkey_manager=self.hotkey_manager,
            parent=self
        )
        dialog.settings_saved.connect(self._update_service_status)
        dialog.exec()
        
    def _update_service_status(self):
        """更新服务状态"""
        statuses = []
        
        # DB 状态
        if self.db_service.conn:
            statuses.append("✓ 数据库")
        else:
            statuses.append("✗ 数据库")
            
        # Embedding 状态
        if self.embedding_service.is_configured():
            statuses.append("✓ 向量服务")
        else:
            statuses.append("○ 向量服务")
            
        # LLM 状态
        if self.llm_service.is_configured():
            statuses.append("✓ LLM 服务")
        else:
            statuses.append("✗ LLM 服务")
            
        self.service_status_label.setText("  |  ".join(statuses))
        
    def _launch_hud(self):
        """启动隐形 HUD"""
        self.launch_hud.emit()
        
    def _paste_from_clipboard(self):
        """从剪贴板粘贴文本"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.review_text_edit.setPlainText(text)
            self.review_image_base64 = None
            self.review_image_preview.setVisible(False)
            
    def _paste_image_to_review(self):
        """粘贴图片到复盘"""
        import base64
        from PySide6.QtCore import QBuffer, QIODevice
        
        clipboard = QApplication.clipboard()
        image = clipboard.image()
        
        if image.isNull():
            self.review_status_label.setText("剪贴板中没有图片")
            return
            
        # 显示预览
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(
            self.review_image_preview.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.review_image_preview.setPixmap(scaled_pixmap)
        self.review_image_preview.setVisible(True)
        
        # 转换为 base64（使用 QBuffer）
        try:
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            pixmap.save(buffer, "PNG")
            buffer.close()
            self.review_image_base64 = base64.b64encode(buffer.data().data()).decode('utf-8')
            self.review_status_label.setText(f"图片已加载，点击清洗入库进行识别")
        except Exception as e:
            self.review_status_label.setText(f"图片转换失败: {str(e)}")
            self.review_image_base64 = None
        
    def _upload_image_to_review(self):
        """上传图片到复盘"""
        import base64
        from PySide6.QtCore import QBuffer, QIODevice
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                self.review_status_label.setText("无法加载图片")
                return
                
            # 显示预览
            scaled_pixmap = pixmap.scaled(
                self.review_image_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.review_image_preview.setPixmap(scaled_pixmap)
            self.review_image_preview.setVisible(True)
            
            # 转换为 base64（使用 QBuffer）
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            pixmap.save(buffer, "PNG")
            buffer.close()
            self.review_image_base64 = base64.b64encode(buffer.data().data()).decode('utf-8')
            self.review_status_label.setText("图片已加载，点击清洗入库进行识别")
            
    def _import_file_to_review(self):
        """导入文件到复盘"""
        from PySide6.QtWidgets import QFileDialog
        from models.file_parser import FileParser
        
        # 获取文件过滤器
        file_filter = FileParser.get_file_filter()
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入文件", "", file_filter
        )
        
        if not file_path:
            return
            
        # 获取 OCR 选项
        use_ocr = self.use_ocr_checkbox.isChecked()
            
        try:
            self.review_status_label.setText(f"正在解析文件: {file_path}")
            QApplication.processEvents()
            
            # 解析文件
            text_content, image_base64, file_type = FileParser.parse_file(file_path, use_ocr)
            
            if file_type == 'text':
                # 文本文件
                self.review_text_edit.setPlainText(text_content)
                self.review_image_base64 = None
                self.review_image_preview.setVisible(False)
                self.review_status_label.setText(f"文件已导入: {file_path}")
                
            elif file_type == 'image':
                # 图片文件
                self.review_image_base64 = image_base64
                
                # 显示预览
                pixmap = QPixmap(file_path)
                scaled_pixmap = pixmap.scaled(
                    self.review_image_preview.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.review_image_preview.setPixmap(scaled_pixmap)
                self.review_image_preview.setVisible(True)
                self.review_status_label.setText(f"图片已导入: {file_path}")
                
        except ImportError as e:
            QMessageBox.warning(self, "缺少依赖", str(e))
        except Exception as e:
            QMessageBox.warning(self, "导入失败", f"无法解析文件: {str(e)}")
            self.review_status_label.setText("导入失败")
            
    def _clear_review_input(self):
        """清空复盘输入"""
        self.review_text_edit.clear()
        self.review_image_base64 = None
        self.review_image_preview.clear()
        self.review_image_preview.setVisible(False)
        self.review_status_label.clear()
            
    def _start_review(self):
        """开始批量复盘"""
        raw_text = self.review_text_edit.toPlainText().strip()
        
        # 检查是否有输入
        if not raw_text and not self.review_image_base64:
            QMessageBox.warning(self, "错误", "请输入题目内容或粘贴图片")
            return
            
        # 获取当前项目
        current_project = self.project_service.get_current_project()
        
        # 禁用按钮
        self.review_btn.setEnabled(False)
        self.review_progress_bar.setVisible(True)
        self.review_progress_bar.setValue(0)
        self.review_status_label.setText("正在清洗...")
        
        # 开始批量复盘
        self.batch_review_service.start_review(raw_text, current_project, self.review_image_base64)
        
    def _on_review_progress(self, percent, message):
        """复盘进度更新"""
        self.review_progress_bar.setValue(percent)
        self.review_status_label.setText(message)
        
    def _on_review_complete(self, success_count, total_count):
        """复盘完成"""
        self.review_btn.setEnabled(True)
        self.review_progress_bar.setVisible(False)
        self.review_status_label.setText(f"完成：成功入库 {success_count}/{total_count} 道题目")
        self.statusBar().showMessage(f"批量复盘完成：{success_count} 道题目已入库", 5000)
        
    def _on_review_error(self, error):
        """复盘错误"""
        self.review_btn.setEnabled(True)
        self.review_progress_bar.setVisible(False)
        self.review_status_label.setText(f"错误：{error}")
        QMessageBox.warning(self, "错误", f"批量复盘失败：{error}")
        
    def closeEvent(self, event):
        """关闭事件"""
        self.db_service.close()
        self.project_service.close()
        super().closeEvent(event)