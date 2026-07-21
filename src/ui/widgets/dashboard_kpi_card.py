from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
)


class DashboardKPICard(QFrame):
    """
    Card hiển thị một KPI trên Dashboard.
    """

    STATUS_COLORS = {
        "NORMAL": "#1565C0",
        "GOOD": "#2E7D32",
        "WARNING": "#EF6C00",
        "DANGER": "#C62828",
        "NEUTRAL": "#455A64",
    }

    def __init__(
        self,
        title,
        value="0",
        unit="",
        parent=None,
    ):
        super().__init__(parent)

        self._title = str(title)
        self._value = str(value)
        self._unit = str(unit)
        self._status = "NORMAL"

        self.setObjectName(
            "DashboardKPICard"
        )

        self.setMinimumWidth(170)
        self.setMinimumHeight(115)

        self.title_label = QLabel(
            self._title
        )

        self.value_label = QLabel(
            self._value
        )

        self.unit_label = QLabel(
            self._unit
        )

        self.build_ui()
        self.apply_style()

    def build_ui(self):
        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            14,
            12,
            14,
            12,
        )

        self.title_label.setAlignment(
            Qt.AlignCenter
        )

        self.title_label.setStyleSheet(
            "font-size:13px;"
            "font-weight:600;"
            "color:#546E7A;"
        )

        self.value_label.setAlignment(
            Qt.AlignCenter
        )

        self.value_label.setStyleSheet(
            "font-size:28px;"
            "font-weight:bold;"
        )

        self.unit_label.setAlignment(
            Qt.AlignCenter
        )

        self.unit_label.setStyleSheet(
            "font-size:12px;"
            "color:#78909C;"
        )

        layout.addWidget(
            self.title_label
        )

        layout.addStretch()

        layout.addWidget(
            self.value_label
        )

        layout.addWidget(
            self.unit_label
        )

    def set_value(
        self,
        value,
        unit=None,
        status=None,
    ):
        if isinstance(value, float):
            value = f"{value:,.2f}"

        elif isinstance(value, int):
            value = f"{value:,}"

        self._value = str(value)

        self.value_label.setText(
            self._value
        )

        if unit is not None:
            self._unit = str(unit)
            self.unit_label.setText(
                self._unit
            )

        if status is not None:
            self.set_status(status)

    def set_title(self, title):
        self._title = str(title)

        self.title_label.setText(
            self._title
        )

    def set_status(self, status):
        status = str(
            status or "NORMAL"
        ).strip().upper()

        if status not in self.STATUS_COLORS:
            status = "NORMAL"

        self._status = status
        self.apply_style()

    def apply_style(self):
        color = self.STATUS_COLORS[
            self._status
        ]

        self.setStyleSheet(f"""
            QFrame#DashboardKPICard {{
                background: #FFFFFF;
                border: 1px solid #CFD8DC;
                border-left: 5px solid {color};
                border-radius: 8px;
            }}
        """)

        self.value_label.setStyleSheet(
            f"font-size:28px;"
            f"font-weight:bold;"
            f"color:{color};"
        )