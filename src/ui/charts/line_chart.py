from src.dto.chart_data import (
    LineChartData,
)
from src.ui.charts.base_chart import (
    BaseChart,
)
from src.ui.charts.renderers.line_renderer import (
    LineRenderer,
)


class LineChart(BaseChart):
    """
    LineChart Widget.

    Widget chỉ điều phối UI và gọi LineRenderer.
    Toàn bộ logic matplotlib nằm trong LineRenderer.
    """

    RENDERER_CLASS = LineRenderer

    def __init__(
        self,
        title="Line Chart",
        subtitle="",
        parent=None,
    ):
        super().__init__(
            title=title,
            subtitle=subtitle,
            parent=parent,
        )

    def plot(
        self,
        axes,
        data,
    ):
        if not isinstance(
            data,
            LineChartData,
        ):
            raise TypeError(
                "LineChart requires "
                "LineChartData."
            )

        self.RENDERER_CLASS.render(
            axes=axes,
            data=data,
        )

    @classmethod
    def validate(
        cls,
        data,
    ):
        return (
            cls.RENDERER_CLASS
            .validate(data)
        )