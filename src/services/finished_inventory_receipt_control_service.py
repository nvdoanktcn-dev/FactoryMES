from __future__ import annotations

from src.framework.exception import ValidationError
from src.repository.finished_inventory_repository import (
    FinishedInventoryRepository,
)
from src.repository.production_log_repository import (
    ProductionLogRepository,
)
from src.repository.production_order_repository import (
    ProductionOrderRepository,
)
from src.repository.work_order_repository import WorkOrderRepository


class FinishedInventoryReceiptControlService:
    """Control finished-goods receipts against final-operation output."""

    def __init__(
        self,
        session=None,
        *,
        work_order_repository=None,
        production_order_repository=None,
        production_log_repository=None,
        finished_inventory_repository=None,
    ) -> None:
        self.work_order_repository = (
            work_order_repository or WorkOrderRepository(session)
        )
        self.production_order_repository = (
            production_order_repository
            or ProductionOrderRepository(session)
        )
        self.production_log_repository = (
            production_log_repository
            or ProductionLogRepository(session)
        )
        self.finished_inventory_repository = (
            finished_inventory_repository
            or FinishedInventoryRepository(session)
        )

    def get_capacity(
        self,
        work_order,
        product_code,
        *,
        exclude_inventory_id=None,
    ) -> dict:
        work_order_no = self._code(work_order)
        product = self._code(product_code)
        order = self.work_order_repository.get_by_no(work_order_no)
        if order is None:
            raise ValidationError(
                f"Work Order does not exist: {work_order_no}"
            )

        expected_product = self._code(
            getattr(order, "product_code", "")
        )
        if expected_product != product:
            raise ValidationError(
                f"Work Order {work_order_no} belongs to Product "
                f"{expected_product}, not {product}."
            )

        production_orders = list(
            self.production_order_repository.get_by_work_order(
                work_order_no
            )
            or []
        )
        logs = [
            record
            for record in (
                self.production_log_repository.get_by_work_order(
                    work_order_no
                )
                or []
            )
            if self._code(
                getattr(record, "product_code", "")
            )
            == product
            and self._code(getattr(record, "status", ""))
            != "CANCELLED"
        ]

        final_operation = self._final_operation(
            production_orders,
            logs,
            product,
        )
        completed_qty = sum(
            self._integer(getattr(record, "ok_qty", 0))
            for record in logs
            if self._operation(
                getattr(record, "op_no", 0)
            )
            == final_operation
        )

        excluded_id = self._optional_integer(
            exclude_inventory_id
        )
        received_qty = sum(
            self._integer(getattr(record, "qty", 0))
            for record in (
                self.finished_inventory_repository.get_all()
                or []
            )
            if self._code(
                getattr(record, "work_order", "")
            )
            == work_order_no
            and self._code(
                getattr(record, "product_code", "")
            )
            == product
            and (
                excluded_id is None
                or self._optional_integer(
                    getattr(record, "inventory_id", None)
                )
                != excluded_id
            )
        )
        available_qty = max(
            completed_qty - received_qty,
            0,
        )
        return {
            "work_order": work_order_no,
            "product_code": product,
            "final_operation": final_operation,
            "final_op_qty": completed_qty,
            "received_qty": received_qty,
            "available_qty": available_qty,
        }

    def validate_receipt(
        self,
        data,
        *,
        exclude_inventory_id=None,
        reserved_qty=0,
    ) -> dict:
        values = dict(data or {})
        qty = self._integer(values.get("qty"))
        if qty <= 0:
            raise ValidationError(
                "Qty must be greater than zero."
            )
        capacity = self.get_capacity(
            values.get("work_order"),
            values.get("product_code"),
            exclude_inventory_id=exclude_inventory_id,
        )
        available = max(
            capacity["available_qty"]
            - self._integer(reserved_qty),
            0,
        )
        if qty > available:
            raise ValidationError(
                "Receipt Qty exceeds Final OP availability: "
                f"requested {qty}, available {available}, "
                f"Final OP {capacity['final_op_qty']}, "
                f"already received {capacity['received_qty']}."
            )
        return {
            **capacity,
            "requested_qty": qty,
            "reserved_qty": self._integer(reserved_qty),
            "remaining_qty": available - qty,
        }

    def get_pending_receipts(self) -> list[dict]:
        rows = []
        seen = set()
        for order in (
            self.work_order_repository.get_all()
            or []
        ):
            key = (
                self._code(
                    getattr(order, "work_order_no", "")
                ),
                self._code(
                    getattr(order, "product_code", "")
                ),
            )
            if not all(key) or key in seen:
                continue
            seen.add(key)
            capacity = self.get_capacity(*key)
            if capacity["available_qty"] > 0:
                rows.append(capacity)
        return sorted(
            rows,
            key=lambda item: (
                item["work_order"],
                item["product_code"],
            ),
        )

    @classmethod
    def _final_operation(
        cls,
        production_orders,
        logs,
        product_code,
    ) -> int:
        operations = [
            cls._operation(
                getattr(order, "operation_no", 0)
            )
            for order in production_orders
            if cls._code(
                getattr(order, "product_code", "")
            )
            == product_code
            and cls._code(getattr(order, "status", ""))
            != "CANCELLED"
        ]
        if not operations:
            operations = [
                cls._operation(
                    getattr(record, "op_no", 0)
                )
                for record in logs
            ]
        return max(operations, default=0)

    @staticmethod
    def _code(value) -> str:
        return str(value or "").strip().upper()

    @staticmethod
    def _operation(value) -> int:
        try:
            return int(float(value or 0))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _integer(value) -> int:
        try:
            return max(int(float(value or 0)), 0)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _optional_integer(value):
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
