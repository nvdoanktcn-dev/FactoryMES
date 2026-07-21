from matplotlib.ticker import FuncFormatter

from src.dto.chart_data import BarChartData
from src.ui.charts.base_chart import BaseChart
from src.ui.charts.chart_formatter import ChartFormatter
from src.ui.charts.chart_theme import ChartTheme
from src.ui.charts.chart_utils import ChartUtils


class BarChart(BaseChart):
    """
    Generic Enterprise Bar Chart.

    Hỗ trợ:
    - Vertical Bar
    - Horizontal Bar
    - Ranking
    - Auto Scale
    - Auto Formatter
    - Value Labels
    - ChartTheme
    """

    def __init__(
        self,
        title="Bar Chart",
        subtitle="",
        parent=None,
    ):
        super().__init__(
            title=title,
            subtitle=subtitle,
            parent=parent,
        )

    # ==========================================================
    # Plot
    # ==========================================================

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
                "BarChart requires BarChartData."
            )

        if data.is_empty:
            return

        self.validate(data)

        labels = ChartUtils.normalize_labels(
            data.labels
        )

        values = ChartUtils.normalize_values(
            data.values,
            allow_negative=False,
        )

        x_positions = list(
            range(len(labels))
        )

        axes.figure.set_facecolor(
            ChartTheme.FIGURE_BACKGROUND
        )

        axes.set_facecolor(
            ChartTheme.AXES_BACKGROUND
        )

        color = ChartTheme.color_for_series(
            data.title
        )

        if data.horizontal:
            bars = axes.barh(
                x_positions,
                values,
                color=color,
            )

            axes.set_yticks(
                x_positions
            )

            axes.set_yticklabels(
                labels
            )

            self._configure_horizontal_chart(
                axes=axes,
                bars=bars,
                values=values,
                data=data,
            )

        else:
            bars = axes.bar(
                x_positions,
                values,
                color=color,
            )

            axes.set_xticks(
                x_positions
            )

            axes.set_xticklabels(
                labels
            )

            self._configure_vertical_chart(
                axes=axes,
                bars=bars,
                values=values,
                data=data,
            )

        self._apply_title(
            axes,
            data,
        )

        self._apply_spines(
            axes
        )

        self._apply_ticks(
            axes,
            data,
        )

    # ==========================================================
    # Vertical chart
    # ==========================================================

    def _configure_vertical_chart(
        self,
        axes,
        bars,
        values,
        data,
    ):
        y_max = ChartUtils.calculate_axis_max(
            values,
            padding_ratio=0.18,
        )

        axes.set_ylim(
            0,
            y_max,
        )

        axes.set_xlabel(
            data.x_label,
            fontsize=ChartTheme.LABEL_SIZE,
        )

        axes.set_ylabel(
            self._build_axis_label(
                data.y_label,
                data.unit,
            ),
            fontsize=ChartTheme.LABEL_SIZE,
        )

        axes.grid(
            True,
            axis="y",
            alpha=ChartTheme.GRID_ALPHA,
            linestyle=ChartTheme.GRID_STYLE,
            color=ChartTheme.GRID_COLOR,
        )

        axes.yaxis.set_major_formatter(
            FuncFormatter(
                lambda value, _:
                    self._format_tick(
                        value,
                        data.unit,
                    )
            )
        )

        if data.show_values:
            self._add_vertical_value_labels(
                axes=axes,
                bars=bars,
                unit=data.unit,
            )

    # ==========================================================
    # Horizontal chart
    # ==========================================================

    def _configure_horizontal_chart(
        self,
        axes,
        bars,
        values,
        data,
    ):
        x_max = ChartUtils.calculate_axis_max(
            values,
            padding_ratio=0.22,
        )

        axes.set_xlim(
            0,
            x_max,
        )

        axes.set_xlabel(
            self._build_axis_label(
                data.x_label,
                data.unit,
            ),
            fontsize=ChartTheme.LABEL_SIZE,
        )

        axes.set_ylabel(
            data.y_label,
            fontsize=ChartTheme.LABEL_SIZE,
        )

        axes.grid(
            True,
            axis="x",
            alpha=ChartTheme.GRID_ALPHA,
            linestyle=ChartTheme.GRID_STYLE,
            color=ChartTheme.GRID_COLOR,
        )

        axes.xaxis.set_major_formatter(
            FuncFormatter(
                lambda value, _:
                    self._format_tick(
                        value,
                        data.unit,
                    )
            )
        )

        # Giá trị lớn nhất nằm ở trên cùng.
        axes.invert_yaxis()

        if data.show_values:
            self._add_horizontal_value_labels(
                axes=axes,
                bars=bars,
                unit=data.unit,
            )

    # ==========================================================
    # Value labels
    # ==========================================================

    @staticmethod
    def _add_vertical_value_labels(
        axes,
        bars,
        unit,
    ):
        for bar in bars:
            value = bar.get_height()

            axes.annotate(
                BarChart._format_value(
                    value,
                    unit,
                ),
                xy=(
                    bar.get_x()
                    + bar.get_width() / 2,
                    value,
                ),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=ChartTheme.AXIS_SIZE,
                color=ChartTheme.NORMAL,
            )

    @staticmethod
    def _add_horizontal_value_labels(
        axes,
        bars,
        unit,
    ):
        for bar in bars:
            value = bar.get_width()

            axes.annotate(
                BarChart._format_value(
                    value,
                    unit,
                ),
                xy=(
                    value,
                    bar.get_y()
                    + bar.get_height() / 2,
                ),
                xytext=(5, 0),
                textcoords="offset points",
                ha="left",
                va="center",
                fontsize=ChartTheme.AXIS_SIZE,
                color=ChartTheme.NORMAL,
            )

    # ==========================================================
    # Style
    # ==========================================================

    @staticmethod
    def _apply_title(
        axes,
        data,
    ):
        axes.set_title(
            data.title,
            fontsize=ChartTheme.TITLE_SIZE,
            pad=ChartTheme.TITLE_PADDING,
        )

    @staticmethod
    def _apply_spines(
        axes,
    ):
        axes.spines[
            "top"
        ].set_visible(False)

        axes.spines[
            "right"
        ].set_visible(False)

        axes.spines[
            "left"
        ].set_color(
            ChartTheme.BORDER_COLOR
        )

        axes.spines[
            "bottom"
        ].set_color(
            ChartTheme.BORDER_COLOR
        )

    @staticmethod
    def _apply_ticks(
        axes,
        data,
    ):
        axes.tick_params(
            axis="x",
            labelsize=ChartTheme.AXIS_SIZE,
        )

        axes.tick_params(
            axis="y",
            labelsize=ChartTheme.AXIS_SIZE,
        )

        if (
            not data.horizontal
            and len(data.labels) > 7
        ):
            axes.tick_params(
                axis="x",
                labelrotation=35,
            )

    # ==========================================================
    # Formatter
    # ==========================================================

    @staticmethod
    def _build_axis_label(
        label,
        unit,
    ):
        label = str(
            label or ""
        ).strip()

        unit = str(
            unit or ""
        ).strip()

        if not unit:
            return label

        if label:
            return f"{label} ({unit})"

        return unit

    @staticmethod
    def _format_tick(
        value,
        unit,
    ):
        normalized_unit = str(
            unit or ""
        ).strip().lower()

        if normalized_unit in {
            "%",
            "percent",
        }:
            return ChartFormatter.format_percent(
                value,
                decimals=0,
            )

        if normalized_unit in {
            "hour",
            "hours",
            "h",
        }:
            return ChartFormatter.format_hour(
                value
            )

        if normalized_unit in {
            "minute",
            "minutes",
            "min",
        }:
            return ChartFormatter.format_minute(
                value
            )

        return ChartFormatter.format_compact(
            value
        )

    @staticmethod
    def _format_value(
        value,
        unit,
    ):
        normalized_unit = str(
            unit or ""
        ).strip().lower()

        if normalized_unit in {
            "pcs",
            "qty",
        }:
            return ChartFormatter.format_integer(
                value
            )

        if normalized_unit in {
            "%",
            "percent",
        }:
            return ChartFormatter.format_percent(
                value,
                decimals=1,
            )

        if normalized_unit in {
            "hour",
            "hours",
            "h",
        }:
            return ChartFormatter.format_hour(
                value
            )

        if normalized_unit in {
            "minute",
            "minutes",
            "min",
        }:
            return ChartFormatter.format_minute(
                value
            )

        return ChartFormatter.format_number(
            value,
            decimals=2,
        )

    # ==========================================================
    # Validation
    # ==========================================================

    @staticmethod
    def validate(
        data,
    ):
        if not isinstance(
            data,
            BarChartData,
        ):
            raise TypeError(
                "Expected BarChartData."
            )

        if not data.labels:
            raise ValueError(
                "BarChartData labels are required."
            )

        if not data.values:
            raise ValueError(
                "BarChartData values are required."
            )

        if len(data.labels) != len(
            data.values
        ):
            raise ValueError(
                "BarChartData labels and values "
                "must have the same length."
            )

        return True