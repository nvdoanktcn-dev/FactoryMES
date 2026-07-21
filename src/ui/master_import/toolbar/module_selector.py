from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QWidget,
)


class ModuleSelector(QWidget):
    """
    Widget chọn loại dữ liệu Master Import.
    """

    module_changed = Signal(str)

    MODULES = [
        ("Product", "PRODUCT"),
        ("Machine", "MACHINE"),
        ("Employee", "EMPLOYEE"),
        ("Routing", "ROUTING"),
        ("Work Order", "WORK_ORDER"),
        ("Shift", "SHIFT"),
        ("Calendar", "CALENDAR"),
    ]

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        self.label = QLabel(
            "Module"
        )

        self.combo = QComboBox()

        self._configure()
        self._build_ui()
        self._connect_events()

    def _configure(self):
        self.label.setMinimumWidth(
            50
        )

        self.combo.setMinimumWidth(
            150
        )

        self.combo.setMaximumWidth(
            220
        )

        for display_name, module_name in self.MODULES:
            self.combo.addItem(
                display_name,
                module_name,
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
            self.combo
        )

    def _connect_events(self):
        self.combo.currentIndexChanged.connect(
            self._emit_module_changed
        )

    def _emit_module_changed(
        self,
        *_,
    ):
        self.module_changed.emit(
            self.module_name()
        )

    def module_name(self):
        return str(
            self.combo.currentData()
            or ""
        ).strip().upper()

    def set_module(
        self,
        module_name,
    ):
        normalized = str(
            module_name or ""
        ).strip().upper()

        index = self.combo.findData(
            normalized
        )

        if index >= 0:
            self.combo.setCurrentIndex(
                index
            )

    def set_loading(
        self,
        loading,
    ):
        self.combo.setEnabled(
            not loading
        )