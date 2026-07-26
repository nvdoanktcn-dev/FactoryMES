from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidgetItem

from src.importer.machine_importer import MachineImporter
from src.services.machine_service import MachineService
from src.ui.dialogs.machine_dialog import MachineDialog
from src.ui.framework.master_crud_page import MasterCRUDPage


class MachinePage(MasterCRUDPage):
    """
    Machine Master Page V2.

    CRUD, Search, Import, Export, Refresh,
    Double-click và Context Menu được xử lý
    bởi MasterCRUDPage.
    """

    ENTITY_NAME = "Machine"

    HEADERS = [
        "Machine Code",
        "Machine Name",
        "Machine Type",
        "Line",
        "Location",
        "Brand",
        "Model",
        "Serial Number",
        "Status",
    ]

    DEFAULT_EXPORT_NAME = "machine_master.xlsx"

    ACTIVE_MACHINE_STATUSES = {
        "ACTIVE",
        "RUNNING",
        "READY",
        "MAINTENANCE",
        "STOPPED",
    }

    def __init__(self):
        super().__init__(
            title="⚙ Machine Management",
            headers=self.HEADERS,
            search_placeholder="Search machine...",
            service=MachineService(),
            importer=MachineImporter(),
            dialog_class=MachineDialog,
        )

        self.initialize_page()

    # ==========================================================
    # Data
    # ==========================================================

    def load_records(self, keyword):
        """
        Hỗ trợ cả API search_machines() và search().
        """
        if hasattr(
            self.service,
            "search_machines",
        ):
            return self.service.search_machines(
                keyword
            )

        if hasattr(
            self.service,
            "search",
        ):
            return self.service.search(
                keyword
            )

        machines = self.service.get_all()

        keyword = str(
            keyword or ""
        ).strip().lower()

        if not keyword:
            return machines

        return [
            machine
            for machine in machines
            if (
                keyword
                in str(
                    machine.machine_code or ""
                ).lower()
                or keyword
                in str(
                    machine.machine_name or ""
                ).lower()
                or keyword
                in str(
                    machine.machine_type or ""
                ).lower()
                or keyword
                in str(
                    machine.line or ""
                ).lower()
                or keyword
                in str(
                    machine.location or ""
                ).lower()
                or keyword
                in str(
                    machine.status or ""
                ).lower()
            )
        ]

    @staticmethod
    def record_to_row(machine):
        return [
            machine.machine_code or "",
            machine.machine_name or "",
            machine.machine_type or "",
            machine.line or "",
            machine.location or "",
            machine.brand or "",
            machine.model or "",
            machine.serial_number or "",
            machine.status or "",
        ]

    @staticmethod
    def get_record_key(machine):
        return machine.machine_code

    # ==========================================================
    # Dialog
    # ==========================================================

    def create_dialog(
        self,
        parent=None,
        record=None,
    ):
        return self.dialog_class(
            parent=parent,
            machine=record,
        )

    # ==========================================================
    # CRUD
    # ==========================================================

    def create_record(self, data):
        """
        Hỗ trợ cả MachineService nhận dictionary
        và MachineService nhận keyword arguments.
        """
        try:
            try:
                result = self.service.create_machine(
                    data
                )

            except TypeError:
                result = self.service.create_machine(
                    machine_code=data.get(
                        "machine_code",
                        "",
                    ),
                    machine_name=data.get(
                        "machine_name",
                        "",
                    ),
                    machine_type=data.get(
                        "machine_type",
                    ),
                    line=data.get(
                        "line",
                    ),
                    location=data.get(
                        "location",
                    ),
                    brand=data.get(
                        "brand",
                    ),
                    model=data.get(
                        "model",
                    ),
                    serial_number=data.get(
                        "serial_number",
                    ),
                    status=data.get(
                        "status",
                        "RUNNING",
                    ),
                )

            self._commit_changes()
            return result

        except Exception:
            self._rollback_changes()
            raise

    def update_record(
        self,
        record_key,
        data,
    ):
        if hasattr(
            self.service,
            "update_machine",
        ):
            try:
                result = self.service.update_machine(
                    record_key,
                    data,
                )
                self._commit_changes()
                return result
            except Exception:
                self._rollback_changes()
                raise

        try:
            result = self.service.update(
                record_key,
                data,
            )
            self._commit_changes()
            return result
        except Exception:
            self._rollback_changes()
            raise

    def delete_record(
        self,
        record_key,
    ):
        if hasattr(
            self.service,
            "delete_machine",
        ):
            try:
                result = self.service.delete_machine(
                    record_key
                )
                self._commit_changes()
                return result
            except Exception:
                self._rollback_changes()
                raise

        try:
            result = self.service.delete(
                record_key
            )
            self._commit_changes()
            return result
        except Exception:
            self._rollback_changes()
            raise

    def add_context_actions(self, menu):
        machine = self.get_selected_record()

        if machine is None:
            return {}

        status = str(
            machine.status or ""
        ).strip().upper()

        if status != "INACTIVE":
            return {}

        action_activate = menu.addAction(
            "Activate Machine"
        )

        return {
            action_activate: self.handle_activate
        }

    def handle_activate(self):
        machine = self.get_selected_record()

        if machine is None:
            return

        confirmed = self.confirm(
            "Activate Machine",
            (
                "Activate Machine:\n\n"
                f"{machine.machine_code}?"
            ),
        )

        if not confirmed:
            return

        try:
            activate_method = getattr(
                self.service,
                "activate_machine",
                None,
            )

            if callable(activate_method):
                activate_method(
                    machine.machine_code
                )
            else:
                self.service.update_machine(
                    machine.machine_code,
                    {
                        **{
                            "machine_code":
                                machine.machine_code,
                            "machine_name":
                                machine.machine_name,
                            "machine_type":
                                machine.machine_type,
                            "line": machine.line,
                            "location":
                                machine.location,
                            "brand": machine.brand,
                            "model": machine.model,
                            "serial_number":
                                machine.serial_number,
                        },
                        "status": "RUNNING",
                    },
                )

            self._commit_changes()
            self.refresh_table()

            self.show_info(
                "Success",
                "Machine activated successfully.",
            )

        except Exception as error:
            self._rollback_changes()
            self.show_error(
                "Activate Machine Error",
                str(error),
            )

    def _commit_changes(self):
        commit_method = getattr(
            self.service,
            "commit_changes",
            None,
        )

        if callable(commit_method):
            commit_method()

    def _rollback_changes(self):
        rollback_method = getattr(
            self.service,
            "rollback_changes",
            None,
        )

        if callable(rollback_method):
            rollback_method()

    # ==========================================================
    # Summary
    # ==========================================================

    def update_page_summary(
        self,
        records,
    ):
        total = len(records)

        inactive = sum(
            1
            for machine in records
            if str(
                machine.status or ""
            ).strip().upper()
            in {
                "INACTIVE",
                "RETIRED",
                "DISABLED",
            }
        )

        active = total - inactive

        self.update_summary(
            total,
            active,
            inactive,
        )

    def get_active_statuses(self):
        return self.ACTIVE_MACHINE_STATUSES

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

        if column_index in {
            0,
            2,
            3,
            8,
        }:
            item.setTextAlignment(
                Qt.AlignCenter
            )

        if column_index == 8:
            status = str(
                value or ""
            ).strip().upper()

            if status in {
                "ACTIVE",
                "RUNNING",
                "READY",
            }:
                item.setForeground(
                    Qt.darkGreen
                )

            elif status == "MAINTENANCE":
                item.setForeground(
                    Qt.darkYellow
                )

            elif status in {
                "STOPPED",
                "INACTIVE",
                "RETIRED",
                "DISABLED",
            }:
                item.setForeground(
                    Qt.red
                )

        return item

    # ==========================================================
    # Validation
    # ==========================================================

    def validate_dialog_data(
        self,
        data,
        is_edit=False,
    ):
        super().validate_dialog_data(
            data,
            is_edit=is_edit,
        )

        machine_code = str(
            data.get(
                "machine_code",
                "",
            )
        ).strip().upper()

        machine_name = str(
            data.get(
                "machine_name",
                "",
            )
        ).strip()

        if not machine_code:
            raise ValueError(
                "Machine Code is required."
            )

        if not machine_name:
            raise ValueError(
                "Machine Name is required."
            )

        return True

    # ==========================================================
    # Export
    # ==========================================================

    @staticmethod
    def record_to_export_row(machine):
        return {
            "Machine Code":
                machine.machine_code or "",

            "Machine Name":
                machine.machine_name or "",

            "Machine Type":
                machine.machine_type or "",

            "Line":
                machine.line or "",

            "Location":
                machine.location or "",

            "Brand":
                machine.brand or "",

            "Model":
                machine.model or "",

            "Serial Number":
                machine.serial_number or "",

            "Status":
                machine.status or "",
        }
