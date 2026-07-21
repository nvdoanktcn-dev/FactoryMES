from dataclasses import dataclass


@dataclass(frozen=True)
class ChartColor:
    name: str
    value: str


class ChartTheme:
    """
    Theme thống nhất cho toàn bộ Chart Framework.

    Không hard-code màu trong từng chart.
    """

    # ======================================================
    # Series Colors
    # ======================================================

    OK_COLOR = "#2E7D32"
    NG_COLOR = "#C62828"

    OUTPUT_COLOR = "#1565C0"
    PLAN_COLOR = "#7B1FA2"

    YIELD_COLOR = "#1976D2"

    OEE_COLOR = "#00897B"

    AVAILABILITY_COLOR = "#0288D1"

    PERFORMANCE_COLOR = "#F9A825"

    QUALITY_COLOR = "#43A047"

    RUNTIME_COLOR = "#3949AB"

    DOWNTIME_COLOR = "#EF6C00"

    UTILIZATION_COLOR = "#00897B"

    TARGET_COLOR = "#D81B60"

    AVERAGE_COLOR = "#5D4037"

    DEFAULT_COLOR = "#455A64"

    # ======================================================
    # KPI Status
    # ======================================================

    GOOD = "#2E7D32"

    WARNING = "#F9A825"

    DANGER = "#C62828"

    INFO = "#1976D2"

    NORMAL = "#455A64"

    # ======================================================
    # Background
    # ======================================================

    FIGURE_BACKGROUND = "#FFFFFF"

    AXES_BACKGROUND = "#FFFFFF"

    CARD_BACKGROUND = "#FFFFFF"

    GRID_COLOR = "#CFD8DC"

    BORDER_COLOR = "#CFD8DC"

    # ======================================================
    # Font
    # ======================================================

    TITLE_SIZE = 13

    LABEL_SIZE = 10

    AXIS_SIZE = 9

    LEGEND_SIZE = 9

    # ======================================================
    # Line
    # ======================================================

    LINE_WIDTH = 2.0

    MARKER_SIZE = 6

    GRID_ALPHA = 0.30

    GRID_STYLE = "--"

    # ======================================================
    # Padding
    # ======================================================

    TITLE_PADDING = 14

    X_MARGIN = 0.02

    Y_MARGIN = 0.08

    # ======================================================
    # Lookup
    # ======================================================

    _SERIES = {

        "OK": OK_COLOR,

        "OK QTY": OK_COLOR,

        "GOOD": OK_COLOR,

        "NG": NG_COLOR,

        "NG QTY": NG_COLOR,

        "DEFECT": NG_COLOR,

        "OUTPUT": OUTPUT_COLOR,

        "TOTAL": OUTPUT_COLOR,

        "TOTAL QTY": OUTPUT_COLOR,

        "PLAN": PLAN_COLOR,

        "ACTUAL": OUTPUT_COLOR,

        "YIELD": YIELD_COLOR,

        "OEE": OEE_COLOR,

        "AVAILABILITY": AVAILABILITY_COLOR,

        "PERFORMANCE": PERFORMANCE_COLOR,

        "QUALITY": QUALITY_COLOR,

        "RUNTIME": RUNTIME_COLOR,

        "DOWNTIME": DOWNTIME_COLOR,

        "UTILIZATION": UTILIZATION_COLOR,

        "TARGET": TARGET_COLOR,

        "AVERAGE": AVERAGE_COLOR,
    }

    @classmethod
    def color_for_series(
        cls,
        name,
    ):
        """
        Trả về màu của một Series.
        """

        key = str(
            name or ""
        ).strip().upper()

        return cls._SERIES.get(
            key,
            cls.DEFAULT_COLOR,
        )

    @classmethod
    def status_color(
        cls,
        status,
    ):
        status = str(
            status or ""
        ).strip().upper()

        return {

            "GOOD": cls.GOOD,

            "WARNING": cls.WARNING,

            "DANGER": cls.DANGER,

            "INFO": cls.INFO,

            "NORMAL": cls.NORMAL,

        }.get(
            status,
            cls.NORMAL,
        )