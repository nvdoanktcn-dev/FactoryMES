from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QWidget,
)


class FileSelector(QWidget):
    """
    Widget chọn file Excel cho Master Import.
    """

    select_file_requested = Signal()

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        self.label = QLabel(
            "File"
        )

        self.path_edit = QLineEdit()

        self.btn_select = QPushButton(
            "Select File"
        )

        self._configure()
        self._build_ui()
        self._connect_events()

    # ==========================================================
    # Setup
    # ==========================================================

    def _configure(self):
        self.label.setMinimumWidth(
            28
        )

        self.path_edit.setReadOnly(
            True
        )

        self.path_edit.setPlaceholderText(
            "Select an Excel file..."
        )

        self.path_edit.setMinimumWidth(
            320
        )

        self.path_edit.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        self.btn_select.setMinimumWidth(
            95
        )

        self.btn_select.setMinimumHeight(
            32
        )

    def _build_ui(self):
        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(8)

        layout.addWidget(
            self.label
        )

        layout.addWidget(
            self.path_edit,
            1,
        )

        layout.addWidget(
            self.btn_select
        )

    def _connect_events(self):
        self.btn_select.clicked.connect(
            self.select_file_requested.emit
        )

    # ==========================================================
    # Public API
    # ==========================================================

    def file_path(self):
        return self.path_edit.text().strip()

    def set_file_path(
        self,
        file_path,
    ):
        normalized_path = str(
            file_path or ""
        ).strip()

        self.path_edit.setText(
            normalized_path
        )

        self.path_edit.setToolTip(
            normalized_path
        )

    def file_name(self):
        file_path = self.file_path()

        if not file_path:
            return ""

        return Path(
            file_path
        ).name

    def clear(self):
        self.path_edit.clear()
        self.path_edit.setToolTip("")

    def has_file(self):
        return bool(
            self.file_path()
        )

    def set_loading(
        self,
        loading,
    ):
        self.btn_select.setEnabled(
            not loading
        )