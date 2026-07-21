from PySide6.QtWidgets import (
    QListWidget,
    QVBoxLayout,
    QWidget,
)


class ValidationPanel(QWidget):
    """
    Hiển thị lỗi validation.
    """

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        self.error_list = QListWidget()

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.addWidget(
            self.error_list
        )

    def set_errors(
        self,
        errors,
    ):
        self.error_list.clear()

        errors = list(errors or [])

        if not errors:
            self.error_list.addItem(
                "Validation passed. No errors."
            )
            return

        for error in errors:
            if isinstance(error, dict):
                row = error.get(
                    "row",
                    "-",
                )

                field = error.get(
                    "field",
                    "",
                )

                message = error.get(
                    "message",
                    str(error),
                )

                text = (
                    f"Row {row}"
                    f" | {field}"
                    f" | {message}"
                )

            else:
                text = str(error)

            self.error_list.addItem(
                text
            )

    def clear_errors(self):
        self.error_list.clear()