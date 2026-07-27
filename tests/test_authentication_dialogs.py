from PySide6.QtWidgets import QDialog
from src.security.user_context import (
    AuthenticatedUser,
)
from src.services.user_authentication_service import (
    AuthenticationError,
)
from src.ui.dialogs.bootstrap_admin_dialog import (
    BootstrapAdminDialog,
)
from src.ui.dialogs.login_dialog import LoginDialog
from tests.qt_test_utils import get_test_app


class FakeAuthenticationService:
    def __init__(self):
        self.created = []
        self.closed = False

    def create_user(
        self,
        username,
        password,
        **kwargs,
    ):
        self.created.append(
            (username, password, kwargs)
        )
        return AuthenticatedUser(
            user_id=1,
            username=username,
            display_name=kwargs["display_name"],
            role=kwargs["role"],
        )

    def authenticate(self, username, password):
        if (
            username != "admin"
            or password != "correct-password"
        ):
            raise AuthenticationError(
                "Invalid username or password."
            )
        return AuthenticatedUser(
            user_id=1,
            username="admin",
            display_name="Administrator",
            role="ADMIN",
        )

    def close(self):
        self.closed = True


def test_bootstrap_dialog_creates_admin():
    get_test_app()
    service = FakeAuthenticationService()
    dialog = BootstrapAdminDialog(
        authentication_service=service
    )
    dialog.password_edit.setText(
        "correct-password"
    )
    dialog.confirm_edit.setText(
        "correct-password"
    )

    dialog.create_administrator()

    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog.created_user.role == "ADMIN"
    assert service.created[0][2]["role"] == "ADMIN"


def test_login_dialog_returns_authenticated_user():
    get_test_app()
    service = FakeAuthenticationService()
    dialog = LoginDialog(
        authentication_service=service
    )
    dialog.username_edit.setText("admin")
    dialog.password_edit.setText(
        "correct-password"
    )

    dialog.authenticate()

    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog.authenticated_user.username == "admin"


def test_login_dialog_rejects_invalid_password():
    get_test_app()
    service = FakeAuthenticationService()
    dialog = LoginDialog(
        authentication_service=service
    )
    dialog.username_edit.setText("admin")
    dialog.password_edit.setText("wrong")

    dialog.authenticate()

    assert dialog.result() != QDialog.DialogCode.Accepted
    assert "Invalid username" in (
        dialog.message_label.text()
    )


def test_injected_services_are_not_closed():
    get_test_app()
    service = FakeAuthenticationService()
    login = LoginDialog(
        authentication_service=service
    )
    setup = BootstrapAdminDialog(
        authentication_service=service
    )

    login.close()
    setup.close()

    assert service.closed is False
