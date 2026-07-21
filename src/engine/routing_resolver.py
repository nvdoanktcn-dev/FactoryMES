from collections import defaultdict

from src.database.session import get_session
from src.framework.exception import NotFoundError, ValidationError
from src.repository.routing_snapshot_repository import (
    RoutingSnapshotRepository,
)
from src.repository.production_log_repository import (
    ProductionLogRepository,
)
from src.repository.work_order_repository import (
    WorkOrderRepository,
)


class RoutingResolver:
    """
    Xác định sản lượng hoàn thành thực tế của Work Order.

    Quy tắc:
    - Một sản phẩm có nhiều OP.
    - OP cuối là OP có sequence lớn nhất trong Routing Snapshot.
    - Sản lượng hoàn thành chỉ lấy từ OP cuối.
    - Không cộng sản lượng của các OP trước.
    """

    def __init__(self):
        self.session = get_session()

        self.work_order_repository = WorkOrderRepository(
            self.session
        )

        self.routing_snapshot_repository = (
            RoutingSnapshotRepository(self.session)
        )

        self.production_log_repository = (
            ProductionLogRepository(self.session)
        )

    def get_last_operation(self, work_order_no):
        """
        Trả về RoutingSnapshot của OP cuối.
        """
        work_order_no = self._normalize_work_order_no(
            work_order_no
        )

        work_order = self.work_order_repository.get_by_no(
            work_order_no
        )

        if work_order is None:
            raise NotFoundError(
                f"Work Order not found: {work_order_no}"
            )

        snapshots = (
            self.routing_snapshot_repository.get_by_work_order(
                work_order_no
            )
        )

        active_snapshots = [
            snapshot
            for snapshot in snapshots
            if (snapshot.status or "").upper()
            not in {"INACTIVE", "CANCELLED"}
        ]

        if not active_snapshots:
            raise ValidationError(
                f"No Routing Snapshot found for "
                f"Work Order: {work_order_no}"
            )

        return max(
            active_snapshots,
            key=lambda item: item.sequence or 0,
        )

    def get_last_op_no(self, work_order_no):
        last_operation = self.get_last_operation(
            work_order_no
        )

        return last_operation.op_no

    def calculate_completed_quantity(self, work_order_no):
        """
        Tổng OK của riêng OP cuối.

        Ví dụ:
            OP10 = 100
            OP20 = 99
            OP30 = 97

        Kết quả:
            completed_qty = 97
        """
        work_order_no = self._normalize_work_order_no(
            work_order_no
        )

        last_operation = self.get_last_operation(
            work_order_no
        )

        production_logs = (
            self.production_log_repository.get_by_work_order(
                work_order_no
            )
        )

        last_op_logs = [
            log
            for log in production_logs
            if self._normalize_op(log.op_no)
            == self._normalize_op(last_operation.op_no)
        ]

        completed_qty = sum(
            int(log.ok_qty or 0)
            for log in last_op_logs
        )

        ng_qty = sum(
            int(log.ng_qty or 0)
            for log in last_op_logs
        )

        return {
            "work_order_no": work_order_no,
            "last_op_no": last_operation.op_no,
            "last_sequence": last_operation.sequence,
            "completed_qty": completed_qty,
            "ng_qty": ng_qty,
            "log_count": len(last_op_logs),
        }

    def calculate_by_batch(
        self,
        work_order_no,
        batch_no,
    ):
        """
        Tính sản lượng OP cuối trong một Batch cụ thể.
        """
        work_order_no = self._normalize_work_order_no(
            work_order_no
        )

        batch_no = str(batch_no or "").strip().upper()

        if not batch_no:
            raise ValidationError(
                "Batch No is required."
            )

        last_operation = self.get_last_operation(
            work_order_no
        )

        production_logs = (
            self.production_log_repository.get_by_work_order(
                work_order_no
            )
        )

        matched_logs = [
            log
            for log in production_logs
            if (
                (log.batch_no or "").upper() == batch_no
                and self._normalize_op(log.op_no)
                == self._normalize_op(
                    last_operation.op_no
                )
            )
        ]

        return {
            "batch_no": batch_no,
            "work_order_no": work_order_no,
            "last_op_no": last_operation.op_no,
            "completed_qty": sum(
                int(log.ok_qty or 0)
                for log in matched_logs
            ),
            "ng_qty": sum(
                int(log.ng_qty or 0)
                for log in matched_logs
            ),
            "log_count": len(matched_logs),
        }

    def get_operation_summary(self, work_order_no):
        """
        Tổng hợp OK/NG của từng OP để kiểm tra tiến độ.
        """
        work_order_no = self._normalize_work_order_no(
            work_order_no
        )

        production_logs = (
            self.production_log_repository.get_by_work_order(
                work_order_no
            )
        )

        summary = defaultdict(
            lambda: {
                "ok_qty": 0,
                "ng_qty": 0,
                "run_time_sec": 0.0,
                "log_count": 0,
            }
        )

        for log in production_logs:
            op_no = self._normalize_op(log.op_no)

            summary[op_no]["ok_qty"] += int(
                log.ok_qty or 0
            )

            summary[op_no]["ng_qty"] += int(
                log.ng_qty or 0
            )

            summary[op_no]["run_time_sec"] += float(
                log.run_time_sec or 0
            )

            summary[op_no]["log_count"] += 1

        return dict(summary)

    @staticmethod
    def _normalize_work_order_no(value):
        value = str(value or "").strip().upper()

        if not value:
            raise ValidationError(
                "Work Order No is required."
            )

        return value

    @staticmethod
    def _normalize_op(value):
        text = str(value or "").strip().upper()

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