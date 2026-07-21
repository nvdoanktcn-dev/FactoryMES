from src.dto.chart_data import (
    LineChartData,
)
from src.ui.charts.chart_theme import (
    ChartTheme,
)
from src.ui.charts.chart_utils import (
    ChartUtils,
)
from src.ui.charts.renderers.base_renderer import (
    BaseRenderer,
)


class LineRenderer(BaseRenderer):
    """
    Renderer cho LineChartData.

    Trách nhiệm:
    - Validate dữ liệu.
    - Vẽ một hoặc nhiều series.
    - Theme.
    - Scale.
    - Formatter.
    - Legend.
    """

    @classmethod
    def render(
        cls,
        axes,
        data,
    ):
        cls.validate(data)

        if data.is_empty:
            return

        labels = ChartUtils.normalize_labels(
            data.labels
        )

        all_values = (
            ChartUtils.flatten_series(
                data.series
            )
        )

        cls.apply_background(
            axes
        )

        x_positions = list(
            range(len(labels))
        )

        for series in data.series:
            cls.render_series(
                axes=axes,
                x_positions=x_positions,
                series=series,
                show_markers=(
                    data.show_markers
                ),
            )

        axes.set_xticks(
            x_positions
        )

        axes.set_xticklabels(
            labels
        )

        cls.apply_title(
            axes,
            data.title,
        )

        cls.apply_axis_labels(
            axes,
            x_label=data.x_label,
            y_label=data.y_label,
            unit=data.unit,
        )

        cls.apply_tick_style(
            axes,
            rotate_x=(
                35
                if len(labels) > 10
                else 0
            ),
        )

        cls.apply_grid(
            axes,
            axis="y",
        )

        cls.apply_spines(
            axes
        )

        cls.apply_y_formatter(
            axes,
            unit=data.unit,
        )

        cls.apply_y_scale(
            axes,
            values=all_values,
            unit=data.unit,
        )

        cls.apply_margins(
            axes,
            x=ChartTheme.X_MARGIN,
            y=0,
        )

        cls.apply_legend(
            axes,
            enabled=data.show_legend,
        )

    # ==========================================================
    # Series
    # ==========================================================

    @classmethod
    def render_series(
        cls,
        axes,
        x_positions,
        series,
        show_markers=True,
    ):
        values = ChartUtils.normalize_values(
            series.values
        )

        plot_options = {
            "label":
                series.name,

            "color":
                ChartTheme.color_for_series(
                    series.name
                ),

            "linewidth":
                ChartTheme.LINE_WIDTH,
        }

        if show_markers:
            plot_options.update({
                "marker":
                    "o",

                "markersize":
                    ChartTheme.MARKER_SIZE,
            })

        axes.plot(
            x_positions,
            values,
            **plot_options,
        )

    # ==========================================================
    # Validation
    # ==========================================================

    @classmethod
    def validate(
        cls,
        data,
    ):
        if not isinstance(
            data,
            LineChartData,
        ):
            raise TypeError(
                "LineRenderer requires "
                "LineChartData."
            )

        if not data.labels:
            raise ValueError(
                "LineChartData labels "
                "are required."
            )

        if not data.series:
            raise ValueError(
                "LineChartData series "
                "are required."
            )

        ChartUtils.validate_series_lengths(
            labels=data.labels,
            series_list=data.series,
        )

        return True