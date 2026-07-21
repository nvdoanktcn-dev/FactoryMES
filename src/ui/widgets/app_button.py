from PySide6.QtWidgets import QPushButton

from src.ui.styles.button_style import (
    SUCCESS,
    INFO,
    WARNING,
    DANGER,
    PURPLE,
    CYAN,
)


class AppButton(QPushButton):

    STYLES = {
        "success": SUCCESS,
        "info": INFO,
        "warning": WARNING,
        "danger": DANGER,
        "purple": PURPLE,
        "cyan": CYAN,
    }

    def __init__(self, text, style="info"):
        super().__init__(text)

        self.setMinimumHeight(36)

        if style in self.STYLES:
            self.setStyleSheet(self.STYLES[style])