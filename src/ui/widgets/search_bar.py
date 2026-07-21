from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit


class SearchBar(QWidget):
    def __init__(self, placeholder="Search..."):
        super().__init__()

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)

        layout = QHBoxLayout()
        layout.addWidget(QLabel("🔍 Search"))
        layout.addWidget(self.input)

        self.setLayout(layout)

    def text(self):
        return self.input.text()

    def text_changed(self):
        return self.input.textChanged