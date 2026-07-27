from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidgetItem

from src.importer.finished_inventory_importer import (
    FinishedInventoryImporter,
)
from src.services.finished_inventory_service import (
    FinishedInventoryService,
)
from src.ui.dialogs.finished_inventory_dialog import (
    FinishedInventoryDialog,
)
from src.ui.framework.master_crud_page import MasterCRUDPage


class FinishedInventoryPage(MasterCRUDPage):
    """
    Tồn kho thành phẩm (FinishedInventory).
    """

    ENTITY_NAME = "Finished Inventory"

    HEADERS = [
        "Date",
        "Work Order",
        "Product Code",
        "Qty",
    ]

    DEFAULT_EXPORT_NAME = "finished_inventory.xlsx"

    def __init__(
        self,
        service=None,
        importer=None,
    ):
        inventory_service = (
            service
            or FinishedInventoryService()
        )

        inventory_importer = (
            importer
            or FinishedInventoryImporter(
                service=inventory_service
            )
        )

        super().__init__(
            title="📦 Finished Inventory",
            headers=self.HEADERS,
            search_placeholder="Search finished inventory...",
            service=inventory_service,
            importer=inventory_importer,
            dialog_class=FinishedInventoryDialog,
        )

        self.initialize_page()

    # ==========================================================
    # Data
    # ==========================================================

    def load_records(self, keyword):
        return self.service.search_inventory(keyword)

    @staticmethod
    def record_to_row(record):
        return [
            (
                record.inventory_date.isoformat()
                if record.inventory_date
                else ""
            ),
            record.work_order or "",
            record.product_code or "",
            record.qty or 0,
        ]

    @staticmethod
    def get_record_key(record):
        return record.inventory_id

    # ==========================================================
    # Dialog
    # ==========================================================

    def create_dialog(self, parent=None, record=None):
        return self.dialog_class(parent=parent, inventory=record)

    # ==========================================================
    # CRUD
    # ==========================================================

    def create_record(self, data):
        return self.service.create_inventory(data)

    def update_record(self, record_key, data):
        return self.service.update_inventory(record_key, data)

    def delete_record(self, record_key):
        return self.service.delete_inventory(record_key)

    # ==========================================================
    # Summary
    # ==========================================================

    def update_page_summary(self, records):
        total = len(records)

        total_qty = sum(int(record.qty or 0) for record in records)

        self.update_summary(total, total, 0)

        self.set_status(
            f"Total {self.ENTITY_NAME}: {total} | "
            f"Total Qty: {total_qty}"
        )

    # ==========================================================
    # Table presentation
    # ==========================================================

    def create_table_item(self, record, column_index, value):
        item = QTableWidgetItem(self.display_value(value))
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)

        if column_index in {0, 3}:
            item.setTextAlignment(Qt.AlignCenter)

        return item

    # ==========================================================
    # Validation
    # ==========================================================

    def validate_dialog_data(self, data, is_edit=False):
        super().validate_dialog_data(data, is_edit=is_edit)

        if not str(data.get("work_order", "")).strip():
            raise ValueError("Work Order is required.")

        if not str(data.get("product_code", "")).strip():
            raise ValueError("Product Code is required.")

        return True

    # ==========================================================
    # Export
    # ==========================================================

    @staticmethod
    def record_to_export_row(record):
        return {
            "Date": (
                record.inventory_date.isoformat()
                if record.inventory_date
                else ""
            ),
            "Work Order": record.work_order or "",
            "Product Code": record.product_code or "",
            "Qty": record.qty or 0,
        }
