from datetime import datetime

from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
)

from src.ui.dashboard.widgets.status_indicator import (
    StatusIndicator,
)


class DashboardStatusPanel(QGroupBox):
    """
    Panel trạng thái hệ thống Dashboard.
    """

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(
            "System Status",
            parent,
        )

        self.database_status = (
            StatusIndicator(
                title="Database"
            )
        )

        self.analytics_status = (
            StatusIndicator(
                title="Analytics"
            )
        )

        self.dashboard_status = (
            StatusIndicator(
                title="Dashboard"
            )
        )

        self.plc_status = (
            StatusIndicator(
                title="PLC / OPC-UA"
            )
        )

        self.shift_value = QLabel("-")
        self.last_refresh_value = QLabel("-")
        self.version_value = QLabel("-")

        self._build_ui()

    # ==========================================================
    # UI
    # ==========================================================

    def _build_ui(self):
        root_layout = QVBoxLayout(self)

        status_layout = QGridLayout()

        status_layout.addWidget(
            self.database_status,
            0,
            0,
        )

        status_layout.addWidget(
            self.analytics_status,
            0,
            1,
        )

        status_layout.addWidget(
            self.dashboard_status,
            1,
            0,
        )

        status_layout.addWidget(
            self.plc_status,
            1,
            1,
        )

        status_layout.setColumnStretch(
            0,
            1,
        )

        status_layout.setColumnStretch(
            1,
            1,
        )

        footer_layout = QGridLayout()

        footer_layout.addWidget(
            QLabel("Current Shift"),
            0,
            0,
        )

        footer_layout.addWidget(
            self.shift_value,
            0,
            1,
        )

        footer_layout.addWidget(
            QLabel("Last Refresh"),
            0,
            2,
        )

        footer_layout.addWidget(
            self.last_refresh_value,
            0,
            3,
        )

        footer_layout.addWidget(
            QLabel("Version"),
            0,
            4,
        )

        footer_layout.addWidget(
            self.version_value,
            0,
            5,
        )

        for label in (
            self.shift_value,
            self.last_refresh_value,
            self.version_value,
        ):
            label.setStyleSheet(
                "font-weight:bold;"
                "color:#37474F;"
            )

        root_layout.addLayout(
            status_layout
        )

        root_layout.addLayout(
            footer_layout
        )

    # ==========================================================
    # Update
    # ==========================================================

    def update_status(
        self,
        data,
    ):
        status_data = self._extract_status(
            data
        )

        database = self._section(
            status_data,
            "database",
            {},
        )

        analytics = self._section(
            status_data,
            "analytics",
            {},
        )

        dashboard = self._section(
            status_data,
            "dashboard",
            {},
        )

        plc = self._section(
            status_data,
            "plc",
            {},
        )

        self.database_status.set_status(
            self._value(
                database,
                "status",
                "UNKNOWN",
            ),
            self._value(
                database,
                "message",
                "",
            ),
        )

        self.analytics_status.set_status(
            self._value(
                analytics,
                "status",
                "UNKNOWN",
            ),
            self._value(
                analytics,
                "message",
                "",
            ),
        )

        self.dashboard_status.set_status(
            self._value(
                dashboard,
                "status",
                "UNKNOWN",
            ),
            self._value(
                dashboard,
                "message",
                "",
            ),
        )

        self.plc_status.set_status(
            self._value(
                plc,
                "status",
                "NOT_CONFIGURED",
            ),
            self._value(
                plc,
                "message",
                "",
            ),
        )

        self.shift_value.setText(
            str(
                self._value(
                    status_data,
                    "current_shift",
                    "-",
                )
            )
        )

        last_check = self._value(
            status_data,
            "last_check",
            None,
        )

        self.last_refresh_value.setText(
            self._format_datetime(
                last_check
            )
        )

        self.version_value.setText(
            str(
                self._value(
                    status_data,
                    "version",
                    "-",
                )
            )
        )

    def set_loading(
        self,
        loading,
    ):
        if loading:
            self.dashboard_status.set_status(
                "WARNING",
                "Dashboard is refreshing...",
            )
        else:
            self.dashboard_status.set_status(
                "ONLINE",
                "Dashboard ready.",
            )

    def set_error(
        self,
        message,
    ):
        self.dashboard_status.set_status(
            "ERROR",
            str(message),
        )

    # ==========================================================
    # Helpers
    # ==========================================================

    @staticmethod
    def _extract_status(data):
        if data is None:
            return {}

        if isinstance(data, dict):
            return data.get(
                "system_status",
                data,
            )

        return getattr(
            data,
            "system_status",
            data,
        )

    @staticmethod
    def _section(
        source,
        field_name,
        default,
    ):
        if source is None:
            return default

        if isinstance(source, dict):
            return source.get(
                field_name,
                default,
            )

        return getattr(
            source,
            field_name,
            default,
        )

    @staticmethod
    def _value(
        source,
        field_name,
        default,
    ):
        if source is None:
            return default

        if isinstance(source, dict):
            value = source.get(
                field_name,
                default,
            )

        else:
            value = getattr(
                source,
                field_name,
                default,
            )

        return (
            default
            if value is None
            else value
        )

    @staticmethod
    def _format_datetime(value):
        if value is None:
            return "-"

        if isinstance(value, datetime):
            return value.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        return str(value)