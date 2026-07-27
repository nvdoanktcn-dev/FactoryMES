from src.security.user_context import (
    AuthenticatedUser,
)
from src.ui.pages.user_management_page import (
    UserManagementPage,
)
from tests.qt_test_utils import get_test_app


class FakeUserService:
    def __init__(self):
        self.closed = False

    def list_users(self):
        return (
            AuthenticatedUser(
                user_id=1,
                username="admin",
                display_name="Administrator",
                role="ADMIN",
                is_active=True,
            ),
            AuthenticatedUser(
                user_id=2,
                username="viewer",
                display_name="Read Only",
                role="VIEWER",
                is_active=False,
            ),
        )

    def close(self):
        self.closed = True


def test_page_loads_user_accounts():
    get_test_app()
    service = FakeUserService()
    page = UserManagementPage(service=service)

    assert page.table.rowCount() == 2
    assert page.table.item(0, 1).text() == "admin"
    assert page.table.item(1, 3).text() == "VIEWER"
    assert page.table.item(1, 4).text() == "No"


def test_injected_service_is_not_closed():
    get_test_app()
    service = FakeUserService()
    page = UserManagementPage(service=service)

    page.close_resources()

    assert service.closed is False
