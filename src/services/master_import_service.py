from pathlib import Path


class MasterImportService:
    """
    Trung tâm điều phối toàn bộ Master Import.

    UI chỉ gọi service này.
    UI không gọi trực tiếp từng Importer.

    Các Importer sẽ được bổ sung lần lượt:
    - ProductImporter
    - MachineImporter
    - EmployeeImporter
    - RoutingImporter
    - WorkOrderImporter
    """

    def __init__(self):
        self._product_importer = None
        self._machine_importer = None
        self._employee_importer = None
        self._routing_importer = None
        self._work_order_importer = None

    # ==========================================================
    # Product
    # ==========================================================

    def preview_product(self, filename):
        importer = self._get_product_importer()
        self._validate_file(filename)

        return importer.preview(filename)

    def import_product(self, filename):
        importer = self._get_product_importer()
        self._validate_file(filename)

        return importer.import_file(filename)

    # ==========================================================
    # Machine
    # ==========================================================

    def preview_machine(self, filename):
        importer = self._get_machine_importer()
        self._validate_file(filename)

        return importer.preview(filename)

    def import_machine(self, filename):
        importer = self._get_machine_importer()
        self._validate_file(filename)

        return importer.import_file(filename)

    # ==========================================================
    # Employee
    # ==========================================================

    def preview_employee(self, filename):
        importer = self._get_employee_importer()
        self._validate_file(filename)

        return importer.preview(filename)

    def import_employee(self, filename):
        importer = self._get_employee_importer()
        self._validate_file(filename)

        return importer.import_file(filename)

    # ==========================================================
    # Routing
    # ==========================================================

    def preview_routing(self, filename):
        importer = self._get_routing_importer()
        self._validate_file(filename)

        return importer.preview(filename)

    def import_routing(self, filename):
        importer = self._get_routing_importer()
        self._validate_file(filename)

        return importer.import_file(filename)

    # ==========================================================
    # Work Order
    # ==========================================================

    def preview_work_order(self, filename):
        importer = self._get_work_order_importer()
        self._validate_file(filename)

        return importer.preview(filename)

    def import_work_order(self, filename):
        importer = self._get_work_order_importer()
        self._validate_file(filename)

        return importer.import_file(filename)

    # ==========================================================
    # Importer factories
    # ==========================================================

    def _get_product_importer(self):
        if self._product_importer is None:
            from src.importer.product_importer import ProductImporter

            self._product_importer = ProductImporter()

        return self._product_importer

    def _get_machine_importer(self):
        if self._machine_importer is None:
            from src.importer.machine_importer import MachineImporter

            self._machine_importer = MachineImporter()

        return self._machine_importer

    def _get_employee_importer(self):
        if self._employee_importer is None:
            from src.importer.employee_importer import EmployeeImporter

            self._employee_importer = EmployeeImporter()

        return self._employee_importer

    def _get_routing_importer(self):
        if self._routing_importer is None:
            from src.importer.routing_importer import RoutingImporter

            self._routing_importer = RoutingImporter()

        return self._routing_importer

    def _get_work_order_importer(self):
        if self._work_order_importer is None:
            from src.importer.work_order_importer import WorkOrderImporter

            self._work_order_importer = WorkOrderImporter()

        return self._work_order_importer

    # ==========================================================
    # Helpers
    # ==========================================================

    @staticmethod
    def _validate_file(filename):
        if not filename:
            raise ValueError("File path is required.")

        path = Path(filename)

        if not path.exists():
            raise FileNotFoundError(
                f"File not found:\n{filename}"
            )

        if not path.is_file():
            raise ValueError(
                f"Path is not a file:\n{filename}"
            )

        return path