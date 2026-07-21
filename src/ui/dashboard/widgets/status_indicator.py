from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from src.ui.charts.chart_theme import (
    ChartTheme,
)


class StatusIndicator(QFrame):
    """
    Widget hiển thị trạng thái một subsystem.
    """

    STATUS_COLORS = {
        "ONLINE": ChartTheme.GOOD,
        "READY": ChartTheme.GOOD,
        "OK": ChartTheme.GOOD,

        "WARNING": ChartTheme.WARNING,
        "DEGRADED": ChartTheme.WARNING,

        "OFFLINE": ChartTheme.DANGER,
        "ERROR": ChartTheme.DANGER,

        "NOT_CONFIGURED": ChartTheme.NORMAL,
        "UNKNOWN": ChartTheme.NORMAL,
    }

    def __init__(
        self,
        title,
        status="UNKNOWN",
        message="",
        parent=None,
    ):
        super().__init__(parent)

        self._title = str(title or "")
        self._status = str(
            status or "UNKNOWN"
        ).strip().upper()
        self._message = str(
            message or ""
        )

        self.setObjectName(
            "DashboardStatusIndicator"
        )

        self.setMinimumHeight(74)

        self.dot_label = QLabel("●")

        self.title_label = QLabel(
            self._title
        )

        self.status_label = QLabel(
            self._status
        )

        self.message_label = QLabel(
            self._message
        )

        self._build_ui()
        self._apply_style()

    # ==========================================================
    # UI
    # ==========================================================

    def _build_ui(self):
        root_layout = QHBoxLayout(self)

        root_layout.setContentsMargins(
            12,
            8,
            12,
            8,
        )

        self.dot_label.setAlignment(
            Qt.AlignTop
        )

        self.dot_label.setStyleSheet(
            "font-size:18px;"
        )

        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)

        header_layout = QHBoxLayout()

        self.title_label.setStyleSheet(
            "font-size:12px;"
            "font-weight:bold;"
            "color:#455A64;"
        )

        self.status_label.setAlignment(
            Qt.AlignRight
        )

        header_layout.addWidget(
            self.title_label
        )

        header_layout.addStretch()

        header_layout.addWidget(
            self.status_label
        )

        self.message_label.setWordWrap(True)

        self.message_label.setStyleSheet(
            "font-size:10px;"
            "color:#78909C;"
        )

        content_layout.addLayout(
            header_layout
        )

        content_layout.addWidget(
            self.message_label
        )

        root_layout.addWidget(
            self.dot_label
        )

        root_layout.addLayout(
            content_layout,
            1,
        )

    # ==========================================================
    # Public API
    # ==========================================================

    def set_status(
        self,
        status,
        message=None,
    ):
        self._status = str(
            status or "UNKNOWN"
        ).strip().upper()

        self.status_label.setText(
            self._status
        )

        if message is not None:
            self._message = str(
                message or ""
            )

            self.message_label.setText(
                self._message
            )

        self._apply_style()

    def set_title(
        self,
        title,
    ):
        self._title = str(
            title or ""
        )

        self.title_label.setText(
            self._title
        )

    # ==========================================================
    # Style
    # ==========================================================

    def _apply_style(self):
        color = self.STATUS_COLORS.get(
            self._status,
            ChartTheme.NORMAL,
        )

        self.dot_label.setStyleSheet(
            f"font-size:18px;"
            f"color:{color};"
        )

        self.status_label.setStyleSheet(
            f"font-size:11px;"
            f"font-weight:bold;"
            f"color:{color};"
        )

        self.setStyleSheet(f"""
            QFrame#DashboardStatusIndicator {{
                background: #FFFFFF;
                border: 1px solid {ChartTheme.BORDER_COLOR};
                border-radius: 7px;
            }}
        """)