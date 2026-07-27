from __future__ import annotations

import os
from unittest.mock import patch

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

from PySide6.QtWidgets import QApplication, QWidget

import src.ui.pages.cnc_page as cnc_module
import src.ui.pages.inventory_page as inventory_module
import src.ui.pages.robot_module_page as robot_module


def get_application() -> QApplication:
    application = QApplication.instance()

    if application is None:
        application = QApplication([])

    return application


class FakeService:
    def __init__(self) -> None:
        self.close_count = 0

    def close(self) -> None:
        self.close_count += 1


class FakeChildPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.service = FakeService()
        self.refresh_count = 0
        self.close_resources_count = 0

    def refresh_table(self) -> None:
        self.refresh_count += 1

    def close_resources(self) -> None:
        self.close_resources_count += 1


def dispose_widget(widget: QWidget) -> None:
    widget.close()
    widget.deleteLater()


def test_cnc_page_builds_tabs_refreshes_and_closes_services() -> None:
    get_application()

    machine_page = FakeChildPage()
    production_log_page = FakeChildPage()

    with (
        patch.object(
            cnc_module,
            "CNCMachinePage",
            return_value=machine_page,
        ),
        patch.object(
            cnc_module,
            "CNCProductionLogPage",
            return_value=production_log_page,
        ),
    ):
        page = cnc_module.CNCPage()

    try:
        assert page.tabs.count() == 2
        assert page.tabs.tabText(0) == "CNC Machine"
        assert page.tabs.tabText(1) == "Production Log"
        assert page.tabs.widget(0) is machine_page
        assert page.tabs.widget(1) is production_log_page

        page.on_page_activated()
        assert machine_page.refresh_count == 1

        page.tabs.setCurrentIndex(1)
        assert production_log_page.refresh_count == 1

        page.close_resources()
        assert machine_page.service.close_count == 1
        assert production_log_page.service.close_count == 1

    finally:
        dispose_widget(page)


def test_robot_page_builds_tabs_refreshes_and_closes_children() -> None:
    get_application()

    robot_page = FakeChildPage()
    operation_log_page = FakeChildPage()

    with (
        patch.object(
            robot_module,
            "RobotPage",
            return_value=robot_page,
        ),
        patch.object(
            robot_module,
            "RobotOperationLogPage",
            return_value=operation_log_page,
        ),
    ):
        page = robot_module.RobotModulePage()

    try:
        assert page.tabs.count() == 2
        assert page.tabs.tabText(0) == "Robot"
        assert page.tabs.tabText(1) == "Operation Log"
        assert page.tabs.widget(0) is robot_page
        assert page.tabs.widget(1) is operation_log_page

        page.on_page_activated()
        assert robot_page.refresh_count == 1

        page.tabs.setCurrentIndex(1)
        assert operation_log_page.refresh_count == 1

        page.close_resources()
        assert robot_page.close_resources_count == 1
        assert operation_log_page.close_resources_count == 1

        # close_resources() của child được ưu tiên, không đóng service lần hai.
        assert robot_page.service.close_count == 0
        assert operation_log_page.service.close_count == 0

    finally:
        dispose_widget(page)


def test_inventory_page_builds_all_three_tabs() -> None:
    get_application()

    stock_in_page = FakeChildPage()
    stock_out_page = FakeChildPage()
    finished_inventory_page = FakeChildPage()

    with (
        patch.object(
            inventory_module,
            "StockInPage",
            return_value=stock_in_page,
        ),
        patch.object(
            inventory_module,
            "StockOutPage",
            return_value=stock_out_page,
        ),
        patch.object(
            inventory_module,
            "FinishedInventoryPage",
            return_value=finished_inventory_page,
        ),
    ):
        page = inventory_module.InventoryPage()

    try:
        assert page.tabs.count() == 3
        assert [
            page.tabs.tabText(index)
            for index in range(page.tabs.count())
        ] == [
            "Stock In",
            "Stock Out",
            "Finished Inventory",
        ]
        assert page.tabs.widget(0) is stock_in_page
        assert page.tabs.widget(1) is stock_out_page
        assert page.tabs.widget(2) is finished_inventory_page

    finally:
        dispose_widget(page)


def test_inventory_page_refreshes_active_tab_and_closes_services() -> None:
    get_application()

    stock_in_page = FakeChildPage()
    stock_out_page = FakeChildPage()
    finished_inventory_page = FakeChildPage()

    with (
        patch.object(
            inventory_module,
            "StockInPage",
            return_value=stock_in_page,
        ),
        patch.object(
            inventory_module,
            "StockOutPage",
            return_value=stock_out_page,
        ),
        patch.object(
            inventory_module,
            "FinishedInventoryPage",
            return_value=finished_inventory_page,
        ),
    ):
        page = inventory_module.InventoryPage()

    try:
        page.on_page_activated()
        assert stock_in_page.refresh_count == 1

        page.tabs.setCurrentIndex(1)
        page.tabs.setCurrentIndex(2)

        assert stock_out_page.refresh_count == 1
        assert finished_inventory_page.refresh_count == 1

        page.close_resources()

        assert stock_in_page.service.close_count == 1
        assert stock_out_page.service.close_count == 1
        assert (
            finished_inventory_page
            .service
            .close_count
            == 1
        )

    finally:
        dispose_widget(page)
