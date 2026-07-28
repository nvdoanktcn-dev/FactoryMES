from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)


class UserAccountDialog(QDialog):
    def __init__(
        self,
        parent=None,
        *,
        account=None,
        protect_identity=False,
    ):
        super().__init__(parent)
        self.account = account
        self.protect_identity = bool(
            protect_identity
        )

        self.setObjectName("UserAccountDialog")
        self.setWindowTitle(
            "Edit User" if account else "Create User"
        )
        self.setModal(True)
        self.setMinimumWidth(560)

        self.username_edit = QLineEdit(self)
        self.display_name_edit = QLineEdit(self)
        self.role_combo = QComboBox(self)
        self.role_combo.addItems([
            "ADMIN",
            "WAREHOUSE",
            "PRODUCTION",
            "VIEWER",
        ])
        self.role_combo.setCurrentText("VIEWER")

        self.active_check = QCheckBox(
            "Active",
            self,
        )
        self.active_check.setChecked(True)

        self.password_edit = QLineEdit(self)
        self.confirm_edit = QLineEdit(self)
        self.password_edit.setEchoMode(
            QLineEdit.Password
        )
        self.confirm_edit.setEchoMode(
            QLineEdit.Password
        )

        if account is not None:
            self.password_edit.setVisible(False)
            self.confirm_edit.setVisible(False)

            self.username_edit.setText(
                account.username
            )
            self.username_edit.setReadOnly(True)
            self.username_edit.setFocusPolicy(
                Qt.FocusPolicy.NoFocus
            )
            self.display_name_edit.setText(
                account.display_name
            )
            self.role_combo.setCurrentText(
                account.role
            )
            self.active_check.setChecked(
                account.is_active
            )
            if self.protect_identity:
                self.role_combo.setEnabled(False)
                self.active_check.setEnabled(False)

        fields = QWidget(self)
        fields.setObjectName("UserAccountFields")
        grid = QGridLayout(fields)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(12)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)

        self._add_row(
            grid,
            0,
            "Username",
            self.username_edit,
        )
        self._add_row(
            grid,
            1,
            "Display name",
            self.display_name_edit,
        )
        self._add_row(
            grid,
            2,
            "Role",
            self.role_combo,
        )
        self._add_row(
            grid,
            3,
            "Status",
            self.active_check,
        )

        if account is None:
            self._add_row(
                grid,
                4,
                "Password",
                self.password_edit,
            )
            self._add_row(
                grid,
                5,
                "Confirm password",
                self.confirm_edit,
            )

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Save
            | QDialogButtonBox.Cancel,
            parent=self,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(16)
        layout.addWidget(fields)
        layout.addWidget(self.buttons)

        self.setStyleSheet("""
            QDialog#UserAccountDialog {
                background: #FFFFFF;
            }

            QDialog#UserAccountDialog QLabel.UserFieldLabel {
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
                min-width: 100px;
            }

            QDialog#UserAccountDialog QLineEdit,
            QDialog#UserAccountDialog QComboBox {
                min-height: 32px;
            }
        """)

        self.buttons.accepted.connect(
            self.validate_and_accept
        )
        self.buttons.rejected.connect(self.reject)

        if account is not None:
            self.display_name_edit.setFocus()
            self.display_name_edit.selectAll()
        else:
            self.username_edit.setFocus()

    @staticmethod
    def _add_row(
        layout,
        row,
        text,
        field,
    ):
        label = QLabel(text)
        label.setProperty(
            "class",
            "UserFieldLabel",
        )
        label.setStyleSheet(
            "background: transparent;"
            "border: none;"
            "padding: 0px;"
            "margin: 0px;"
            "min-width: 100px;"
        )
        label.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(label, row, 0)
        layout.addWidget(field, row, 1)

    def validate_and_accept(self):
        if not self.username_edit.text().strip():
            QMessageBox.warning(
                self,
                "Invalid User",
                "Username is required.",
            )
            return
        if (
            self.account is None
            and self.password_edit.text()
            != self.confirm_edit.text()
        ):
            QMessageBox.warning(
                self,
                "Invalid Password",
                "Password confirmation does not match.",
            )
            return
        self.accept()

    def values(self):
        return {
            "username": self.username_edit.text().strip(),
            "display_name": (
                self.display_name_edit.text().strip()
            ),
            "role": self.role_combo.currentText(),
            "is_active": self.active_check.isChecked(),
            "password": self.password_edit.text(),
        }
