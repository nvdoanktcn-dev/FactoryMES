from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QWidget,
)


class ActionButtons(QWidget):
    """
    Các nút thao tác của Master Import.
    """

    preview_requested = Signal()

    validate_requested = Signal()

    import_requested = Signal()

    rollback_requested = Signal()

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        self.btn_preview = QPushButton(
            "Preview"
        )

        self.btn_validate = QPushButton(
            "Validate"
        )

        self.btn_import = QPushButton(
            "Import"
        )

        self.btn_rollback = QPushButton(
            "Rollback"
        )

        self._configure()

        self._build_ui()

        self._connect_events()

    # ======================================================

    def _configure(self):

        for button in (
            self.btn_preview,
            self.btn_validate,
            self.btn_import,
            self.btn_rollback,
        ):

            button.setMinimumWidth(
                90
            )

            button.setMinimumHeight(
                32
            )

        self.btn_import.setEnabled(
            False
        )

        self.btn_rollback.setEnabled(
            False
        )

    # ======================================================

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
            self.btn_preview
        )

        layout.addWidget(
            self.btn_validate
        )

        layout.addWidget(
            self.btn_import
        )

        layout.addWidget(
            self.btn_rollback
        )

    # ======================================================

    def _connect_events(self):

        self.btn_preview.clicked.connect(
            self.preview_requested.emit
        )

        self.btn_validate.clicked.connect(
            self.validate_requested.emit
        )

        self.btn_import.clicked.connect(
            self.import_requested.emit
        )

        self.btn_rollback.clicked.connect(
            self.rollback_requested.emit
        )

    # ======================================================

    def set_validation_state(
        self,
        valid,
    ):

        self.btn_import.setEnabled(
            bool(valid)
        )

    def set_rollback_enabled(
        self,
        enabled,
    ):

        self.btn_rollback.setEnabled(
            bool(enabled)
        )

    def set_loading(
        self,
        loading,
    ):
        enabled = not loading

        self.btn_preview.setEnabled(
            enabled
        )

        self.btn_validate.setEnabled(
            enabled
        )

        if loading:
            self.btn_import.setEnabled(
                False
            )

            self.btn_rollback.setEnabled(
                False
            )