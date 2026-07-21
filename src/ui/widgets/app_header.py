from datetime import datetime
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel


class AppHeader(QWidget):
    def __init__(self):
        super().__init__()

        layout = QHBoxLayout()

        title = QLabel("🏭 FactoryMES V1.0")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")

        info = QLabel("🌐 VI | 中文    👤 Admin")
        info.setStyleSheet("font-size: 14px; color: white;")

        self.clock = QLabel()
        self.clock.setStyleSheet("font-size: 14px; color: white;")
        self.update_clock()

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(info)
        layout.addWidget(self.clock)

        self.setLayout(layout)
        self.setStyleSheet("background-color: #1976D2; padding: 8px;")

    def update_clock(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.clock.setText(f"🕒 {now}")