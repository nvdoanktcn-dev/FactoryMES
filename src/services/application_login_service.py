from __future__ import annotations

from PySide6.QtWidgets import QDialog

from src.services.user_authentication_service import (
    UserAuthenticationService,
)
from src.ui.dialogs.bootstrap_admin_dialog import (
    BootstrapAdminDialog,
)
from src.ui.dialogs.login_dialog import LoginDialog


class ApplicationLoginService:
    def __init__(
        self,
        authentication_service=None,
    ):
        self._owns_service = (
            authentication_service is None
        )
        self.authentication_service = (
            authentication_service
            or UserAuthenticationService()
        )

    def request_user(self, parent=None):
        if not self.authentication_service.has_users():
            setup = BootstrapAdminDialog(
                parent,
                authentication_service=(
                    self.authentication_service
                ),
            )
            if setup.exec() != QDialog.DialogCode.Accepted:
                return None

        login = LoginDialog(
            parent,
            authentication_service=(
                self.authentication_service
            ),
        )
        if login.exec() != QDialog.DialogCode.Accepted:
            return None
        return login.authenticated_user

    def close(self) -> None:
        if self._owns_service:
            self.authentication_service.close()
