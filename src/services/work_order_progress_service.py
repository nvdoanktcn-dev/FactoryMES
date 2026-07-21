from datetime import date, datetime

from src.database.session import get_session
from src.engine.last_operation_resolver import LastOperationResolver
from src.engine.production_snapshot import ProductionSnapshot
from src.engine.work_order_progress_engine import WorkOrderProgressEngine
from src.framework.exception import NotFoundError, ValidationError
from src.repository.production_log_repository import (
    ProductionLogRepository,
)
from src.repository.routing_repository import RoutingRepository
from src.repository.work_order_repository import WorkOrderRepository


class WorkOrderProgressService:
    """
    Điều phối việc tính và cập nhật tiến độ Work Order.

    Database
        -> Work Order
        -> Routing
        -> Production Log
        -> ProductionSnapshot
        -> LastOperationResolver
        -> WorkOrderProgressEngine
        -> cập nhật Work Order
    """

    ACTIVE_STATUSES = {
        "RELEASED",
        "RUNNING",
        "PAUSED",
    }

    def __init__(self, session=None):
        self.session = session or get_session()

        self.work_order_repository = WorkOrderRepository(
            self.session
        )
        self.routing_repository = RoutingRepository(
            self.session
        )
        self.production_log_repository = (
            ProductionLogRepository(self.session)
        )

        self.last_operation_resolver = (
            LastOperationResolver()
        )
        self.progress_engine = WorkOrderProgressEngine()

    # ==========================================================
    # Public API
    # ==========================================================

    def calculate_progress(self, work_order_no):
        """
        Tính tiến độ nhưng không cập nhật database.
        """
        work_order_no = self._normalize_code(
            work_order_no
        )

        work_order = self.work_order_repository.get_by_no(
            work_order_no
        )

        if work_order is None:
            raise NotFoundError(
                f"Work Order not found: {work_order_no}"
            )

        last_routing = self._get_last_routing(
            work_order.product_code
        )

        logs = self.production_log_repository.get_by_work_order(
            work_order_no
        )

        snapshots = [
            self._create_snapshot(log)
            for log in logs
        ]

        last_operation_result = (
            self.last_operation_resolver.resolve(
                work_order_no=work_order_no,
                last_operation=last_routing,
                snapshots=snapshots,
            )
        )

        progress_result = self.progress_engine.calculate(
            work_order=work_order,
            last_operation_result=last_operation_result,
        )

        return {
            "work_order": work_order,
            "last_routing": last_routing,
            "snapshots": snapshots,
            "last_operation_result": last_operation_result,
            "progress_result": progress_result,
        }

    def update_progress(self, work_order_no):
        """
        Tính lại completed_qty, ng_qty và status,
        sau đó cập nhật database.
        """
        calculation = self.calculate_progress(
            work_order_no
        )

        work_order = calculation["work_order"]
        progress = calculation["progress_result"]

        work_order.completed_qty = progress.completed_qty
        work_order.ng_qty = progress.ng_qty

        if (
            progress.suggested_status
            != progress.current_status
        ):
            work_order.status = (
                progress.suggested_status
            )

        self.repository_update()

        return progress

    def update_all_active(self):
        """
        Cập nhật tất cả Work Order đang hoạt động.

        Một Work Order lỗi không làm dừng toàn bộ danh sách.
        """
        work_orders = self.work_order_repository.get_all()

        results = []
        errors = []

        for work_order in work_orders:
            status = str(
                work_order.status or ""
            ).strip().upper()

            if status not in self.ACTIVE_STATUSES:
                continue

            try:
                progress = self.update_progress(
                    work_order.work_order_no
                )

                results.append(progress)

            except Exception as error:
                self.session.rollback()

                errors.append({
                    "work_order_no":
                        work_order.work_order_no,
                    "message": str(error),
                })

        return {
            "updated": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors,
        }

    def build_dashboard_summary(self):
        """
        Tổng hợp tiến độ Work Order cho Dashboard.
        Không cập nhật database.
        """
        work_orders = self.work_order_repository.get_all()

        items = []
        errors = []

        for work_order in work_orders:
            try:
                calculation = self.calculate_progress(
                    work_order.work_order_no
                )

                progress = calculation[
                    "progress_result"
                ]
                last_result = calculation[
                    "last_operation_result"
                ]

                items.append({
                    "work_order_no":
                        progress.work_order_no,
                    "product_code":
                        last_result.product_code,
                    "last_op":
                        last_result.last_op,
                    "plan_qty":
                        progress.plan_qty,
                    "completed_qty":
                        progress.completed_qty,
                    "ng_qty":
                        progress.ng_qty,
                    "remaining_qty":
                        progress.remaining_qty,
                    "progress_percent":
                        progress.progress_percent,
                    "status":
                        progress.suggested_status,
                })

            except Exception as error:
                errors.append({
                    "work_order_no":
                        work_order.work_order_no,
                    "message": str(error),
                })

        return {
            "items": items,
            "errors": errors,
        }

    # ==========================================================
    # Routing
    # ==========================================================

    def _get_last_routing(self, product_code):
        product_code = self._normalize_code(
            product_code
        )

        routings = self.routing_repository.get_by_product(
            product_code
        )

        active_routings = [
            routing
            for routing in routings
            if str(
                routing.status or "ACTIVE"
            ).strip().upper()
            not in {
                "INACTIVE",
                "CANCELLED",
            }
        ]

        if not active_routings:
            raise ValidationError(
                f"No active Routing found for "
                f"Product: {product_code}"
            )

        return max(
            active_routings,
            key=lambda routing:
                int(routing.sequence or 0),
        )

    # ==========================================================
    # Production Snapshot adapter
    # ==========================================================

    def _create_snapshot(self, log):
        """
        Chuyển ProductionLog thật thành ProductionSnapshot.

        Hỗ trợ các tên trường đang tồn tại trong project:
        - employee_code / operator_code
        - finish_time / end_time
        - run_time_sec
        """
        start_time = getattr(
            log,
            "start_time",
            None,
        )

        finish_time = (
            getattr(log, "finish_time", None)
            or getattr(log, "end_time", None)
        )

        runtime_sec = self._resolve_runtime(
            log=log,
            start_time=start_time,
            finish_time=finish_time,
        )

        production_date = self._resolve_date(
            log=log,
            start_time=start_time,
        )

        operator_code = (
            getattr(log, "employee_code", None)
            or getattr(log, "operator_code", None)
            or ""
        )

        return ProductionSnapshot(
            work_order_no=self._normalize_code(
                getattr(log, "work_order_no", "")
            ),
            product_code=self._normalize_code(
                getattr(log, "product_code", "")
            ),
            op_no=self._normalize_op(
                getattr(log, "op_no", "")
            ),
            machine_code=self._normalize_code(
                getattr(log, "machine_code", "")
            ),
            operator_code=self._normalize_code(
                operator_code
            ),
            production_date=production_date,
            runtime_sec=runtime_sec,
            ok_qty=self._to_non_negative_int(
                getattr(log, "ok_qty", 0)
            ),
            ng_qty=self._to_non_negative_int(
                getattr(log, "ng_qty", 0)
            ),
        )

    @staticmethod
    def _resolve_runtime(
        log,
        start_time,
        finish_time,
    ):
        supplied_runtime = getattr(
            log,
            "run_time_sec",
            0,
        )

        try:
            supplied_runtime = float(
                supplied_runtime or 0
            )
        except (TypeError, ValueError):
            supplied_runtime = 0.0

        if supplied_runtime > 0:
            return supplied_runtime

        if (
            isinstance(start_time, datetime)
            and isinstance(finish_time, datetime)
        ):
            seconds = (
                finish_time - start_time
            ).total_seconds()

            return max(seconds, 0.0)

        return 0.0

    @staticmethod
    def _resolve_date(log, start_time):
        production_date = getattr(
            log,
            "production_date",
            None,
        )

        if isinstance(production_date, datetime):
            return production_date.date()

        if isinstance(production_date, date):
            return production_date

        if isinstance(start_time, datetime):
            return start_time.date()

        return date.today()

    # ==========================================================
    # Helpers
    # ==========================================================

    def repository_update(self):
        try:
            self.work_order_repository.update()

        except Exception:
            self.session.rollback()
            raise

    @staticmethod
    def _normalize_code(value):
        return str(value or "").strip().upper()

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

    @staticmethod
    def _to_non_negative_int(value):
        try:
            number = int(float(value or 0))
        except (TypeError, ValueError):
            return 0

        return max(number, 0)