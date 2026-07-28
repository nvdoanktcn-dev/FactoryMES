from src.security.user_context import (
    AuthenticatedUser,
)
from src.ui.main_window import MainWindow
from tests.qt_test_utils import get_test_app


def test_logout_button_emits_request(monkeypatch):
    get_test_app()
    monkeypatch.setattr(
        MainWindow,
        "open_default_page",
        lambda self: None,
    )
    window = MainWindow(
        current_user=AuthenticatedUser(
            user_id=1,
            username="admin",
            display_name="Administrator",
            role="ADMIN",
        )
    )
    emitted = []
    window.logout_requested.connect(
        lambda: emitted.append(True)
    )

    window.btn_logout.click()

    assert emitted == [True]
    assert window.btn_logout.text() == "Logout"
    window.close()
