import base64
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTextEdit, QGroupBox, QMessageBox,
                               QLineEdit, QFrame, QFileDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QClipboard, QImage

class ReviewPanel(QWidget):
    """错题复盘录入面板（支持文本和图片）"""
    
    # 信号：question, options, answer, project, image_base64
    question_submitted = Signal(str, str, str, str, object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_project = "默认项目"
        self.current_image_base64 = None
        self._setup_ui()
        self._apply_style()
        
    def _setup_ui(self):
        """设置 UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        # 标题
        title_label = QLabel("错题录入")
        title_label.setObjectName("panelTitle")
        main_layout.addWidget(title_label)
        
        # 项目选择
        project_layout = QHBoxLayout()
        project_label = QLabel("当前项目:")
        self.project_display = QLabel("默认项目")
        self.project_display.setObjectName("projectDisplay")
        project_layout.addWidget(project_label)
        project_layout.addWidget(self.project_display)
        project_layout.addStretch()
        main_layout.addLayout(project_layout)
        
        # 原始内容输入
        input_group = QGroupBox("原始内容（粘贴文本或图片）")
        input_layout = QVBoxLayout(input_group)
        
        # 图片预览区域
        self.image_preview = QLabel()
        self.image_preview.setObjectName("imagePreview")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setMinimumHeight(100)
        self.image_preview.setMaximumHeight(200)
        self.image_preview.setVisible(False)
        input_layout.addWidget(self.image_preview)
        
        # 文本输入
        self.input_text = QTextEdit()
        self.input_text.setObjectName("inputText")
        self.input_text.setPlaceholderText(
            "在此粘贴题目内容...\n\n"
            "支持格式：\n"
            "- 纯文本题目\n"
            "- 带选项的选择题\n"
            "- 粘贴图片（Ctrl+V）\n"
            "- 任意格式，AI 会自动清洗"
        )
        self.input_text.setMinimumHeight(120)
        input_layout.addWidget(self.input_text)
        
        # 按钮区域
        button_row = QHBoxLayout()
        
        paste_btn = QPushButton("📋 粘贴文本")
        paste_btn.setObjectName("pasteButton")
        paste_btn.clicked.connect(self._paste_text)
        button_row.addWidget(paste_btn)
        
        paste_image_btn = QPushButton("🖼️ 粘贴图片")
        paste_image_btn.setObjectName("pasteImageButton")
        paste_image_btn.clicked.connect(self._paste_image)
        button_row.addWidget(paste_image_btn)
        
        upload_btn = QPushButton("📁 上传图片")
        upload_btn.setObjectName("uploadButton")
        upload_btn.clicked.connect(self._upload_image)
        button_row.addWidget(upload_btn)
        
        clear_btn = QPushButton("🗑️ 清空")
        clear_btn.setObjectName("clearButton")
        clear_btn.clicked.connect(self._clear_input)
        button_row.addWidget(clear_btn)
        
        input_layout.addLayout(button_row)
        
        main_layout.addWidget(input_group)
        
        # AI 清洗结果
        result_group = QGroupBox("AI 清洗结果")
        result_layout = QVBoxLayout(result_group)
        
        # 题干
        q_layout = QHBoxLayout()
        q_label = QLabel("题干:")
        self.question_edit = QLineEdit()
        self.question_edit.setObjectName("questionEdit")
        self.question_edit.setPlaceholderText("AI 提取的题干")
        q_layout.addWidget(q_label)
        q_layout.addWidget(self.question_edit)
        result_layout.addLayout(q_layout)
        
        # 选项
        o_layout = QHBoxLayout()
        o_label = QLabel("选项:")
        self.options_edit = QLineEdit()
        self.options_edit.setObjectName("optionsEdit")
        self.options_edit.setPlaceholderText("AI 提取的选项")
        o_layout.addWidget(o_label)
        o_layout.addWidget(self.options_edit)
        result_layout.addLayout(o_layout)
        
        # 答案
        a_layout = QHBoxLayout()
        a_label = QLabel("答案:")
        self.answer_edit = QLineEdit()
        self.answer_edit.setObjectName("answerEdit")
        self.answer_edit.setPlaceholderText("AI 提取的答案")
        a_layout.addWidget(a_label)
        a_layout.addWidget(self.answer_edit)
        result_layout.addLayout(a_layout)
        
        main_layout.addWidget(result_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.ai_clean_btn = QPushButton("🤖 AI 清洗")
        self.ai_clean_btn.setObjectName("aiCleanButton")
        self.ai_clean_btn.clicked.connect(self._request_ai_clean)
        button_layout.addWidget(self.ai_clean_btn)
        
        self.submit_btn = QPushButton("✅ 确认入库")
        self.submit_btn.setObjectName("submitButton")
        self.submit_btn.clicked.connect(self._submit_question)
        self.submit_btn.setEnabled(False)
        button_layout.addWidget(self.submit_btn)
        
        main_layout.addLayout(button_layout)
        
        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        main_layout.addWidget(self.status_label)
        
        main_layout.addStretch()
        
        # 启用粘贴事件
        self.input_text.installEventFilter(self)
        
    def eventFilter(self, obj, event):
        """事件过滤器：处理粘贴事件"""
        if obj == self.input_text and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_V and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self._paste_image()
                return True
        return super().eventFilter(obj, event)
        
    def _apply_style(self):
        """应用样式"""
        self.setStyleSheet("""
            #panelTitle {
                color: #009688;
                font-size: 18px;
                font-weight: bold;
                padding: 8px 0;
            }
            
            #projectDisplay {
                color: #FF9800;
                font-weight: bold;
                padding: 4px 8px;
                background-color: rgba(255, 152, 0, 0.1);
                border-radius: 4px;
            }
            
            #imagePreview {
                background-color: rgba(50, 50, 50, 0.9);
                border: 2px dashed rgba(0, 150, 136, 0.5);
                border-radius: 8px;
                padding: 8px;
            }
            
            QGroupBox {
                background-color: rgba(40, 40, 40, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                color: #ffffff;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #009688;
            }
            
            QTextEdit {
                background-color: rgba(50, 50, 50, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                padding: 8px;
                color: #ffffff;
                font-size: 13px;
            }
            
            QLineEdit {
                background-color: rgba(50, 50, 50, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                padding: 8px;
                color: #ffffff;
                font-size: 13px;
            }
            
            QLineEdit:focus {
                border: 1px solid #009688;
            }
            
            QPushButton {
                background-color: rgba(0, 150, 136, 0.8);
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                color: white;
                font-weight: bold;
                font-size: 12px;
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
            
            #pasteButton {
                background-color: rgba(33, 150, 243, 0.8);
            }
            
            #pasteButton:hover {
                background-color: rgba(33, 150, 243, 1.0);
            }
            
            #pasteImageButton {
                background-color: rgba(156, 39, 176, 0.8);
            }
            
            #pasteImageButton:hover {
                background-color: rgba(156, 39, 176, 1.0);
            }
            
            #uploadButton {
                background-color: rgba(255, 152, 0, 0.8);
            }
            
            #uploadButton:hover {
                background-color: rgba(255, 152, 0, 1.0);
            }
            
            #clearButton {
                background-color: rgba(244, 67, 54, 0.8);
            }
            
            #clearButton:hover {
                background-color: rgba(244, 67, 54, 1.0);
            }
            
            #aiCleanButton {
                background-color: rgba(255, 152, 0, 0.8);
            }
            
            #aiCleanButton:hover {
                background-color: rgba(255, 152, 0, 1.0);
            }
            
            #submitButton {
                background-color: rgba(76, 175, 80, 0.8);
            }
            
            #submitButton:hover {
                background-color: rgba(76, 175, 80, 1.0);
            }
            
            #statusLabel {
                color: #aaaaaa;
                font-style: italic;
            }
        """)
        
    def _paste_text(self):
        """粘贴文本"""
        clipboard = QClipboard()
        text = clipboard.text()
        if text:
            self.input_text.setPlainText(text)
            self.current_image_base64 = None
            self.image_preview.setVisible(False)
            
    def _paste_image(self):
        """粘贴图片"""
        clipboard = QClipboard()
        image = clipboard.image()
        
        if image.isNull():
            self.status_label.setText("剪贴板中没有图片")
            return
            
        # 显示预览
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(
            self.image_preview.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_preview.setPixmap(scaled_pixmap)
        self.image_preview.setVisible(True)
        
        # 转换为 base64
        self.current_image_base64 = self._image_to_base64(image)
        self.status_label.setText("图片已加载，点击 AI 清洗进行识别")
        
    def _upload_image(self):
        """上传图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                self.status_label.setText("无法加载图片")
                return
                
            # 显示预览
            scaled_pixmap = pixmap.scaled(
                self.image_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_preview.setPixmap(scaled_pixmap)
            self.image_preview.setVisible(True)
            
            # 转换为 base64
            image = pixmap.toImage()
            self.current_image_base64 = self._image_to_base64(image)
            self.status_label.setText("图片已加载，点击 AI 清洗进行识别")
            
    def _image_to_base64(self, image):
        """将 QImage 转换为 base64 字符串"""
        import io
        buffer = io.BytesIO()
        pixmap = QPixmap.fromImage(image)
        pixmap.save(buffer, "PNG")
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')
        
    def _clear_input(self):
        """清空输入"""
        self.input_text.clear()
        self.current_image_base64 = None
        self.image_preview.clear()
        self.image_preview.setVisible(False)
        self.question_edit.clear()
        self.options_edit.clear()
        self.answer_edit.clear()
        self.submit_btn.setEnabled(False)
        self.status_label.clear()
        
    def _request_ai_clean(self):
        """请求 AI 清洗"""
        raw_text = self.input_text.toPlainText().strip()
        
        # 检查是否有输入
        if not raw_text and not self.current_image_base64:
            self.status_label.setText("请输入题目内容或粘贴图片")
            return
            
        self.status_label.setText("正在请求 AI 清洗...")
        self.ai_clean_btn.setEnabled(False)
        
        # 发送信号（由外部处理）
        self.question_submitted.emit(
            raw_text, "", "", self.current_project, self.current_image_base64
        )
        
    def _submit_question(self):
        """确认入库"""
        question = self.question_edit.text().strip()
        options = self.options_edit.text().strip()
        answer = self.answer_edit.text().strip()
        
        if not question:
            self.status_label.setText("题干不能为空")
            return
            
        if not answer:
            self.status_label.setText("答案不能为空")
            return
            
        # 发送信号
        self.question_submitted.emit(
            question, options, answer, self.current_project, None
        )
        self.status_label.setText("已提交入库")
        
    def set_project(self, project_name):
        """设置当前项目"""
        self.current_project = project_name
        self.project_display.setText(project_name)
        
    def set_ai_result(self, question, options, answer):
        """设置 AI 清洗结果"""
        self.question_edit.setText(question)
        self.options_edit.setText(options)
        self.answer_edit.setText(answer)
        self.submit_btn.setEnabled(True)
        self.ai_clean_btn.setEnabled(True)
        self.status_label.setText("AI 清洗完成，请确认后入库")
        
    def set_status(self, message):
        """设置状态信息"""
        self.status_label.setText(message)
        
    def clear(self):
        """清空面板"""
        self.input_text.clear()
        self.question_edit.clear()
        self.options_edit.clear()
        self.answer_edit.clear()
        self.current_image_base64 = None
        self.image_preview.clear()
        self.image_preview.setVisible(False)
        self.submit_btn.setEnabled(False)
        self.ai_clean_btn.setEnabled(True)
        self.status_label.clear()