from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMessageBox,
    QTableWidgetItem,
)

from src.repository.production_log_repository import (
    ProductionLogRepository,
)
from src.database.session import get_session
from src.ui.dialogs.production_entry_dialog import (
    ProductionEntryDialog,
)
from src.ui.framework.master_crud_page import (
    MasterCRUDPage,
)


class ProductionPage(MasterCRUDPage):
    """
    Production History Page V2.

    Chức năng:
    - Add Production Entry
    - Xem lịch sử Production Log
    - Search
    - Refresh
    - Export Excel
    - Xem chi tiết
    - Không cho sửa trực tiếp bản ghi hoàn thành
    """

    ENTITY_NAME = "Production Log"

    HEADERS = [
        "ID",
        "Production Date",
        "Work Order",
        "Product",
        "OP",
        "Machine",
        "Employee",
        "Shift",
        "Start Time",
        "Finish Time",
        "Runtime (H)",
        "OK Qty",
        "NG Qty",
        "Total Qty",
        "Yield",
        "Downtime (Min)",
        "Downtime Reason",
        "Status",
        "Remark",
    ]

    DEFAULT_EXPORT_NAME = (
        "production_history.xlsx"
    )

    ACTIVE_STATUSES = {
        "RUNNING",
        "STARTED",
    }

    FINAL_STATUSES = {
        "COMPLETED",
        "CLOSED",
    }

    def __init__(self):
        self.session = get_session()

        self.production_repository = (
            ProductionLogRepository(
                self.session
            )
        )

        super().__init__(
            title="🏭 Production History",
            headers=self.HEADERS,
            search_placeholder=(
                "Search WO, Product, Machine, "
                "Employee, OP..."
            ),
            service=None,
            importer=None,
            dialog_class=ProductionEntryDialog,
        )

        # Production Log không dùng Import từ Toolbar.
        self.toolbar.btn_import.setVisible(
            False
        )

        self.initialize_page()

    # ==========================================================
    # Data loading
    # ==========================================================

    def load_records(self, keyword):
        records = self._get_all_logs()

        keyword = str(
            keyword or ""
        ).strip().lower()

        if keyword:
            records = [
                production_log
                for production_log in records
                if self._matches_keyword(
                    production_log,
                    keyword,
                )
            ]

        return sorted(
            list(records or []),
            key=lambda item: (
                self._datetime_sort_value(
                    getattr(
                        item,
                        "start_time",
                        None,
                    )
                ),
                self._to_int(
                    getattr(
                        item,
                        "id",
                        0,
                    )
                ),
            ),
            reverse=True,
        )

    def _get_all_logs(self):
        if hasattr(
            self.production_repository,
            "get_all",
        ):
            return (
                self.production_repository
                .get_all()
            )

        if hasattr(
            self.production_repository,
            "list_all",
        ):
            return (
                self.production_repository
                .list_all()
            )

        raise AttributeError(
            "ProductionLogRepository does not "
            "provide get_all() or list_all()."
        )

    @classmethod
    def _matches_keyword(
        cls,
        production_log,
        keyword,
    ):
        searchable_values = [
            getattr(
                production_log,
                "work_order_no",
                "",
            ),
            getattr(
                production_log,
                "product_code",
                "",
            ),
            getattr(
                production_log,
                "op_no",
                "",
            ),
            getattr(
                production_log,
                "machine_code",
                "",
            ),
            getattr(
                production_log,
                "employee_code",
                "",
            ),
            getattr(
                production_log,
                "shift",
                "",
            ),
            getattr(
                production_log,
                "status",
                "",
            ),
            getattr(
                production_log,
                "downtime_reason",
                "",
            ),
            getattr(
                production_log,
                "remark",
                "",
            ),
        ]

        return any(
            keyword in str(
                value or ""
            ).lower()
            for value in searchable_values
        )

    # ==========================================================
    # Table mapping
    # ==========================================================

    @classmethod
    def record_to_row(
        cls,
        production_log,
    ):
        runtime_sec = cls._to_float(
            getattr(
                production_log,
                "run_time_sec",
                0,
            )
        )

        runtime_hour = (
            runtime_sec / 3600
        )

        ok_qty = cls._to_int(
            getattr(
                production_log,
                "ok_qty",
                0,
            )
        )

        ng_qty = cls._to_int(
            getattr(
                production_log,
                "ng_qty",
                0,
            )
        )

        total_qty = ok_qty + ng_qty

        yield_percent = (
            ok_qty / total_qty * 100
            if total_qty > 0
            else 0.0
        )

        start_time = getattr(
            production_log,
            "start_time",
            None,
        )

        finish_time = getattr(
            production_log,
            "finish_time",
            None,
        )

        production_date = (
            start_time.date().isoformat()
            if isinstance(
                start_time,
                datetime,
            )
            else ""
        )

        return [
            getattr(
                production_log,
                "id",
                "",
            ),

            production_date,

            getattr(
                production_log,
                "work_order_no",
                "",
            )
            or "",

            getattr(
                production_log,
                "product_code",
                "",
            )
            or "",

            getattr(
                production_log,
                "op_no",
                "",
            )
            or "",

            getattr(
                production_log,
                "machine_code",
                "",
            )
            or "",

            getattr(
                production_log,
                "employee_code",
                "",
            )
            or "",

            getattr(
                production_log,
                "shift",
                "",
            )
            or "",

            cls._format_datetime(
                start_time
            ),

            cls._format_datetime(
                finish_time
            ),

            round(
                runtime_hour,
                3,
            ),

            ok_qty,
            ng_qty,
            total_qty,

            f"{yield_percent:.2f}%",

            cls._to_float(
                getattr(
                    production_log,
                    "downtime_min",
                    0,
                )
            ),

            getattr(
                production_log,
                "downtime_reason",
                "",
            )
            or "",

            getattr(
                production_log,
                "status",
                "",
            )
            or "",

            getattr(
                production_log,
                "remark",
                "",
            )
            or "",
        ]

    @staticmethod
    def get_record_key(
        production_log,
    ):
        return production_log.id

    # ==========================================================
    # Add Production Entry
    # ==========================================================

    def create_dialog(
        self,
        parent=None,
        record=None,
    ):
        if record is not None:
            raise ValueError(
                "Production Log cannot be edited "
                "from Production History."
            )

        return ProductionEntryDialog(
            parent=parent
        )

    def handle_add(self):
        try:
            dialog = self.create_dialog(
                parent=self,
                record=None,
            )

            if not dialog.exec():
                return

            # ProductionEntryDialog tự lưu dữ liệu
            # thông qua ProductionExecutionService.
            self.refresh_table()

        except Exception as error:
            self.show_error(
                "Production Entry Error",
                str(error),
            )

    # ==========================================================
    # Edit disabled
    # ==========================================================

    def handle_edit(self, *_):
        record = self.get_selected_record()

        if record is None:
            self.show_warning(
                "Production Details",
                (
                    "Please select a "
                    "Production Log."
                ),
            )
            return

        self.show_selected_details()

    def update_record(
        self,
        record_key,
        data,
    ):
        raise NotImplementedError(
            "Production Log editing is disabled."
        )

    # ==========================================================
    # Delete disabled
    # ==========================================================

    def handle_delete(self):
        self.show_warning(
            "Delete Production Log",
            (
                "Production Logs cannot be deleted "
                "from the user interface.\n\n"
                "Use an audit correction workflow "
                "instead."
            ),
        )

    def delete_record(
        self,
        record_key,
    ):
        raise NotImplementedError(
            "Production Log deletion is disabled."
        )

    def create_record(
        self,
        data,
    ):
        raise NotImplementedError(
            "ProductionEntryDialog handles saving."
        )

    # ==========================================================
    # Summary
    # ==========================================================

    def update_page_summary(
        self,
        records,
    ):
        total_records = len(records)

        running_count = sum(
            1
            for item in records
            if self._normalize_code(
                getattr(
                    item,
                    "status",
                    "",
                )
            )
            in self.ACTIVE_STATUSES
        )

        completed_count = sum(
            1
            for item in records
            if self._normalize_code(
                getattr(
                    item,
                    "status",
                    "",
                )
            )
            in self.FINAL_STATUSES
        )

        self.update_summary(
            total_records,
            running_count,
            completed_count,
        )

    # ==========================================================
    # Table presentation
    # ==========================================================

    def create_table_item(
        self,
        record,
        column_index,
        value,
    ):
        item = QTableWidgetItem(
            self.display_value(value)
        )

        item.setFlags(
            item.flags()
            & ~Qt.ItemIsEditable
        )

        centered_columns = {
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            17,
        }

        if column_index in centered_columns:
            item.setTextAlignment(
                Qt.AlignCenter
            )

        # Yield
        if column_index == 14:
            yield_percent = (
                self._parse_percent(
                    value
                )
            )

            if yield_percent >= 98:
                item.setForeground(
                    Qt.darkGreen
                )

            elif yield_percent >= 95:
                item.setForeground(
                    Qt.darkYellow
                )

            else:
                item.setForeground(
                    Qt.red
                )

        # NG quantity
        if column_index == 12:
            ng_qty = self._to_int(
                value
            )

            if ng_qty > 0:
                item.setForeground(
                    Qt.red
                )

        # Status
        if column_index == 17:
            status = self._normalize_code(
                value
            )

            if status in {
                "COMPLETED",
                "CLOSED",
            }:
                item.setForeground(
                    Qt.darkGreen
                )

            elif status in {
                "RUNNING",
                "STARTED",
            }:
                item.setForeground(
                    Qt.blue
                )

            elif status in {
                "CANCELLED",
                "ERROR",
            }:
                item.setForeground(
                    Qt.red
                )

        return item

    # ==========================================================
    # Context menu
    # ==========================================================

    def add_context_actions(
        self,
        menu,
    ):
        menu.addSeparator()

        action_details = menu.addAction(
            "View Production Details"
        )

        action_work_order = menu.addAction(
            "Show Work Order Logs"
        )

        action_machine = menu.addAction(
            "Show Machine Logs"
        )

        return {
            action_details:
                self.show_selected_details,

            action_work_order:
                self.filter_selected_work_order,

            action_machine:
                self.filter_selected_machine,
        }

    # ==========================================================
    # Details
    # ==========================================================

    def show_selected_details(self):
        record = self.get_selected_record()

        if record is None:
            self.show_warning(
                "Production Details",
                "Please select a Production Log.",
            )
            return

        values = self.record_to_row(
            record
        )

        lines = [
            (
                f"{header}: "
                f"{values[index]}"
            )
            for index, header
            in enumerate(self.HEADERS)
        ]

        record_hash = getattr(
            record,
            "record_hash",
            "",
        )

        if record_hash:
            lines.extend([
                "",
                f"Record Hash: {record_hash}",
            ])

        QMessageBox.information(
            self,
            "Production Log Details",
            "\n".join(lines),
        )

    def filter_selected_work_order(self):
        record = self.get_selected_record()

        if record is None:
            return

        work_order_no = getattr(
            record,
            "work_order_no",
            "",
        )

        self._set_search_text(
            work_order_no
        )

    def filter_selected_machine(self):
        record = self.get_selected_record()

        if record is None:
            return

        machine_code = getattr(
            record,
            "machine_code",
            "",
        )

        self._set_search_text(
            machine_code
        )

    def _set_search_text(self, text):
        if hasattr(
            self.search_bar,
            "setText",
        ):
            self.search_bar.setText(
                str(text or "")
            )
            return

        line_edit = self._get_search_line_edit()

        if line_edit is not None:
            line_edit.setText(
                str(text or "")
            )

    # ==========================================================
    # Export
    # ==========================================================

    @classmethod
    def record_to_export_row(
        cls,
        production_log,
    ):
        runtime_sec = cls._to_float(
            getattr(
                production_log,
                "run_time_sec",
                0,
            )
        )

        ok_qty = cls._to_int(
            getattr(
                production_log,
                "ok_qty",
                0,
            )
        )

        ng_qty = cls._to_int(
            getattr(
                production_log,
                "ng_qty",
                0,
            )
        )

        total_qty = ok_qty + ng_qty

        yield_percent = (
            ok_qty / total_qty * 100
            if total_qty > 0
            else 0.0
        )

        return {
            "ID":
                getattr(
                    production_log,
                    "id",
                    "",
                ),

            "Record Hash":
                getattr(
                    production_log,
                    "record_hash",
                    "",
                )
                or "",

            "Work Order No":
                getattr(
                    production_log,
                    "work_order_no",
                    "",
                )
                or "",

            "Product Code":
                getattr(
                    production_log,
                    "product_code",
                    "",
                )
                or "",

            "OP No":
                getattr(
                    production_log,
                    "op_no",
                    "",
                )
                or "",

            "Machine Code":
                getattr(
                    production_log,
                    "machine_code",
                    "",
                )
                or "",

            "Employee Code":
                getattr(
                    production_log,
                    "employee_code",
                    "",
                )
                or "",

            "Shift":
                getattr(
                    production_log,
                    "shift",
                    "",
                )
                or "",

            "Start Time":
                cls._format_datetime(
                    getattr(
                        production_log,
                        "start_time",
                        None,
                    )
                ),

            "Finish Time":
                cls._format_datetime(
                    getattr(
                        production_log,
                        "finish_time",
                        None,
                    )
                ),

            "Runtime Sec":
                runtime_sec,

            "Runtime Hour":
                round(
                    runtime_sec / 3600,
                    4,
                ),

            "OK Qty":
                ok_qty,

            "NG Qty":
                ng_qty,

            "Total Qty":
                total_qty,

            "Yield Percent":
                round(
                    yield_percent,
                    4,
                ),

            "Downtime Min":
                cls._to_float(
                    getattr(
                        production_log,
                        "downtime_min",
                        0,
                    )
                ),

            "Downtime Reason":
                getattr(
                    production_log,
                    "downtime_reason",
                    "",
                )
                or "",

            "Status":
                getattr(
                    production_log,
                    "status",
                    "",
                )
                or "",

            "Remark":
                getattr(
                    production_log,
                    "remark",
                    "",
                )
                or "",
        }

    # ==========================================================
    # Helpers
    # ==========================================================

    @staticmethod
    def _normalize_code(value):
        return str(
            value or ""
        ).strip().upper()

    @staticmethod
    def _to_int(value):
        try:
            return int(
                float(value or 0)
            )

        except (
            TypeError,
            ValueError,
        ):
            return 0

    @staticmethod
    def _to_float(value):
        try:
            return float(
                value or 0
            )

        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    @staticmethod
    def _parse_percent(value):
        try:
            return float(
                str(
                    value or "0"
                ).replace(
                    "%",
                    "",
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    @staticmethod
    def _format_datetime(value):
        if value is None:
            return ""

        if isinstance(value, datetime):
            return value.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        return str(value)

    @staticmethod
    def _datetime_sort_value(value):
        if isinstance(value, datetime):
            return value

        try:
            return datetime.fromisoformat(
                str(value)
            )

        except (
            TypeError,
            ValueError,
        ):
            return datetime.min