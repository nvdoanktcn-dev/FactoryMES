from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QWidget,
)


class ImportToolbar(QFrame):
    select_file_requested = Signal()
    preview_requested = Signal()
    validate_requested = Signal()
    import_requested = Signal()
    rollback_requested = Signal()
    sheet_changed = Signal(str)
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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MasterImportToolbar")

        self.module_combo = QComboBox(self)
        self.sheet_combo = QComboBox(self)
        self.file_path_edit = QLineEdit(self)

        self.rows_label = QLabel("Rows: -", self)
        self.columns_label = QLabel("Columns: -", self)
        self.header_label = QLabel("Header: -", self)
        self.duration_label = QLabel("Time: -", self)

        self.btn_select_file = QPushButton("Select File", self)
        self.btn_preview = QPushButton("Preview", self)
        self.btn_validate = QPushButton("Validate", self)
        self.btn_import = QPushButton("Import", self)
        self.btn_rollback = QPushButton("Rollback", self)

        self._configure()
        self._build_ui()
        self._connect_events()
        self._apply_style()

    def _configure(self):
        for display_name, module_name in self.MODULES:
            self.module_combo.addItem(display_name, module_name)

        self.module_combo.setMinimumWidth(150)
        self.module_combo.setMaximumWidth(220)

        self.sheet_combo.setMinimumWidth(180)
        self.sheet_combo.setMaximumWidth(280)
        self.sheet_combo.setEnabled(False)

        self.file_path_edit.setReadOnly(True)
        self.file_path_edit.setPlaceholderText(
            "Select an Excel file..."
        )
        self.file_path_edit.setMinimumWidth(320)
        self.file_path_edit.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        self.btn_select_file.setMinimumWidth(95)

        for button in (
            self.btn_select_file,
            self.btn_preview,
            self.btn_validate,
            self.btn_import,
            self.btn_rollback,
        ):
            button.setMinimumHeight(32)

        self.btn_import.setEnabled(False)
        self.btn_rollback.setEnabled(False)

    def _build_ui(self):
        root_layout = QGridLayout(self)
        root_layout.setContentsMargins(12, 10, 12, 10)
        root_layout.setHorizontalSpacing(10)
        root_layout.setVerticalSpacing(8)

        file_row = QWidget(self)
        file_layout = QHBoxLayout(file_row)
        file_layout.setContentsMargins(0, 0, 0, 0)
        file_layout.setSpacing(8)

        module_label = QLabel("Module", file_row)
        module_label.setMinimumWidth(50)
        file_label = QLabel("File", file_row)
        file_label.setMinimumWidth(28)

        file_layout.addWidget(module_label)
        file_layout.addWidget(self.module_combo)
        file_layout.addSpacing(8)
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_path_edit, 1)
        file_layout.addWidget(self.btn_select_file)

        action_row = QWidget(self)
        action_layout = QHBoxLayout(action_row)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(8)

        sheet_label = QLabel("Sheet", action_row)
        sheet_label.setMinimumWidth(36)

        action_layout.addWidget(sheet_label)
        action_layout.addWidget(self.sheet_combo)
        action_layout.addSpacing(8)
        action_layout.addWidget(self.btn_preview)
        action_layout.addWidget(self.btn_validate)
        action_layout.addWidget(self.btn_import)
        action_layout.addWidget(self.btn_rollback)
        action_layout.addStretch()
        action_layout.addWidget(self.rows_label)
        action_layout.addSpacing(8)
        action_layout.addWidget(self.columns_label)
        action_layout.addSpacing(8)
        action_layout.addWidget(self.header_label)
        action_layout.addSpacing(8)
        action_layout.addWidget(self.duration_label)

        root_layout.addWidget(file_row, 0, 0)
        root_layout.addWidget(action_row, 1, 0)
        root_layout.setColumnStretch(0, 1)

    def _connect_events(self):
        self.btn_select_file.clicked.connect(
            self.select_file_requested.emit
        )
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
        self.sheet_combo.currentTextChanged.connect(
            self._emit_sheet_changed
        )
        self.module_combo.currentIndexChanged.connect(
            self._emit_module_changed
        )

    def _apply_style(self):
        self.setMinimumHeight(112)
        self.setStyleSheet(
            """
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
            """
        )

    def _emit_sheet_changed(self, sheet_name):
        value = str(sheet_name or "").strip()
        if value:
            self.sheet_changed.emit(value)

    def _emit_module_changed(self, *_):
        self.module_changed.emit(self.module_name())

    def module_name(self):
        return str(
            self.module_combo.currentData() or ""
        ).strip().upper()

    def set_module(self, module_name):
        value = str(module_name or "").strip().upper()
        index = self.module_combo.findData(value)
        if index >= 0:
            self.module_combo.setCurrentIndex(index)
            return True
        return False

    def file_path(self):
        return self.file_path_edit.text().strip()

    def set_file_path(self, file_path):
        value = str(file_path or "").strip()
        self.file_path_edit.setText(value)
        self.file_path_edit.setToolTip(value)

    def clear_file(self):
        self.file_path_edit.clear()
        self.file_path_edit.setToolTip("")

    def set_sheet_names(
        self,
        sheet_names,
        selected_sheet=None,
    ):
        names = [
            str(sheet).strip()
            for sheet in (sheet_names or [])
            if str(sheet).strip()
        ]
        selected_value = str(
            selected_sheet or ""
        ).strip()

        self.sheet_combo.blockSignals(True)
        try:
            self.sheet_combo.clear()
            self.sheet_combo.addItems(names)

            if names:
                if selected_value in names:
                    self.sheet_combo.setCurrentText(
                        selected_value
                    )
                else:
                    self.sheet_combo.setCurrentIndex(0)
            else:
                self.sheet_combo.setCurrentIndex(-1)

            self.sheet_combo.setEnabled(bool(names))
        finally:
            self.sheet_combo.blockSignals(False)

    def sheet_name(self):
        return str(
            self.sheet_combo.currentText() or ""
        ).strip()

    def set_sheet(self, sheet_name):
        value = str(sheet_name or "").strip()
        if not value:
            return False

        index = self.sheet_combo.findText(value)
        if index < 0:
            return False

        self.sheet_combo.setCurrentIndex(index)
        return True

    def clear_sheets(self):
        self.sheet_combo.blockSignals(True)
        try:
            self.sheet_combo.clear()
            self.sheet_combo.setCurrentIndex(-1)
            self.sheet_combo.setEnabled(False)
        finally:
            self.sheet_combo.blockSignals(False)

    def update_preview_info(
        self,
        total_rows,
        total_columns,
        header_row,
        duration=None,
    ):
        rows = self._to_int(total_rows)
        columns = self._to_int(total_columns)

        if header_row is None:
            header_text = "-"
        else:
            try:
                header_text = str(int(header_row))
            except (TypeError, ValueError):
                header_text = str(header_row)

        self.rows_label.setText(f"Rows : {rows}")
        self.columns_label.setText(
            f"Columns : {columns}"
        )
        self.header_label.setText(
            f"Header : {header_text}"
        )

        if duration is None:
            self.duration_label.setText("Time: -")
        else:
            try:
                duration_text = (
                    f"{float(duration):.3f}s"
                )
            except (TypeError, ValueError):
                duration_text = str(duration)

            self.duration_label.setText(
                f"Time : {duration_text}"
            )

    def reset_preview_info(self):
        self.rows_label.setText("Rows: -")
        self.columns_label.setText("Columns: -")
        self.header_label.setText("Header: -")
        self.duration_label.setText("Time: -")

    def set_validation_state(self, valid):
        self.btn_import.setEnabled(bool(valid))

    def set_rollback_enabled(self, enabled):
        self.btn_rollback.setEnabled(bool(enabled))

    def set_loading(self, loading):
        enabled = not bool(loading)

        self.module_combo.setEnabled(enabled)
        self.btn_select_file.setEnabled(enabled)
        self.btn_preview.setEnabled(enabled)
        self.btn_validate.setEnabled(enabled)
        self.sheet_combo.setEnabled(
            enabled and self.sheet_combo.count() > 0
        )

        if loading:
            self.btn_import.setEnabled(False)
            self.btn_rollback.setEnabled(False)

    @staticmethod
    def _to_int(value):
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0
