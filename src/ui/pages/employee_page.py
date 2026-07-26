from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidgetItem

from src.importer.employee_importer import EmployeeImporter
from src.services.employee_service import EmployeeService
from src.ui.dialogs.employee_dialog import EmployeeDialog
from src.ui.framework.master_crud_page import MasterCRUDPage


class EmployeePage(MasterCRUDPage):
    """
    Employee Master Page V2.

    CRUD, Search, Import, Export, Refresh,
    Double-click và Context Menu được xử lý
    bởi MasterCRUDPage.
    """

    ENTITY_NAME = "Employee"

    HEADERS = [
        "Employee Code",
        "Employee Name",
        "Department",
        "Position",
        "Shift",
        "Remark",
        "Status",
    ]

    DEFAULT_EXPORT_NAME = "employee_master.xlsx"

    def __init__(self):
        super().__init__(
            title="👷 Employee Management",
            headers=self.HEADERS,
            search_placeholder="Search employee...",
            service=EmployeeService(),
            importer=EmployeeImporter(),
            dialog_class=EmployeeDialog,
        )

        self.initialize_page()

    # ==========================================================
    # Data
    # ==========================================================

    def load_records(self, keyword):
        """
        Hỗ trợ nhiều tên API EmployeeService.
        """
        if hasattr(
            self.service,
            "search_employees",
        ):
            return self.service.search_employees(
                keyword
            )

        if hasattr(
            self.service,
            "search",
        ):
            return self.service.search(
                keyword
            )

        if hasattr(
            self.service,
            "get_all_employees",
        ):
            employees = (
                self.service.get_all_employees()
            )

        elif hasattr(
            self.service,
            "get_all",
        ):
            employees = self.service.get_all()

        else:
            raise AttributeError(
                "EmployeeService does not provide "
                "a supported query method."
            )

        keyword = str(
            keyword or ""
        ).strip().lower()

        if not keyword:
            return employees

        return [
            employee
            for employee in employees
            if (
                keyword
                in str(
                    employee.employee_code or ""
                ).lower()
                or keyword
                in str(
                    employee.employee_name or ""
                ).lower()
                or keyword
                in str(
                    employee.department or ""
                ).lower()
                or keyword
                in str(
                    getattr(
                        employee,
                        "position",
                        "",
                    )
                    or ""
                ).lower()
                or keyword
                in str(
                    getattr(
                        employee,
                        "shift",
                        "",
                    )
                    or ""
                ).lower()
                or keyword
                in str(
                    getattr(
                        employee,
                        "remark",
                        "",
                    )
                    or ""
                ).lower()
                or keyword
                in str(
                    employee.status or ""
                ).lower()
            )
        ]

    @staticmethod
    def record_to_row(employee):
        return [
            employee.employee_code or "",
            employee.employee_name or "",
            employee.department or "",
            getattr(
                employee,
                "position",
                "",
            )
            or "",
            getattr(
                employee,
                "shift",
                "",
            )
            or "",
            getattr(
                employee,
                "remark",
                "",
            )
            or "",
            employee.status or "",
        ]

    @staticmethod
    def get_record_key(employee):
        return employee.employee_code

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
            employee=record,
        )

    # ==========================================================
    # CRUD
    # ==========================================================

    def create_record(self, data):
        try:
            if hasattr(
                self.service,
                "create_employee",
            ):
                try:
                    result = self.service.create_employee(
                        data
                    )

                except TypeError:
                    result = self.service.create_employee(
                        employee_code=data.get(
                            "employee_code",
                            "",
                        ),
                        employee_name=data.get(
                            "employee_name",
                            "",
                        ),
                        department=data.get(
                            "department",
                        ),
                        position=data.get(
                            "position",
                        ),
                        shift=data.get(
                            "shift",
                        ),
                        remark=data.get(
                            "remark",
                        ),
                        status=data.get(
                            "status",
                            "ACTIVE",
                        ),
                    )

                self._commit_changes()
                return result

            if hasattr(
                self.service,
                "create",
            ):
                result = self.service.create(
                    data
                )
                self._commit_changes()
                return result

            raise AttributeError(
                "EmployeeService does not provide "
                "create_employee() or create()."
            )

        except Exception:
            self._rollback_changes()
            raise

    def update_record(
        self,
        record_key,
        data,
    ):
        try:
            if hasattr(
                self.service,
                "update_employee",
            ):
                result = self.service.update_employee(
                    record_key,
                    data,
                )
                self._commit_changes()
                return result

            if hasattr(
                self.service,
                "update",
            ):
                result = self.service.update(
                    record_key,
                    data,
                )
                self._commit_changes()
                return result

            raise AttributeError(
                "EmployeeService does not provide "
                "update_employee() or update()."
            )

        except Exception:
            self._rollback_changes()
            raise

    def delete_record(
        self,
        record_key,
    ):
        try:
            if hasattr(
                self.service,
                "delete_employee",
            ):
                result = self.service.delete_employee(
                    record_key
                )
                self._commit_changes()
                return result

            if hasattr(
                self.service,
                "delete",
            ):
                result = self.service.delete(
                    record_key
                )
                self._commit_changes()
                return result

            raise AttributeError(
                "EmployeeService does not provide "
                "delete_employee() or delete()."
            )

        except Exception:
            self._rollback_changes()
            raise

    def add_context_actions(self, menu):
        employee = self.get_selected_record()

        if employee is None:
            return {}

        status = str(
            employee.status or ""
        ).strip().upper()

        if status != "INACTIVE":
            return {}

        action_activate = menu.addAction(
            "Activate Employee"
        )

        return {
            action_activate: self.handle_activate
        }

    def handle_activate(self):
        employee = self.get_selected_record()

        if employee is None:
            return

        confirmed = self.confirm(
            "Activate Employee",
            (
                "Activate Employee:\n\n"
                f"{employee.employee_code}?"
            ),
        )

        if not confirmed:
            return

        try:
            activate_method = getattr(
                self.service,
                "activate_employee",
                None,
            )

            if not callable(activate_method):
                raise AttributeError(
                    (
                        "EmployeeService does not provide "
                        "activate_employee()."
                    )
                )

            activate_method(
                employee.employee_code
            )
            self._commit_changes()
            self.refresh_table()

            self.show_info(
                "Success",
                "Employee activated successfully.",
            )

        except Exception as error:
            self._rollback_changes()
            self.show_error(
                "Activate Employee Error",
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

        active = sum(
            1
            for employee in records
            if str(
                employee.status or ""
            ).strip().upper()
            == "ACTIVE"
        )

        inactive = total - active

        self.update_summary(
            total,
            active,
            inactive,
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

        if column_index in {
            0,
            2,
            3,
            4,
            6,
        }:
            item.setTextAlignment(
                Qt.AlignCenter
            )

        if column_index == 6:
            status = str(
                value or ""
            ).strip().upper()

            if status == "ACTIVE":
                item.setForeground(
                    Qt.darkGreen
                )

            elif status == "INACTIVE":
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

        employee_code = str(
            data.get(
                "employee_code",
                "",
            )
        ).strip().upper()

        employee_name = str(
            data.get(
                "employee_name",
                "",
            )
        ).strip()

        if not employee_code:
            raise ValueError(
                "Employee Code is required."
            )

        if not employee_name:
            raise ValueError(
                "Employee Name is required."
            )

        return True

    # ==========================================================
    # Export
    # ==========================================================

    @staticmethod
    def record_to_export_row(employee):
        return {
            "Employee Code":
                employee.employee_code or "",

            "Employee Name":
                employee.employee_name or "",

            "Department":
                employee.department or "",

            "Position":
                getattr(
                    employee,
                    "position",
                    "",
                )
                or "",

            "Shift":
                getattr(
                    employee,
                    "shift",
                    "",
                )
                or "",

            "Remark":
                getattr(
                    employee,
                    "remark",
                    "",
                )
                or "",

            "Status":
                employee.status or "",
        }
