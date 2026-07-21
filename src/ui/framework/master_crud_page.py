from abc import ABC, ABCMeta, abstractmethod
from pathlib import Path

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHeaderView,
    QMenu,
    QMessageBox,
    QTableWidgetItem,
)

from src.ui.pages.base_page import BasePage


class QABCMeta(type(BasePage), ABCMeta):
    """Metaclass kết hợp giữa metaclass của QWidget (Shiboken) và ABCMeta,
    để tránh xung đột metaclass khi dùng ABC cùng với các lớp Qt."""
    pass


class MasterCRUDPage(BasePage, ABC, metaclass=QABCMeta):
    """
    Framework dùng chung cho các màn hình Master Data.

    Chức năng được cung cấp sẵn:
    - Add
    - Edit
    - Delete/Deactivate
    - Search
    - Refresh
    - Import Excel/CSV
    - Export Excel
    - Double-click Edit
    - Context Menu
    - Summary Cards
    - Error Handling
    - Status Bar

    Lớp con cần khai báo:
    - ENTITY_NAME
    - HEADERS

    Và triển khai:
    - load_records()
    - record_to_row()
    - get_record_key()
    - create_dialog()
    - create_record()
    - update_record()
    - delete_record()
    """

    ENTITY_NAME = "Record"

    HEADERS = []

    DEFAULT_EXPORT_NAME = "master_data.xlsx"

    IMPORT_FILE_FILTER = (
        "Master Data Files "
        "(*.xlsx *.xlsm *.xls *.csv);;"
        "Excel Files (*.xlsx *.xlsm *.xls);;"
        "CSV Files (*.csv);;"
        "All Files (*.*)"
    )

    EXPORT_FILE_FILTER = (
        "Excel Files (*.xlsx)"
    )

    def __init__(
        self,
        title,
        headers=None,
        search_placeholder="Search...",
        service=None,
        importer=None,
        dialog_class=None,
    ):
        super().__init__(
            title=title,
            search_placeholder=search_placeholder,
        )

        self.service = service
        self.importer = importer
        self.dialog_class = dialog_class

        self.headers = list(
            headers or self.HEADERS
        )

        if not self.headers:
            raise ValueError(
                f"{self.__class__.__name__} "
                "must define HEADERS."
            )

        self.records = []
        self.current_keyword = ""

        self.setup_table(self.headers)
        self.configure_table()
        self.connect_crud_events()

    # ==========================================================
    # Initialization
    # ==========================================================

    def initialize_page(self):
        """
        Gọi ở cuối __init__ của lớp con.

        Không gọi trực tiếp trong constructor cha để tránh
        load dữ liệu trước khi lớp con khởi tạo xong.
        """
        self.refresh_table()

    def configure_table(self):
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)

        self.table.setContextMenuPolicy(
            Qt.CustomContextMenu
        )

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        header.setStretchLastSection(True)

    def connect_crud_events(self):
        self.toolbar.btn_add.clicked.connect(
            self.handle_add
        )

        self.toolbar.btn_edit.clicked.connect(
            self.handle_edit
        )

        self.toolbar.btn_delete.clicked.connect(
            self.handle_delete
        )

        self.toolbar.btn_import.clicked.connect(
            self.handle_import
        )

        self.toolbar.btn_export.clicked.connect(
            self.handle_export
        )

        self.toolbar.btn_refresh.clicked.connect(
            self.refresh_table
        )

        self.table.doubleClicked.connect(
            self.handle_edit
        )

        self.table.customContextMenuRequested.connect(
            self.show_context_menu
        )

        self._connect_search_signal()

    def _connect_search_signal(self):
        """
        Hỗ trợ các phiên bản SearchBar khác nhau.
        """

        if hasattr(
            self.search_bar,
            "textChanged",
        ):
            self.search_bar.textChanged.connect(
                self.handle_search
            )
            return

        if hasattr(
            self.search_bar,
            "search_changed",
        ):
            signal = getattr(
                self.search_bar,
                "search_changed"
            )

            if callable(signal):
                signal = signal()

            signal.connect(
                self.handle_search
            )
            return

        if hasattr(
            self.search_bar,
            "text_changed",
        ):
            signal = getattr(
                self.search_bar,
                "text_changed"
            )

            if callable(signal):
                signal = signal()

            signal.connect(
                self.handle_search
            )
            return

        line_edit = self._get_search_line_edit()

        if line_edit is not None:
            line_edit.textChanged.connect(
                self.handle_search
            )

    # ==========================================================
    # Data loading
    # ==========================================================

    def refresh_table(self):
        self.handle_search(
            self.get_search_text()
        )

    def handle_search(self, keyword=None):
        try:
            if keyword is None:
                keyword = self.get_search_text()

            keyword = str(
                keyword or ""
            ).strip()

            self.current_keyword = keyword

            records = self.load_records(
                keyword
            )

            self.records = list(
                records or []
            )

            self.populate_table(
                self.records
            )

            self.update_page_summary(
                self.records
            )

            self.set_status(
                f"Total {self.ENTITY_NAME}: "
                f"{len(self.records)}"
            )

        except Exception as error:
            self.show_error(
                f"Load {self.ENTITY_NAME} Error",
                str(error),
            )

    def populate_table(self, records):
        self.table.setSortingEnabled(False)

        self.table.clearContents()
        self.table.setRowCount(
            len(records)
        )

        for row_index, record in enumerate(
            records
        ):
            values = list(
                self.record_to_row(record)
            )

            for column_index in range(
                len(self.headers)
            ):
                value = (
                    values[column_index]
                    if column_index < len(values)
                    else ""
                )

                item = self.create_table_item(
                    record=record,
                    column_index=column_index,
                    value=value,
                )

                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )

            self.table.setRowHeight(
                row_index,
                34,
            )

        self.table.setSortingEnabled(True)

    def create_table_item(
        self,
        record,
        column_index,
        value,
    ):
        """
        Có thể override để đặt màu, căn lề hoặc icon.
        """
        item = QTableWidgetItem(
            self.display_value(value)
        )

        item.setFlags(
            item.flags()
            & ~Qt.ItemIsEditable
        )

        if isinstance(
            value,
            (int, float),
        ):
            item.setTextAlignment(
                Qt.AlignCenter
            )

        return item

    # ==========================================================
    # Summary
    # ==========================================================

    def update_page_summary(
        self,
        records,
    ):
        total = len(records)

        active = sum(
            1
            for record in records
            if self.get_record_status(record)
            in self.get_active_statuses()
        )

        inactive = total - active

        self.update_summary(
            total,
            active,
            inactive,
        )

    def get_active_statuses(self):
        return {
            "ACTIVE",
            "RUNNING",
            "RELEASED",
            "READY",
            "PLANNED",
        }

    @staticmethod
    def get_record_status(record):
        return str(
            getattr(
                record,
                "status",
                "",
            )
            or ""
        ).strip().upper()

    # ==========================================================
    # Add
    # ==========================================================

    def handle_add(self):
        try:
            dialog = self.create_dialog(
                parent=self,
                record=None,
            )

            if dialog is None:
                raise RuntimeError(
                    "create_dialog() returned None."
                )

            if not dialog.exec():
                return

            data = dialog.get_data()

            self.validate_dialog_data(
                data,
                is_edit=False,
            )

            self.create_record(data)

            self.show_info(
                "Success",
                (
                    f"{self.ENTITY_NAME} "
                    "created successfully."
                ),
            )

            self.refresh_table()

        except Exception as error:
            self.show_error(
                f"Create {self.ENTITY_NAME} Error",
                str(error),
            )

    # ==========================================================
    # Edit
    # ==========================================================

    def handle_edit(self, *_):
        record = self.get_selected_record()

        if record is None:
            self.show_warning(
                f"Edit {self.ENTITY_NAME}",
                (
                    f"Please select a "
                    f"{self.ENTITY_NAME}."
                ),
            )
            return

        try:
            dialog = self.create_dialog(
                parent=self,
                record=record,
            )

            if dialog is None:
                raise RuntimeError(
                    "create_dialog() returned None."
                )

            if not dialog.exec():
                return

            data = dialog.get_data()

            self.validate_dialog_data(
                data,
                is_edit=True,
            )

            record_key = self.get_record_key(
                record
            )

            self.update_record(
                record_key,
                data,
            )

            self.show_info(
                "Success",
                (
                    f"{self.ENTITY_NAME} "
                    "updated successfully."
                ),
            )

            self.refresh_table()

        except Exception as error:
            self.show_error(
                f"Update {self.ENTITY_NAME} Error",
                str(error),
            )

    # ==========================================================
    # Delete / Deactivate
    # ==========================================================

    def handle_delete(self):
        record = self.get_selected_record()

        if record is None:
            self.show_warning(
                f"Delete {self.ENTITY_NAME}",
                (
                    f"Please select a "
                    f"{self.ENTITY_NAME}."
                ),
            )
            return

        record_key = self.get_record_key(
            record
        )

        confirmed = self.confirm(
            f"Confirm {self.ENTITY_NAME}",
            (
                f"Delete or deactivate "
                f"{self.ENTITY_NAME}:\n\n"
                f"{self.format_record_key(record_key)}?"
            ),
        )

        if not confirmed:
            return

        try:
            self.delete_record(
                record_key
            )

            self.show_info(
                "Success",
                (
                    f"{self.ENTITY_NAME} "
                    "deleted or deactivated successfully."
                ),
            )

            self.refresh_table()

        except Exception as error:
            self.show_error(
                f"Delete {self.ENTITY_NAME} Error",
                str(error),
            )

    # ==========================================================
    # Import
    # ==========================================================

    def handle_import(self):
        if self.importer is None:
            self.show_warning(
                f"Import {self.ENTITY_NAME}",
                (
                    f"Importer is not configured for "
                    f"{self.ENTITY_NAME}."
                ),
            )
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Import {self.ENTITY_NAME}",
            "",
            self.IMPORT_FILE_FILTER,
        )

        if not file_path:
            return

        try:
            preview = self.importer.preview(
                file_path
            )

            preview_result = preview["result"]

            errors = list(
                preview.get(
                    "errors",
                    preview_result.errors,
                )
                or []
            )

            message = self.build_preview_message(
                file_path=file_path,
                result=preview_result,
                errors=errors,
            )

            if errors:
                QMessageBox.warning(
                    self,
                    f"{self.ENTITY_NAME} Import Preview",
                    message,
                )
                return

            confirmed = self.confirm(
                f"Confirm {self.ENTITY_NAME} Import",
                (
                    f"{message}\n\n"
                    "Continue importing?"
                ),
            )

            if not confirmed:
                return

            result = self.importer.import_file(
                file_path
            )

            result_message = (
                self.build_import_result_message(
                    result
                )
            )

            if result.invalid == 0:
                self.show_info(
                    f"{self.ENTITY_NAME} Import Completed",
                    result_message,
                )
            else:
                self.show_warning(
                    f"{self.ENTITY_NAME} Import Completed",
                    result_message,
                )

            self.refresh_table()

        except Exception as error:
            self.show_error(
                f"{self.ENTITY_NAME} Import Error",
                str(error),
            )

    def build_preview_message(
        self,
        file_path,
        result,
        errors,
    ):
        message = (
            f"File: {Path(file_path).name}\n\n"
            f"Total rows: {result.total}\n"
            f"Valid rows: {result.valid}\n"
            f"Invalid rows: {len(errors)}"
        )

        if errors:
            message += (
                "\n\nFirst errors:\n"
                + self.format_errors(errors)
            )

        return message

    def build_import_result_message(
        self,
        result,
    ):
        message = (
            f"Total: {result.total}\n"
            f"Created: {result.created}\n"
            f"Updated: {result.updated}\n"
            f"Skipped: {result.skipped}\n"
            f"Invalid: {result.invalid}"
        )

        if result.errors:
            message += (
                "\n\nFirst errors:\n"
                + self.format_errors(
                    result.errors
                )
            )

        return message

    @staticmethod
    def format_errors(
        errors,
        limit=10,
    ):
        lines = []

        for error in errors[:limit]:
            if isinstance(error, dict):
                row = error.get(
                    "row",
                    "?",
                )

                message = error.get(
                    "message",
                    str(error),
                )

                lines.append(
                    f"Row {row}: {message}"
                )

            else:
                lines.append(
                    str(error)
                )

        return "\n".join(lines)

    # ==========================================================
    # Export
    # ==========================================================

    def handle_export(self):
        records = list(
            self.records or []
        )

        if not records:
            records = list(
                self.load_records(
                    self.get_search_text()
                )
                or []
            )

        if not records:
            self.show_warning(
                f"Export {self.ENTITY_NAME}",
                (
                    f"There is no "
                    f"{self.ENTITY_NAME} data to export."
                ),
            )
            return

        default_name = (
            self.get_default_export_name()
        )

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export {self.ENTITY_NAME}",
            default_name,
            self.EXPORT_FILE_FILTER,
        )

        if not file_path:
            return

        if not file_path.lower().endswith(
            ".xlsx"
        ):
            file_path += ".xlsx"

        try:
            export_rows = [
                self.record_to_export_row(
                    record
                )
                for record in records
            ]

            dataframe = pd.DataFrame(
                export_rows
            )

            dataframe.to_excel(
                file_path,
                index=False,
            )

            self.show_info(
                f"Export {self.ENTITY_NAME}",
                (
                    f"Exported {len(records)} records."
                    f"\n\n{file_path}"
                ),
            )

        except Exception as error:
            self.show_error(
                f"{self.ENTITY_NAME} Export Error",
                str(error),
            )

    def get_default_export_name(self):
        return self.DEFAULT_EXPORT_NAME

    def record_to_export_row(
        self,
        record,
    ):
        """
        Mặc định dùng HEADERS và record_to_row().
        Có thể override để đặt tên cột Excel riêng.
        """
        values = list(
            self.record_to_row(record)
        )

        return {
            header: (
                values[index]
                if index < len(values)
                else ""
            )
            for index, header in enumerate(
                self.headers
            )
        }

    # ==========================================================
    # Context menu
    # ==========================================================

    def show_context_menu(
        self,
        position,
    ):
        menu = QMenu(self)

        action_add = menu.addAction(
            f"Add {self.ENTITY_NAME}"
        )

        action_edit = menu.addAction(
            f"Edit {self.ENTITY_NAME}"
        )

        action_delete = menu.addAction(
            f"Delete/Deactivate {self.ENTITY_NAME}"
        )

        menu.addSeparator()

        action_refresh = menu.addAction(
            "Refresh"
        )

        extra_actions = self.add_context_actions(
            menu
        )

        selected_action = menu.exec(
            self.table.viewport().mapToGlobal(
                position
            )
        )

        if selected_action == action_add:
            self.handle_add()

        elif selected_action == action_edit:
            self.handle_edit()

        elif selected_action == action_delete:
            self.handle_delete()

        elif selected_action == action_refresh:
            self.refresh_table()

        elif selected_action in extra_actions:
            callback = extra_actions[
                selected_action
            ]

            callback()

    def add_context_actions(
        self,
        menu,
    ):
        """
        Lớp con có thể bổ sung action riêng.

        Returns:
            {
                QAction: callback
            }
        """
        return {}

    # ==========================================================
    # Selection
    # ==========================================================

    def get_selected_record(self):
        row = self.get_selected_row()

        if row is None:
            return None

        if (
            row < 0
            or row >= len(self.records)
        ):
            return None

        return self.records[row]

    def get_search_text(self):
        if hasattr(
            self.search_bar,
            "text",
        ):
            value = self.search_bar.text()

            if isinstance(value, str):
                return value

        line_edit = self._get_search_line_edit()

        if line_edit is not None:
            return line_edit.text()

        return ""

    def _get_search_line_edit(self):
        possible_names = [
            "input",
            "search_input",
            "line_edit",
            "txt_search",
        ]

        for name in possible_names:
            widget = getattr(
                self.search_bar,
                name,
                None,
            )

            if widget is not None:
                return widget

        return None

    # ==========================================================
    # Extension points
    # ==========================================================

    def validate_dialog_data(
        self,
        data,
        is_edit=False,
    ):
        if not isinstance(data, dict):
            raise ValueError(
                "Dialog data must be a dictionary."
            )

        return True

    @staticmethod
    def display_value(value):
        if value is None:
            return ""

        return str(value)

    @staticmethod
    def format_record_key(
        record_key,
    ):
        if isinstance(
            record_key,
            (tuple, list),
        ):
            return " / ".join(
                str(value)
                for value in record_key
            )

        return str(record_key)

    # ==========================================================
    # Required subclass API
    # ==========================================================

    @abstractmethod
    def load_records(
        self,
        keyword,
    ):
        """
        Lấy danh sách model theo từ khóa.
        """

    @abstractmethod
    def record_to_row(
        self,
        record,
    ):
        """
        Chuyển model thành danh sách giá trị hiển thị.
        """

    @abstractmethod
    def get_record_key(
        self,
        record,
    ):
        """
        Trả về khóa nghiệp vụ của model.
        """

    @abstractmethod
    def create_dialog(
        self,
        parent=None,
        record=None,
    ):
        """
        Trả về dialog Add/Edit.
        """

    @abstractmethod
    def create_record(
        self,
        data,
    ):
        """
        Tạo bản ghi.
        """

    @abstractmethod
    def update_record(
        self,
        record_key,
        data,
    ):
        """
        Cập nhật bản ghi.
        """

    @abstractmethod
    def delete_record(
        self,
        record_key,
    ):
        """
        Xóa hoặc deactivate bản ghi.
        """