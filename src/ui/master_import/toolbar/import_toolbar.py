from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
)

from src.ui.master_import.toolbar import (
    ActionButtons,
    FileSelector,
    ImportStatistics,
    ModuleSelector,
    SheetSelector,
)


class ImportToolbar(QFrame):
    """
    Toolbar tổng hợp cho Master Import Center.

    Chỉ chịu trách nhiệm:
    - Ghép các widget con.
    - Chuyển tiếp signal.
    - Giữ API tương thích với MasterImportPage
      và MasterImportController hiện tại.
    """

    select_file_requested = Signal()
    preview_requested = Signal()
    validate_requested = Signal()
    import_requested = Signal()
    rollback_requested = Signal()
    sheet_changed = Signal(str)
    module_changed = Signal(str)

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName(
            "MasterImportToolbar"
        )

        self.module_selector = (
            ModuleSelector()
        )

        self.file_selector = (
            FileSelector()
        )

        self.sheet_selector = (
            SheetSelector()
        )

        self.action_buttons = (
            ActionButtons()
        )

        self.statistics = (
            ImportStatistics()
        )

        self._build_ui()
        self._connect_events()
        self._apply_style()

    # ==========================================================
    # UI
    # ==========================================================

    def _build_ui(self):
        root_layout = QVBoxLayout(self)

        root_layout.setContentsMargins(
            12,
            10,
            12,
            10,
        )

        root_layout.setSpacing(
            10
        )

        first_row = QHBoxLayout()

        first_row.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        first_row.setSpacing(
            10
        )

        first_row.addWidget(
            self.module_selector
        )

        first_row.addWidget(
            self.file_selector,
            1,
        )

        second_row = QHBoxLayout()

        second_row.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        second_row.setSpacing(
            10
        )

        second_row.addWidget(
            self.sheet_selector
        )

        second_row.addWidget(
            self.action_buttons
        )

        second_row.addStretch()

        second_row.addWidget(
            self.statistics
        )

        root_layout.addLayout(
            first_row
        )

        root_layout.addLayout(
            second_row
        )

    def _connect_events(self):
        self.file_selector.select_file_requested.connect(
            self.select_file_requested.emit
        )

        self.action_buttons.preview_requested.connect(
            self.preview_requested.emit
        )

        self.action_buttons.validate_requested.connect(
            self.validate_requested.emit
        )

        self.action_buttons.import_requested.connect(
            self.import_requested.emit
        )

        self.action_buttons.rollback_requested.connect(
            self.rollback_requested.emit
        )

        self.sheet_selector.sheet_changed.connect(
            self.sheet_changed.emit
        )

        self.module_selector.module_changed.connect(
            self.module_changed.emit
        )

    def _apply_style(self):
        self.setMinimumHeight(
            118
        )

        self.setStyleSheet("""
            QFrame#MasterImportToolbar {
                background: #FFFFFF;
                border: 1px solid #CFD8DC;
                border-radius: 8px;
            }

            QLabel {
                color: #37474F;
            }

            QComboBox,
            QLineEdit {
                min-height: 30px;
                padding: 2px 7px;
            }

            QPushButton {
                min-height: 31px;
                padding: 4px 11px;
            }

            QPushButton:disabled {
                color: #90A4AE;
                background: #ECEFF1;
            }
        """)

    # ==========================================================
    # Compatibility API
    # ==========================================================

    def module_name(self):
        return (
            self.module_selector
            .module_name()
        )

    def set_module(
        self,
        module_name,
    ):
        self.module_selector.set_module(
            module_name
        )

    def file_path(self):
        return (
            self.file_selector
            .file_path()
        )

    def file_name(self):
        return (
            self.file_selector
            .file_name()
        )

    def set_file_path(
        self,
        file_path,
    ):
        self.file_selector.set_file_path(
            file_path
        )

    def clear_file(self):
        self.file_selector.clear()

    def sheet_name(self):
        return (
            self.sheet_selector
            .sheet_name()
        )

    def set_sheet_names(
        self,
        sheet_names,
        selected_sheet=None,
    ):
        self.sheet_selector.set_sheet_names(
            sheet_names=sheet_names,
            selected_sheet=selected_sheet,
        )

    def set_sheet(
        self,
        sheet_name,
    ):
        return (
            self.sheet_selector
            .set_sheet(
                sheet_name
            )
        )

    def clear_sheets(self):
        self.sheet_selector.clear()

    def update_preview_info(
        self,
        total_rows,
        total_columns,
        header_row,
        duration=None,
    ):
        self.statistics.update_preview_info(
            total_rows=total_rows,
            total_columns=total_columns,
            header_row=header_row,
            duration=duration,
        )

    def reset_preview_info(self):
        self.statistics.reset()

    def set_validation_state(
        self,
        valid,
    ):
        self.action_buttons.set_validation_state(
            valid
        )

    def set_rollback_enabled(
        self,
        enabled,
    ):
        self.action_buttons.set_rollback_enabled(
            enabled
        )

    def set_loading(
        self,
        loading,
    ):
        self.module_selector.set_loading(
            loading
        )

        self.file_selector.set_loading(
            loading
        )

        self.sheet_selector.set_loading(
            loading
        )

        self.action_buttons.set_loading(
            loading
        )