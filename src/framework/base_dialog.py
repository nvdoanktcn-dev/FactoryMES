from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
)


class BaseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.main_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()

        self.btn_save = QPushButton("💾 Save")
        self.btn_cancel = QPushButton("❌ Cancel")

        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        self.button_layout.addStretch()
        self.button_layout.addWidget(self.btn_save)
        self.button_layout.addWidget(self.btn_cancel)

    def finish_layout(self):
        self.main_layout.addLayout(self.button_layout)
        self.setLayout(self.main_layout)