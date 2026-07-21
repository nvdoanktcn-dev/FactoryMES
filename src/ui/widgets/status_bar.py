from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel


class AppStatusBar(QWidget):
    def __init__(self):
        super().__init__()

        layout = QHBoxLayout()

        self.db_status = QLabel("🟢 DB Connected")
        self.user = QLabel("👤 Admin")
        self.version = QLabel("Version 0.3.0")

        layout.addWidget(self.db_status)
        layout.addStretch()
        layout.addWidget(self.user)
        layout.addWidget(self.version)

        self.setLayout(layout)
        self.setStyleSheet(
            """
            QWidget {
                background-color: #ECEFF1;
                padding: 6px;
                border-top: 1px solid #CFD8DC;
            }
            QLabel {
                color: #263238;
                font-size: 12px;
            }
            """
        )