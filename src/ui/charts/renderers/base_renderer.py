from matplotlib.ticker import FuncFormatter

from src.ui.charts.chart_formatter import (
    ChartFormatter,
)
from src.ui.charts.chart_theme import (
    ChartTheme,
)
from src.ui.charts.chart_utils import (
    ChartUtils,
)


class BaseRenderer:
    """
    Renderer nền dùng chung cho Chart Framework.

    Không phụ thuộc PySide6.
    Chỉ làm việc với matplotlib Axes/Figure.
    """

    # ==========================================================
    # Background
    # ==========================================================

    @classmethod
    def apply_background(
        cls,
        axes,
    ):
        axes.figure.set_facecolor(
            ChartTheme.FIGURE_BACKGROUND
        )

        axes.set_facecolor(
            ChartTheme.AXES_BACKGROUND
        )

    # ==========================================================
    # Title
    # ==========================================================

    @classmethod
    def apply_title(
        cls,
        axes,
        title,
    ):
        axes.set_title(
            str(title or ""),
            fontsize=ChartTheme.TITLE_SIZE,
            pad=ChartTheme.TITLE_PADDING,
        )

    # ==========================================================
    # Axis labels
    # ==========================================================

    @classmethod
    def apply_axis_labels(
        cls,
        axes,
        x_label="",
        y_label="",
        unit="",
    ):
        axes.set_xlabel(
            str(x_label or ""),
            fontsize=ChartTheme.LABEL_SIZE,
        )

        formatted_y_label = (
            cls.build_axis_label(
                y_label,
                unit,
            )
        )

        axes.set_ylabel(
            formatted_y_label,
            fontsize=ChartTheme.LABEL_SIZE,
        )

    @staticmethod
    def build_axis_label(
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

    # ==========================================================
    # Tick style
    # ==========================================================

    @classmethod
    def apply_tick_style(
        cls,
        axes,
        rotate_x=0,
    ):
        axes.tick_params(
            axis="x",
            labelsize=ChartTheme.AXIS_SIZE,
            labelrotation=rotate_x,
        )

        axes.tick_params(
            axis="y",
            labelsize=ChartTheme.AXIS_SIZE,
        )

    # ==========================================================
    # Grid
    # ==========================================================

    @classmethod
    def apply_grid(
        cls,
        axes,
        axis="y",
    ):
        axes.grid(
            True,
            axis=axis,
            alpha=ChartTheme.GRID_ALPHA,
            linestyle=ChartTheme.GRID_STYLE,
            color=ChartTheme.GRID_COLOR,
        )

    # ==========================================================
    # Spines
    # ==========================================================

    @classmethod
    def apply_spines(
        cls,
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

    # ==========================================================
    # Legend
    # ==========================================================

    @classmethod
    def apply_legend(
        cls,
        axes,
        enabled=True,
    ):
        if not enabled:
            return

        handles, labels = (
            axes.get_legend_handles_labels()
        )

        if not handles:
            return

        axes.legend(
            fontsize=ChartTheme.LEGEND_SIZE,
            frameon=False,
        )

    # ==========================================================
    # Formatter
    # ==========================================================

    @classmethod
    def apply_y_formatter(
        cls,
        axes,
        unit="",
    ):
        axes.yaxis.set_major_formatter(
            FuncFormatter(
                lambda value, _:
                    cls.format_tick(
                        value,
                        unit,
                    )
            )
        )

    @classmethod
    def apply_x_formatter(
        cls,
        axes,
        unit="",
    ):
        axes.xaxis.set_major_formatter(
            FuncFormatter(
                lambda value, _:
                    cls.format_tick(
                        value,
                        unit,
                    )
            )
        )

    @staticmethod
    def format_tick(
        value,
        unit="",
    ):
        normalized_unit = str(
            unit or ""
        ).strip().lower()

        if normalized_unit in {
            "%",
            "percent",
        }:
            return (
                ChartFormatter
                .format_percent(
                    value,
                    decimals=0,
                )
            )

        if normalized_unit in {
            "pcs",
            "qty",
        }:
            return (
                ChartFormatter
                .format_compact(value)
            )

        if normalized_unit in {
            "hour",
            "hours",
            "h",
        }:
            return (
                ChartFormatter
                .format_hour(value)
            )

        if normalized_unit in {
            "minute",
            "minutes",
            "min",
        }:
            return (
                ChartFormatter
                .format_minute(value)
            )

        if normalized_unit in {
            "second",
            "seconds",
            "sec",
            "s",
        }:
            return (
                ChartFormatter
                .format_second(value)
            )

        return (
            ChartFormatter
            .format_compact(value)
        )

    # ==========================================================
    # Axis scale
    # ==========================================================

    @classmethod
    def apply_y_scale(
        cls,
        axes,
        values,
        unit="",
        force_zero=None,
        padding_ratio=None,
    ):
        values = ChartUtils.normalize_values(
            values
        )

        if not values:
            return

        minimum_value = ChartUtils.minimum(
            values
        )

        if force_zero is None:
            force_zero = (
                minimum_value >= 0
            )

        if padding_ratio is None:
            padding_ratio = (
                ChartTheme.Y_MARGIN
            )

        y_min = (
            ChartUtils
            .calculate_axis_min(
                values,
                force_zero=force_zero,
            )
        )

        y_max = (
            ChartUtils
            .calculate_axis_max(
                values,
                padding_ratio=padding_ratio,
            )
        )

        normalized_unit = str(
            unit or ""
        ).strip().lower()

        if normalized_unit in {
            "%",
            "percent",
        }:
            y_min = max(
                y_min,
                0.0,
            )

            y_max = max(
                y_max,
                100.0,
            )

        if y_max <= y_min:
            y_max = y_min + 1.0

        axes.set_ylim(
            y_min,
            y_max,
        )

    @classmethod
    def apply_x_scale(
        cls,
        axes,
        values,
        padding_ratio=0.10,
    ):
        values = ChartUtils.normalize_values(
            values,
            allow_negative=False,
        )

        if not values:
            return

        x_max = (
            ChartUtils
            .calculate_axis_max(
                values,
                padding_ratio=padding_ratio,
            )
        )

        axes.set_xlim(
            0,
            x_max,
        )

    # ==========================================================
    # Margins
    # ==========================================================

    @classmethod
    def apply_margins(
        cls,
        axes,
        x=None,
        y=None,
    ):
        if x is None:
            x = ChartTheme.X_MARGIN

        if y is None:
            y = ChartTheme.Y_MARGIN

        axes.margins(
            x=x,
            y=y,
        )

    # ==========================================================
    # Common styling
    # ==========================================================

    @classmethod
    def apply_common_style(
        cls,
        axes,
        title="",
        x_label="",
        y_label="",
        unit="",
        grid_axis="y",
        rotate_x=0,
    ):
        cls.apply_background(
            axes
        )

        cls.apply_title(
            axes,
            title,
        )

        cls.apply_axis_labels(
            axes,
            x_label=x_label,
            y_label=y_label,
            unit=unit,
        )

        cls.apply_tick_style(
            axes,
            rotate_x=rotate_x,
        )

        cls.apply_grid(
            axes,
            axis=grid_axis,
        )

        cls.apply_spines(
            axes
        )