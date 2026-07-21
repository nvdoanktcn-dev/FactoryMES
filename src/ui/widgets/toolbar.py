from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout

from src.ui.styles.button_style import (
    SUCCESS,
    INFO,
    DANGER,
    WARNING,
    PURPLE,
    CYAN,
)


class Toolbar(QWidget):

    def __init__(self):
        super().__init__()

        self.btn_add = QPushButton("➕  Add")
        self.btn_edit = QPushButton("✏  Edit")
        self.btn_delete = QPushButton("🗑  Delete")

        self.btn_import = QPushButton("📥  Import")
        self.btn_export = QPushButton("📤  Export")

        self.btn_refresh = QPushButton("🔄  Refresh")

        self.btn_add.setStyleSheet(SUCCESS)
        self.btn_edit.setStyleSheet(INFO)
        self.btn_delete.setStyleSheet(DANGER)

        self.btn_import.setStyleSheet(WARNING)
        self.btn_export.setStyleSheet(PURPLE)

        self.btn_refresh.setStyleSheet(CYAN)

        layout = QHBoxLayout()

        layout.addWidget(self.btn_add)
        layout.addWidget(self.btn_edit)
        layout.addWidget(self.btn_delete)

        layout.addSpacing(20)

        layout.addWidget(self.btn_import)
        layout.addWidget(self.btn_export)

        layout.addSpacing(20)

        layout.addWidget(self.btn_refresh)

        layout.addStretch()

        self.setLayout(layout)