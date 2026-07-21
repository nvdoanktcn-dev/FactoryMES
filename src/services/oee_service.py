from datetime import date, datetime

from src.database.session import get_session
from src.engine.machine_utilization_engine import (
    MachineUtilizationEngine,
)
from src.engine.oee_engine import OEEEngine
from src.engine.production_snapshot import (
    ProductionSnapshot,
)
from src.framework.exception import (
    NotFoundError,
    ValidationError,
)
from src.repository.production_log_repository import (
    ProductionLogRepository,
)
from src.repository.routing_repository import (
    RoutingRepository,
)


class OEEService:
    """
    Điều phối việc tính OEE từ dữ liệu thật.

    ProductionLog
        -> ProductionSnapshot
        -> MachineUtilizationEngine
        -> Routing Cycle Time
        -> OEEEngine
    """

    def __init__(self, session=None):
        self.session = session or get_session()

        self.production_repository = (
            ProductionLogRepository(self.session)
        )

        self.routing_repository = RoutingRepository(
            self.session
        )

        self.utilization_engine = (
            MachineUtilizationEngine()
        )

        self.oee_engine = OEEEngine()

    # ==========================================================
    # Public API
    # ==========================================================

    def calculate_machine_day(
        self,
        machine_code,
        production_date,
        shift=None,
    ):
        machine_code = self._normalize_code(
            machine_code
        )

        production_date = self._normalize_date(
            production_date
        )

        normalized_shift = self._normalize_shift(
            shift
        )

        if not machine_code:
            raise ValidationError(
                "Machine Code is required."
            )

        logs = (
            self.production_repository
            .get_by_machine_date(
                machine_code,
                production_date,
            )
        )

        snapshots = [
            self._create_snapshot(log)
            for log in logs
        ]

        utilization_results = (
            self.utilization_engine.calculate(
                snapshots=snapshots,
                machine_code=machine_code,
                production_date=production_date,
                shift=normalized_shift or None,
            )
        )

        if not utilization_results:
            return {
                "machine_code": machine_code,
                "production_date": production_date,
                "shift": normalized_shift,
                "items": [],
                "errors": [],
            }

        items = []
        errors = []

        for utilization in utilization_results:
            try:
                cycle_time_sec = (
                    self._resolve_cycle_time(
                        logs=logs,
                        machine_code=machine_code,
                        shift=utilization.shift,
                    )
                )

                oee_result = self.oee_engine.calculate(
                    utilization_result=utilization,
                    ideal_cycle_time_sec=cycle_time_sec,
                )

                items.append(oee_result)

            except Exception as error:
                errors.append({
                    "machine_code": machine_code,
                    "production_date":
                        production_date,
                    "shift": utilization.shift,
                    "message": str(error),
                })

        return {
            "machine_code": machine_code,
            "production_date": production_date,
            "shift": normalized_shift,
            "items": items,
            "errors": errors,
        }

    def calculate_date(self, production_date):
        production_date = self._normalize_date(
            production_date
        )

        logs = (
            self.production_repository
            .get_by_date_range(
                production_date,
                production_date,
            )
        )

        snapshots = [
            self._create_snapshot(log)
            for log in logs
        ]

        utilization_results = (
            self.utilization_engine.calculate(
                snapshots=snapshots,
                production_date=production_date,
            )
        )

        items = []
        errors = []

        for utilization in utilization_results:
            try:
                matching_logs = [
                    log
                    for log in logs
                    if (
                        self._normalize_code(
                            log.machine_code
                        )
                        == utilization.machine_code
                        and self._normalize_shift(
                            log.shift
                        )
                        == utilization.shift
                    )
                ]

                cycle_time_sec = (
                    self._resolve_cycle_time(
                        logs=matching_logs,
                        machine_code=(
                            utilization.machine_code
                        ),
                        shift=utilization.shift,
                    )
                )

                items.append(
                    self.oee_engine.calculate(
                        utilization_result=utilization,
                        ideal_cycle_time_sec=(
                            cycle_time_sec
                        ),
                    )
                )

            except Exception as error:
                errors.append({
                    "machine_code":
                        utilization.machine_code,
                    "production_date":
                        production_date,
                    "shift": utilization.shift,
                    "message": str(error),
                })

        return {
            "production_date": production_date,
            "items": items,
            "errors": errors,
            "summary": self._build_summary(items),
        }

    def calculate_range(
        self,
        start_date,
        end_date,
        machine_code=None,
    ):
        start_date = self._normalize_date(start_date)
        end_date = self._normalize_date(end_date)

        if end_date < start_date:
            raise ValidationError(
                "End Date cannot be earlier "
                "than Start Date."
            )

        logs = (
            self.production_repository
            .get_by_date_range(
                start_date=start_date,
                end_date=end_date,
                machine_code=machine_code,
            )
        )

        dates = sorted({
            log.start_time.date()
            for log in logs
            if isinstance(
                log.start_time,
                datetime,
            )
        })

        daily_results = [
            self.calculate_date(item_date)
            for item_date in dates
        ]

        all_items = [
            item
            for daily in daily_results
            for item in daily["items"]
            if (
                not machine_code
                or item.machine_code
                == self._normalize_code(
                    machine_code
                )
            )
        ]

        all_errors = [
            error
            for daily in daily_results
            for error in daily["errors"]
        ]

        return {
            "start_date": start_date,
            "end_date": end_date,
            "machine_code":
                self._normalize_code(machine_code),
            "daily_results": daily_results,
            "items": all_items,
            "errors": all_errors,
            "summary": self._build_summary(
                all_items
            ),
        }

    # ==========================================================
    # Snapshot adapter
    # ==========================================================

    def _create_snapshot(self, log):
        production_date = (
            log.start_time.date()
            if isinstance(
                log.start_time,
                datetime,
            )
            else date.today()
        )

        runtime_sec = float(
            log.run_time_sec or 0
        )

        if (
            runtime_sec <= 0
            and isinstance(log.start_time, datetime)
            and isinstance(log.finish_time, datetime)
        ):
            runtime_sec = max(
                (
                    log.finish_time
                    - log.start_time
                ).total_seconds(),
                0.0,
            )

        return ProductionSnapshot(
            work_order_no=self._normalize_code(
                log.work_order_no
            ),
            product_code=self._normalize_code(
                log.product_code
            ),
            op_no=self._normalize_op(
                log.op_no
            ),
            machine_code=self._normalize_code(
                log.machine_code
            ),
            operator_code=self._normalize_code(
                log.employee_code
            ),
            production_date=production_date,
            runtime_sec=runtime_sec,
            ok_qty=int(log.ok_qty or 0),
            ng_qty=int(log.ng_qty or 0),
            shift=(
                self._normalize_shift(log.shift)
                or self._infer_shift(log.start_time)
            ),
        )

    # ==========================================================
    # Cycle Time
    # ==========================================================

    def _resolve_cycle_time(
        self,
        logs,
        machine_code,
        shift,
    ):
        """
        Dùng cycle time bình quân gia quyền theo số lượng
        khi một máy chạy nhiều Product/OP trong cùng ca.
        """
        weighted_cycle_total = 0.0
        quantity_total = 0

        for log in logs:
            if (
                self._normalize_code(
                    log.machine_code
                )
                != self._normalize_code(
                    machine_code
                )
            ):
                continue

            if (
                shift
                and self._normalize_shift(log.shift)
                != self._normalize_shift(shift)
            ):
                continue

            routing = (
                self.routing_repository.get_by_op(
                    self._normalize_code(
                        log.product_code
                    ),
                    self._normalize_op(
                        log.op_no
                    ),
                )
            )

            if routing is None:
                raise NotFoundError(
                    "Routing not found: "
                    f"{log.product_code} - "
                    f"{log.op_no}"
                )

            routing_machine = self._normalize_code(
                routing.machine_code
            )

            if (
                routing_machine
                and routing_machine
                != self._normalize_code(
                    machine_code
                )
            ):
                raise ValidationError(
                    "Routing Machine does not match "
                    f"Production Machine: "
                    f"{routing_machine} != "
                    f"{machine_code}"
                )

            cycle_time = float(
                routing.cycle_time_sec or 0
            )

            if cycle_time <= 0:
                raise ValidationError(
                    "Cycle Time must be greater "
                    f"than zero: "
                    f"{log.product_code} - "
                    f"{log.op_no}"
                )

            total_qty = int(
                (log.ok_qty or 0)
                + (log.ng_qty or 0)
            )

            if total_qty <= 0:
                continue

            weighted_cycle_total += (
                cycle_time * total_qty
            )
            quantity_total += total_qty

        if quantity_total <= 0:
            raise ValidationError(
                "Unable to resolve Cycle Time: "
                "no production quantity found."
            )

        return (
            weighted_cycle_total
            / quantity_total
        )

    # ==========================================================
    # Summary
    # ==========================================================

    @staticmethod
    def _build_summary(items):
        if not items:
            return {
                "machine_shift_count": 0,
                "runtime_sec": 0.0,
                "available_sec": 0.0,
                "ok_qty": 0,
                "ng_qty": 0,
                "availability_percent": 0.0,
                "performance_percent": 0.0,
                "quality_percent": 0.0,
                "oee_percent": 0.0,
            }

        runtime_sec = sum(
            item.runtime_sec
            for item in items
        )

        available_sec = sum(
            item.available_sec
            for item in items
        )

        ok_qty = sum(
            item.ok_qty
            for item in items
        )

        total_qty = sum(
            item.total_qty
            for item in items
        )

        availability = (
            runtime_sec / available_sec * 100
            if available_sec > 0
            else 0.0
        )

        performance_numerator = sum(
            item.ideal_cycle_time_sec
            * item.total_qty
            for item in items
        )

        performance = (
            performance_numerator
            / runtime_sec
            * 100
            if runtime_sec > 0
            else 0.0
        )

        quality = (
            ok_qty / total_qty * 100
            if total_qty > 0
            else 0.0
        )

        availability = min(
            availability,
            100.0,
        )
        performance = min(
            performance,
            100.0,
        )
        quality = min(
            quality,
            100.0,
        )

        oee = (
            availability
            * performance
            * quality
            / 10000
        )

        return {
            "machine_shift_count": len(items),
            "runtime_sec": runtime_sec,
            "available_sec": available_sec,
            "ok_qty": ok_qty,
            "ng_qty": total_qty - ok_qty,
            "availability_percent":
                availability,
            "performance_percent":
                performance,
            "quality_percent": quality,
            "oee_percent": oee,
        }

    # ==========================================================
    # Helpers
    # ==========================================================

    @staticmethod
    def _normalize_code(value):
        return str(
            value or ""
        ).strip().upper()

    @staticmethod
    def _normalize_op(value):
        text = str(
            value or ""
        ).strip().upper()

        digits = "".join(
            character
            for character in text
            if character.isdigit()
        )

        if digits:
            return f"OP{int(digits)}"

        return text

    @staticmethod
    def _normalize_shift(value):
        text = str(
            value or ""
        ).strip().upper()

        mapping = {
            "DAY": "DAY",
            "D": "DAY",
            "NGÀY": "DAY",
            "CA NGÀY": "DAY",
            "NIGHT": "NIGHT",
            "N": "NIGHT",
            "ĐÊM": "NIGHT",
            "CA ĐÊM": "NIGHT",
        }

        return mapping.get(text, text)

    @staticmethod
    def _infer_shift(start_time):
        if isinstance(start_time, datetime):
            if 8 <= start_time.hour < 20:
                return "DAY"

        return "NIGHT"

    @staticmethod
    def _normalize_date(value):
        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        try:
            return datetime.fromisoformat(
                str(value).strip()
            ).date()

        except ValueError as error:
            raise ValidationError(
                f"Invalid Date: {value}"
            ) from error