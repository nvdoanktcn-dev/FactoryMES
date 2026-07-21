from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
)


class WarningPanel(QFrame):
    """
    Hiển thị Validation Error và Warning
    của Production Engine.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("WarningPanel")

        self.title_label = QLabel(
            "Validation Result"
        )

        self.title_label.setStyleSheet(
            "font-size:15px;"
            "font-weight:bold;"
        )

        self.message_layout = QVBoxLayout()

        self.build_ui()
        self.clear_messages()

    def build_ui(self):
        root_layout = QVBoxLayout(self)

        root_layout.addWidget(
            self.title_label
        )

        root_layout.addLayout(
            self.message_layout
        )

    def clear_messages(self):
        self._clear_layout()

        label = QLabel(
            "No validation result."
        )

        label.setStyleSheet(
            "color:#607D8B;"
        )

        self.message_layout.addWidget(
            label
        )

        self.setStyleSheet("""
            QFrame#WarningPanel {
                border: 1px solid #CFD8DC;
                border-radius: 8px;
                background: #FAFAFA;
            }
        """)

    def set_engine_result(
        self,
        engine_result,
    ):
        self._clear_layout()

        if engine_result is None:
            self.clear_messages()
            return

        errors = list(
            engine_result.errors
        )

        warnings = list(
            engine_result.warnings
        )

        if not errors and not warnings:
            label = QLabel(
                "✓ Production Entry is valid."
            )

            label.setStyleSheet(
                "color:#2E7D32;"
                "font-weight:bold;"
            )

            self.message_layout.addWidget(
                label
            )

            self.setStyleSheet("""
                QFrame#WarningPanel {
                    border: 1px solid #81C784;
                    border-radius: 8px;
                    background: #E8F5E9;
                }
            """)

            return

        for issue in errors:
            self.add_issue(
                prefix="✖",
                code=issue.code,
                message=issue.message,
                color="#C62828",
            )

        for warning in warnings:
            self.add_issue(
                prefix="⚠",
                code=warning.code,
                message=warning.message,
                color="#EF6C00",
            )

        if errors:
            background = "#FFEBEE"
            border = "#E57373"

        else:
            background = "#FFF8E1"
            border = "#FFB74D"

        self.setStyleSheet(f"""
            QFrame#WarningPanel {{
                border: 1px solid {border};
                border-radius: 8px;
                background: {background};
            }}
        """)

    def add_issue(
        self,
        prefix,
        code,
        message,
        color,
    ):
        label = QLabel(
            f"{prefix} [{code}] {message}"
        )

        label.setWordWrap(True)

        label.setStyleSheet(
            f"color:{color};"
            "font-weight:bold;"
        )

        self.message_layout.addWidget(
            label
        )

    def _clear_layout(self):
        while (
            self.message_layout.count()
        ):
            item = (
                self.message_layout
                .takeAt(0)
            )

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()