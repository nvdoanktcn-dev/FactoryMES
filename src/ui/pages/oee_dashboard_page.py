from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol, Sequence

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDateEdit, QFileDialog, QFrame,
    QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QPushButton, QSizePolicy, QTabWidget, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from src.ui.models.oee_dashboard_models import OEEDashboardData, OEEDashboardFilters
from src.ui.controllers.oee_dashboard_flow_controller import OEEDashboardFlowController
from src.ui.widgets.top_machine_widget import MachineRow, TopMachineWidget
from src.ui.widgets.oee_filter_panel import OEEFilterPanel
from src.ui.widgets.oee_kpi_panel import KPIValueCard, OEEKPIPanel
from src.ui.widgets.oee_breakdown_panel import DEFAULT_TABLE_COLUMNS, OEEBreakdownPanel

try:
    from src.services.oee_dashboard_export_service import OEEDashboardExportService
except ImportError:
    OEEDashboardExportService = None

class DashboardControllerProtocol(Protocol):
    def load_dashboard(self, filters: OEEDashboardFilters) -> OEEDashboardData: ...

class ExportServiceProtocol(Protocol):
    def export(self, dashboard: OEEDashboardData, output_path: str | Path, *, report_title: str = "OEE Dashboard Report", generated_at: Any = None) -> Path: ...

