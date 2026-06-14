from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QSizePolicy, QScrollArea)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QFont, QColor

class AnswerCard(QWidget):
    """答案卡片：Material Design 风格"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._expanded = False
        self._setup_ui()
        self._apply_style()
        
    def _setup_ui(self):
        """设置 UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 卡片容器
        self.card_frame = QFrame()
        self.card_frame.setObjectName("answerCard")
        self.card_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(8)
        
        # 来源标签
        self.source_label = QLabel()
        self.source_label.setObjectName("sourceLabel")
        self.source_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        card_layout.addWidget(self.source_label)
        
        # 答案区域
        answer_layout = QHBoxLayout()
        answer_layout.setSpacing(8)
        
        # 答案标题
        answer_title = QLabel("建议答案:")
        answer_title.setObjectName("answerTitle")
        answer_layout.addWidget(answer_title)
        
        # 答案内容
        self.answer_label = QLabel()
        self.answer_label.setObjectName("answerContent")
        self.answer_label.setWordWrap(True)
        self.answer_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        answer_layout.addWidget(self.answer_label, 1)
        
        card_layout.addLayout(answer_layout)
        
        # 展开/折叠按钮
        self.expand_btn = QPushButton("▼ 展开解析")
        self.expand_btn.setObjectName("expandButton")
        self.expand_btn.clicked.connect(self._toggle_expand)
        card_layout.addWidget(self.expand_btn)
        
        # 解析区域（默认隐藏）
        self.reasoning_frame = QFrame()
        self.reasoning_frame.setObjectName("reasoningFrame")
        self.reasoning_frame.setVisible(False)
        
        reasoning_layout = QVBoxLayout(self.reasoning_frame)
        reasoning_layout.setContentsMargins(0, 8, 0, 0)
        reasoning_layout.setSpacing(4)
        
        reasoning_title = QLabel("推理过程:")
        reasoning_title.setObjectName("reasoningTitle")
        reasoning_layout.addWidget(reasoning_title)
        
        self.reasoning_label = QLabel()
        self.reasoning_label.setObjectName("reasoningContent")
        self.reasoning_label.setWordWrap(True)
        self.reasoning_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        reasoning_layout.addWidget(self.reasoning_label)
        
        card_layout.addWidget(self.reasoning_frame)
        
        main_layout.addWidget(self.card_frame)
        
    def _apply_style(self):
        """应用样式"""
        self.setStyleSheet("""
            #answerCard {
                background-color: rgba(45, 45, 45, 0.95);
                border: 1px solid rgba(0, 150, 136, 0.3);
                border-radius: 8px;
            }
            
            #sourceLabel {
                color: #4CAF50;
                font-size: 12px;
                font-weight: bold;
                padding: 4px 8px;
                background-color: rgba(76, 175, 80, 0.1);
                border-radius: 4px;
            }
            
            #answerTitle {
                color: #aaaaaa;
                font-size: 11px;
            }
            
            #answerContent {
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
                padding: 8px;
                background-color: rgba(0, 150, 136, 0.1);
                border-radius: 4px;
            }
            
            #expandButton {
                background-color: transparent;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                padding: 6px;
                color: #aaaaaa;
                font-size: 11px;
            }
            
            #expandButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: #ffffff;
            }
            
            #reasoningFrame {
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                padding-top: 8px;
            }
            
            #reasoningTitle {
                color: #FF9800;
                font-size: 11px;
                font-weight: bold;
            }
            
            #reasoningContent {
                color: #cccccc;
                font-size: 12px;
                padding: 8px;
                background-color: rgba(255, 152, 0, 0.1);
                border-radius: 4px;
                border-left: 3px solid #FF9800;
            }
        """)
        
    def _toggle_expand(self):
        """切换展开/折叠状态"""
        self._expanded = not self._expanded
        self.reasoning_frame.setVisible(self._expanded)
        
        if self._expanded:
            self.expand_btn.setText("▲ 折叠解析")
        else:
            self.expand_btn.setText("▼ 展开解析")
            
        # 调整大小
        self.adjustSize()
        self.updateGeometry()
        
    def set_answer(self, data):
        """设置答案数据"""
        # 设置来源
        source_label = data.get("source_label", "未知来源")
        self.source_label.setText(source_label)
        
        # 根据来源设置颜色
        if "极速" in source_label:
            self.source_label.setStyleSheet("color: #4CAF50; background-color: rgba(76, 175, 80, 0.1);")
        elif "语义" in source_label:
            self.source_label.setStyleSheet("color: #2196F3; background-color: rgba(33, 150, 243, 0.1);")
        elif "AI" in source_label:
            self.source_label.setStyleSheet("color: #FF9800; background-color: rgba(255, 152, 0, 0.1);")
            
        # 设置答案
        answer = data.get("answer", "")
        self.answer_label.setText(answer)
        
        # 设置推理过程
        reasoning = data.get("reasoning", "")
        if reasoning:
            self.reasoning_label.setText(reasoning)
            self.expand_btn.setVisible(True)
        else:
            self.expand_btn.setVisible(False)
            self.reasoning_frame.setVisible(False)
            
        # 重置展开状态
        self._expanded = False
        self.expand_btn.setText("▼ 展开解析")
        
    def clear(self):
        """清空卡片"""
        self.source_label.setText("")
        self.answer_label.setText("")
        self.reasoning_label.setText("")
        self.reasoning_frame.setVisible(False)
        self.expand_btn.setVisible(False)