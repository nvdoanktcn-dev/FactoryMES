from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from src.ui.pages.robot_operation_log_page import (
    RobotOperationLogPage,
)
from src.ui.pages.robot_page import RobotPage


class RobotModulePage(QWidget):
    """
    Module Robot: Danh mục Robot + Log vận hành.
    """

    def __init__(self):
        super().__init__()

        self.robot_page = RobotPage()
        self.robot_operation_log_page = RobotOperationLogPage()

        self.tabs = QTabWidget()
        self.tabs.addTab(self.robot_page, "Robot")
        self.tabs.addTab(
            self.robot_operation_log_page, "Operation Log"
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
            self.robot_page,
            self.robot_operation_log_page,
        ):
            close_resources = getattr(
                page, "close_resources", None
            )

            if callable(close_resources):
                try:
                    close_resources()
                except Exception:
                    pass
                continue

            service = getattr(page, "service", None)

            if service is not None and hasattr(service, "close"):
                try:
                    service.close()
                except Exception:
                    pass
