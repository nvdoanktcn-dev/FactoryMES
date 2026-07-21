from src.ui.charts.base_chart import (
    BaseChart,
)


class DemoLineChart(BaseChart):
    """
    Biểu đồ demo dùng để kiểm thử BaseChart.
    """

    def plot(
        self,
        axes,
        data,
    ):
        labels = [
            str(
                self.value_from(
                    item,
                    "label",
                    "",
                )
            )
            for item in data
        ]

        values = [
            self.normalize_number(
                self.value_from(
                    item,
                    "value",
                    0,
                )
            )
            for item in data
        ]

        x_positions = list(
            range(len(labels))
        )

        axes.plot(
            x_positions,
            values,
            marker="o",
        )

        axes.set_xticks(
            x_positions
        )

        axes.set_xticklabels(
            labels
        )

        axes.set_xlabel(
            "Production Date"
        )

        axes.set_ylabel(
            "Output (PCS)"
        )

        axes.set_title(
            self._title
        )

        axes.tick_params(
            axis="x",
            labelrotation=35,
        )