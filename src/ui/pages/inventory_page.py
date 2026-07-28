from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from src.ui.pages.finished_inventory_page import (
    FinishedInventoryPage,
)
from src.ui.pages.stock_in_page import StockInPage
from src.ui.pages.stock_out_page import StockOutPage


class InventoryPage(QWidget):
    """
    Module Inventory: gộp Stock In, Stock Out, Finished Inventory
    trong một trang có tab, theo đúng README (module "Inventory").

    Mỗi tab là một MasterCRUDPage độc lập với Service/Repository
    riêng; NavigationManager sẽ dispose các Service này qua
    close_resources() khi ứng dụng đóng hoặc page bị reload.
    """

    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user

        self.stock_in_page = StockInPage()
        self.stock_out_page = StockOutPage()
        self.finished_inventory_page = FinishedInventoryPage(
            current_user=current_user
        )

        self.tabs = QTabWidget()
        self.tabs.addTab(self.stock_in_page, "Stock In")
        self.tabs.addTab(self.stock_out_page, "Stock Out")
        self.tabs.addTab(
            self.finished_inventory_page, "Finished Inventory"
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
            self.stock_in_page,
            self.stock_out_page,
            self.finished_inventory_page,
        ):
            service = getattr(page, "service", None)

            if service is not None and hasattr(service, "close"):
                try:
                    service.close()
                except Exception:
                    pass