class OEEDashboardPage(QWidget):
    """V2 OEE dashboard page with backward-compatible public API."""

    TABLE_COLUMNS = list(DEFAULT_TABLE_COLUMNS)
    REPORT_TITLE = "FactoryMES OEE Dashboard Report"

    def __init__(
        self,
        controller: DashboardControllerProtocol | None = None,
        export_service: ExportServiceProtocol | None = None,
        pareto_controller: Any | None = None,
        parent: QWidget | None = None,
        top_machine_controller: Any | None = None,
    ) -> None:
        super().__init__(parent)

        # Sử dụng cơ chế nạp an toàn, nếu thiếu sẽ tự quét đúng mục src.ui.controllers
        if controller is None:
            try:
                from src.database.database import engine
                from sqlalchemy.orm import sessionmaker
                from src.ui.controllers.oee_dashboard_controller import OEEDashboardController
                from src.services.oee_dashboard_service import OEEDashboardService 
                
                session_factory = sessionmaker(bind=engine)
                self.controller = OEEDashboardController(
                    session_factory=session_factory,
                    service_class=OEEDashboardService
                )
            except Exception as e:
                raise ValueError(
                    f"OEEDashboardPage yêu cầu một DashboardControllerProtocol hợp lệ. Lỗi khởi tạo: {e}"
                )
        else:
            self.controller = controller

        self.export_service = export_service or self._create_default_export_service()
        self.pareto_controller = pareto_controller
        self.top_machine_controller = top_machine_controller
        
        if self.top_machine_controller is None:
            class _DefaultTopMachineController:
                def __init__(self, widget):
                    self.widget = widget
                    self.rows = []
                def load(self, filters):
                    return self.rows
            self._default_top_machine_controller_factory = _DefaultTopMachineController

        self._dashboard_data: OEEDashboardData | None = None
        self._pareto_data: Any | None = None
        self._loading = False    

        self.flow_controller = OEEDashboardFlowController(
            load_dashboard=self.controller.load_dashboard,
            export_dashboard=self._export_dashboard_data,
            parent=self,
        )

        self._build_ui()
        self._bind_filter_legacy_api()
        self._bind_kpi_legacy_api()
        self._bind_breakdown_legacy_api()
        self._apply_styles()
        self._connect_flow_controller()
        self.load_data()

    def _set_loading_state(self, loading: bool) -> None:
        self._loading = loading
        self.refresh_button.setDisabled(loading)
        self.filter_panel.setDisabled(loading)
        self.export_button.setEnabled(not loading and self._dashboard_data is not None and self.export_service is not None)
        if loading:
            self.status_label.setText("Đang tải dữ liệu OEE...")

    def _bind_filter_legacy_api(self) -> None:
        self.start_date_edit = self.filter_panel.start_date_edit
        self.end_date_edit = self.filter_panel.end_date_edit
        self.machine_edit = self.filter_panel.machine_edit
        self.employee_edit = self.filter_panel.employee_edit
        self.shift_combo = self.filter_panel.shift_combo
        self.work_order_edit = self.filter_panel.work_order_edit
        self.product_edit = self.filter_panel.product_edit
        self.operation_edit = self.filter_panel.operation_edit
        self.apply_button = self.filter_panel.apply_button
        self.reset_button = self.filter_panel.reset_button

    def _bind_kpi_legacy_api(self) -> None:
        self.oee_card = self.kpi_panel.oee_card
        self.availability_card = self.kpi_panel.availability_card
        self.performance_card = self.kpi_panel.performance_card
        self.quality_card = self.kpi_panel.quality_card
        self.execution_card = self.kpi_panel.execution_card
        self.runtime_card = self.kpi_panel.runtime_card
        self.downtime_card = self.kpi_panel.downtime_card
        self.output_card = self.kpi_panel.output_card

    def _bind_breakdown_legacy_api(self) -> None:
        self.machine_table = self.breakdown_panel.machine_table
        self.employee_table = self.breakdown_panel.employee_table
        self.work_order_table = self.breakdown_panel.work_order_table
        self.product_table = self.breakdown_panel.product_table
        self.operation_table = self.breakdown_panel.operation_table

    def _connect_flow_controller(self) -> None:
        flow = self.flow_controller
        flow.loading_changed.connect(self._set_loading_state)
        flow.data_loaded.connect(self._on_dashboard_loaded)
        flow.load_failed.connect(self._on_dashboard_load_failed)
        flow.export_completed.connect(self._on_export_completed)
        flow.export_failed.connect(self._on_export_failed)

    def _fetch_dashboard_data(self, filters):
        return self.dashboard_service.get_dashboard(filters)

    def _export_dashboard_data(self, data: OEEDashboardData, file_path: str) -> Path:
        if self.export_service is None:
            raise RuntimeError("OEEDashboardExportService chưa được cấu hình.")
        return self.export_service.export(dashboard=data, output_path=Path(file_path), report_title=self.REPORT_TITLE)

    @staticmethod
    def _create_default_export_service() -> ExportServiceProtocol | None:
        if OEEDashboardExportService is None:
            return None
        return OEEDashboardExportService()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title_row = QHBoxLayout()
        title = QLabel("OEE Dashboard")
        title.setObjectName("pageTitle")

        self.export_button = QPushButton("Export Excel")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_excel)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_data)

        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(self.export_button)
        title_row.addWidget(self.refresh_button)
        root.addLayout(title_row)

        self.filter_panel = OEEFilterPanel()
        self.filter_panel.apply_requested.connect(self.load_data)
        self.filter_panel.reset_requested.connect(self.reset_filters)

        root.addWidget(self.filter_panel)
        self.kpi_panel = OEEKPIPanel()
        root.addWidget(self.kpi_panel)

        self.tabs = QTabWidget()
        self.top_machine_widget = TopMachineWidget()
        self.top_machine = self.top_machine_widget
        if self.top_machine_controller is None:
            self.top_machine_controller = self._default_top_machine_controller_factory(self.top_machine_widget)

        self.breakdown_panel = OEEBreakdownPanel(columns=self.TABLE_COLUMNS)

        self.tabs.addTab(self.top_machine_widget, "Top Machine")
        for index in range(self.breakdown_panel.count()):
            widget = self.breakdown_panel.widget(index)
            tab_title = self.breakdown_panel.tabText(index)
            self.tabs.addTab(widget, tab_title)
        root.addWidget(self.tabs, 1)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        root.addWidget(self.status_label)
        
    def reset_filters(self) -> None:
        self.filter_panel.reset_values()
        self.load_data()

    def refresh(self) -> None:
        self.load_data()

    def load_data(self) -> None:
        if self._loading:
            return
        try:
            filters = self._build_filters()
        except ValueError as exc:
            self._dashboard_data = None
            self.export_button.setEnabled(False)
            self.status_label.setText("Bộ lọc OEE không hợp lệ.")
            QMessageBox.warning(self, "Bộ lọc không hợp lệ", str(exc))
            return

        self.flow_controller.refresh(filters)
        if self.pareto_controller is not None:
            load_all = getattr(self.pareto_controller, "load_all", None)
            if callable(load_all):
                self._pareto_data = load_all(filters)

    def _on_dashboard_loaded(self, data: object) -> None:
        required_attributes = ("summary", "by_machine", "by_employee", "by_work_order", "by_product", "by_operation")
        if not all(hasattr(data, name) for name in required_attributes):
            self._on_dashboard_load_failed("Controller phải trả về dữ liệu OEE Dashboard hợp lệ.")
            return
        filters = self.flow_controller.current_filters
        self._dashboard_data = data
        self._render_dashboard(data)
        self._load_top_machine(filters, data)
        self.export_button.setEnabled(self.export_service is not None)
        execution_count = data.summary.get("execution_count", 0)
        self.status_label.setText(f"Đã tải dữ liệu OEE: {execution_count} execution(s).")

    def _on_dashboard_load_failed(self, message: str) -> None:
        self._dashboard_data = None
        self._clear_dashboard()
        self.export_button.setEnabled(False)
        self.status_label.setText("Tải dữ liệu OEE thất bại.")
        QMessageBox.critical(self, "Không thể tải OEE Dashboard", f"Đã xảy ra lỗi khi tải dữ liệu OEE.\n\n{message}")

    def _render_dashboard(self, data: OEEDashboardData) -> None:
        self.kpi_panel.set_summary(data.summary)
        self.breakdown_panel.set_data(
            by_machine=data.by_machine, by_employee=data.by_employee,
            by_work_order=data.by_work_order, by_product=data.by_product, by_operation=data.by_operation
        )

    def _clear_dashboard(self) -> None:
        self.kpi_panel.set_summary({}) 
        self.breakdown_panel.set_data(by_machine=[], by_employee=[], by_work_order=[], by_product=[], by_operation=[])
        self.top_machine_widget.set_data([])
        if self.top_machine_controller is not None:
            self.top_machine_controller.rows = ()

    def _populate_table(self, table, rows) -> None:
        self.breakdown_panel.populate_table(table, rows)

    def _load_top_machine(self, filters: OEEDashboardFilters, dashboard: OEEDashboardData) -> None:
        del filters
        machine_rows = self._to_machine_rows(dashboard.by_machine)
        self.top_machine_widget.set_data(machine_rows)
        if self.top_machine_controller is not None:
            self.top_machine_controller.rows = tuple(machine_rows)

    @classmethod
    def _to_machine_rows(cls, rows: Iterable[Any] | None) -> list[MachineRow]:
        result: list[MachineRow] = []
        for item in rows or []:
            if isinstance(item, MachineRow):
                result.append(item)
                continue
            row = cls._as_mapping(item)
            result.append(
                MachineRow(
                    machine=str(row.get("machine") or row.get("machine_code") or row.get("group_label") or row.get("group_key") or ""),
                    oee=cls._number(row.get("oee")),
                    availability=cls._number(row.get("availability")),
                    performance=cls._number(row.get("performance")),
                    quality=cls._number(row.get("quality")),
                    runtime=cls._number(row.get("runtime", row.get("runtime_minutes"))),
                    downtime=cls._number(row.get("downtime", row.get("downtime_minutes"))),
                    ok_qty=cls._integer(row.get("ok_qty", row.get("ok_quantity"))),
                    ng_qty=cls._integer(row.get("ng_qty", row.get("ng_quantity"))),
                )
            )
        return result

    @staticmethod
    def _as_mapping(value: Any) -> Mapping[str, Any]:
        if isinstance(value, Mapping):
            return value
        if hasattr(value, "__dict__"):
            return vars(value)
        return {}

    def _build_filters(self) -> OEEDashboardFilters:
        return OEEDashboardFilters(
            start_date=self.start_date_edit.date().toPython(),
            end_date=self.end_date_edit.date().toPython(),
            machine_code=self.machine_edit.text().strip(),
            employee_code=self.employee_edit.text().strip(),
            shift=self.shift_combo.currentText().strip(),
            work_order_no=self.work_order_edit.text().strip(),
            product_code=self.product_edit.text().strip(),
            operation_no=self.operation_edit.text().strip(),
        )

    def export_excel(self) -> None:
        if self._dashboard_data is None:
            QMessageBox.warning(self, "Chưa có dữ liệu", "Không có dữ liệu OEE để xuất.")
            return
        if self.export_service is None:
            QMessageBox.warning(self, "Không thể xuất Excel", "OEEDashboardExportService chưa được cấu hình.")    
            return

        selected_path, _ = QFileDialog.getSaveFileName(self, "Xuất OEE Dashboard", "oee_dashboard.xlsx", "Excel Workbook (*.xlsx)")
        if not selected_path:
            return

        output_path = Path(selected_path)
        if output_path.suffix.lower() != ".xlsx":
            output_path = output_path.with_suffix(".xlsx")

        self.export_button.setDisabled(True)
        self.flow_controller.export_excel(output_path)

    def _on_export_completed(self, file_path: str) -> None:
        self.export_button.setEnabled(self._dashboard_data is not None)
        self.status_label.setText(f"Đã xuất báo cáo OEE: {file_path}")
        QMessageBox.information(self, "Xuất Excel thành công", f"Đã xuất báo cáo OEE:\n{file_path}")

    def _render_summary(self, summary) -> None:
        self.kpi_panel.set_summary(summary)

    def _on_export_failed(self, message: str) -> None:
        self.export_button.setEnabled(self._dashboard_data is not None and self.export_service is not None)
        self.status_label.setText(message or "Xuất Excel thất bại.")
        QMessageBox.critical(self, "Xuất Excel thất bại", message or "Không thể xuất dữ liệu OEE Dashboard.")
        
    @staticmethod
    def _number(value: Any) -> float:
        try: return float(value or 0)
        except (TypeError, ValueError): return 0.0

    @staticmethod
    def _integer(value: Any) -> int:
        try: return int(round(float(value or 0)))
        except (TypeError, ValueError): return 0

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QLabel#pageTitle { font-size: 22px; font-weight: 700; }
            QFrame#filterPanel, QFrame#kpiCard { border: 1px solid #d7dce2; border-radius: 8px; background: palette(base); }
            QLabel#kpiCardTitle { font-size: 12px; font-weight: 600; }
            QLabel#kpiCardValue { font-size: 24px; font-weight: 700; }
            QLabel#statusLabel { padding-top: 4px; }
            QPushButton { min-height: 30px; padding: 4px 14px; }
            QLineEdit, QComboBox, QDateEdit { min-height: 28px; }
            QTableWidget { gridline-color: #d7dce2; }
            QHeaderView::section { font-weight: 600; padding: 6px; }
            """
        )