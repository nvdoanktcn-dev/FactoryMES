from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from src.ui.pages.cnc_machine_page import CNCMachinePage
from src.ui.pages.cnc_production_log_page import (
    CNCProductionLogPage,
)


class CNCPage(QWidget):
    """
    Module CNC: Danh mục máy CNC + Log sản xuất CNC (từ file import).
    """

    def __init__(self):
        super().__init__()

        self.cnc_machine_page = CNCMachinePage()
        self.cnc_production_log_page = CNCProductionLogPage()

        self.tabs = QTabWidget()
        self.tabs.addTab(self.cnc_machine_page, "CNC Machine")
        self.tabs.addTab(
            self.cnc_production_log_page, "Production Log"
        )

        self.tabs.currentChanged.connect(self._on_tab_changed)

        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)

    def _on_tab_changed(self, index):
        del index

        current = self.tabs.currentWidget()

        refresh = getattr(current, "refresh_table", None)

        if callable(refresh):
            refresh()

    def on_page_activated(self):
        self._on_tab_changed(self.tabs.currentIndex())

    def close_resources(self):
        for page in (
            self.cnc_machine_page,
            self.cnc_production_log_page,
        ):
            service = getattr(page, "service", None)

            if service is not None and hasattr(service, "close"):
                try:
                    service.close()
                except Exception:
                    pass
