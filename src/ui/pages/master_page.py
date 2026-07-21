from abc import abstractmethod

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QTableWidgetItem,
)

from src.ui.pages.base_page import BasePage


class MasterPage(BasePage):
    """
    Lớp cơ sở cho các màn hình Master Data.

    Importer con cần triển khai:
    - load_records()
    - record_to_row()
    - get_record_key()
    - create_record()
    - update_record()
    - delete_record()
    - create_dialog()
    """

    def __init__(
        self,
        title,
        headers,
        search_placeholder="Search...",
    ):
        super().__init__(
            title=title,
            search_placeholder=search_placeholder,
        )

        self.headers = list(headers)
        self.records = []

        self.setup_table(self.headers)
        self.configure_table()
        self.connect_events()

    # ==========================================================
    # UI configuration
    # ==========================================================

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

        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)

    def connect_events(self):
        self.toolbar.btn_add.clicked.connect(
            self.handle_add
        )

        self.toolbar.btn_edit.clicked.connect(
            self.handle_edit
        )

        self.toolbar.btn_delete.clicked.connect(
            self.handle_delete
        )

        self.toolbar.btn_refresh.clicked.connect(
            self.refresh_table
        )

        self.toolbar.btn_import.clicked.connect(
            self.handle_import
        )

        self.toolbar.btn_export.clicked.connect(
            self.handle_export
        )

        self.table.doubleClicked.connect(
            self.handle_edit
        )

        self._connect_search_signal()

    def _connect_search_signal(self):
        """
        Hỗ trợ nhiều cách triển khai SearchBar.
        """

        if hasattr(self.search_bar, "textChanged"):
            self.search_bar.textChanged.connect(
                self.handle_search
            )
            return

        if hasattr(self.search_bar, "search_changed"):
            self.search_bar.search_changed.connect(
                self.handle_search
            )
            return

        line_edit = getattr(
            self.search_bar,
            "input",
            None,
        )

        if line_edit is None:
            line_edit = getattr(
                self.search_bar,
                "search_input",
                None,
            )

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

            keyword = str(keyword or "").strip()

            self.records = self.load_records(
                keyword
            )

            if self.records is None:
                self.records = []

            self.populate_table(self.records)
            self.update_page_summary(self.records)

            self.set_status(
                f"Total records: {len(self.records)}"
            )

        except Exception as error:
            self.show_error(
                "Load Data Error",
                str(error),
            )

    def populate_table(self, records):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(records))

        for row_index, record in enumerate(records):
            row_values = self.record_to_row(record)

            for column_index, value in enumerate(
                row_values
            ):
                item = QTableWidgetItem(
                    self.display_value(value)
                )

                item.setFlags(
                    item.flags()
                    & ~Qt.ItemIsEditable
                )

                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        self.table.resizeColumnsToContents()
        self.table.setSortingEnabled(True)

    def update_page_summary(self, records):
        total = len(records)

        active = sum(
            1
            for record in records
            if self.get_record_status(record)
            == "ACTIVE"
        )

        inactive = total - active

        self.update_summary(
            total,
            active,
            inactive,
        )

    # ==========================================================
    # Add
    # ==========================================================

    def handle_add(self):
        try:
            dialog = self.create_dialog(
                parent=self,
                record=None,
            )

            if not dialog.exec():
                return

            data = dialog.get_data()

            self.create_record(data)

            self.show_info(
                "Success",
                "Record created successfully.",
            )

            self.refresh_table()

        except Exception as error:
            self.show_error(
                "Create Error",
                str(error),
            )

    # ==========================================================
    # Edit
    # ==========================================================

    def handle_edit(self, *_):
        record = self.get_selected_record()

        if record is None:
            self.show_warning(
                "Edit",
                "Please select a record.",
            )
            return

        try:
            dialog = self.create_dialog(
                parent=self,
                record=record,
            )

            if not dialog.exec():
                return

            data = dialog.get_data()
            record_key = self.get_record_key(
                record
            )

            self.update_record(
                record_key,
                data,
            )

            self.show_info(
                "Success",
                "Record updated successfully.",
            )

            self.refresh_table()

        except Exception as error:
            self.show_error(
                "Update Error",
                str(error),
            )

    # ==========================================================
    # Delete
    # ==========================================================

    def handle_delete(self):
        record = self.get_selected_record()

        if record is None:
            self.show_warning(
                "Delete",
                "Please select a record.",
            )
            return

        record_key = self.get_record_key(
            record
        )

        confirmed = self.confirm(
            "Confirm Delete",
            (
                "Are you sure you want to delete "
                f"or deactivate:\n{record_key}?"
            ),
        )

        if not confirmed:
            return

        try:
            self.delete_record(record_key)

            self.show_info(
                "Success",
                "Record deleted or deactivated successfully.",
            )

            self.refresh_table()

        except Exception as error:
            self.show_error(
                "Delete Error",
                str(error),
            )

    # ==========================================================
    # Import / Export
    # ==========================================================

    def handle_import(self):
        self.show_info(
            "Import",
            "Import is not configured for this page yet.",
        )

    def handle_export(self):
        self.show_info(
            "Export",
            "Export is not configured for this page yet.",
        )

    # ==========================================================
    # Selection helpers
    # ==========================================================

    def get_selected_record(self):
        row = self.get_selected_row()

        if row is None:
            return None

        if row < 0 or row >= len(self.records):
            return None

        return self.records[row]

    def get_search_text(self):
        if hasattr(self.search_bar, "text"):
            value = self.search_bar.text()

            if isinstance(value, str):
                return value

        line_edit = getattr(
            self.search_bar,
            "input",
            None,
        )

        if line_edit is None:
            line_edit = getattr(
                self.search_bar,
                "search_input",
                None,
            )

        if line_edit is not None:
            return line_edit.text()

        return ""

    @staticmethod
    def get_record_status(record):
        status = getattr(
            record,
            "status",
            "",
        )

        return str(
            status or ""
        ).strip().upper()

    @staticmethod
    def display_value(value):
        if value is None:
            return ""

        return str(value)

    # ==========================================================
    # Abstract module API
    # ==========================================================

    @abstractmethod
    def load_records(self, keyword):
        """
        Trả về danh sách model theo từ khóa.
        """

    @abstractmethod
    def record_to_row(self, record):
        """
        Chuyển model thành danh sách giá trị cho bảng.
        """

    @abstractmethod
    def get_record_key(self, record):
        """
        Trả về khóa chính nghiệp vụ.
        """

    @abstractmethod
    def create_dialog(
        self,
        parent=None,
        record=None,
    ):
        """
        Tạo dialog Add/Edit.
        """

    @abstractmethod
    def create_record(self, data):
        """
        Tạo bản ghi mới.
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
    def delete_record(self, record_key):
        """
        Xóa hoặc chuyển trạng thái bản ghi.
        """