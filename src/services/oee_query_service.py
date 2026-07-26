from __future__ import annotations

from datetime import date, datetime, time, timedelta

from src.services.oee_aggregation_service import (
    OEEAggregationRow,
    OEEAggregationService,
)


class OEEQueryService:
    """
    Application/query service for OEE reporting.

    This service coordinates existing repositories and delegates
    all OEE mathematics to OEEAggregationService.
    """

    def __init__(
        self,
        *,
        execution_repository,
        assignment_repository,
        production_order_repository,
        routing_repository,
    ):
        self.execution_repository = (
            execution_repository
        )
        self.assignment_repository = (
            assignment_repository
        )
        self.production_order_repository = (
            production_order_repository
        )
        self.routing_repository = (
            routing_repository
        )

    def get_assignment_oee(
        self,
        assignment_id,
        *,
        start_time=None,
        end_time=None,
    ):
        assignment = (
            self.assignment_repository
            .get_by_id(assignment_id)
        )

        if assignment is None:
            return OEEAggregationService.empty_result()

        rows = self._build_rows_for_assignments(
            [assignment],
            start_time=start_time,
            end_time=end_time,
        )
        return OEEAggregationService.aggregate(rows)

    def get_machine_oee(
        self,
        machine_code,
        *,
        start_time=None,
        end_time=None,
    ):
        code = self._normalize_code(
            machine_code,
            "Machine Code",
        )

        assignments = (
            self.assignment_repository
            .get_by_machine(code)
        )

        rows = self._build_rows_for_assignments(
            assignments,
            start_time=start_time,
            end_time=end_time,
        )
        return OEEAggregationService.aggregate(rows)

    def get_employee_oee(
        self,
        employee_code,
        *,
        start_time=None,
        end_time=None,
    ):
        code = self._normalize_code(
            employee_code,
            "Employee Code",
        )

        assignments = (
            self.assignment_repository
            .get_by_employee(code)
        )

        rows = self._build_rows_for_assignments(
            assignments,
            start_time=start_time,
            end_time=end_time,
        )
        return OEEAggregationService.aggregate(rows)

    def get_shift_oee(
        self,
        shift,
        *,
        start_time=None,
        end_time=None,
    ):
        normalized_shift = str(
            shift or ""
        ).strip().upper()

        if not normalized_shift:
            raise ValueError(
                "Shift is required."
            )

        assignments = [
            assignment
            for assignment in (
                self.assignment_repository
                .get_active_assignments()
            )
            if str(
                getattr(
                    assignment,
                    "shift",
                    "",
                )
                or ""
            ).strip().upper()
            == normalized_shift
        ]

        rows = self._build_rows_for_assignments(
            assignments,
            start_time=start_time,
            end_time=end_time,
        )
        return OEEAggregationService.aggregate(rows)

    def get_product_oee(
        self,
        product_code,
        *,
        start_time=None,
        end_time=None,
    ):
        code = self._normalize_code(
            product_code,
            "Product Code",
        )

        orders = self._all_orders()
        matching_orders = [
            order
            for order in orders
            if str(
                getattr(
                    order,
                    "product_code",
                    "",
                )
                or ""
            ).strip().upper()
            == code
        ]

        assignments = (
            self._assignments_for_orders(
                matching_orders
            )
        )

        rows = self._build_rows_for_assignments(
            assignments,
            start_time=start_time,
            end_time=end_time,
        )
        return OEEAggregationService.aggregate(rows)

    def get_work_order_oee(
        self,
        work_order_no,
        *,
        start_time=None,
        end_time=None,
    ):
        number = self._normalize_code(
            work_order_no,
            "Work Order No",
        )

        orders = (
            self.production_order_repository
            .get_by_work_order(number)
        )

        assignments = (
            self._assignments_for_orders(orders)
        )

        rows = self._build_rows_for_assignments(
            assignments,
            start_time=start_time,
            end_time=end_time,
        )
        return OEEAggregationService.aggregate(rows)

    def get_daily_oee(
        self,
        target_date,
    ):
        day = self._normalize_date(
            target_date,
            "Target Date",
        )
        start_time = datetime.combine(
            day,
            time.min,
        )
        end_time = start_time + timedelta(days=1)

        return self.get_all_oee(
            start_time=start_time,
            end_time=end_time,
        )

    def get_monthly_oee(
        self,
        year,
        month,
    ):
        try:
            normalized_year = int(year)
            normalized_month = int(month)
            start_time = datetime(
                normalized_year,
                normalized_month,
                1,
            )
        except (TypeError, ValueError) as error:
            raise ValueError(
                "Invalid year or month."
            ) from error

        if normalized_month == 12:
            end_time = datetime(
                normalized_year + 1,
                1,
                1,
            )
        else:
            end_time = datetime(
                normalized_year,
                normalized_month + 1,
                1,
            )

        return self.get_all_oee(
            start_time=start_time,
            end_time=end_time,
        )

    def get_all_oee(
        self,
        *,
        start_time=None,
        end_time=None,
    ):
        assignments = self._all_assignments()

        rows = self._build_rows_for_assignments(
            assignments,
            start_time=start_time,
            end_time=end_time,
        )
        return OEEAggregationService.aggregate(rows)

    def _build_rows_for_assignments(
        self,
        assignments,
        *,
        start_time=None,
        end_time=None,
    ):
        normalized_start, normalized_end = (
            self._normalize_range(
                start_time,
                end_time,
            )
        )
        final_operations = (
            self._final_operations_by_order()
        )

        rows = []

        for assignment in assignments or []:
            order = (
                self.production_order_repository
                .get_by_id(
                    getattr(
                        assignment,
                        "production_order_id",
                        None,
                    )
                )
            )

            if order is None:
                continue

            routing = (
                self.routing_repository
                .get_by_product_operation(
                    getattr(
                        order,
                        "product_code",
                        None,
                    ),
                    getattr(
                        order,
                        "operation_no",
                        None,
                    ),
                )
            )

            if routing is None:
                raise ValueError(
                    "Routing not found for "
                    f"product {getattr(order, 'product_code', None)} "
                    f"operation {getattr(order, 'operation_no', None)}."
                )

            cycle_time_sec = getattr(
                routing,
                "cycle_time_sec",
                None,
            )

            executions = (
                self.execution_repository
                .get_by_assignment_id(
                    getattr(
                        assignment,
                        "id",
                        None,
                    )
                )
            )

            for execution in executions or []:
                if not self._is_completed_execution(
                    execution
                ):
                    continue

                if not self._execution_in_range(
                    execution,
                    normalized_start,
                    normalized_end,
                ):
                    continue

                rows.append(
                    OEEAggregationRow(
                        runtime_minutes=getattr(
                            execution,
                            "runtime_minutes",
                            0,
                        ),
                        downtime_minutes=getattr(
                            execution,
                            "downtime_minutes",
                            0,
                        ),
                        ok_qty=getattr(
                            execution,
                            "ok_qty",
                            0,
                        ),
                        ng_qty=getattr(
                            execution,
                            "ng_qty",
                            0,
                        ),
                        cycle_time_sec=(
                            cycle_time_sec
                        ),
                        work_order_no=getattr(
                            order,
                            "work_order_no",
                            "",
                        ),
                        product_code=getattr(
                            order,
                            "product_code",
                            "",
                        ),
                        operation_no=(
                            self._operation_number(
                                getattr(
                                    order,
                                    "operation_no",
                                    None,
                                )
                            )
                        ),
                        is_final_operation=(
                            self._is_final_operation(
                                order,
                                final_operations,
                            )
                        ),
                    )
                )

        return rows

    def _final_operations_by_order(self):
        final_operations = {}

        for order in self._all_orders():
            routing = (
                self.routing_repository
                .get_by_product_operation(
                    getattr(
                        order,
                        "product_code",
                        None,
                    ),
                    getattr(
                        order,
                        "operation_no",
                        None,
                    ),
                )
            )
            if (
                routing is not None
                and str(
                    getattr(
                        routing,
                        "status",
                        "",
                    )
                    or ""
                ).strip().upper()
                == "INACTIVE"
            ):
                continue

            operation_no = self._operation_number(
                getattr(
                    order,
                    "operation_no",
                    None,
                )
            )
            if operation_no is None:
                continue

            key = self._order_route_key(order)
            current = final_operations.get(key)
            if current is None or operation_no > current:
                final_operations[key] = operation_no

        return final_operations

    def _is_final_operation(
        self,
        order,
        final_operations,
    ):
        explicit = getattr(
            order,
            "is_final_operation",
            getattr(
                order,
                "is_final_op",
                None,
            ),
        )
        if explicit is not None:
            return self._boolean(explicit)

        operation_no = self._operation_number(
            getattr(
                order,
                "operation_no",
                None,
            )
        )
        if operation_no is None:
            return None

        highest_op = final_operations.get(
            self._order_route_key(order)
        )
        return (
            highest_op is not None
            and operation_no == highest_op
        )

    @staticmethod
    def _order_route_key(order):
        return (
            str(
                getattr(
                    order,
                    "work_order_no",
                    "",
                )
                or ""
            ).strip().upper(),
            str(
                getattr(
                    order,
                    "product_code",
                    "",
                )
                or ""
            ).strip().upper(),
        )

    @staticmethod
    def _operation_number(value):
        if value is None:
            return None

        text = str(value).strip().upper()
        if text.startswith("OP"):
            text = text[2:].strip()

        try:
            number = int(float(text))
        except (TypeError, ValueError, OverflowError):
            return None

        return number if number >= 0 else None

    @staticmethod
    def _boolean(value):
        if isinstance(value, bool):
            return value

        return str(value or "").strip().upper() in {
            "1",
            "TRUE",
            "YES",
            "Y",
        }

    def _assignments_for_orders(
        self,
        orders,
    ):
        assignments = []

        for order in orders or []:
            assignments.extend(
                self.assignment_repository
                .get_by_production_order_id(
                    getattr(
                        order,
                        "id",
                        None,
                    )
                )
                or []
            )

        return assignments

    def _all_assignments(self):
        getter = getattr(
            self.assignment_repository,
            "get_all",
            None,
        )

        if callable(getter):
            return getter() or []

        return (
            self.assignment_repository
            .get_active_assignments()
            or []
        )

    def _all_orders(self):
        getter = getattr(
            self.production_order_repository,
            "get_all",
            None,
        )

        if callable(getter):
            return getter() or []

        return (
            self.production_order_repository
            .get_open_orders()
            or []
        )

    @staticmethod
    def _is_completed_execution(
        execution,
    ):
        return str(
            getattr(
                execution,
                "status",
                "",
            )
            or ""
        ).strip().upper() == "COMPLETED"

    @staticmethod
    def _execution_in_range(
        execution,
        start_time,
        end_time,
    ):
        execution_start = getattr(
            execution,
            "start_time",
            None,
        )
        execution_end = getattr(
            execution,
            "end_time",
            None,
        )

        if execution_start is None:
            return False

        effective_end = (
            execution_end
            if execution_end is not None
            else execution_start
        )

        if (
            start_time is not None
            and effective_end < start_time
        ):
            return False

        if (
            end_time is not None
            and execution_start >= end_time
        ):
            return False

        return True

    @classmethod
    def _normalize_range(
        cls,
        start_time,
        end_time,
    ):
        normalized_start = (
            cls._normalize_datetime(
                start_time,
                "Start Time",
            )
            if start_time is not None
            else None
        )
        normalized_end = (
            cls._normalize_datetime(
                end_time,
                "End Time",
            )
            if end_time is not None
            else None
        )

        if (
            normalized_start is not None
            and normalized_end is not None
            and normalized_end <= normalized_start
        ):
            raise ValueError(
                "End Time must be after Start Time."
            )

        return normalized_start, normalized_end

    @staticmethod
    def _normalize_datetime(
        value,
        field_name,
    ):
        if isinstance(value, datetime):
            return value

        if isinstance(value, date):
            return datetime.combine(
                value,
                time.min,
            )

        if isinstance(value, str):
            text = value.strip()

            if not text:
                raise ValueError(
                    f"{field_name} is required."
                )

            try:
                return datetime.fromisoformat(text)
            except ValueError as error:
                raise ValueError(
                    f"Invalid {field_name}: {value}"
                ) from error

        raise ValueError(
            f"Invalid {field_name}: {value}"
        )

    @staticmethod
    def _normalize_date(
        value,
        field_name,
    ):
        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        if isinstance(value, str):
            text = value.strip()

            try:
                return date.fromisoformat(text)
            except ValueError as error:
                raise ValueError(
                    f"Invalid {field_name}: {value}"
                ) from error

        raise ValueError(
            f"Invalid {field_name}: {value}"
        )

    @staticmethod
    def _normalize_code(
        value,
        field_name,
    ):
        normalized = str(
            value or ""
        ).strip().upper()

        if not normalized:
            raise ValueError(
                f"{field_name} is required."
            )

        return normalized
