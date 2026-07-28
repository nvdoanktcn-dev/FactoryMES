from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QPushButton,
    QTableWidgetItem,
)

from src.importer.finished_inventory_importer import (
    FinishedInventoryImporter,
)
from src.services.finished_inventory_import_history_service import (
    FinishedInventoryImportHistoryService,
)
from src.services.finished_inventory_service import (
    FinishedInventoryService,
)
from src.ui.dialogs.finished_inventory_dialog import (
    FinishedInventoryDialog,
)
from src.ui.dialogs.finished_inventory_import_history_dialog import (
    FinishedInventoryImportHistoryDialog,
)
from src.ui.dialogs.finished_inventory_pending_receipts_dialog import (
    FinishedInventoryPendingReceiptsDialog,
)
from src.ui.dialogs.finished_inventory_receipt_audit_dialog import (
    FinishedInventoryReceiptAuditDialog,
)
from src.ui.framework.master_crud_page import MasterCRUDPage


class FinishedInventoryPage(MasterCRUDPage):
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
        history_service=None,
        current_user=None,
    ):
        self.current_user = current_user
        self.audit_username = str(
            getattr(current_user, "audit_username", None)
            or getattr(current_user, "username", None)
            or "System"
        )
        self._owns_service = service is None
        service = service or FinishedInventoryService()
        session = getattr(
            getattr(service, "repository", None),
            "session",
            None,
        )
        self._owns_history_service = (
            history_service is None
            and session is not None
        )
        history_service = (
            history_service
            or (
                FinishedInventoryImportHistoryService(
                    session=session
                )
                if session is not None
                else None
            )
        )
        importer = (
            importer
            or FinishedInventoryImporter(
                service=service,
                history_service=history_service,
                username=self.audit_username,
            )
        )

        super().__init__(
            title="📦 Finished Inventory",
            headers=self.HEADERS,
            search_placeholder="Search finished inventory...",
            service=service,
            importer=importer,
            dialog_class=FinishedInventoryDialog,
        )

        self.history_service = history_service
        self.pending_receipts_button = QPushButton(
            "📥 Pending Receipts"
        )
        self.receipt_audit_button = QPushButton(
            "📋 Receipt History"
        )
        self.history_button = QPushButton(
            "🕘 Import History"
        )
        toolbar_layout = self.toolbar.layout()
        insert_at = max(
            0,
            toolbar_layout.count() - 1,
        )
        toolbar_layout.insertWidget(
            insert_at,
            self.pending_receipts_button,
        )
        toolbar_layout.insertWidget(
            insert_at + 1,
            self.receipt_audit_button,
        )
        toolbar_layout.insertWidget(
            insert_at + 2,
            self.history_button,
        )
        self.pending_receipts_button.clicked.connect(
            self.show_pending_receipts
        )
        self.receipt_audit_button.clicked.connect(
            self.show_receipt_audit_history
        )
        self.history_button.clicked.connect(
            self.show_import_history
        )

        self.initialize_page()

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

    def create_dialog(self, parent=None, record=None):
        return self.dialog_class(
            parent=parent,
            inventory=record,
            service=self.service,
        )

    def create_record(self, data):
        return self.service.create_inventory(
            data,
            username=self.audit_username,
        )

    def update_record(self, record_key, data):
        return self.service.update_inventory(
            record_key,
            data,
            username=self.audit_username,
        )

    def delete_record(self, record_key):
        return self.service.delete_inventory(
            record_key,
            username=self.audit_username,
        )

    def update_page_summary(self, records):
        total = len(records)
        total_qty = sum(
            int(record.qty or 0)
            for record in records
        )
        self.update_summary(total, total, 0)
        self.set_status(
            f"Total {self.ENTITY_NAME}: {total} | "
            f"Total Qty: {total_qty}"
        )

    def create_table_item(
        self,
        record,
        column_index,
        value,
    ):
        del record
        item = QTableWidgetItem(
            self.display_value(value)
        )
        item.setFlags(
            item.flags() & ~Qt.ItemIsEditable
        )
        if column_index in {0, 3}:
            item.setTextAlignment(Qt.AlignCenter)
        return item

    def validate_dialog_data(
        self,
        data,
        is_edit=False,
    ):
        super().validate_dialog_data(
            data,
            is_edit=is_edit,
        )
        if not str(
            data.get("work_order", "")
        ).strip():
            raise ValueError(
                "Work Order is required."
            )
        if not str(
            data.get("product_code", "")
        ).strip():
            raise ValueError(
                "Product Code is required."
            )
        return True

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

    def show_pending_receipts(self):
        dialog = (
            FinishedInventoryPendingReceiptsDialog(
                parent=self,
                service=self.service,
                username=self.audit_username,
            )
        )
        dialog.exec()
        self.refresh_table()

    def show_receipt_audit_history(self):
        if getattr(
            self.service,
            "receipt_audit_service",
            None,
        ) is None:
            self.show_warning(
                "Receipt Audit History",
                "Receipt audit is unavailable for "
                "the injected test service.",
            )
            return
        dialog = FinishedInventoryReceiptAuditDialog(
            parent=self,
            service=self.service,
            username=self.audit_username,
        )
        dialog.exec()
        self.refresh_table()

    def show_import_history(self):
        if self.history_service is None:
            self.show_warning(
                "Finished Inventory Import History",
                "Import history is unavailable for "
                "the injected test service.",
            )
            return
        dialog = FinishedInventoryImportHistoryDialog(
            parent=self,
            service=self.history_service,
            username=self.audit_username,
        )
        dialog.exec()
        self.refresh_table()

    def add_context_actions(self, menu):
        pending_action = menu.addAction(
            "Finished Inventory Pending Receipts"
        )
        audit_action = menu.addAction(
            "Finished Inventory Receipt History"
        )
        history_action = menu.addAction(
            "Finished Inventory Import History"
        )
        return {
            pending_action: self.show_pending_receipts,
            audit_action: self.show_receipt_audit_history,
            history_action: self.show_import_history,
        }

    def close_resources(self):
        close_importer = getattr(
            self.importer,
            "close",
            None,
        )
        if callable(close_importer):
            close_importer()
        if (
            self._owns_history_service
            and self.history_service is not None
        ):
            self.history_service.close()
        if self._owns_service:
            self.service.close()
