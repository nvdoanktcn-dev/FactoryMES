from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidgetItem

from src.services.cnc_machine_service import CNCMachineService
from src.ui.dialogs.cnc_machine_dialog import CNCMachineDialog
from src.ui.framework.master_crud_page import MasterCRUDPage


class CNCMachinePage(MasterCRUDPage):
    """
    Danh mục máy CNC.
    """

    ENTITY_NAME = "CNC Machine"

    HEADERS = [
        "Machine Code",
        "Machine Name",
        "Type",
        "Controller",
        "Location",
        "Status",
    ]

    DEFAULT_EXPORT_NAME = "cnc_machine.xlsx"

    def __init__(self):
        super().__init__(
            title="🛠️ CNC Machine",
            headers=self.HEADERS,
            search_placeholder="Search CNC machine...",
            service=CNCMachineService(),
            importer=None,
            dialog_class=CNCMachineDialog,
        )

        self.initialize_page()

    # ==========================================================
    # Data
    # ==========================================================

    def load_records(self, keyword):
        return self.service.search_cnc_machines(keyword)

    @staticmethod
    def record_to_row(machine):
        return [
            machine.machine_code or "",
            machine.machine_name or "",
            machine.machine_type or "",
            machine.controller or "",
            machine.location or "",
            machine.status or "",
        ]

    @staticmethod
    def get_record_key(machine):
        return machine.machine_code

    # ==========================================================
    # Dialog
    # ==========================================================

    def create_dialog(self, parent=None, record=None):
        return self.dialog_class(parent=parent, machine=record)

    # ==========================================================
    # CRUD
    # ==========================================================

    def create_record(self, data):
        return self.service.create_cnc_machine(data)

    def update_record(self, record_key, data):
        return self.service.update_cnc_machine(record_key, data)

    def delete_record(self, record_key):
        return self.service.delete_cnc_machine(record_key)

    # ==========================================================
    # Table presentation
    # ==========================================================

    def create_table_item(self, record, column_index, value):
        item = QTableWidgetItem(self.display_value(value))
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)

        if column_index in {0, 2, 3, 4, 5}:
            item.setTextAlignment(Qt.AlignCenter)

        if column_index == 5:
            status = str(value or "").strip().upper()

            if status == "ACTIVE":
                item.setForeground(Qt.darkGreen)
            elif status == "INACTIVE":
                item.setForeground(Qt.red)

        return item

    # ==========================================================
    # Validation
    # ==========================================================

    def validate_dialog_data(self, data, is_edit=False):
        super().validate_dialog_data(data, is_edit=is_edit)

        if not str(data.get("machine_code", "")).strip():
            raise ValueError("Machine Code is required.")

        if not str(data.get("machine_name", "")).strip():
            raise ValueError("Machine Name is required.")

        return True

    # ==========================================================
    # Export
    # ==========================================================

    @staticmethod
    def record_to_export_row(machine):
        return {
            "Machine Code": machine.machine_code or "",
            "Machine Name": machine.machine_name or "",
            "Type": machine.machine_type or "",
            "Controller": machine.controller or "",
            "Location": machine.location or "",
            "Status": machine.status or "",
        }
