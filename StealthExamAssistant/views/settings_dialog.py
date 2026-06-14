from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QLineEdit, QGroupBox, QMessageBox,
                               QFrame, QScrollArea, QWidget, QFormLayout,
                               QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, Signal
from models.env_manager import EnvManager


# Material Design 3 样式表
MD3_STYLESHEET = """
QDialog {
    background-color: #121212;
    color: #E0E0E0;
    font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif;
}

/* 标题 */
#dialogTitle {
    color: #FFFFFF;
    font-size: 22px;
    font-weight: 600;
    padding: 16px 0 8px 0;
}

/* 卡片容器 */
#card {
    background-color: #1E1E1E;
    border: none;
    border-radius: 12px;
    padding: 0;
}

/* 区域标题 */
#sectionTitle {
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 600;
    padding: 0;
}

/* 说明文字 */
#description {
    color: #9E9E9E;
    font-size: 12px;
    line-height: 1.5;
}

/* 提示信息 */
#infoLabel {
    color: #FFB74D;
    font-size: 11px;
    padding: 12px 16px;
    background-color: rgba(255, 183, 77, 0.08);
    border-radius: 8px;
    border: none;
}

/* 输入框 */
QLineEdit {
    background-color: #2C2C2C;
    border: 1px solid #3C3C3C;
    border-radius: 8px;
    padding: 12px 16px;
    color: #FFFFFF;
    font-size: 13px;
    selection-background-color: #00BCD4;
}

QLineEdit:hover {
    border: 1px solid #4CAF50;
}

QLineEdit:focus {
    border: 2px solid #00BCD4;
    background-color: #333333;
}

QLineEdit::placeholder {
    color: #616161;
}

/* 标签 */
QLabel {
    color: #BDBDBD;
    font-size: 13px;
}

/* 状态标签 */
#statusLabel {
    font-size: 12px;
    padding: 8px 12px;
    border-radius: 6px;
    background-color: rgba(255, 255, 255, 0.05);
}

/* 按钮基础样式 */
QPushButton {
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 13px;
    font-weight: 600;
}

/* 测试连接按钮 - Outlined 风格 */
#testButton {
    background-color: transparent;
    border: 1px solid #00BCD4;
    color: #00BCD4;
}

#testButton:hover {
    background-color: rgba(0, 188, 212, 0.08);
}

#testButton:pressed {
    background-color: rgba(0, 188, 212, 0.15);
}

/* 保存按钮 - Filled 风格 */
#saveButton {
    background-color: #00BCD4;
    color: #000000;
    font-weight: 700;
}

#saveButton:hover {
    background-color: #26C6DA;
}

#saveButton:pressed {
    background-color: #00ACC1;
}

/* 关闭按钮 - Text 风格 */
#closeButton {
    background-color: transparent;
    color: #9E9E9E;
    padding: 8px 16px;
}

#closeButton:hover {
    background-color: rgba(255, 255, 255, 0.05);
    color: #FFFFFF;
}

/* 滚动区域 */
#scrollArea {
    background-color: transparent;
    border: none;
}

/* 滚动内容 */
#scrollContent {
    background-color: transparent;
}
"""


