from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QLabel,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.ui.master_import.history_panel import HistoryPanel
from src.ui.master_import.import_toolbar import ImportToolbar
from src.ui.master_import.master_import_controller import (
    MasterImportController,
)
from src.ui.master_import.preview_table import PreviewTable
from src.ui.master_import.progress_panel import ProgressPanel
from src.ui.master_import.validation_panel import ValidationPanel


class MasterImportPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MasterImportPage")

        self.title_label = QLabel("MASTER IMPORT CENTER")
        self.subtitle_label = QLabel(
            "Preview, validate and import master data"
        )

        self.toolbar = ImportToolbar()
        self.preview_table = PreviewTable()
        self.validation_panel = ValidationPanel()
        self.progress_panel = ProgressPanel()
        self.history_panel = HistoryPanel()

        self.controller = MasterImportController(page=self)

        self._build_ui()
        self._connect_events()
        self._apply_style()
        self.controller.load_history()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(10)

        self.title_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setAlignment(Qt.AlignCenter)

        preview_group = QGroupBox("Excel Preview")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.addWidget(self.preview_table)

        validation_group = QGroupBox("Validation Result")
        validation_layout = QVBoxLayout(validation_group)
        validation_layout.addWidget(self.validation_panel)

        progress_group = QGroupBox("Import Progress")
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.addWidget(self.progress_panel)

        history_group = QGroupBox("Import History")
        history_layout = QVBoxLayout(history_group)
        history_layout.addWidget(self.history_panel)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(preview_group)
        content_layout.addWidget(validation_group)
        content_layout.addWidget(progress_group)
        content_layout.addWidget(history_group)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content_widget)

        root_layout.addWidget(self.title_label)
        root_layout.addWidget(self.subtitle_label)
        root_layout.addWidget(self.toolbar)
        root_layout.addWidget(scroll_area, 1)

    def _connect_events(self):
        self.toolbar.select_file_requested.connect(self.select_file)
        self.toolbar.preview_requested.connect(self.preview)
        self.toolbar.validate_requested.connect(self.validate)
        self.toolbar.import_requested.connect(self.import_data)
        self.toolbar.rollback_requested.connect(self.rollback)
        self.toolbar.module_changed.connect(self._module_changed)

    def _apply_style(self):
        self.title_label.setStyleSheet(
            "font-size:24px;font-weight:bold;color:#263238;"
        )
        self.subtitle_label.setStyleSheet(
            "font-size:12px;color:#78909C;"
        )
        self.setStyleSheet(
            """
            QWidget#MasterImportPage {
                background: #F4F6F8;
            }
            QGroupBox {
                font-size: 13px;
                font-weight: bold;
                color: #37474F;
                border: 1px solid #CFD8DC;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 7px;
                background: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
            }
            """
        )

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Excel File",
            "",
            "Excel Files (*.xlsx *.xls);;All Files (*.*)",
        )
        if not file_path:
            return

        inferred_module = self._infer_module_from_file(file_path)
        if inferred_module:
            self.toolbar.set_module(inferred_module)

        self.toolbar.set_file_path(file_path)
        self._reset_import_state()

        self.progress_panel.set_status(
            f"Selected: {Path(file_path).name}"
        )

    def preview(self):
        try:
            self._validate_file_selected()
            self.controller.preview()
        except Exception as error:
            self.show_error(error)

    def validate(self):
        try:
            self._validate_file_selected()
            self.controller.validate()
        except Exception as error:
            self.show_error(error)

    def import_data(self):
        try:
            self._validate_file_selected()

            result = QMessageBox.question(
                self,
                "Confirm Import",
                "Import the validated data?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if result != QMessageBox.Yes:
                return

            self.controller.import_data()
        except Exception as error:
            self.show_error(error)

    def rollback(self):
        try:
            self.controller.rollback()
        except Exception as error:
            self.show_error(error)

    def _module_changed(self, _module_name):
        self._reset_import_state()

    def _reset_import_state(self):
        self.toolbar.clear_sheets()
        self.toolbar.reset_preview_info()
        self.toolbar.set_validation_state(False)
        self.toolbar.set_rollback_enabled(False)
        self.preview_table.clear_preview()
        self.validation_panel.clear_errors()
        self.progress_panel.reset()

    def _validate_file_selected(self):
        if not self.toolbar.file_path():
            raise ValueError("Please select an Excel file.")

    @staticmethod
    def _infer_module_from_file(file_path):
        stem = Path(file_path).stem.strip().upper()
        aliases = {
            "PRODUCT": "PRODUCT",
            "MACHINE": "MACHINE",
            "EMPLOYEE": "EMPLOYEE",
            "ROUTING": "ROUTING",
            "WORK_ORDER": "WORK_ORDER",
            "WORK ORDER": "WORK_ORDER",
            "SHIFT": "SHIFT",
            "CALENDAR": "CALENDAR",
        }
        return aliases.get(stem)

    def show_error(self, error):
        message = str(error)
        self.progress_panel.set_status(message)
        QMessageBox.warning(
            self,
            "Master Import Error",
            message,
        )
