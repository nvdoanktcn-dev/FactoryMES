from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidgetItem

from src.importer.cnc_importer import CNCImporter
from src.services.cnc_production_log_service import (
    CNCProductionLogService,
)
from src.ui.dialogs.cnc_production_log_dialog import (
    CNCProductionLogDialog,
)
from src.ui.framework.master_crud_page import MasterCRUDPage


class CNCProductionLogPage(MasterCRUDPage):
    """
    Log sản xuất CNC.

    Dữ liệu chủ yếu được nạp bằng nút Import (CNCImporter đọc file
    Excel/CSV theo mẫu báo cáo CNC), có thể Add/Edit/Delete thủ công
    để sửa sai sót.
    """

    ENTITY_NAME = "CNC Production Log"

    HEADERS = [
        "Date",
        "Machine",
        "Work Order",
        "Product",
        "Operator",
        "Shift",
        "Actual PCS",
        "Total NG",
    ]

    DEFAULT_EXPORT_NAME = "cnc_production_log.xlsx"

    def __init__(self):
        super().__init__(
            title="📈 CNC Production Log",
            headers=self.HEADERS,
            search_placeholder="Search CNC log...",
            service=CNCProductionLogService(),
            importer=CNCImporter(),
            dialog_class=CNCProductionLogDialog,
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
            log.machine_name or "",
            log.work_order_no or "",
            log.product_name or "",
            log.operator_name or "",
            log.shift or "",
            log.actual_pcs or 0,
            log.total_ng or 0,
        ]

    @staticmethod
    def get_record_key(log):
        return log.id

    # ==========================================================
    # Dialog
    # ==========================================================

    def create_dialog(self, parent=None, record=None):
        return self.dialog_class(parent=parent, log=record)

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

        with_ng = sum(
            1 for record in records if float(record.total_ng or 0) > 0
        )

        without_ng = total - with_ng

        self.update_summary(total, without_ng, with_ng)

        total_ng_qty = sum(
            float(record.total_ng or 0) for record in records
        )

        self.set_status(
            f"Total {self.ENTITY_NAME}: {total} | "
            f"Total NG Qty: {total_ng_qty:g}"
        )

    # ==========================================================
    # Table presentation
    # ==========================================================

    def create_table_item(self, record, column_index, value):
        item = QTableWidgetItem(self.display_value(value))
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)

        if column_index in {0, 6, 7}:
            item.setTextAlignment(Qt.AlignCenter)

        return item

    # ==========================================================
    # Validation
    # ==========================================================

    def validate_dialog_data(self, data, is_edit=False):
        super().validate_dialog_data(data, is_edit=is_edit)

        if not str(data.get("machine_name", "")).strip():
            raise ValueError("Machine Name is required.")

        if not str(data.get("work_order_no", "")).strip():
            raise ValueError("Work Order No is required.")

        return True

    # ==========================================================
    # Export
    # ==========================================================

    @staticmethod
    def record_to_export_row(log):
        return {
            "Date": log.log_date.isoformat() if log.log_date else "",
            "Machine": log.machine_name or "",
            "Work Order": log.work_order_no or "",
            "Product": log.product_name or "",
            "Operator": log.operator_name or "",
            "Shift": log.shift or "",
            "Actual PCS": log.actual_pcs or 0,
            "Total NG": log.total_ng or 0,
        }
