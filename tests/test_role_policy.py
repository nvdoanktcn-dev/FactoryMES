from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QStackedWidget,
    QTreeWidget,
)

from src.security.role_policy import RolePolicy
from src.security.user_context import AuthenticatedUser
from src.ui.navigation.menu_manager import MenuManager
from src.ui.navigation.navigation_manager import (
    NavigationManager,
)
from tests.qt_test_utils import get_test_app


def user(role):
    return AuthenticatedUser(
        user_id=1,
        username=role.lower(),
        display_name=role.title(),
        role=role,
    )


def menu_keys(tree):
    values = []

    def visit(item):
        key = item.data(0, Qt.UserRole)
        if key:
            values.append(str(key))
        for index in range(item.childCount()):
            visit(item.child(index))

    root = tree.invisibleRootItem()
    for index in range(root.childCount()):
        visit(root.child(index))
    return set(values)


def test_admin_has_every_page():
    assert (
        RolePolicy.allowed_pages_for(user("ADMIN"))
        == RolePolicy.ALL_PAGES
    )


def test_viewer_cannot_open_transaction_pages():
    viewer = user("VIEWER")

    assert RolePolicy.can_access(
        viewer,
        "Dashboard",
    )
    assert not RolePolicy.can_access(
        viewer,
        "Production Execution",
    )
    assert not RolePolicy.can_access(
        viewer,
        "Inventory",
    )


def test_unknown_role_falls_back_to_viewer():
    assert (
        RolePolicy.allowed_pages_for(user("UNKNOWN"))
        == RolePolicy.ROLE_PAGES["VIEWER"]
    )


def test_menu_and_navigation_use_same_role_pages():
    get_test_app()

    for role in (
        "ADMIN",
        "WAREHOUSE",
        "PRODUCTION",
        "VIEWER",
    ):
        allowed = RolePolicy.allowed_pages_for(
            user(role)
        )
        tree = QTreeWidget()
        stack = QStackedWidget()
        manager = NavigationManager(
            stack,
            allowed_pages=allowed,
        )
        try:
            MenuManager.build_menu(
                tree,
                allowed_pages=allowed,
            )
            manager.build_pages()
            assert menu_keys(tree) == allowed
            assert set(manager.page_names()) == allowed
            assert manager.pages == {}
        finally:
            manager.close_all_pages()
            tree.close()
            stack.close()
