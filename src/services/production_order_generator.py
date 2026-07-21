from __future__ import annotations

from datetime import datetime, time, timedelta

from src.database.session import get_session
from src.services.production_order_service import (
    ProductionOrderService,
)
from src.services.routing_service import RoutingService
from src.services.work_order_service import (
    WorkOrderService,
)


class ProductionOrderGenerator:
    """
    Sinh Production Order từ Work Order và Routing.
    """

    def __init__(
        self,
        session=None,
    ):
        self._owns_session = session is None
        self.session = session or get_session()

        self.work_order_service = WorkOrderService(
            session=self.session
        )
        self.routing_service = RoutingService(
            session=self.session
        )
        self.production_order_service = (
            ProductionOrderService(
                session=self.session
            )
        )

    def generate(
        self,
        work_order_no,
        *,
        replace_existing=False,
        auto_commit=True,
    ):
        work_order = (
            self.work_order_service
            .get_work_order(
                work_order_no
            )
        )

        if work_order is None:
            raise ValueError(
                (
                    "Work Order does not exist: "
                    f"{work_order_no}"
                )
            )

        if str(
            work_order.status or ""
        ).strip().upper() == "CANCELLED":
            raise ValueError(
                (
                    "Cannot generate Production Orders "
                    "for a CANCELLED Work Order."
                )
            )

        routings = (
            self.routing_service
            .get_product_routing(
                work_order.product_code
            )
        )

        routings = [
            routing
            for routing in routings
            if str(
                routing.status or ""
            ).strip().upper() == "ACTIVE"
        ]

        routings.sort(
            key=lambda routing: int(
                routing.operation_no
            )
        )

        if not routings:
            raise ValueError(
                (
                    "No ACTIVE Routing found for Product: "
                    f"{work_order.product_code}"
                )
            )

        existing_orders = (
            self.production_order_service
            .get_by_work_order(
                work_order.work_order_no
            )
        )

        existing_by_operation = {
            int(order.operation_no): order
            for order in existing_orders
        }

        if replace_existing:
            self._delete_replaceable_orders(
                existing_orders
            )
            existing_by_operation = {}

        created = []
        skipped = []

        planned_start = datetime.combine(
            work_order.start_date,
            time(hour=8),
        )

        last_operation_no = max(
            int(routing.operation_no)
            for routing in routings
        )

        try:
            for routing in routings:
                operation_no = int(
                    routing.operation_no
                )

                if operation_no in existing_by_operation:
                    skipped.append(
                        existing_by_operation[
                            operation_no
                        ]
                    )
                    continue

                required_hours = (
                    self._calculate_required_hours(
                        plan_qty=work_order.plan_qty,
                        cycle_time_sec=(
                            routing
                            .standard_cycle_time_sec
                        ),
                    )
                )

                planned_finish = (
                    planned_start
                    + timedelta(
                        hours=required_hours
                    )
                )

                remark_parts = []

                if operation_no == last_operation_no:
                    remark_parts.append(
                        "FINAL_OPERATION"
                    )

                if routing.remark:
                    remark_parts.append(
                        str(routing.remark)
                    )

                production_order = (
                    self.production_order_service
                    .create_production_order(
                        {
                            "work_order_no": (
                                work_order
                                .work_order_no
                            ),
                            "product_code": (
                                work_order
                                .product_code
                            ),
                            "operation_no": (
                                operation_no
                            ),
                            "operation_name": (
                                routing
                                .operation_name
                            ),
                            "process_type": (
                                routing
                                .process_type
                            ),
                            "machine_type": (
                                routing
                                .machine_type
                            ),
                            "machine_code": None,
                            "employee_code": None,
                            "shift": None,
                            "plan_qty": (
                                work_order
                                .plan_qty
                            ),
                            "completed_qty": 0,
                            "ng_qty": 0,
                            "status": "PLANNED",
                            "planned_start": (
                                planned_start
                            ),
                            "planned_finish": (
                                planned_finish
                            ),
                            "actual_start": None,
                            "actual_finish": None,
                            "remark": (
                                " | ".join(
                                    remark_parts
                                )
                                or None
                            ),
                        }
                    )
                )

                created.append(
                    production_order
                )

                planned_start = planned_finish

            if auto_commit:
                self.session.commit()

            return {
                "success": True,
                "work_order_no": (
                    work_order.work_order_no
                ),
                "product_code": (
                    work_order.product_code
                ),
                "routing_count": len(routings),
                "created_count": len(created),
                "skipped_count": len(skipped),
                "created": created,
                "skipped": skipped,
                "last_operation_no": (
                    last_operation_no
                ),
            }

        except Exception:
            self.session.rollback()
            raise

    def regenerate(
        self,
        work_order_no,
        *,
        auto_commit=True,
    ):
        return self.generate(
            work_order_no,
            replace_existing=True,
            auto_commit=auto_commit,
        )

    def _delete_replaceable_orders(
        self,
        production_orders,
    ):
        protected_statuses = {
            "IN_PROGRESS",
            "COMPLETED",
        }

        for production_order in production_orders:
            status = str(
                production_order.status or ""
            ).strip().upper()

            if status in protected_statuses:
                raise ValueError(
                    (
                        "Cannot regenerate because "
                        "Production Order has status "
                        f"{status}: "
                        f"{production_order.work_order_no} / "
                        f"OP{production_order.operation_no}"
                    )
                )

        for production_order in production_orders:
            self.session.delete(
                production_order
            )

        self.session.flush()

    @staticmethod
    def _calculate_required_hours(
        *,
        plan_qty,
        cycle_time_sec,
    ):
        try:
            quantity = int(
                plan_qty
            )
            cycle_time = float(
                cycle_time_sec
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                (
                    "Invalid quantity or cycle time "
                    "for Production Order generation."
                )
            ) from error

        if quantity <= 0:
            raise ValueError(
                "Plan Qty must be greater than zero."
            )

        if cycle_time <= 0:
            raise ValueError(
                (
                    "Routing Cycle Time must be "
                    "greater than zero."
                )
            )

        return (
            quantity * cycle_time
        ) / 3600.0

    def close(self):
        if self._owns_session:
            self.session.close()