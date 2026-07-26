from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidgetItem

from src.services.robot_operation_log_service import (
    RobotOperationLogService,
)
from src.services.robot_service import RobotService
from src.ui.dialogs.robot_operation_log_dialog import (
    RobotOperationLogDialog,
)
from src.ui.framework.master_crud_page import MasterCRUDPage


class RobotOperationLogPage(MasterCRUDPage):
    """
    Log vận hành Robot (thời gian chạy, sản lượng, lỗi).

    Nhập thủ công, chưa có importer Excel (khác CNC Production Log).
    """

    ENTITY_NAME = "Robot Operation Log"

    HEADERS = [
        "Date",
        "Robot",
        "Shift",
        "Output Qty",
        "NG Qty",
        "Error Code",
        "Status",
    ]

    DEFAULT_EXPORT_NAME = "robot_operation_log.xlsx"

    def __init__(self):
        self.robot_service = RobotService()

        super().__init__(
            title="🦾 Robot Operation Log",
            headers=self.HEADERS,
            search_placeholder="Search robot log...",
            service=RobotOperationLogService(),
            importer=None,
            dialog_class=RobotOperationLogDialog,
        )

        self.initialize_page()

    # ==========================================================
    # Data
    # ==========================================================

    def load_records(self, keyword):
        return self.service.search_logs(keyword)

    @staticmethod
    def record_to_row(log):
        return [
            log.log_date.isoformat() if log.log_date else "",
            log.robot_code or "",
            log.shift or "",
            log.output_qty or 0,
            log.ng_qty or 0,
            log.error_code or "",
            log.status or "",
        ]

    @staticmethod
    def get_record_key(log):
        return log.id

    # ==========================================================
    # Dialog
    # ==========================================================

    def create_dialog(self, parent=None, record=None):
        robot_codes = [
            robot.robot_code
            for robot in self.robot_service.get_all_robots()
        ]

        return self.dialog_class(
            parent=parent,
            log=record,
            robot_codes=robot_codes,
        )

    # ==========================================================
    # CRUD
    # ==========================================================

    def create_record(self, data):
        return self.service.create_log(data)

    def update_record(self, record_key, data):
        return self.service.update_log(record_key, data)

    def delete_record(self, record_key):
        return self.service.delete_log(record_key)

    # ==========================================================
    # Summary
    # ==========================================================

    def update_page_summary(self, records):
        total = len(records)

        with_error = sum(
            1
            for record in records
            if str(record.status or "").strip().upper() == "ERROR"
        )

        self.update_summary(total, total - with_error, with_error)

    # ==========================================================
    # Table presentation
    # ==========================================================

    def create_table_item(self, record, column_index, value):
        item = QTableWidgetItem(self.display_value(value))
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)

        if column_index in {0, 3, 4, 6}:
            item.setTextAlignment(Qt.AlignCenter)

        if column_index == 6:
            status = str(value or "").strip().upper()

            if status == "ERROR":
                item.setForeground(Qt.red)
            elif status == "COMPLETED":
                item.setForeground(Qt.darkGreen)

        return item

    # ==========================================================
    # Validation
    # ==========================================================

    def validate_dialog_data(self, data, is_edit=False):
        super().validate_dialog_data(data, is_edit=is_edit)

        if not str(data.get("robot_code", "")).strip():
            raise ValueError("Robot Code is required.")

        return True

    # ==========================================================
    # Export
    # ==========================================================

    @staticmethod
    def record_to_export_row(log):
        return {
            "Date": log.log_date.isoformat() if log.log_date else "",
            "Robot": log.robot_code or "",
            "Shift": log.shift or "",
            "Output Qty": log.output_qty or 0,
            "NG Qty": log.ng_qty or 0,
            "Error Code": log.error_code or "",
            "Status": log.status or "",
        }

    # ==========================================================
    # Lifecycle
    # ==========================================================

    def close_resources(self):
        if self.service is not None:
            self.service.close()

        if self.robot_service is not None:
            self.robot_service.close()
