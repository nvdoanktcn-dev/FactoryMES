from PySide6.QtWidgets import (
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)


class ProgressPanel(QWidget):
    """
    Hiển thị trạng thái và tiến trình import.
    """

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        self.status_label = QLabel(
            "Ready"
        )

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(
            0,
            100,
        )
        self.progress_bar.setValue(
            0
        )

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.addWidget(
            self.status_label
        )

        layout.addWidget(
            self.progress_bar
        )

    def set_status(
        self,
        message,
    ):
        self.status_label.setText(
            str(message or "")
        )

    def set_progress(
        self,
        value,
    ):
        self.progress_bar.setValue(
            max(
                0,
                min(
                    int(value),
                    100,
                ),
            )
        )

    def reset(self):
        self.set_status("Ready")
        self.set_progress(0)