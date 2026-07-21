from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QWidget,
)


class SheetSelector(QWidget):
    """
    Widget chọn sheet Excel.

    Chức năng:
    - Nhận danh sách sheet.
    - Hiển thị sheet hiện tại.
    - Phát signal khi người dùng đổi sheet.
    """

    sheet_changed = Signal(str)

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        self.label = QLabel(
            "Sheet"
        )

        self.combo = QComboBox()

        self._configure()
        self._build_ui()
        self._connect_events()

    # ==========================================================
    # Setup
    # ==========================================================

    def _configure(self):
        self.label.setMinimumWidth(
            36
        )

        self.combo.setMinimumWidth(
            180
        )

        self.combo.setMaximumWidth(
            280
        )

        self.combo.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        self.combo.setEnabled(
            False
        )

        self.combo.setToolTip(
            "Select an Excel file to load sheets."
        )

    def _build_ui(self):
        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(
            8
        )

        layout.addWidget(
            self.label
        )

        layout.addWidget(
            self.combo,
            1,
        )

    def _connect_events(self):
        self.combo.currentTextChanged.connect(
            self._emit_sheet_changed
        )

    # ==========================================================
    # Public API
    # ==========================================================

    def set_sheet_names(
        self,
        sheet_names,
        selected_sheet=None,
    ):
        normalized_names = [
            str(name or "").strip()
            for name in (sheet_names or [])
            if str(name or "").strip()
        ]

        self.combo.blockSignals(True)

        try:
            self.combo.clear()
            self.combo.addItems(
                normalized_names
            )
            self.combo.setEnabled(
                bool(normalized_names)
            )

            if selected_sheet:
                index = self.combo.findText(
                    str(selected_sheet).strip()
                )

                if index >= 0:
                    self.combo.setCurrentIndex(
                        index
                    )

        finally:
            self.combo.blockSignals(False)    

    def sheet_name(self):
        return str(
            self.combo.currentText()
            or ""
        ).strip()

    def set_sheet(
        self,
        sheet_name,
    ):
        normalized = str(
            sheet_name or ""
        ).strip()

        if not normalized:
            return False

        index = self.combo.findText(
            normalized
        )

        if index < 0:
            return False

        self.combo.setCurrentIndex(
            index
        )

        return True

    def clear(self):
        self.combo.blockSignals(
            True
        )

        try:
            self.combo.clear()
            self.combo.setEnabled(
                False
            )
            self.combo.setToolTip(
                (
                    "Select an Excel file "
                    "to load sheets."
                )
            )

        finally:
            self.combo.blockSignals(
                False
            )

    def has_sheet(self):
        return bool(
            self.sheet_name()
        )

    def set_loading(
        self,
        loading,
    ):
        self.combo.setEnabled(
            (
                not loading
                and self.combo.count() > 0
            )
        )

    # ==========================================================
    # Signal helpers
    # ==========================================================

    def _emit_sheet_changed(
        self,
        sheet_name,
    ):
        normalized = str(
            sheet_name or ""
        ).strip()

        if not normalized:
            return

        self.sheet_changed.emit(
            normalized
        )