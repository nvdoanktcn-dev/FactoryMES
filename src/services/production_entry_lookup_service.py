from src.database.session import get_session
from src.framework.exception import (
    NotFoundError,
    ValidationError,
)
from src.repository.employee_repository import (
    EmployeeRepository,
)
from src.repository.machine_repository import (
    MachineRepository,
)
from src.repository.routing_repository import (
    RoutingRepository,
)
from src.repository.work_order_repository import (
    WorkOrderRepository,
)


class ProductionEntryLookupService:
    """
    Cung cấp dữ liệu tra cứu cho Production Entry UI.

    Không ghi hoặc cập nhật database.
    """

    WORK_ORDER_STATUSES = {
        "PLANNED",
        "RELEASED",
        "RUNNING",
        "PAUSED",
    }

    ACTIVE_STATUSES = {
        "ACTIVE",
        "RUNNING",
        "READY",
    }

    def __init__(self, session=None):
        self.session = session or get_session()

        self.work_order_repository = (
            WorkOrderRepository(self.session)
        )

        self.routing_repository = RoutingRepository(
            self.session
        )

        self.machine_repository = MachineRepository(
            self.session
        )

        self.employee_repository = EmployeeRepository(
            self.session
        )

    # ==========================================================
    # Work Order
    # ==========================================================

    def get_available_work_orders(self):
        work_orders = self.work_order_repository.get_all()

        result = [
            work_order
            for work_order in work_orders
            if self._normalize_code(
                getattr(
                    work_order,
                    "status",
                    "",
                )
            )
            in self.WORK_ORDER_STATUSES
        ]

        return sorted(
            result,
            key=lambda item:
                self._normalize_code(
                    item.work_order_no
                ),
        )

    def get_work_order(self, work_order_no):
        work_order_no = self._normalize_code(
            work_order_no
        )

        if not work_order_no:
            raise ValidationError(
                "Work Order No is required."
            )

        work_order = (
            self.work_order_repository.get_by_no(
                work_order_no
            )
        )

        if work_order is None:
            raise NotFoundError(
                f"Work Order not found: {work_order_no}"
            )

        return work_order

    # ==========================================================
    # Routing / OP
    # ==========================================================

    def get_work_order_routing(
        self,
        work_order_no,
    ):
        work_order = self.get_work_order(
            work_order_no
        )

        product_code = self._normalize_code(
            work_order.product_code
        )

        routings = (
            self.routing_repository.get_by_product(
                product_code
            )
        )

        active_routings = [
            routing
            for routing in routings
            if self._normalize_code(
                getattr(
                    routing,
                    "status",
                    "ACTIVE",
                )
            )
            == "ACTIVE"
        ]

        if not active_routings:
            raise NotFoundError(
                "No active Routing found for Product: "
                f"{product_code}"
            )

        return sorted(
            active_routings,
            key=lambda item: (
                int(item.sequence or 0),
                self._normalize_op(
                    item.op_no
                ),
            ),
        )

    def get_routing_operation(
        self,
        work_order_no,
        op_no,
    ):
        op_no = self._normalize_op(op_no)

        routings = self.get_work_order_routing(
            work_order_no
        )

        for routing in routings:
            if (
                self._normalize_op(routing.op_no)
                == op_no
            ):
                return routing

        raise NotFoundError(
            f"Routing OP not found: {op_no}"
        )

    # ==========================================================
    # Machine
    # ==========================================================

    def get_machines_for_operation(
        self,
        work_order_no,
        op_no,
    ):
        routing = self.get_routing_operation(
            work_order_no,
            op_no,
        )

        required_machine_code = (
            self._normalize_code(
                getattr(
                    routing,
                    "machine_code",
                    "",
                )
            )
        )

        required_machine_type = (
            self._normalize_code(
                getattr(
                    routing,
                    "machine_type",
                    "",
                )
            )
        )

        machines = self.machine_repository.get_all()

        result = []

        for machine in machines:
            machine_status = self._normalize_code(
                getattr(
                    machine,
                    "status",
                    "",
                )
            )

            if machine_status not in self.ACTIVE_STATUSES:
                continue

            machine_code = self._normalize_code(
                getattr(
                    machine,
                    "machine_code",
                    "",
                )
            )

            machine_type = self._normalize_code(
                getattr(
                    machine,
                    "machine_type",
                    "",
                )
            )

            # Routing chỉ định đúng một máy cụ thể.
            if required_machine_code:
                if machine_code == required_machine_code:
                    result.append(machine)

                continue

            # Nếu không chỉ định mã máy, dùng Machine Type.
            if (
                required_machine_type
                and machine_type
                == required_machine_type
            ):
                result.append(machine)

        return sorted(
            result,
            key=lambda item:
                self._normalize_code(
                    item.machine_code
                ),
        )

    # ==========================================================
    # Employee
    # ==========================================================

    def get_active_employees(self):
        employees = self.employee_repository.get_all()

        result = [
            employee
            for employee in employees
            if self._normalize_code(
                getattr(
                    employee,
                    "status",
                    "",
                )
            )
            == "ACTIVE"
        ]

        return sorted(
            result,
            key=lambda item:
                self._normalize_code(
                    item.employee_code
                ),
        )

    # ==========================================================
    # Complete UI context
    # ==========================================================

    def build_entry_context(
        self,
        work_order_no,
        op_no=None,
    ):
        work_order = self.get_work_order(
            work_order_no
        )

        routings = self.get_work_order_routing(
            work_order_no
        )

        selected_routing = None
        machines = []

        if op_no:
            selected_routing = (
                self.get_routing_operation(
                    work_order_no,
                    op_no,
                )
            )

            machines = (
                self.get_machines_for_operation(
                    work_order_no,
                    op_no,
                )
            )

        return {
            "work_order": work_order,
            "product_code": self._normalize_code(
                work_order.product_code
            ),
            "routings": routings,
            "selected_routing": selected_routing,
            "machines": machines,
            "employees": self.get_active_employees(),
        }

    # ==========================================================
    # Helpers
    # ==========================================================

    @staticmethod
    def _normalize_code(value):
        return str(
            value or ""
        ).strip().upper()

    @classmethod
    def _normalize_op(cls, value):
        text = cls._normalize_code(value)

        if not text:
            return ""

        digits = "".join(
            character
            for character in text
            if character.isdigit()
        )

        if digits:
            return f"OP{int(digits)}"

        return text