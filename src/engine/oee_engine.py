from src.engine.oee_result import OEEResult


class OEEEngine:
    """
    Pure Engine tính OEE.

    Không truy cập database.
    Không phụ thuộc SQLAlchemy.

    Input:
        - MachineUtilizationResult
        - Ideal Cycle Time
    """

    def calculate(
        self,
        utilization_result,
        ideal_cycle_time_sec,
    ):
        if utilization_result is None:
            raise ValueError(
                "Machine Utilization Result is required."
            )

        ideal_cycle_time_sec = (
            self._to_positive_float(
                ideal_cycle_time_sec,
                "Ideal Cycle Time",
            )
        )

        available_sec = self._to_non_negative_float(
            getattr(
                utilization_result,
                "available_sec",
                0,
            )
        )

        runtime_sec = self._to_non_negative_float(
            getattr(
                utilization_result,
                "runtime_sec",
                0,
            )
        )

        ok_qty = self._to_non_negative_int(
            getattr(
                utilization_result,
                "ok_qty",
                0,
            )
        )

        ng_qty = self._to_non_negative_int(
            getattr(
                utilization_result,
                "ng_qty",
                0,
            )
        )

        total_qty = ok_qty + ng_qty

        availability = self.calculate_availability(
            runtime_sec=runtime_sec,
            available_sec=available_sec,
        )

        performance = self.calculate_performance(
            total_qty=total_qty,
            runtime_sec=runtime_sec,
            ideal_cycle_time_sec=ideal_cycle_time_sec,
        )

        quality = self.calculate_quality(
            ok_qty=ok_qty,
            total_qty=total_qty,
        )

        oee = (
            availability
            * performance
            * quality
            / 10000
        )

        return OEEResult(
            machine_code=str(
                getattr(
                    utilization_result,
                    "machine_code",
                    "",
                )
                or ""
            ).strip().upper(),

            production_date=getattr(
                utilization_result,
                "production_date",
                None,
            ),

            shift=str(
                getattr(
                    utilization_result,
                    "shift",
                    "",
                )
                or ""
            ).strip().upper(),

            available_sec=available_sec,
            runtime_sec=runtime_sec,
            ideal_cycle_time_sec=ideal_cycle_time_sec,

            ok_qty=ok_qty,
            ng_qty=ng_qty,
            total_qty=total_qty,

            availability_percent=availability,
            performance_percent=performance,
            quality_percent=quality,
            oee_percent=oee,
        )

    def calculate_many(
        self,
        utilization_results,
        cycle_time_resolver,
    ):
        """
        Tính OEE cho nhiều kết quả sử dụng máy.

        cycle_time_resolver là callable:

            cycle_time_resolver(result) -> cycle_time_sec
        """
        if utilization_results is None:
            return []

        if not callable(cycle_time_resolver):
            raise ValueError(
                "Cycle Time Resolver must be callable."
            )

        results = []

        for utilization_result in utilization_results:
            cycle_time_sec = cycle_time_resolver(
                utilization_result
            )

            results.append(
                self.calculate(
                    utilization_result,
                    cycle_time_sec,
                )
            )

        return results

    @staticmethod
    def calculate_availability(
        runtime_sec,
        available_sec,
    ):
        runtime_sec = max(
            float(runtime_sec or 0),
            0.0,
        )

        available_sec = max(
            float(available_sec or 0),
            0.0,
        )

        if available_sec <= 0:
            return 0.0

        return min(
            runtime_sec / available_sec * 100,
            100.0,
        )

    @staticmethod
    def calculate_performance(
        total_qty,
        runtime_sec,
        ideal_cycle_time_sec,
    ):
        total_qty = max(
            int(total_qty or 0),
            0,
        )

        runtime_sec = max(
            float(runtime_sec or 0),
            0.0,
        )

        ideal_cycle_time_sec = max(
            float(ideal_cycle_time_sec or 0),
            0.0,
        )

        if (
            total_qty <= 0
            or runtime_sec <= 0
            or ideal_cycle_time_sec <= 0
        ):
            return 0.0

        performance = (
            ideal_cycle_time_sec
            * total_qty
            / runtime_sec
            * 100
        )

        return min(
            performance,
            100.0,
        )

    @staticmethod
    def calculate_quality(
        ok_qty,
        total_qty,
    ):
        ok_qty = max(
            int(ok_qty or 0),
            0,
        )

        total_qty = max(
            int(total_qty or 0),
            0,
        )

        if total_qty <= 0:
            return 0.0

        return min(
            ok_qty / total_qty * 100,
            100.0,
        )

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