class SettingsDialog(QDialog):
    """设置对话框：Material Design 3 风格"""
    
    # 信号
    settings_saved = Signal()
    
    def __init__(self, embedding_service=None, llm_service=None, hotkey_manager=None, parent=None):
        super().__init__(parent)
        self.embedding_service = embedding_service
        self.llm_service = llm_service
        self.hotkey_manager = hotkey_manager
        self.env_manager = EnvManager()
        
        self.setWindowTitle("设置")
        self.setMinimumSize(520, 480)
        self.resize(520, 620)
        self.setModal(True)
        
        self.setStyleSheet(MD3_STYLESHEET)
        self._setup_ui()
        self._load_settings()
        
    def _setup_ui(self):
        """设置 UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 16, 24, 24)
        main_layout.setSpacing(16)
        
        # 标题
        title_label = QLabel("设置")
        title_label.setObjectName("dialogTitle")
        main_layout.addWidget(title_label)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setObjectName("scrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 滚动内容
        scroll_content = QWidget()
        scroll_content.setObjectName("scrollContent")
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(0, 0, 8, 0)
        content_layout.setSpacing(16)
        
        # ==================== 云端 API 卡片 ====================
        cloud_card = self._create_card(
            "☁️  云端 API（LLM 推理）",
            [
                ("API 地址", "cloud_base_input", "https://your-api-endpoint.com/v1"),
                ("API Key", "cloud_key_input", "输入云端 API Key"),
                ("推理模型", "cloud_model_input", "输入模型名称"),
            ],
            "test_cloud_btn",
            "测试云端连接"
        )
        content_layout.addWidget(cloud_card)
        
        # 云端状态
        self.cloud_status_label = QLabel("")
        self.cloud_status_label.setObjectName("statusLabel")
        content_layout.addWidget(self.cloud_status_label)
        
        # ==================== 本地 Embedding 卡片 ====================
        embedding_card = self._create_card(
            "🔧  本地 Embedding（向量检索）",
            [
                ("API 地址", "ollama_base_input", "http://127.0.0.1:11434/v1"),
                ("模型名称", "ollama_model_input", "nomic-embed-text"),
            ],
            "test_ollama_btn",
            "测试 Ollama 连接"
        )
        content_layout.addWidget(embedding_card)
        
        # 提示信息
        info_label = QLabel("💡 首次使用请在终端执行: ollama pull nomic-embed-text")
        info_label.setObjectName("infoLabel")
        info_label.setWordWrap(True)
        content_layout.addWidget(info_label)
        
        # Ollama 状态
        self.ollama_status_label = QLabel("")
        self.ollama_status_label.setObjectName("statusLabel")
        content_layout.addWidget(self.ollama_status_label)
        
        # ==================== 快捷键卡片 ====================
        hotkey_card = self._create_card(
            "⌨️  快捷键配置",
            [
                ("显示/隐藏 HUD", "hotkey_toggle_input", "ctrl+shift+o"),
                ("单次识别", "hotkey_recognize_input", "ctrl+shift+a"),
                ("老板键（紧急隐藏）", "hotkey_panic_input", "ctrl+shift+x"),
                ("退出程序", "hotkey_quit_input", "ctrl+shift+q"),
            ]
        )
        content_layout.addWidget(hotkey_card)
        
        # 快捷键提示
        hotkey_info = QLabel("💡 格式: ctrl+shift+字母（修改后需重启程序生效）")
        hotkey_info.setObjectName("infoLabel")
        hotkey_info.setWordWrap(True)
        content_layout.addWidget(hotkey_info)
        
        content_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)
        
        # ==================== 底部按钮 ====================
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        close_btn = QPushButton("关闭")
        close_btn.setObjectName("closeButton")
        close_btn.setFixedSize(80, 36)
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        # 添加弹性空间，将保存按钮推到右下角
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        save_btn = QPushButton("保存配置")
        save_btn.setObjectName("saveButton")
        save_btn.setFixedSize(100, 36)
        save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(save_btn)
        
        main_layout.addLayout(button_layout)
        
    def _create_card(self, title, fields, test_btn_name=None, test_btn_text=None):
        """创建卡片组件"""
        card = QFrame()
        card.setObjectName("card")
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(16)
        
        # 标题
        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        card_layout.addWidget(title_label)
        
        # 表单布局
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        for label_text, field_name, placeholder in fields:
            label = QLabel(f"{label_text}:")
            input_field = QLineEdit()
            input_field.setObjectName(field_name)
            input_field.setPlaceholderText(placeholder)
            
            # 密码模式（仅对 API Key 输入框生效，排除快捷键输入框）
            if ("api_key" in field_name.lower() or field_name == "cloud_key_input") and "hotkey" not in field_name.lower():
                input_field.setEchoMode(QLineEdit.EchoMode.Password)
                
            form_layout.addRow(label, input_field)
            
            # 保存引用
            setattr(self, field_name, input_field)
            
        card_layout.addLayout(form_layout)
        
        # 测试按钮
        if test_btn_name and test_btn_text:
            test_btn = QPushButton(test_btn_text)
            test_btn.setObjectName("testButton")
            test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            if "cloud" in test_btn_name:
                test_btn.clicked.connect(self._test_cloud_connection)
            elif "ollama" in test_btn_name:
                test_btn.clicked.connect(self._test_ollama_connection)
                
            card_layout.addWidget(test_btn)
            
        return card
        
    def _load_settings(self):
        """加载设置"""
        # 云端 API
        self.cloud_base_input.setText(self.env_manager.read("LLM_API_BASE_URL", ""))
        self.cloud_key_input.setText(self.env_manager.read("LLM_API_KEY", ""))
        self.cloud_model_input.setText(self.env_manager.read("LLM_MODEL_NAME", ""))
        
        # Ollama
        self.ollama_base_input.setText(self.env_manager.read("EMBEDDING_API_BASE_URL", "http://127.0.0.1:11434/v1"))
        self.ollama_model_input.setText(self.env_manager.read("EMBEDDING_MODEL_NAME", "nomic-embed-text"))
        
        # 快捷键
        self.hotkey_toggle_input.setText(self.env_manager.read("HOTKEY_TOGGLE", "ctrl+shift+o"))
        self.hotkey_recognize_input.setText(self.env_manager.read("HOTKEY_RECOGNIZE", "ctrl+shift+a"))
        self.hotkey_panic_input.setText(self.env_manager.read("HOTKEY_PANIC", "ctrl+shift+x"))
        self.hotkey_quit_input.setText(self.env_manager.read("HOTKEY_QUIT", "ctrl+shift+q"))
        
        # 更新状态
        self._update_status()
        
    def _update_status(self):
        """更新状态显示"""
        # 云端状态
        if self.llm_service and self.llm_service.is_configured():
            self.cloud_status_label.setText("✓ 云端 API 已配置")
            self.cloud_status_label.setStyleSheet("color: #4CAF50;")
        else:
            self.cloud_status_label.setText("○ 云端 API 未配置")
            self.cloud_status_label.setStyleSheet("color: #FF9800;")
            
        # Ollama 状态
        if self.embedding_service and self.embedding_service.is_configured():
            self.ollama_status_label.setText("✓ Ollama 已连接")
            self.ollama_status_label.setStyleSheet("color: #4CAF50;")
        else:
            self.ollama_status_label.setText("○ Ollama 未连接")
            self.ollama_status_label.setStyleSheet("color: #FF9800;")
            
    def _test_cloud_connection(self):
        """测试云端连接"""
        api_base = self.cloud_base_input.text().strip()
        api_key = self.cloud_key_input.text().strip()
        model_name = self.cloud_model_input.text().strip()
        
        if not api_base or not api_key:
            QMessageBox.warning(self, "错误", "请输入云端 API 地址和 API Key")
            return
            
        if self.llm_service:
            self.llm_service.api_base = api_base
            self.llm_service.api_key = api_key
            self.llm_service.model_name = model_name
            
            self.cloud_status_label.setText("正在测试...")
            self.cloud_status_label.setStyleSheet("color: #FFB74D;")
            
            success, message = self.llm_service.test_connection()
            
            if success:
                self.cloud_status_label.setText(f"✓ {message[:50]}")
                self.cloud_status_label.setStyleSheet("color: #4CAF50;")
                QMessageBox.information(self, "成功", message)
            else:
                self.cloud_status_label.setText(f"✗ {message[:50]}")
                self.cloud_status_label.setStyleSheet("color: #F44336;")
                QMessageBox.warning(self, "失败", message)
                
    def _test_ollama_connection(self):
        """测试 Ollama 连接"""
        api_base = self.ollama_base_input.text().strip()
        model_name = self.ollama_model_input.text().strip()
        
        if not api_base or not model_name:
            QMessageBox.warning(self, "错误", "请输入 Ollama API 地址和模型名称")
            return
            
        if self.embedding_service:
            self.embedding_service.api_base = api_base
            self.embedding_service.model_name = model_name
            
            self.ollama_status_label.setText("正在测试...")
            self.ollama_status_label.setStyleSheet("color: #FFB74D;")
            
            success, message = self.embedding_service.test_connection()
            
            if success:
                self.ollama_status_label.setText(f"✓ {message[:50]}")
                self.ollama_status_label.setStyleSheet("color: #4CAF50;")
                QMessageBox.information(self, "成功", message)
            else:
                self.ollama_status_label.setText(f"✗ {message[:50]}")
                self.ollama_status_label.setStyleSheet("color: #F44336;")
                QMessageBox.warning(self, "失败", message)
                
    def _save_settings(self):
        """保存设置"""
        # 云端 API
        self.env_manager.write("LLM_API_BASE_URL", self.cloud_base_input.text().strip())
        self.env_manager.write("LLM_API_KEY", self.cloud_key_input.text().strip())
        self.env_manager.write("LLM_MODEL_NAME", self.cloud_model_input.text().strip())
        
        # Ollama
        self.env_manager.write("EMBEDDING_MODE", "local")
        self.env_manager.write("EMBEDDING_API_KEY", "ollama")
        self.env_manager.write("EMBEDDING_API_BASE_URL", self.ollama_base_input.text().strip())
        self.env_manager.write("EMBEDDING_MODEL_NAME", self.ollama_model_input.text().strip())
        
        # 快捷键
        self.env_manager.write("HOTKEY_TOGGLE", self.hotkey_toggle_input.text().strip())
        self.env_manager.write("HOTKEY_RECOGNIZE", self.hotkey_recognize_input.text().strip())
        self.env_manager.write("HOTKEY_PANIC", self.hotkey_panic_input.text().strip())
        self.env_manager.write("HOTKEY_QUIT", self.hotkey_quit_input.text().strip())
        
        # 热更新运行时配置
        self._update_runtime_config()
        
        self.settings_saved.emit()
        QMessageBox.information(self, "成功", "配置已保存并立即生效！")
        
    def _update_runtime_config(self):
        """热更新运行时配置"""
        # 更新 LLM 服务配置
        if self.llm_service:
            self.llm_service.api_base = self.cloud_base_input.text().strip()
            self.llm_service.api_key = self.cloud_key_input.text().strip()
            self.llm_service.model_name = self.cloud_model_input.text().strip()
            print("[Settings] LLM 服务配置已热更新")
            
        # 更新 Embedding 服务配置
        if self.embedding_service:
            self.embedding_service.api_base = self.ollama_base_input.text().strip()
            self.embedding_service.model_name = self.ollama_model_input.text().strip()
            print("[Settings] Embedding 服务配置已热更新")
            
        # 更新快捷键配置
        if self.hotkey_manager:
            self.hotkey_manager.update_hotkeys(
                toggle=self.hotkey_toggle_input.text().strip(),
                quit_app=self.hotkey_quit_input.text().strip(),
                panic=self.hotkey_panic_input.text().strip(),
                recognize=self.hotkey_recognize_input.text().strip()
            )
            print("[Settings] 快捷键配置已热更新")