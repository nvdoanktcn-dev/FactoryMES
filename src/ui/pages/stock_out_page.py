from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidgetItem

from src.services.stock_out_service import StockOutService
from src.ui.dialogs.stock_out_dialog import StockOutDialog
from src.ui.framework.master_crud_page import MasterCRUDPage


class StockOutPage(MasterCRUDPage):
    """
    Xuất kho (StockOut).
    """

    ENTITY_NAME = "Stock Out"

    HEADERS = [
        "Date",
        "Item Code",
        "Qty",
        "Remark",
    ]

    DEFAULT_EXPORT_NAME = "stock_out.xlsx"

    def __init__(self):
        super().__init__(
            title="📤 Stock Out",
            headers=self.HEADERS,
            search_placeholder="Search stock out...",
            service=StockOutService(),
            importer=None,
            dialog_class=StockOutDialog,
        )

        self.initialize_page()

    # ==========================================================
    # Data
    # ==========================================================

    def load_records(self, keyword):
        return self.service.search_stock_out(keyword)

    @staticmethod
    def record_to_row(record):
        return [
            (
                record.stock_out_date.isoformat()
                if record.stock_out_date
                else ""
            ),
            record.item_code or "",
            record.qty or 0,
            record.remark or "",
        ]

    @staticmethod
    def get_record_key(record):
        return record.stock_out_id

    # ==========================================================
    # Dialog
    # ==========================================================

    def create_dialog(self, parent=None, record=None):
        return self.dialog_class(parent=parent, stock_out=record)

    # ==========================================================
    # CRUD
    # ==========================================================

    def create_record(self, data):
        return self.service.create_stock_out(data)

    def update_record(self, record_key, data):
        return self.service.update_stock_out(record_key, data)

    def delete_record(self, record_key):
        return self.service.delete_stock_out(record_key)

    # ==========================================================
    # Summary
    # ==========================================================

    def update_page_summary(self, records):
        total = len(records)

        total_qty = sum(float(record.qty or 0) for record in records)

        self.update_summary(total, total, 0)

        self.set_status(
            f"Total {self.ENTITY_NAME}: {total} | "
            f"Total Qty: {total_qty:g}"
        )

    # ==========================================================
    # Table presentation
    # ==========================================================

    def create_table_item(self, record, column_index, value):
        item = QTableWidgetItem(self.display_value(value))
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)

        if column_index in {0, 2}:
            item.setTextAlignment(Qt.AlignCenter)

        return item

    # ==========================================================
    # Validation
    # ==========================================================

    def validate_dialog_data(self, data, is_edit=False):
        super().validate_dialog_data(data, is_edit=is_edit)

        if not str(data.get("item_code", "")).strip():
            raise ValueError("Item Code is required.")

        return True

    # ==========================================================
    # Export
    # ==========================================================

    @staticmethod
    def record_to_export_row(record):
        return {
            "Date": (
                record.stock_out_date.isoformat()
                if record.stock_out_date
                else ""
            ),
            "Item Code": record.item_code or "",
            "Qty": record.qty or 0,
            "Remark": record.remark or "",
        }
