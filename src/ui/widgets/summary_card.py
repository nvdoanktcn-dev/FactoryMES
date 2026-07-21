from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QFrame


class SummaryCard(QFrame):

    def __init__(self, title, value="0", color="#1976D2", icon="📊"):
        super().__init__()

        self.setMinimumHeight(100)

        self.setStyleSheet(f"""
        QFrame{{
            background:white;
            border-radius:10px;
            border:1px solid #CFD8DC;
            border-left:8px solid {color};
        }}
        """)

        layout = QVBoxLayout()

        self.title = QLabel(f"{icon}  {title}")
        self.title.setStyleSheet("""
            font-size:15px;
            color:#616161;
            font-weight:bold;
        """)

        self.value = QLabel(value)

        self.value.setAlignment(Qt.AlignCenter)

        self.value.setStyleSheet("""
            font-size:30px;
            font-weight:bold;
            color:#263238;
        """)

        layout.addWidget(self.title)
        layout.addStretch()
        layout.addWidget(self.value)

        self.setLayout(layout)

    def set_value(self, value):
        self.value.setText(str(value))