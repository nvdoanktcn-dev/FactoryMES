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
        if hasattr(
            self.service,
            "create_employee",
        ):
            try:
                return self.service.create_employee(
                    data
                )

            except TypeError:
                return self.service.create_employee(
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
                    status=data.get(
                        "status",
                        "ACTIVE",
                    ),
                )

        if hasattr(
            self.service,
            "create",
        ):
            return self.service.create(
                data
            )

        raise AttributeError(
            "EmployeeService does not provide "
            "create_employee() or create()."
        )

    def update_record(
        self,
        record_key,
        data,
    ):
        if hasattr(
            self.service,
            "update_employee",
        ):
            return self.service.update_employee(
                record_key,
                data,
            )

        if hasattr(
            self.service,
            "update",
        ):
            return self.service.update(
                record_key,
                data,
            )

        raise AttributeError(
            "EmployeeService does not provide "
            "update_employee() or update()."
        )

    def delete_record(
        self,
        record_key,
    ):
        if hasattr(
            self.service,
            "delete_employee",
        ):
            return self.service.delete_employee(
                record_key
            )

        if hasattr(
            self.service,
            "delete",
        ):
            return self.service.delete(
                record_key
            )

        raise AttributeError(
            "EmployeeService does not provide "
            "delete_employee() or delete()."
        )

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
        }:
            item.setTextAlignment(
                Qt.AlignCenter
            )

        if column_index == 4:
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

            "Status":
                employee.status or "",
        }