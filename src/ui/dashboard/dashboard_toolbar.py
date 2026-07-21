import logging
from datetime import date

from PySide6.QtCore import (
    QDate,
    QTimer,
    Signal,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QWidget,
)

from src.services.dashboard import DashboardRequest

logger = logging.getLogger(__name__)


class DashboardToolbar(QFrame):
    """Thanh lọc và điều khiển Dashboard."""

    refresh_requested = Signal(object)
    filters_changed = Signal(object)
    auto_refresh_changed = Signal(bool, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DashboardToolbar")

        self.start_date_edit = QDateEdit()
        self.end_date_edit = QDateEdit()

        self.shift_combo = QComboBox()
        self.machine_combo = QComboBox()
        self.work_order_combo = QComboBox()
        self.employee_combo = QComboBox()
        self.product_combo = QComboBox()

        self.btn_today = QPushButton("Today")
        self.btn_this_month = QPushButton("This Month")
        self.btn_clear = QPushButton("Clear Filters")
        self.btn_refresh = QPushButton("Refresh")

        self.auto_refresh_check = QCheckBox("Auto Refresh")
        self.refresh_interval = QSpinBox()
        self.auto_refresh_timer = QTimer(self)

        self._configure_widgets()
        self._build_ui()
        self._connect_events()
        self._apply_style()
        self.select_this_month(emit_refresh=False)

    def _configure_widgets(self):
        for date_edit in (self.start_date_edit, self.end_date_edit):
            date_edit.setCalendarPopup(True)
            date_edit.setDisplayFormat("yyyy-MM-dd")
            date_edit.setMinimumWidth(125)
            date_edit.setMaximumWidth(150)

        self.shift_combo.addItem("All Shifts", "")
        self.shift_combo.addItem("Day Shift", "DAY")
        self.shift_combo.addItem("Night Shift", "NIGHT")
        self.shift_combo.setMinimumWidth(120)
        self.shift_combo.setMaximumWidth(180)

        self._initialize_filter_combo(self.machine_combo, "All Machines")
        self._initialize_filter_combo(self.work_order_combo, "All Work Orders")
        self._initialize_filter_combo(self.employee_combo, "All Employees")
        self._initialize_filter_combo(self.product_combo, "All Products")

        self.btn_today.setMinimumWidth(72)
        self.btn_this_month.setMinimumWidth(96)
        self.btn_clear.setMinimumWidth(105)
        self.btn_refresh.setMinimumWidth(86)
        self.auto_refresh_check.setMinimumWidth(105)

        # Tránh Qt tự gán "default button" (khiến 1 nút bị vẽ
        # khác các nút còn lại tuỳ theo theme/OS).
        for button in (
            self.btn_today,
            self.btn_this_month,
            self.btn_clear,
            self.btn_refresh,
        ):
            button.setAutoDefault(False)
            button.setDefault(False)

        self.refresh_interval.setRange(10, 3600)
        self.refresh_interval.setValue(60)
        self.refresh_interval.setSuffix(" sec")
        self.refresh_interval.setMinimumWidth(88)
        self.refresh_interval.setMaximumWidth(105)
        self.refresh_interval.setEnabled(False)
        self.auto_refresh_timer.setSingleShot(False)

    @staticmethod
    def _initialize_filter_combo(combo, placeholder):
        combo.clear()
        combo.addItem(placeholder, "")
        combo.setMinimumWidth(120)
        combo.setMaximumWidth(220)
        combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def _build_ui(self):
        root_layout = QGridLayout(self)
        root_layout.setContentsMargins(12, 10, 12, 10)
        root_layout.setHorizontalSpacing(10)
        root_layout.setVerticalSpacing(8)

        date_row = QWidget(self)
        date_layout = QHBoxLayout(date_row)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(8)

        from_label = QLabel("From")
        to_label = QLabel("To")
        from_label.setMinimumWidth(36)
        to_label.setMinimumWidth(20)

        date_layout.addWidget(from_label)
        date_layout.addWidget(self.start_date_edit)
        date_layout.addWidget(to_label)
        date_layout.addWidget(self.end_date_edit)
        date_layout.addWidget(self.btn_today)
        date_layout.addWidget(self.btn_this_month)
        date_layout.addStretch()

        filter_row = QWidget(self)
        filter_layout = QHBoxLayout(filter_row)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(8)

        for combo in (
            self.shift_combo,
            self.machine_combo,
            self.work_order_combo,
            self.employee_combo,
            self.product_combo,
        ):
            filter_layout.addWidget(combo, 1)

        filter_layout.addSpacing(6)
        filter_layout.addWidget(self.auto_refresh_check)
        filter_layout.addWidget(self.refresh_interval)
        filter_layout.addWidget(self.btn_clear)
        filter_layout.addWidget(self.btn_refresh)

        root_layout.addWidget(date_row, 0, 0)
        root_layout.addWidget(filter_row, 1, 0)
        root_layout.setColumnStretch(0, 1)

    def _apply_style(self):
        self.setMinimumHeight(112)
        self.setStyleSheet("""
            QFrame#DashboardToolbar {
                background: #FFFFFF;
                border: 1px solid #CFD8DC;
                border-radius: 8px;
            }
            QLabel { color: #37474F; }
            QComboBox, QDateEdit, QSpinBox {
                min-height: 30px;
                padding: 2px 7px;
            }

            /* Ô "xx sec" (refresh_interval) - làm rõ 2 nút tăng/giảm */
            QSpinBox {
                padding-right: 2px;
                border: 1px solid #CFD8DC;
                border-radius: 6px;
                background: #FFFFFF;
            }
            QSpinBox:disabled {
                background: #F4F6F8;
                color: #B0BEC5;
            }
            QSpinBox::up-button,
            QSpinBox::down-button {
                width: 20px;
                border-left: 1px solid #CFD8DC;
                background: #ECEFF1;
            }
            QSpinBox::up-button {
                subcontrol-position: top right;
                border-top-right-radius: 6px;
                border-bottom: 1px solid #CFD8DC;
            }
            QSpinBox::down-button {
                subcontrol-position: bottom right;
                border-bottom-right-radius: 6px;
            }
            QSpinBox::up-button:hover,
            QSpinBox::down-button:hover {
                background: #CFD8DC;
            }
            QSpinBox::up-button:pressed,
            QSpinBox::down-button:pressed {
                background: #90A4AE;
            }
            QSpinBox::up-button:disabled,
            QSpinBox::down-button:disabled {
                background: #F4F6F8;
            }
            QSpinBox::up-arrow {
                width: 8px;
                height: 8px;
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 5px solid #455A64;
            }
            QSpinBox::down-arrow {
                width: 8px;
                height: 8px;
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #455A64;
            }
            QSpinBox::up-arrow:disabled,
            QSpinBox::down-arrow:disabled {
                border-bottom-color: #CFD8DC;
                border-top-color: #CFD8DC;
            }
            QPushButton {
                min-height: 31px;
                padding: 4px 14px;
                border: 1px solid #CFD8DC;
                border-radius: 6px;
                background: #FFFFFF;
                color: #37474F;
            }
            QPushButton:hover {
                background: #ECEFF1;
            }
            QPushButton:pressed {
                background: #CFD8DC;
            }
            QPushButton:disabled {
                color: #B0BEC5;
                background: #F4F6F8;
                border-color: #E0E4E7;
            }
            QPushButton#DashboardRefreshButton {
                font-weight: bold;
                border-color: #90A4AE;
            }
            QCheckBox { spacing: 6px; }
        """)
        self.btn_refresh.setObjectName("DashboardRefreshButton")

    def _connect_events(self):
        self.btn_refresh.clicked.connect(self.emit_refresh)
        self.btn_today.clicked.connect(self.select_today)
        self.btn_this_month.clicked.connect(self.select_this_month)
        self.btn_clear.clicked.connect(self.clear_filters)
        self.auto_refresh_check.toggled.connect(self._on_auto_refresh_toggled)
        self.refresh_interval.valueChanged.connect(self._on_interval_changed)
        self.auto_refresh_timer.timeout.connect(self.emit_refresh)
        self.start_date_edit.dateChanged.connect(self._emit_filters_changed)
        self.end_date_edit.dateChanged.connect(self._emit_filters_changed)

        for combo in (
            self.shift_combo,
            self.machine_combo,
            self.work_order_combo,
            self.employee_combo,
            self.product_combo,
        ):
            combo.currentIndexChanged.connect(self._emit_filters_changed)

    def get_filters(self):
        start_date = self.start_date_edit.date().toPython()
        end_date = self.end_date_edit.date().toPython()

        if end_date < start_date:
            raise ValueError("End Date cannot be earlier than Start Date.")

        return {
            "start_date": start_date,
            "end_date": end_date,
            "shift": self._optional_code(self._current_data(self.shift_combo)),
            "machine_code": self._optional_code(self._current_data(self.machine_combo)),
            "work_order_no": self._optional_code(self._current_data(self.work_order_combo)),
            "employee_code": self._optional_code(self._current_data(self.employee_combo)),
            "product_code": self._optional_code(self._current_data(self.product_combo)),
        }

    def get_request(self):
        filters = self.get_filters()
        return DashboardRequest(
            start_date=filters["start_date"],
            end_date=filters["end_date"],
            shift=filters.get("shift"),
            machine_code=filters.get("machine_code"),
            employee_code=filters.get("employee_code"),
            product_code=filters.get("product_code"),
            work_order_no=filters.get("work_order_no"),
            auto_refresh=self.auto_refresh_check.isChecked(),
            refresh_interval=self.refresh_interval.value(),
        )

    def request(self):
        return self.get_request()

    @staticmethod
    def _current_data(combo):
        return str(combo.currentData() or "").strip().upper()

    @staticmethod
    def _optional_code(value):
        text = str(value or "").strip().upper()
        return text or None

    def emit_refresh(self):
        try:
            request = self.get_request()
        except (TypeError, ValueError) as error:
            logger.warning(
                "DashboardToolbar.emit_refresh bị chặn do "
                "get_request() lỗi: %s",
                error,
            )
            return
        self.refresh_requested.emit(request)

    def _emit_filters_changed(self, *_):
        try:
            request = self.get_request()
        except (TypeError, ValueError) as error:
            logger.warning(
                "DashboardToolbar._emit_filters_changed bị chặn "
                "do get_request() lỗi: %s",
                error,
            )
            return
        self.filters_changed.emit(request)

    def select_today(self, emit_refresh=True):
        today = QDate.currentDate()
        self.start_date_edit.blockSignals(True)
        self.end_date_edit.blockSignals(True)
        self.start_date_edit.setDate(today)
        self.end_date_edit.setDate(today)
        self.start_date_edit.blockSignals(False)
        self.end_date_edit.blockSignals(False)
        self._emit_filters_changed()
        if emit_refresh:
            self.emit_refresh()

    def select_this_month(self, emit_refresh=True):
        today = date.today()
        self.start_date_edit.blockSignals(True)
        self.end_date_edit.blockSignals(True)
        self.start_date_edit.setDate(QDate(today.year, today.month, 1))
        self.end_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.blockSignals(False)
        self.end_date_edit.blockSignals(False)
        self._emit_filters_changed()
        if emit_refresh:
            self.emit_refresh()

    def clear_filters(self):
        for combo in (
            self.shift_combo,
            self.machine_combo,
            self.work_order_combo,
            self.employee_combo,
            self.product_combo,
        ):
            combo.blockSignals(True)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)

        self.select_this_month(emit_refresh=False)
        self._emit_filters_changed()
        self.emit_refresh()

    def _on_auto_refresh_toggled(self, enabled):
        self.refresh_interval.setEnabled(enabled)
        interval_seconds = self.refresh_interval.value()

        if enabled:
            self.auto_refresh_timer.start(interval_seconds * 1000)
        else:
            self.auto_refresh_timer.stop()

        self.auto_refresh_changed.emit(enabled, interval_seconds)
        self._emit_filters_changed()

    def _on_interval_changed(self, interval_seconds):
        if self.auto_refresh_timer.isActive():
            self.auto_refresh_timer.start(interval_seconds * 1000)

        self.auto_refresh_changed.emit(
            self.auto_refresh_check.isChecked(),
            interval_seconds,
        )
        self._emit_filters_changed()

    def set_machines(self, machines):
        self._set_combo_items(
            combo=self.machine_combo,
            placeholder="All Machines",
            items=machines,
            key_getter=lambda item: self._value_from(item, "machine_code", ""),
            text_getter=lambda item: (
                f"{self._value_from(item, 'machine_code', '')} - "
                f"{self._value_from(item, 'machine_name', '')}"
            ),
        )

    def set_work_orders(self, work_orders):
        self._set_combo_items(
            combo=self.work_order_combo,
            placeholder="All Work Orders",
            items=work_orders,
            key_getter=lambda item: self._value_from(item, "work_order_no", ""),
            text_getter=lambda item: (
                f"{self._value_from(item, 'work_order_no', '')} - "
                f"{self._value_from(item, 'product_code', '')}"
            ),
        )

    def set_employees(self, employees):
        self._set_combo_items(
            combo=self.employee_combo,
            placeholder="All Employees",
            items=employees,
            key_getter=lambda item: self._value_from(item, "employee_code", ""),
            text_getter=lambda item: (
                f"{self._value_from(item, 'employee_code', '')} - "
                f"{self._value_from(item, 'employee_name', '')}"
            ),
        )

    def set_products(self, products):
        self._set_combo_items(
            combo=self.product_combo,
            placeholder="All Products",
            items=products,
            key_getter=lambda item: self._value_from(item, "product_code", ""),
            text_getter=lambda item: (
                f"{self._value_from(item, 'product_code', '')} - "
                f"{self._product_name(item)}"
            ),
        )

    @staticmethod
    def _value_from(item, field_name, default=""):
        if isinstance(item, dict):
            value = item.get(field_name, default)
        else:
            value = getattr(item, field_name, default)
        return default if value is None else value

    @classmethod
    def _product_name(cls, item):
        for field_name in ("product_name_vi", "product_name", "name"):
            value = cls._value_from(item, field_name, "")
            if value:
                return str(value)
        return ""

    @staticmethod
    def _set_combo_items(combo, placeholder, items, key_getter, text_getter):
        current_value = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(placeholder, "")

        for item in items or []:
            key = str(key_getter(item) or "").strip().upper()
            if not key:
                continue

            text = str(text_getter(item) or key).strip()
            if text.endswith(" -"):
                text = text[:-2].strip()
            combo.addItem(text, key)

        if current_value:
            index = combo.findData(current_value)
            if index >= 0:
                combo.setCurrentIndex(index)

        combo.blockSignals(False)

    def set_loading(self, loading):
        self.btn_refresh.setEnabled(not loading)
        self.btn_clear.setEnabled(not loading)
        self.btn_refresh.setText("Loading..." if loading else "Refresh")