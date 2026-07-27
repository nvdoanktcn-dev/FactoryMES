from __future__ import annotations

import os

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QStackedWidget,
    QTreeWidget,
    QWidget,
)

from src.ui.navigation.menu_manager import MenuManager
from src.ui.navigation.navigation_manager import NavigationManager


EXPECTED_PAGE_NAMES = (
    "Dashboard",
    "Master Import",
    "Product",
    "Machine",
    "Employee",
    "Routing",
    "Work Order",
    "CNC",
    "Robot",
    "Inventory",
    "Machine Utilization Report",
    "Production",
    "Production Assignment",
    "Production Execution",
    "Production Downtime",
    "Production NG",
    "OEE Dashboard",
)


def get_application() -> QApplication:
    application = QApplication.instance()

    if application is None:
        application = QApplication([])

    return application


def collect_menu_page_keys(
    tree: QTreeWidget,
) -> tuple[str, ...]:
    keys: list[str] = []

    def visit(item) -> None:
        page_key = item.data(
            0,
            Qt.UserRole,
        )

        if page_key is not None:
            keys.append(str(page_key))

        for child_index in range(
            item.childCount()
        ):
            visit(
                item.child(child_index)
            )

    root = tree.invisibleRootItem()

    for index in range(
        root.childCount()
    ):
        visit(root.child(index))

    return tuple(keys)


class LifecyclePage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.activation_count = 0
        self.close_count = 0

    def on_page_activated(self) -> None:
        self.activation_count += 1

    def close_resources(self) -> None:
        self.close_count += 1


def test_menu_and_navigation_register_the_same_pages() -> None:
    get_application()

    tree = QTreeWidget()
    stack = QStackedWidget()
    manager = NavigationManager(stack)

    try:
        MenuManager.build_menu(tree)
        manager.build_pages()

        assert manager.page_names() == EXPECTED_PAGE_NAMES
        assert set(
            collect_menu_page_keys(tree)
        ) == set(EXPECTED_PAGE_NAMES)

        # build_pages() chỉ đăng ký factory, không tạo page.
        assert manager.pages == {}
        assert stack.count() == 0

    finally:
        manager.close_all_pages()
        tree.close()
        stack.close()
        tree.deleteLater()
        stack.deleteLater()


def test_navigation_is_lazy_and_reuses_page_instance() -> None:
    get_application()

    stack = QStackedWidget()
    manager = NavigationManager(stack)
    created_pages: list[LifecyclePage] = []

    def create_page() -> LifecyclePage:
        page = LifecyclePage()
        created_pages.append(page)
        return page

    manager.register_factory(
        "Test Page",
        create_page,
    )

    try:
        assert not manager.is_page_created(
            "Test Page"
        )
        assert created_pages == []

        first_page = manager.navigate(
            "Test Page"
        )
        second_page = manager.navigate(
            "Test Page"
        )

        assert first_page is second_page
        assert len(created_pages) == 1
        assert stack.count() == 1
        assert stack.currentWidget() is first_page
        assert manager.current_page_name() == "Test Page"
        assert first_page.activation_count == 2

    finally:
        manager.close_all_pages()
        stack.close()
        stack.deleteLater()


def test_reload_disposes_old_page_and_creates_new_page() -> None:
    get_application()

    stack = QStackedWidget()
    manager = NavigationManager(stack)
    created_pages: list[LifecyclePage] = []

    def create_page() -> LifecyclePage:
        page = LifecyclePage()
        created_pages.append(page)
        return page

    manager.register_factory(
        "Reloadable",
        create_page,
    )

    try:
        old_page = manager.navigate(
            "Reloadable"
        )
        new_page = manager.reload_page(
            "Reloadable"
        )

        assert new_page is not old_page
        assert len(created_pages) == 2
        assert old_page.close_count == 1
        assert new_page.activation_count == 1
        assert manager.get_page(
            "Reloadable"
        ) is new_page
        assert stack.count() == 1

    finally:
        manager.close_all_pages()
        stack.close()
        stack.deleteLater()


def test_close_all_pages_releases_each_created_page_once() -> None:
    get_application()

    stack = QStackedWidget()
    manager = NavigationManager(stack)
    first_page = LifecyclePage()
    second_page = LifecyclePage()

    manager.register_factory(
        "First",
        lambda: first_page,
    )
    manager.register_factory(
        "Second",
        lambda: second_page,
    )

    manager.navigate("First")
    manager.navigate("Second")
    manager.close_all_pages()
    manager.close_all_pages()

    assert first_page.close_count == 1
    assert second_page.close_count == 1
    assert manager.pages == {}
    assert stack.count() == 0

    stack.close()
    stack.deleteLater()


def test_unknown_page_is_rejected_without_creating_widget() -> None:
    get_application()

    stack = QStackedWidget()
    manager = NavigationManager(stack)

    try:
        try:
            manager.navigate(
                "Missing Page"
            )
        except KeyError as error:
            assert "Missing Page" in str(error)
        else:
            raise AssertionError(
                "Unknown navigation page must raise KeyError."
            )

        assert manager.pages == {}
        assert stack.count() == 0

    finally:
        manager.close_all_pages()
        stack.close()
        stack.deleteLater()
