from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from src.services.user_authentication_service import (
    AuthenticationError,
    UserAuthenticationService,
)


class LoginDialog(QDialog):
    def __init__(
        self,
        parent=None,
        *,
        authentication_service=None,
    ):
        super().__init__(parent)
        self._owns_service = (
            authentication_service is None
        )
        self.authentication_service = (
            authentication_service
            or UserAuthenticationService()
        )
        self.authenticated_user = None

        self.setWindowTitle("FactoryMES Login")
        self.setModal(True)
        self.setMinimumWidth(420)

        self.username_edit = QLineEdit(self)
        self.password_edit = QLineEdit(self)
        self.password_edit.setEchoMode(
            QLineEdit.Password
        )
        self.message_label = QLabel(self)
        self.message_label.setStyleSheet(
            "color:#C62828;"
        )
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok
            | QDialogButtonBox.Cancel,
            parent=self,
        )
        self.buttons.button(
            QDialogButtonBox.Ok
        ).setText("Login")

        form = QFormLayout()
        form.addRow("Username", self.username_edit)
        form.addRow("Password", self.password_edit)

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                "<b>Sign in to FactoryMES</b>",
                self,
            )
        )
        layout.addLayout(form)
        layout.addWidget(self.message_label)
        layout.addWidget(self.buttons)

        self.buttons.accepted.connect(
            self.authenticate
        )
        self.buttons.rejected.connect(
            self.reject
        )
        self.password_edit.returnPressed.connect(
            self.authenticate
        )

    def authenticate(self) -> None:
        try:
            self.authenticated_user = (
                self.authentication_service
                .authenticate(
                    self.username_edit.text(),
                    self.password_edit.text(),
                )
            )
        except AuthenticationError as error:
            self.password_edit.clear()
            self.message_label.setText(str(error))
            self.password_edit.setFocus()
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                "Login Error",
                str(error),
            )
            return
        self.accept()

    def closeEvent(self, event) -> None:
        if self._owns_service:
            self.authentication_service.close()
        super().closeEvent(event)
