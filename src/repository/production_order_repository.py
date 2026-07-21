from __future__ import annotations

from src.models.production_order import (
    ProductionOrder,
)
from src.repository.base_repository import (
    BaseRepository,
)


class ProductionOrderRepository(
    BaseRepository
):
    def __init__(
        self,
        session,
    ):
        super().__init__(
            session=session,
            model=ProductionOrder,
        )

    def get_by_work_order_operation(
        self,
        work_order_no,
        operation_no,
    ):
        number = str(
            work_order_no or ""
        ).strip().upper()

        try:
            operation = int(
                operation_no
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

        if not number:
            return None

        return (
            self.session
            .query(ProductionOrder)
            .filter(
                ProductionOrder.work_order_no
                == number,
                ProductionOrder.operation_no
                == operation,
            )
            .first()
        )

    def exists(
        self,
        work_order_no,
        operation_no,
    ) -> bool:
        return (
            self.get_by_work_order_operation(
                work_order_no,
                operation_no,
            )
            is not None
        )

    def get_by_work_order(
        self,
        work_order_no,
    ):
        number = str(
            work_order_no or ""
        ).strip().upper()

        if not number:
            return []

        return (
            self.session
            .query(ProductionOrder)
            .filter(
                ProductionOrder.work_order_no
                == number
            )
            .order_by(
                ProductionOrder.operation_no.asc()
            )
            .all()
        )

    def get_by_machine(
        self,
        machine_code,
    ):
        code = str(
            machine_code or ""
        ).strip().upper()

        if not code:
            return []

        return (
            self.session
            .query(ProductionOrder)
            .filter(
                ProductionOrder.machine_code
                == code
            )
            .order_by(
                ProductionOrder.planned_start.asc()
            )
            .all()
        )

    def get_by_employee(
        self,
        employee_code,
    ):
        code = str(
            employee_code or ""
        ).strip().upper()

        if not code:
            return []

        return (
            self.session
            .query(ProductionOrder)
            .filter(
                ProductionOrder.employee_code
                == code
            )
            .order_by(
                ProductionOrder.planned_start.asc()
            )
            .all()
        )

    def get_open_orders(self):
        return (
            self.session
            .query(ProductionOrder)
            .filter(
                ProductionOrder.status.in_(
                    [
                        "PLANNED",
                        "RELEASED",
                        "IN_PROGRESS",
                        "ON_HOLD",
                    ]
                )
            )
            .order_by(
                ProductionOrder.planned_start.asc(),
                ProductionOrder.work_order_no.asc(),
                ProductionOrder.operation_no.asc(),
            )
            .all()
        )

    def get_last_operation(
        self,
        work_order_no,
    ):
        number = str(
            work_order_no or ""
        ).strip().upper()

        if not number:
            return None

        return (
            self.session
            .query(ProductionOrder)
            .filter(
                ProductionOrder.work_order_no
                == number
            )
            .order_by(
                ProductionOrder.operation_no.desc()
            )
            .first()
        )