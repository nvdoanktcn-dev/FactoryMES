from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)

from src.ui.models.oee_dashboard_models import (
    OEEDashboardFilters,
)

class OEEFilterPanel(QFrame):
    """
    Panel bộ lọc dùng cho OEE Dashboard.

    Trách nhiệm:
    - Quản lý các control bộ lọc.
    - Tạo OEEDashboardFilters.
    - Phát tín hiệu Apply và Reset.
    """

    apply_requested = Signal()
    reset_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setObjectName("filterPanel")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        self._build_ui()
        self.reset_values()

    def _build_ui(self) -> None:
        layout = QGridLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(8)

        self.start_date_edit = self._create_date_edit()
        self.end_date_edit = self._create_date_edit()

        self.machine_edit = self._create_line_edit(
            "Tất cả máy"
        )
        self.employee_edit = self._create_line_edit(
            "Tất cả nhân viên"
        )

        self.shift_combo = QComboBox()
        self.shift_combo.addItems(
            [
                "Tất cả",
                "DAY",
                "NIGHT",
            ]
        )

        self.work_order_edit = self._create_line_edit(
            "Tất cả Work Order"
        )
        self.product_edit = self._create_line_edit(
            "Tất cả sản phẩm"
        )
        self.operation_edit = self._create_line_edit(
            "Ví dụ: OP1 hoặc 1"
        )

        self.apply_button = QPushButton("Áp dụng")
        self.reset_button = QPushButton("Đặt lại")

        self.apply_button.clicked.connect(
            self.apply_requested.emit
        )
        self.reset_button.clicked.connect(
            self.reset_requested.emit
        )

        controls = (
            ("Từ ngày", self.start_date_edit),
            ("Đến ngày", self.end_date_edit),
            ("Máy", self.machine_edit),
            ("Nhân viên", self.employee_edit),
            ("Ca", self.shift_combo),
            ("Work Order", self.work_order_edit),
            ("Sản phẩm", self.product_edit),
            ("OP", self.operation_edit),
        )

        for index, (label, widget) in enumerate(controls):
            row = index // 4
            column = (index % 4) * 2

            layout.addWidget(
                QLabel(label),
                row,
                column,
            )
            layout.addWidget(
                widget,
                row,
                column + 1,
            )

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.apply_button)

        layout.addLayout(
            button_layout,
            2,
            0,
            1,
            8,
        )

        for column in range(8):
            layout.setColumnStretch(column, 1)

    @staticmethod
    def _create_date_edit() -> QDateEdit:
        edit = QDateEdit()
        edit.setCalendarPopup(True)
        edit.setDisplayFormat("dd/MM/yyyy")
        return edit

    @staticmethod
    def _create_line_edit(
        placeholder: str,
    ) -> QLineEdit:
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        return edit

    def reset_values(self) -> None:
        """
        Đặt bộ lọc về tháng hiện tại.
        """

        today = date.today()
        first_day = today.replace(day=1)

        self.start_date_edit.setDate(
            QDate(
                first_day.year,
                first_day.month,
                first_day.day,
            )
        )
        self.end_date_edit.setDate(
            QDate(
                today.year,
                today.month,
                today.day,
            )
        )

        self.machine_edit.clear()
        self.employee_edit.clear()
        self.shift_combo.setCurrentIndex(0)
        self.work_order_edit.clear()
        self.product_edit.clear()
        self.operation_edit.clear()

    def filters(self) -> OEEDashboardFilters:
        shift_text = self.shift_combo.currentText()

        return OEEDashboardFilters(
            start_date=self.start_date_edit.date().toPython(),
            end_date=self.end_date_edit.date().toPython(),
            machine=self.machine_edit.text().strip() or None,
            employee=self.employee_edit.text().strip() or None,
            shift=(
                None
                if shift_text == "Tất cả"
                else shift_text
            ),
            work_order=(
                self.work_order_edit.text().strip()
                or None
            ),
            product=(
                self.product_edit.text().strip()
                or None
            ),
            operation=(
                self.operation_edit.text().strip()
                or None
            ),
        )

    def set_loading(
        self,
        loading: bool,
    ) -> None:
        self.apply_button.setDisabled(loading)
        self.reset_button.setDisabled(loading)