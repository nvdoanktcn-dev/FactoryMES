from src.engine.work_order_progress_result import (
    WorkOrderProgressResult,
)


class WorkOrderProgressEngine:
    """
    Tính tiến độ Work Order từ kết quả OP cuối.

    Engine thuần:
    - Không truy cập database
    - Không tự cập nhật Work Order
    """

    ACTIVE_STATUSES = {
        "RELEASED",
        "RUNNING",
        "PAUSED",
    }

    FINAL_STATUSES = {
        "COMPLETED",
        "CLOSED",
    }

    def calculate(
        self,
        work_order,
        last_operation_result,
    ):
        if work_order is None:
            raise ValueError(
                "Work Order is required."
            )

        if last_operation_result is None:
            raise ValueError(
                "Last Operation Result is required."
            )

        work_order_no = self._normalize_text(
            getattr(
                work_order,
                "work_order_no",
                "",
            )
        ).upper()

        if not work_order_no:
            raise ValueError(
                "Work Order No is required."
            )

        result_work_order_no = self._normalize_text(
            getattr(
                last_operation_result,
                "work_order_no",
                "",
            )
        ).upper()

        if result_work_order_no != work_order_no:
            raise ValueError(
                "Work Order does not match "
                "Last Operation Result."
            )

        plan_qty = self._to_non_negative_int(
            getattr(
                work_order,
                "plan_qty",
                0,
            )
        )

        if plan_qty <= 0:
            raise ValueError(
                "Plan Qty must be greater than zero."
            )

        completed_qty = self._to_non_negative_int(
            getattr(
                last_operation_result,
                "completed_qty",
                0,
            )
        )

        ng_qty = self._to_non_negative_int(
            getattr(
                last_operation_result,
                "ng_qty",
                0,
            )
        )

        remaining_qty = max(
            plan_qty - completed_qty,
            0,
        )

        progress_percent = min(
            completed_qty / plan_qty * 100,
            100.0,
        )

        current_status = self._normalize_text(
            getattr(
                work_order,
                "status",
                "PLANNED",
            )
        ).upper() or "PLANNED"

        suggested_status = self._suggest_status(
            current_status=current_status,
            completed_qty=completed_qty,
            plan_qty=plan_qty,
        )

        return WorkOrderProgressResult(
            work_order_no=work_order_no,
            plan_qty=plan_qty,
            completed_qty=completed_qty,
            ng_qty=ng_qty,
            remaining_qty=remaining_qty,
            progress_percent=progress_percent,
            current_status=current_status,
            suggested_status=suggested_status,
            is_complete=completed_qty >= plan_qty,
        )

    def _suggest_status(
        self,
        current_status,
        completed_qty,
        plan_qty,
    ):
        if current_status == "CLOSED":
            return "CLOSED"

        if completed_qty >= plan_qty:
            return "COMPLETED"

        if completed_qty > 0:
            if current_status in {
                "PLANNED",
                "RELEASED",
                "PAUSED",
            }:
                return "RUNNING"

        return current_status

    @staticmethod
    def _normalize_text(value):
        if value is None:
            return ""

        text = str(value).strip()

        if text.lower() in {
            "nan",
            "none",
            "nat",
        }:
            return ""

        return " ".join(text.split())

    @staticmethod
    def _to_non_negative_int(value):
        try:
            number = int(
                float(value or 0)
            )

        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                f"Invalid integer value: {value}"
            ) from error

        if number < 0:
            raise ValueError(
                f"Value cannot be negative: {value}"
            )

        return number