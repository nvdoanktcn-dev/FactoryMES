from src.engine.production.production_calculation_result import (
    ProductionCalculationResult,
)


class ProductionCalculator:
    """
    Pure Engine tính KPI cho một Production Entry.

    Không query database.
    Không commit.
    Không phụ thuộc SQLAlchemy.

    Input:
        normalized_data từ ProductionValidator
        routing hoặc standard_cycle_time_sec

    Output:
        ProductionCalculationResult
    """

    def calculate(
        self,
        data,
        routing=None,
        standard_cycle_time_sec=None,
    ):
        if not isinstance(data, dict):
            raise ValueError(
                "Production data must be a dictionary."
            )

        runtime_sec = self._to_non_negative_float(
            data.get("run_time_sec")
            or data.get("runtime_sec")
            or 0
        )

        if runtime_sec <= 0:
            raise ValueError(
                "Runtime must be greater than zero."
            )

        downtime_min = self._to_non_negative_float(
            data.get("downtime_min") or 0
        )

        downtime_sec = downtime_min * 60

        net_runtime_sec = max(
            runtime_sec - downtime_sec,
            0.0,
        )

        ok_qty = self._to_non_negative_int(
            data.get("ok_qty")
        )

        ng_qty = self._to_non_negative_int(
            data.get("ng_qty")
        )

        total_qty = ok_qty + ng_qty

        if total_qty <= 0:
            raise ValueError(
                "Total Qty must be greater than zero."
            )

        standard_cycle = (
            self._resolve_standard_cycle_time(
                routing=routing,
                explicit_cycle_time=(
                    standard_cycle_time_sec
                ),
            )
        )

        actual_cycle = self.calculate_actual_cycle_time(
            net_runtime_sec=net_runtime_sec,
            total_qty=total_qty,
        )

        output_per_hour = self.calculate_output_per_hour(
            total_qty=total_qty,
            net_runtime_sec=net_runtime_sec,
        )

        standard_output_per_hour = (
            3600.0 / standard_cycle
        )

        yield_percent = self.calculate_yield(
            ok_qty=ok_qty,
            total_qty=total_qty,
        )

        ng_percent = self.calculate_ng_rate(
            ng_qty=ng_qty,
            total_qty=total_qty,
        )

        performance_percent = (
            self.calculate_performance(
                standard_cycle_time_sec=standard_cycle,
                total_qty=total_qty,
                net_runtime_sec=net_runtime_sec,
            )
        )

        downtime_percent = (
            self.calculate_downtime_rate(
                downtime_sec=downtime_sec,
                runtime_sec=runtime_sec,
            )
        )

        return ProductionCalculationResult(
            work_order_no=self._normalize_code(
                data.get("work_order_no")
            ),
            product_code=self._normalize_code(
                data.get("product_code")
            ),
            op_no=self._normalize_op(
                data.get("op_no")
            ),
            machine_code=self._normalize_code(
                data.get("machine_code")
            ),
            employee_code=self._normalize_code(
                data.get("employee_code")
                or data.get("operator_code")
            ),
            shift=self._normalize_code(
                data.get("shift")
            ),

            runtime_sec=runtime_sec,
            downtime_sec=downtime_sec,
            net_runtime_sec=net_runtime_sec,

            ok_qty=ok_qty,
            ng_qty=ng_qty,
            total_qty=total_qty,

            standard_cycle_time_sec=standard_cycle,
            actual_cycle_time_sec=actual_cycle,

            output_per_hour=output_per_hour,
            standard_output_per_hour=(
                standard_output_per_hour
            ),

            yield_percent=yield_percent,
            ng_percent=ng_percent,
            performance_percent=performance_percent,
            downtime_percent=downtime_percent,
        )

    # ==========================================================
    # KPI formulas
    # ==========================================================

    @staticmethod
    def calculate_actual_cycle_time(
        net_runtime_sec,
        total_qty,
    ):
        net_runtime_sec = float(
            net_runtime_sec or 0
        )
        total_qty = int(
            total_qty or 0
        )

        if (
            net_runtime_sec <= 0
            or total_qty <= 0
        ):
            return 0.0

        return (
            net_runtime_sec
            / total_qty
        )

    @staticmethod
    def calculate_output_per_hour(
        total_qty,
        net_runtime_sec,
    ):
        total_qty = int(
            total_qty or 0
        )
        net_runtime_sec = float(
            net_runtime_sec or 0
        )

        if (
            total_qty <= 0
            or net_runtime_sec <= 0
        ):
            return 0.0

        return (
            total_qty
            * 3600
            / net_runtime_sec
        )

    @staticmethod
    def calculate_yield(
        ok_qty,
        total_qty,
    ):
        ok_qty = int(ok_qty or 0)
        total_qty = int(total_qty or 0)

        if total_qty <= 0:
            return 0.0

        return min(
            ok_qty / total_qty * 100,
            100.0,
        )

    @staticmethod
    def calculate_ng_rate(
        ng_qty,
        total_qty,
    ):
        ng_qty = int(ng_qty or 0)
        total_qty = int(total_qty or 0)

        if total_qty <= 0:
            return 0.0

        return min(
            ng_qty / total_qty * 100,
            100.0,
        )

    @staticmethod
    def calculate_performance(
        standard_cycle_time_sec,
        total_qty,
        net_runtime_sec,
    ):
        standard_cycle_time_sec = float(
            standard_cycle_time_sec or 0
        )
        total_qty = int(total_qty or 0)
        net_runtime_sec = float(
            net_runtime_sec or 0
        )

        if (
            standard_cycle_time_sec <= 0
            or total_qty <= 0
            or net_runtime_sec <= 0
        ):
            return 0.0

        performance = (
            standard_cycle_time_sec
            * total_qty
            / net_runtime_sec
            * 100
        )

        return min(
            performance,
            100.0,
        )

    @staticmethod
    def calculate_downtime_rate(
        downtime_sec,
        runtime_sec,
    ):
        downtime_sec = float(
            downtime_sec or 0
        )
        runtime_sec = float(
            runtime_sec or 0
        )

        if runtime_sec <= 0:
            return 0.0

        return min(
            downtime_sec / runtime_sec * 100,
            100.0,
        )

    # ==========================================================
    # Cycle Time
    # ==========================================================

    def _resolve_standard_cycle_time(
        self,
        routing=None,
        explicit_cycle_time=None,
    ):
        if explicit_cycle_time is not None:
            return self._to_positive_float(
                explicit_cycle_time,
                "Standard Cycle Time",
            )

        if routing is None:
            raise ValueError(
                "Routing or Standard Cycle Time is required."
            )

        cycle_time = getattr(
            routing,
            "cycle_time_sec",
            0,
        )

        return self._to_positive_float(
            cycle_time,
            "Routing Cycle Time",
        )

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

    @staticmethod
    def _to_non_negative_float(value):
        try:
            number = float(
                value or 0
            )

        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                f"Invalid numeric value: {value}"
            ) from error

        if number < 0:
            raise ValueError(
                f"Value cannot be negative: {value}"
            )

        return number

    @staticmethod
    def _to_positive_float(
        value,
        field_name,
    ):
        try:
            number = float(value)

        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                f"{field_name} must be numeric: {value}"
            ) from error

        if number <= 0:
            raise ValueError(
                f"{field_name} must be greater than zero."
            )

        return number