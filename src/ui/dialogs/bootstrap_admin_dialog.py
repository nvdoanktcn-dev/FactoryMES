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
    UserAuthenticationService,
)


class BootstrapAdminDialog(QDialog):
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
        self.created_user = None

        self.setWindowTitle(
            "FactoryMES Initial Administrator"
        )
        self.setModal(True)
        self.setMinimumWidth(480)

        self.username_edit = QLineEdit("admin", self)
        self.display_name_edit = QLineEdit(
            "Administrator",
            self,
        )
        self.password_edit = QLineEdit(self)
        self.confirm_edit = QLineEdit(self)
        self.password_edit.setEchoMode(
            QLineEdit.Password
        )
        self.confirm_edit.setEchoMode(
            QLineEdit.Password
        )

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Save
            | QDialogButtonBox.Cancel,
            parent=self,
        )
        self.buttons.button(
            QDialogButtonBox.Save
        ).setText("Create Administrator")

        form = QFormLayout()
        form.addRow("Username", self.username_edit)
        form.addRow(
            "Display name",
            self.display_name_edit,
        )
        form.addRow("Password", self.password_edit)
        form.addRow(
            "Confirm password",
            self.confirm_edit,
        )

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                "No user account exists. Create the first "
                "administrator account.",
                self,
            )
        )
        layout.addLayout(form)
        layout.addWidget(self.buttons)

        self.buttons.accepted.connect(
            self.create_administrator
        )
        self.buttons.rejected.connect(
            self.reject
        )

    def create_administrator(self) -> None:
        password = self.password_edit.text()
        if password != self.confirm_edit.text():
            QMessageBox.warning(
                self,
                "Invalid Password",
                "Password confirmation does not match.",
            )
            self.confirm_edit.clear()
            self.confirm_edit.setFocus()
            return
        try:
            self.created_user = (
                self.authentication_service.create_user(
                    self.username_edit.text(),
                    password,
                    display_name=(
                        self.display_name_edit.text()
                    ),
                    role="ADMIN",
                )
            )
        except Exception as error:
            QMessageBox.warning(
                self,
                "Cannot Create Administrator",
                str(error),
            )
            return
        self.accept()

    def closeEvent(self, event) -> None:
        if self._owns_service:
            self.authentication_service.close()
        super().closeEvent(event)
