from __future__ import annotations

from src.models.work_order import WorkOrder
from src.repository.base_repository import (
    BaseRepository,
)


class WorkOrderRepository(BaseRepository):
    def __init__(
        self,
        session,
    ):
        super().__init__(
            session=session,
            model=WorkOrder,
        )

    def get_by_no(
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
            .query(WorkOrder)
            .filter(
                WorkOrder.work_order_no == number
            )
            .first()
        )

    def exists(
        self,
        work_order_no,
    ) -> bool:
        return (
            self.get_by_no(
                work_order_no
            )
            is not None
        )

    def get_by_product(
        self,
        product_code,
    ):
        code = str(
            product_code or ""
        ).strip().upper()

        if not code:
            return []

        return (
            self.session
            .query(WorkOrder)
            .filter(
                WorkOrder.product_code == code
            )
            .order_by(
                WorkOrder.start_date.desc(),
                WorkOrder.work_order_no.asc(),
            )
            .all()
        )

    def get_by_status(
        self,
        status,
    ):
        normalized = str(
            status or ""
        ).strip().upper()

        if not normalized:
            return []

        return (
            self.session
            .query(WorkOrder)
            .filter(
                WorkOrder.status == normalized
            )
            .order_by(
                WorkOrder.start_date.asc(),
                WorkOrder.priority.desc(),
            )
            .all()
        )

    def get_open_orders(
        self,
    ):
        return (
            self.session
            .query(WorkOrder)
            .filter(
                WorkOrder.status.in_(
                    [
                        "PLANNED",
                        "RELEASED",
                        "IN_PROGRESS",
                        "ON_HOLD",
                    ]
                )
            )
            .order_by(
                WorkOrder.due_date.asc(),
                WorkOrder.priority.desc(),
            )
            .all()
        )