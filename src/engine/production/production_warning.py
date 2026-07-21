from dataclasses import dataclass, field


@dataclass(slots=True)
class ProductionWarning:
    code: str
    message: str
    severity: str = "WARNING"
    field: str = ""


@dataclass(slots=True)
class ProductionWarningResult:
    warnings: list[ProductionWarning] = field(
        default_factory=list
    )

    @property
    def has_warnings(self):
        return len(self.warnings) > 0

    def add(
        self,
        code,
        message,
        field="",
        severity="WARNING",
    ):
        self.warnings.append(
            ProductionWarning(
                code=code,
                message=message,
                field=field,
                severity=severity,
            )
        )


class ProductionWarningEngine:
    """
    Tạo cảnh báo từ kết quả ProductionCalculator.

    Không truy cập database.
    """

    def __init__(
        self,
        minimum_performance_percent=85.0,
        minimum_yield_percent=95.0,
        maximum_ng_percent=5.0,
        maximum_downtime_percent=15.0,
    ):
        self.minimum_performance_percent = float(
            minimum_performance_percent
        )
        self.minimum_yield_percent = float(
            minimum_yield_percent
        )
        self.maximum_ng_percent = float(
            maximum_ng_percent
        )
        self.maximum_downtime_percent = float(
            maximum_downtime_percent
        )

    def evaluate(self, calculation):
        if calculation is None:
            raise ValueError(
                "Production Calculation Result is required."
            )

        result = ProductionWarningResult()

        self._check_performance(
            calculation,
            result,
        )

        self._check_quality(
            calculation,
            result,
        )

        self._check_downtime(
            calculation,
            result,
        )

        self._check_cycle_time(
            calculation,
            result,
        )

        return result

    def _check_performance(
        self,
        calculation,
        result,
    ):
        performance = float(
            calculation.performance_percent or 0
        )

        if (
            performance
            < self.minimum_performance_percent
        ):
            result.add(
                code="LOW_PERFORMANCE",
                message=(
                    f"Performance is {performance:.2f}%, "
                    f"below target "
                    f"{self.minimum_performance_percent:.2f}%."
                ),
                field="performance_percent",
            )

    def _check_quality(
        self,
        calculation,
        result,
    ):
        yield_percent = float(
            calculation.yield_percent or 0
        )

        ng_percent = float(
            calculation.ng_percent or 0
        )

        if (
            yield_percent
            < self.minimum_yield_percent
        ):
            result.add(
                code="LOW_YIELD",
                message=(
                    f"Yield is {yield_percent:.2f}%, "
                    f"below target "
                    f"{self.minimum_yield_percent:.2f}%."
                ),
                field="yield_percent",
            )

        if ng_percent > self.maximum_ng_percent:
            result.add(
                code="HIGH_NG_RATE",
                message=(
                    f"NG Rate is {ng_percent:.2f}%, "
                    f"above limit "
                    f"{self.maximum_ng_percent:.2f}%."
                ),
                field="ng_percent",
            )

    def _check_downtime(
        self,
        calculation,
        result,
    ):
        downtime_percent = float(
            calculation.downtime_percent or 0
        )

        if (
            downtime_percent
            > self.maximum_downtime_percent
        ):
            result.add(
                code="HIGH_DOWNTIME",
                message=(
                    f"Downtime Rate is "
                    f"{downtime_percent:.2f}%, "
                    f"above limit "
                    f"{self.maximum_downtime_percent:.2f}%."
                ),
                field="downtime_percent",
            )

    @staticmethod
    def _check_cycle_time(
        calculation,
        result,
    ):
        standard_cycle = float(
            calculation.standard_cycle_time_sec
            or 0
        )

        actual_cycle = float(
            calculation.actual_cycle_time_sec
            or 0
        )

        if (
            standard_cycle > 0
            and actual_cycle > standard_cycle
        ):
            deviation = (
                actual_cycle
                / standard_cycle
                - 1
            ) * 100

            result.add(
                code="SLOW_ACTUAL_CYCLE",
                message=(
                    f"Actual Cycle Time is "
                    f"{actual_cycle:.3f} sec, "
                    f"{deviation:.2f}% slower than "
                    f"standard {standard_cycle:.3f} sec."
                ),
                field="actual_cycle_time_sec",
            )