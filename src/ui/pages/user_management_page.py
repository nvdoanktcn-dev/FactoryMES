from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.services.user_authentication_service import (
    UserAuthenticationService,
)
from src.ui.dialogs.user_account_dialog import (
    UserAccountDialog,
)


class UserManagementPage(QWidget):
    HEADERS = (
        "ID",
        "Username",
        "Display Name",
        "Role",
        "Active",
    )

    def __init__(
        self,
        parent=None,
        *,
        service=None,
        current_user=None,
    ):
        super().__init__(parent)
        self._owns_service = service is None
        self.service = (
            service
            or UserAuthenticationService()
        )
        self.current_user = current_user
        self.accounts = []

        self.table = QTableWidget(self)
        self.table.setColumnCount(len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(
            self.HEADERS
        )
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.add_button = QPushButton("Add User", self)
        self.edit_button = QPushButton("Edit", self)
        self.password_button = QPushButton(
            "Reset Password",
            self,
        )
        self.refresh_button = QPushButton("Refresh", self)

        buttons = QHBoxLayout()
        buttons.addWidget(self.add_button)
        buttons.addWidget(self.edit_button)
        buttons.addWidget(self.password_button)
        buttons.addStretch()
        buttons.addWidget(self.refresh_button)

        layout = QVBoxLayout(self)
        layout.addLayout(buttons)
        layout.addWidget(self.table, 1)

        self.add_button.clicked.connect(self.add_user)
        self.edit_button.clicked.connect(self.edit_user)
        self.password_button.clicked.connect(
            self.reset_password
        )
        self.refresh_button.clicked.connect(
            self.load_users
        )
        self.load_users()

    def load_users(self):
        self.accounts = list(
            self.service.list_users()
        )
        self.table.setRowCount(len(self.accounts))
        for row, account in enumerate(self.accounts):
            values = (
                account.user_id,
                account.username,
                account.display_name,
                account.role,
                "Yes" if account.is_active else "No",
            )
            for column, value in enumerate(values):
                self.table.setItem(
                    row,
                    column,
                    QTableWidgetItem(str(value)),
                )

    def selected_account(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.accounts):
            return None
        return self.accounts[row]

    def add_user(self):
        dialog = UserAccountDialog(self)
        if (
            dialog.exec()
            != QDialog.DialogCode.Accepted
        ):
            return
        values = dialog.values()
        try:
            self.service.create_user(
                values["username"],
                values["password"],
                display_name=values["display_name"],
                role=values["role"],
                is_active=values["is_active"],
            )
        except Exception as error:
            QMessageBox.warning(
                self,
                "Cannot Create User",
                str(error),
            )
            return
        self.load_users()

    def edit_user(self):
        account = self.selected_account()
        if account is None:
            return
        dialog = UserAccountDialog(
            self,
            account=account,
            protect_identity=(
                self.current_user is not None
                and account.user_id
                == self.current_user.user_id
            ),
        )
        if (
            dialog.exec()
            != QDialog.DialogCode.Accepted
        ):
            return
        values = dialog.values()
        try:
            self.service.update_user(
                account.user_id,
                display_name=values["display_name"],
                role=values["role"],
                is_active=values["is_active"],
                actor_user_id=(
                    self.current_user.user_id
                    if self.current_user is not None
                    else None
                ),
            )
        except Exception as error:
            QMessageBox.warning(
                self,
                "Cannot Update User",
                str(error),
            )
            return
        self.load_users()

    def reset_password(self):
        account = self.selected_account()
        if account is None:
            return
        password, accepted = QInputDialog.getText(
            self,
            "Reset Password",
            f"New password for {account.username}:",
            QLineEdit.Password,
        )
        if not accepted:
            return
        try:
            self.service.change_password(
                account.user_id,
                password,
            )
        except Exception as error:
            QMessageBox.warning(
                self,
                "Cannot Reset Password",
                str(error),
            )
            return
        QMessageBox.information(
            self,
            "Password Updated",
            "The password was reset successfully.",
        )

    def on_page_activated(self):
        self.load_users()

    def close_resources(self):
        if self._owns_service:
            self.service.close()
