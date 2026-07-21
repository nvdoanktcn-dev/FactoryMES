from dataclasses import dataclass, field




@dataclass(slots=True)
class ChartSeries:
    """
    Một chuỗi dữ liệu trên biểu đồ.

    Ví dụ:
        name = "OK Qty"
        values = [100, 150, 200]
    """

    name: str
    values: list[float] = field(
        default_factory=list
    )

    unit: str = ""

    def __post_init__(self):
        self.name = str(
            self.name or ""
        ).strip()

        self.unit = str(
            self.unit or ""
        ).strip()

        self.values = [
            self._to_float(value)
            for value in self.values
        ]

    @staticmethod
    def _to_float(value):
        try:
            return float(
                value or 0
            )

        except (
            TypeError,
            ValueError,
        ):
            return 0.0


@dataclass(slots=True)
class LineChartData:
    """
    Dữ liệu cho Line Chart.

    labels:
        Trục X.

    series:
        Một hoặc nhiều đường dữ liệu.
    """

    title: str
    labels: list[str] = field(
        default_factory=list
    )

    series: list[ChartSeries] = field(
        default_factory=list
    )

    x_label: str = ""
    y_label: str = ""
    unit: str = ""

    show_legend: bool = True
    show_markers: bool = True

    @property
    def is_empty(self):
        if not self.labels:
            return True

        if not self.series:
            return True

        return not any(
            series.values
            for series in self.series
        )


@dataclass(slots=True)
class BarChartData:
    """
    Dữ liệu cho Bar Chart hoặc Ranking Chart.
    """

    title: str
    labels: list[str] = field(
        default_factory=list
    )

    values: list[float] = field(
        default_factory=list
    )

    x_label: str = ""
    y_label: str = ""
    unit: str = ""

    horizontal: bool = False
    show_values: bool = True

    @property
    def is_empty(self):
        return (
            not self.labels
            or not self.values
        )


@dataclass(slots=True)
class ParetoChartData:
    """
    Dữ liệu cho Pareto Chart.

    values:
        Số lượng từng nhóm.

    cumulative_percent:
        Tỷ lệ tích lũy tương ứng.
    """

    title: str
    labels: list[str] = field(
        default_factory=list
    )

    values: list[float] = field(
        default_factory=list
    )

    cumulative_percent: list[float] = field(
        default_factory=list
    )

    value_unit: str = "PCS"
    percent_unit: str = "%"

    threshold_percent: float = 80.0

    @property
    def is_empty(self):
        return (
            not self.labels
            or not self.values
            or not self.cumulative_percent
        )