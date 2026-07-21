from dataclasses import replace

from src.dto.chart_data import BarChartData
from src.ui.charts.bar_chart import BarChart
from src.ui.charts.chart_utils import ChartUtils


class RankingChart(BarChart):
    """
    Horizontal Ranking Chart.

    Chức năng:
    - Tự sắp xếp giảm dần.
    - Tự giới hạn Top N.
    - Luôn hiển thị dạng horizontal.
    - Giá trị lớn nhất ở trên cùng.
    """

    def __init__(
        self,
        title="Ranking Chart",
        subtitle="",
        top_n=10,
        parent=None,
    ):
        self.top_n = max(
            int(top_n or 10),
            1,
        )

        super().__init__(
            title=title,
            subtitle=subtitle,
            parent=parent,
        )

    def set_top_n(
        self,
        top_n,
    ):
        self.top_n = max(
            int(top_n or 1),
            1,
        )

        self.refresh_chart()

    def plot(
        self,
        axes,
        data,
    ):
        if not isinstance(
            data,
            BarChartData,
        ):
            raise TypeError(
                "RankingChart requires "
                "BarChartData."
            )

        ranked_pairs = ChartUtils.top_n(
            labels=data.labels,
            values=data.values,
            limit=self.top_n,
        )

        ranked_data = replace(
            data,
            labels=[
                label
                for label, _ in ranked_pairs
            ],
            values=[
                value
                for _, value in ranked_pairs
            ],
            horizontal=True,
        )

        super().plot(
            axes,
            ranked_data,
        )