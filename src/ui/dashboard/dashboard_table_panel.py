from PySide6.QtWidgets import (
    QGroupBox,
    QTabWidget,
    QVBoxLayout,
)

from src.ui.dashboard.tables.alarm_table import (
    AlarmTable,
)
from src.ui.dashboard.tables.import_history_table import (
    ImportHistoryTable,
)
from src.ui.dashboard.tables.recent_production_table import (
    RecentProductionTable,
)


class DashboardTablePanel(QGroupBox):
    """
    Panel bảng dữ liệu Dashboard.

    Bao gồm:
    - Recent Production
    - Import History
    - Alarm / Validation
    """

    DEFAULT_LIMIT = 20

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(
            "Recent Activity",
            parent,
        )

        self.recent_production_table = (
            RecentProductionTable()
        )

        self.import_history_table = (
            ImportHistoryTable()
        )

        self.alarm_table = AlarmTable()

        self.tabs = QTabWidget()

        self._build_ui()

    # ==========================================================
    # UI
    # ==========================================================

    def _build_ui(self):
        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            10,
            12,
            10,
            10,
        )

        self.tabs.addTab(
            self.recent_production_table,
            "Recent Production",
        )

        self.tabs.addTab(
            self.import_history_table,
            "Import History",
        )

        self.tabs.addTab(
            self.alarm_table,
            "Alarm / Validation",
        )

        layout.addWidget(
            self.tabs
        )

    # ==========================================================
    # Update
    # ==========================================================

    def update_data(
        self,
        analytics,
    ):
        production_records = list(
            self._section(
                analytics,
                "records",
                [],
            )
            or []
        )

        import_history = list(
            self._section(
                analytics,
                "import_history",
                [],
            )
            or []
        )

        alarms = list(
            self._section(
                analytics,
                "alarms",
                [],
            )
            or []
        )

        self.recent_production_table.set_records(
            production_records[
                :self.DEFAULT_LIMIT
            ]
        )

        self.import_history_table.set_records(
            import_history[
                :self.DEFAULT_LIMIT
            ]
        )

        self.alarm_table.set_records(
            alarms[
                :self.DEFAULT_LIMIT
            ]
        )

        self.tabs.setTabText(
            0,
            (
                "Recent Production "
                f"({len(production_records)})"
            ),
        )

        self.tabs.setTabText(
            1,
            (
                "Import History "
                f"({len(import_history)})"
            ),
        )

        self.tabs.setTabText(
            2,
            (
                "Alarm / Validation "
                f"({len(alarms)})"
            ),
        )

    def clear_data(self):
        self.recent_production_table.clear_records()
        self.import_history_table.clear_records()
        self.alarm_table.clear_records()

        self.tabs.setTabText(
            0,
            "Recent Production (0)",
        )

        self.tabs.setTabText(
            1,
            "Import History (0)",
        )

        self.tabs.setTabText(
            2,
            "Alarm / Validation (0)",
        )

    def set_loading(
        self,
        loading,
    ):
        self.tabs.setEnabled(
            not loading
        )

    # ==========================================================
    # Helpers
    # ==========================================================

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