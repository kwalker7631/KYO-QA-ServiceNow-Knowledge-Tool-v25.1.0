# gui_components.py
from PySide6.QtWidgets import QPushButton, QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer, Qt
import random

class RudeButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.original_text = text
        self.is_animating = False
        self.animation_frames = ["┌П┐(•_•)", "┌П┐(¬_¬)", "┌П┐(°_°)", "┌П┐(>_<)"]
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._animate_step)
        self.stop_timer = QTimer(self)
        self.stop_timer.setSingleShot(True)
        self.stop_timer.timeout.connect(self.stop_animation)

    def start_animation(self):
        if self.is_animating: return
        self.is_animating = True
        self.setStyleSheet("background-color: #E31A2F; color: white;")
        self.animation_timer.start(100)
        self.stop_timer.start(5000)

    def _animate_step(self):
        if not self.is_animating: return
        self.setText(random.choice(self.animation_frames))

    def stop_animation(self):
        self.is_animating = False
        self.animation_timer.stop()
        self.setStyleSheet("")
        self.setText(self.original_text)

class StatusIndicator(QFrame):
    def __init__(self, label_text, icon_char, color, parent=None):
        super().__init__(parent)
        self.count = 0
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        self.icon_label = QLabel(icon_char)
        self.icon_label.setStyleSheet(f"color: {color}; font-size: 24px;")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.text_label = QLabel(label_text)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.count_label = QLabel(str(self.count))
        self.count_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self.count_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.count_label)
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)

    def increment(self):
        self.count += 1
        self.count_label.setText(str(self.count))

    def reset(self):
        self.count = 0
        self.count_label.setText(str(self.count))