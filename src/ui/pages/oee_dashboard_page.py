from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol, Sequence

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from src.ui.models.oee_dashboard_models import (
    OEEDashboardData,
    OEEDashboardFilters,
)

from src.ui.controllers.oee_dashboard_flow_controller import (
    OEEDashboardFlowController,
)
from src.ui.controllers.pareto_controller import (
    ParetoController,
    ParetoMode,
)
from src.ui.controllers.top_machine_controller import TopMachineController

from src.services.trend_service import (
    TrendGranularity,
    TrendService,
)
from src.services.progress_service import ProgressService
from src.repository.dashboard_repository import (
    DashboardRepository,
)
from src.cache.dashboard_data_cache import (
    DashboardDataCache,
)
from src.providers.dashboard_data_provider import (
    DashboardDataProvider,
)
from src.coordinators.dashboard_coordinator import (
    DashboardCoordinator,
)
from src.ui.widgets.top_machine_widget import MachineRow, TopMachineWidget
from src.ui.widgets.oee_filter_panel import OEEFilterPanel
from src.ui.widgets.oee_kpi_panel import (
    KPIValueCard,
    OEEKPIPanel,
)
from src.ui.widgets.oee_breakdown_panel import (
    DEFAULT_TABLE_COLUMNS,
    OEEBreakdownPanel,
)
from src.ui.widgets.pareto_widget import ParetoWidget
from src.ui.widgets.trend_widget import TrendWidget
from src.ui.widgets.production_progress_widget import (
    ProductionProgressWidget,
)
from src.ui.widgets.oee_gauge_widget import (
    OEEGaugeWidget,
)



try:
    from src.services.oee_dashboard_export_service import OEEDashboardExportService
except ImportError:  # pragma: no cover - compatibility with partial deployments
    OEEDashboardExportService = None  # type: ignore[assignment,misc]


class DashboardControllerProtocol(Protocol):
    def load_dashboard(self, filters: OEEDashboardFilters) -> OEEDashboardData: ...


class ExportServiceProtocol(Protocol):
    def export(
        self,
        dashboard: OEEDashboardData,
        output_path: str | Path,
        *,
        report_title: str = "OEE Dashboard Report",
        generated_at: Any = None,
    ) -> Path: ...


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

        if controller is None:
            raise ValueError(
                "OEEDashboardPage yêu cầu một "
                "DashboardControllerProtocol."
            )

        self.controller = controller

        self.export_service = (
            export_service
            or self._create_default_export_service()
        )

        self.pareto_controller = pareto_controller
        self.top_machine_controller = (
            top_machine_controller
        )

        self._dashboard_data: (
                OEEDashboardData | None
        ) = None

        self._pareto_data: Any | None = None
        self._loading = False

        self.trend_service = TrendService()
        self.progress_service = ProgressService()

        self.dashboard_repository = DashboardRepository(
            self.controller
        )
        self.dashboard_cache = DashboardDataCache(
            self.dashboard_repository
        )
        self.dashboard_provider = DashboardDataProvider(
            self.dashboard_cache
        )
        self.dashboard_coordinator = DashboardCoordinator(
            self.dashboard_cache,
            self.dashboard_provider,
        )

        self.flow_controller = OEEDashboardFlowController(
            export_dashboard=self._export_dashboard_data,
            parent=self,
            coordinator=self.dashboard_coordinator,
        )

        self._build_ui()
        self._bind_filter_legacy_api()
        self._bind_kpi_legacy_api()
        self._bind_breakdown_legacy_api()
        self._apply_styles()

        self._connect_flow_controller()

        self.load_data()

    def _set_loading_state(
        self,
        loading: bool,
    ) -> None:
        self._loading = loading

        self.refresh_button.setDisabled(loading)
        self.filter_panel.setDisabled(loading)

        self.export_button.setEnabled(
            not loading
            and self._dashboard_data is not None
            and self.export_service is not None
        )

        if loading:
            self.status_label.setText(
                "Đang tải dữ liệu OEE..."
            )

    def _bind_filter_legacy_api(self) -> None:
        """
        Giữ tương thích với code và test Dashboard cũ.
        """

        self.start_date_edit = (
            self.filter_panel.start_date_edit
        )
        self.end_date_edit = (
            self.filter_panel.end_date_edit
        )
        self.machine_edit = self.filter_panel.machine_edit
        self.employee_edit = (
            self.filter_panel.employee_edit
        )
        self.shift_combo = self.filter_panel.shift_combo
        self.work_order_edit = (
            self.filter_panel.work_order_edit
        )
        self.product_edit = self.filter_panel.product_edit
        self.operation_edit = (
            self.filter_panel.operation_edit
        )
        self.apply_button = self.filter_panel.apply_button
        self.reset_button = self.filter_panel.reset_button

    def _bind_kpi_legacy_api(self) -> None:
        """
        Giữ tương thích với code và test cũ.
        """

        self.oee_card = self.kpi_panel.oee_card

        self.availability_card = (
            self.kpi_panel.availability_card
        )

        self.performance_card = (
            self.kpi_panel.performance_card
        )

        self.quality_card = (
            self.kpi_panel.quality_card
        )

        self.execution_card = (
            self.kpi_panel.execution_card
        )

        self.runtime_card = (
            self.kpi_panel.runtime_card
        )

        self.downtime_card = (
            self.kpi_panel.downtime_card
        )

        self.output_card = (
            self.kpi_panel.output_card
        )

    def _bind_breakdown_legacy_api(self) -> None:
        """
        Giữ nguyên tên table cũ.
        """

        self.machine_table = (
            self.breakdown_panel.machine_table
        )

        self.employee_table = (
            self.breakdown_panel.employee_table
        )

        self.work_order_table = (
            self.breakdown_panel.work_order_table
        )

        self.product_table = (
            self.breakdown_panel.product_table
        )

        self.operation_table = (
            self.breakdown_panel.operation_table
        )

    def _connect_flow_controller(
        self,
    ) -> None:
        flow = self.flow_controller

        flow.loading_changed.connect(
            self._set_loading_state
        )

        flow.data_loaded.connect(
            self._on_dashboard_loaded
        )

        flow.load_failed.connect(
            self._on_dashboard_load_failed
        )

        flow.export_completed.connect(
            self._on_export_completed
        )

        flow.export_failed.connect(
            self._on_export_failed
        )

    def _fetch_dashboard_data(
        self,
        filters,
    ):
        return self.dashboard_service.get_dashboard(
            filters
        )

    def _export_dashboard_data(
        self,
        data: OEEDashboardData,
        file_path: str,
    ) -> Path:
        if self.export_service is None:
            raise RuntimeError(
                "OEEDashboardExportService "
                "chưa được cấu hình."
            )

        return self.export_service.export(
            dashboard=data,
            output_path=Path(file_path),
            report_title=self.REPORT_TITLE,
        )

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

        self.filter_panel.apply_requested.connect(
            self.load_data
        )
        self.filter_panel.reset_requested.connect(
            self.reset_filters
        )

        root.addWidget(self.filter_panel)

        self.oee_gauge = OEEGaugeWidget()
        self.oee_gauge.setMaximumWidth(280)

        self.kpi_panel = OEEKPIPanel()

        overview_row = QHBoxLayout()
        overview_row.setSpacing(12)
        overview_row.addWidget(self.oee_gauge)
        overview_row.addWidget(self.kpi_panel, 1)
        root.addLayout(overview_row)

        self.tabs = QTabWidget()

        self.top_machine_widget = TopMachineWidget()

        # Alias retained for integrations that use the shorter name.
        self.top_machine = self.top_machine_widget

        self.trend_widget = TrendWidget()
        self.progress_widget = ProductionProgressWidget()

        # Compatibility aliases.
        self.trend = self.trend_widget
        self.production_progress_widget = (
            self.progress_widget
        )

        self.trend_widget.granularity_changed.connect(
            self._on_trend_granularity_changed
        )

        if self.top_machine_controller is None:
            self.top_machine_controller = TopMachineController(
                self.top_machine_widget
            )

        existing_pareto_widget = getattr(
            self.pareto_controller,
            "widget",
            None,
        )

        if isinstance(existing_pareto_widget, ParetoWidget):
            self.pareto_widget = existing_pareto_widget
        else:
            self.pareto_widget = ParetoWidget()

        self.pareto_widget.setMinimumHeight(340)

        if self.pareto_controller is None:
            self.pareto_controller = ParetoController(
                self.pareto_widget,
                mode=ParetoMode.BY_MACHINE,
                value_field="ng",
            )

        self.breakdown_panel = OEEBreakdownPanel(
            columns=self.TABLE_COLUMNS
        )

        self.pareto_panel = self._create_pareto_panel()

        self.tabs.addTab(
            self.top_machine_widget,
            "Top Machine",
        )
        self.tabs.addTab(
            self.pareto_panel,
            "Pareto NG",
        )

        self.tabs.addTab(
            self.trend_widget,
            "Trend",
        )

        self.tabs.addTab(
            self.progress_widget,
            "Tiến độ sản xuất",
        )

        for index in range(
            self.breakdown_panel.count()
        ):
            widget = self.breakdown_panel.widget(index)
            title = self.breakdown_panel.tabText(index)

            self.tabs.addTab(
                widget,
                title,
            )

        root.addWidget(self.tabs, 1)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        root.addWidget(self.status_label)
        
    def _create_pareto_panel(self) -> QWidget:
        container = QWidget()

        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        control_layout = QHBoxLayout()
        mode_label = QLabel("Phân tích theo:")

        self.pareto_mode_combo = QComboBox()
        self.pareto_mode_combo.addItem(
            "Máy",
            ParetoMode.BY_MACHINE,
        )
        self.pareto_mode_combo.addItem(
            "Sản phẩm",
            ParetoMode.BY_PRODUCT,
        )
        self.pareto_mode_combo.addItem(
            "Công lệnh",
            ParetoMode.BY_WORK_ORDER,
        )
        self.pareto_mode_combo.addItem(
            "Nhân viên",
            ParetoMode.BY_OPERATOR,
        )

        self.pareto_mode_combo.currentIndexChanged.connect(
            self._on_pareto_mode_changed
        )

        control_layout.addWidget(mode_label)
        control_layout.addWidget(self.pareto_mode_combo)
        control_layout.addStretch()

        layout.addLayout(control_layout)
        layout.addWidget(self.pareto_widget, 1)

        return container

    def _on_pareto_mode_changed(
        self,
        index: int,
    ) -> None:
        del index

        if self._dashboard_data is None:
            clear_method = getattr(
                self.pareto_controller,
                "clear",
                None,
            )

            if callable(clear_method):
                clear_method()

            return

        self._load_pareto(self._dashboard_data)

    def _load_pareto(
        self,
        dashboard: OEEDashboardData,
    ) -> None:
        raw_mode = self.pareto_mode_combo.currentData()

        try:
            mode = ParetoMode(raw_mode)
        except (TypeError, ValueError):
            mode = ParetoMode.BY_MACHINE

        source_rows = self._pareto_source_rows(
            dashboard,
            mode,
        )

        self.pareto_controller.set_mode(mode)

        self._pareto_data = (
            self.pareto_controller.set_data(
                source_rows
            )
        )

    @classmethod
    def _pareto_source_rows(
        cls,
        dashboard: OEEDashboardData,
        mode: ParetoMode,
    ) -> list[dict[str, Any]]:
        mode_config = {
            ParetoMode.BY_MACHINE: (
                dashboard.by_machine,
                "machine",
            ),
            ParetoMode.BY_PRODUCT: (
                dashboard.by_product,
                "product",
            ),
            ParetoMode.BY_WORK_ORDER: (
                dashboard.by_work_order,
                "work_order",
            ),
            ParetoMode.BY_OPERATOR: (
                dashboard.by_employee,
                "operator",
            ),
        }

        rows, group_field = mode_config.get(
            mode,
            (
                dashboard.by_machine,
                "machine",
            ),
        )

        result: list[dict[str, Any]] = []

        for item in rows or []:
            row = cls._as_mapping(item)

            name = str(
                row.get("group_label")
                or row.get("group_key")
                or row.get(group_field)
                or ""
            ).strip()

            ng_quantity = cls._number(
                row.get(
                    "ng_quantity",
                    row.get(
                        "ng_qty",
                        row.get("ng", 0),
                    ),
                )
            )

            result.append(
                {
                    group_field: name,
                    "ng": ng_quantity,
                }
            )

        return result


    def _on_trend_granularity_changed(
        self,
        granularity: object,
    ) -> None:
        """
        Tạo lại dữ liệu Trend khi người dùng đổi chu kỳ.
        """

        if self._dashboard_data is None:
            self.trend_widget.clear()
            return

        try:
            resolved = TrendGranularity(granularity)
        except (TypeError, ValueError):
            resolved = TrendGranularity.DAILY

        self._load_trend(
            self._dashboard_data,
            granularity=resolved,
        )

    def _load_trend(
        self,
        dashboard: OEEDashboardData,
        *,
        granularity: TrendGranularity | str | None = None,
    ) -> None:
        """
        Tổng hợp và hiển thị xu hướng OEE.
        """

        resolved_granularity = (
            granularity
            if granularity is not None
            else self.trend_widget.granularity
        )

        source_rows = self._trend_source_rows(
            dashboard
        )

        points = self.trend_service.build(
            source_rows,
            granularity=resolved_granularity,
        )

        self.trend_widget.set_data(points)

    def _load_progress(
        self,
        dashboard: OEEDashboardData,
    ) -> None:
        """
        Tổng hợp và hiển thị tiến độ công lệnh.
        """

        source_rows = self._progress_source_rows(
            dashboard
        )

        items = self.progress_service.build(
            source_rows
        )

        self.progress_widget.set_data(items)

    @classmethod
    def _trend_source_rows(
        cls,
        dashboard: OEEDashboardData,
    ) -> list[Any]:
        """
        Lấy nguồn dữ liệu chi tiết cho TrendService.

        Ưu tiên các thuộc tính chứa execution hoặc dữ liệu chi tiết.
        Nếu Dashboard model hiện tại chưa có dữ liệu này, phương thức
        sẽ thử sử dụng các bảng breakdown có sẵn.

        TrendService tự bỏ qua những dòng không có ngày giờ hợp lệ.
        """

        preferred_attributes = (
            "trend_rows",
            "execution_rows",
            "executions",
            "detail_rows",
            "details",
            "raw_rows",
            "rows",
        )

        for attribute in preferred_attributes:
            value = getattr(
                dashboard,
                attribute,
                None,
            )

            if value:
                return list(value)

        fallback: list[Any] = []

        for attribute in (
            "by_machine",
            "by_employee",
            "by_work_order",
            "by_product",
            "by_operation",
        ):
            value = getattr(
                dashboard,
                attribute,
                None,
            )

            if value:
                fallback.extend(value)

        return fallback

    @classmethod
    def _progress_source_rows(
        cls,
        dashboard: OEEDashboardData,
    ) -> list[dict[str, Any]]:
        """
        Chuẩn hóa dữ liệu công lệnh cho ProgressService.
        """

        explicit_rows = getattr(
            dashboard,
            "progress_rows",
            None,
        )

        if explicit_rows:
            source_rows = explicit_rows
        else:
            source_rows = (
                getattr(
                    dashboard,
                    "by_work_order",
                    None,
                )
                or []
            )

        result: list[dict[str, Any]] = []

        for item in source_rows:
            row = dict(cls._as_mapping(item))

            work_order = str(
                row.get("work_order")
                or row.get("work_order_no")
                or row.get("order_code")
                or row.get("production_order")
                or row.get("group_label")
                or row.get("group_key")
                or ""
            ).strip()

            product = str(
                row.get("product")
                or row.get("product_code")
                or row.get("product_name")
                or row.get("ten_san_pham")
                or ""
            ).strip()

            planned_qty = cls._integer(
                row.get(
                    "planned_qty",
                    row.get(
                        "plan_qty",
                        row.get(
                            "target_qty",
                            row.get(
                                "order_qty",
                                row.get(
                                    "quantity_plan",
                                    0,
                                ),
                            ),
                        ),
                    ),
                )
            )

            completed_qty = cls._integer(
                row.get(
                    "completed_qty",
                    row.get(
                        "actual_qty",
                        row.get(
                            "finished_qty",
                            row.get(
                                "output_qty",
                                row.get(
                                    "ok_qty",
                                    row.get(
                                        "ok_quantity",
                                        0,
                                    ),
                                ),
                            ),
                        ),
                    ),
                )
            )

            normalized = dict(row)

            normalized.update(
                {
                    "work_order": work_order,
                    "product": product,
                    "planned_qty": planned_qty,
                    "completed_qty": completed_qty,
                }
            )

            result.append(normalized)

        return result

    def reset_filters(self) -> None:
        self.filter_panel.reset_values()
        self.load_data()

    def refresh(self) -> None:
        """Compatibility alias used by some V2 page containers."""
        self.load_data()

    def load_data(self) -> None:
        if self._loading:
            return

        try:
            filters = self._build_filters()
        except ValueError as exc:
            self._dashboard_data = None
            self.export_button.setEnabled(False)
            self.status_label.setText(
                "Bộ lọc OEE không hợp lệ."
            )

            QMessageBox.warning(
                self,
                "Bộ lọc không hợp lệ",
                str(exc),
            )
            return

        self.flow_controller.refresh(
            filters
        )

    def closeEvent(self, event) -> None:
        self.flow_controller.clear()

        super().closeEvent(event)

    def _on_dashboard_loaded(
        self,
        data: object,
    ) -> None:
        required_attributes = (
            "summary",
            "by_machine",
            "by_employee",
            "by_work_order",
            "by_product",
            "by_operation",
        )

        if not all(
            hasattr(data, attribute)
            for attribute in required_attributes
        ):
            self._on_dashboard_load_failed(
                "Controller phải trả về dữ liệu Dashboard "
                "có đầy đủ summary và các bảng breakdown."
            )
            return

        filters = self.flow_controller.current_filters

        self._dashboard_data = data  # type: ignore[assignment]
        self._render_dashboard(data)  # type: ignore[arg-type]

        if not isinstance(filters, OEEDashboardFilters):
            filters = self._build_filters()

        self._load_top_machine(
            filters,
            data,  # type: ignore[arg-type]
        )

        legacy_load_all = getattr(
            self.pareto_controller,
            "load_all",
            None,
        )

        if callable(legacy_load_all):
            self._pareto_data = legacy_load_all(filters)
        else:
            self._load_pareto(
                data  # type: ignore[arg-type]
            )

        self._load_trend(
            data  # type: ignore[arg-type]
        )

        self._load_progress(
            data  # type: ignore[arg-type]
        )

        self.export_button.setEnabled(
            self.export_service is not None
        )

        summary = getattr(data, "summary", {}) or {}
        execution_count = summary.get(
            "execution_count",
            0,
        )

        self.status_label.setText(
            "Đã tải dữ liệu OEE: "
            f"{execution_count} execution(s)."
        )

    def _on_dashboard_load_failed(
        self,
        message: str,
    ) -> None:
        self._dashboard_data = None

        self._clear_dashboard()
        self.export_button.setEnabled(False)

        self.status_label.setText(
            "Tải dữ liệu OEE thất bại."
        )

        QMessageBox.critical(
            self,
            "Không thể tải OEE Dashboard",
            "Đã xảy ra lỗi khi tải dữ liệu OEE."
            f"\n\n{message}",
        )

    def _render_dashboard(
        self,
        data: OEEDashboardData,
    ) -> None:
        self.oee_gauge.set_value(
            self._read_metric(
                data.summary,
                "oee",
            )
        )

        self.kpi_panel.set_summary(
            data.summary
        )

        self.breakdown_panel.set_data(
            by_machine=data.by_machine,
            by_employee=data.by_employee,
            by_work_order=data.by_work_order,
            by_product=data.by_product,
            by_operation=data.by_operation,
        )

    def _clear_dashboard(self) -> None:
        self.oee_gauge.clear()
        self.kpi_panel.set_summary({})

        self.breakdown_panel.set_data(
            by_machine=[],
            by_employee=[],
            by_work_order=[],
            by_product=[],
            by_operation=[],
        )

        if self.top_machine_controller is not None:
            clear_method = getattr(
                self.top_machine_controller,
                "clear",
                None,
            )
            if callable(clear_method):
                clear_method()
            else:
                self.top_machine_widget.set_data([])
        else:
            self.top_machine_widget.set_data([])

        if self.pareto_controller is not None:
            clear_method = getattr(
                self.pareto_controller,
                "clear",
                None,
            )
            if callable(clear_method):
                clear_method()
            else:
                self.pareto_widget.clear()

        self._pareto_data = None

        self.trend_widget.clear()
        self.progress_widget.clear()

    def _populate_table(
        self,
        table,
        rows,
    ) -> None:
        self.breakdown_panel.populate_table(
            table,
            rows,
        )

    def _load_top_machine(
        self,
        filters: OEEDashboardFilters,
        dashboard: OEEDashboardData,
    ) -> None:
        del filters

        rows = getattr(
            dashboard,
            "by_machine",
            [],
        )

        set_machine_data = getattr(
            self.top_machine_controller,
            "set_machine_data",
            None,
        )

        if callable(set_machine_data):
            set_machine_data(rows)
            return

        self.top_machine_widget.set_data(
            self._to_machine_rows(rows)
        )

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
                    machine=str(
                        row.get("machine")
                        or row.get("machine_code")
                        or row.get("group_label")
                        or row.get("group_key")
                        or ""
                    ),
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

    @staticmethod
    def _read_metric(source: Any, name: str) -> Any:
        if isinstance(source, Mapping):
            return source.get(name, 0)

        return getattr(source, name, 0)

    def _build_filters(self) -> OEEDashboardFilters:
        """Build dashboard filters using the current model field names."""
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
            QMessageBox.warning(
                self,
                "Chưa có dữ liệu",
                "Không có dữ liệu OEE để xuất.",
            )
            return

        if self.export_service is None:
            QMessageBox.warning(
                self,
                "Không thể xuất Excel",
                "OEEDashboardExportService "
                "chưa được cấu hình.",
            )    
            return

        selected_path, _ = (
            QFileDialog.getSaveFileName(
                self,
                "Xuất OEE Dashboard",
                "oee_dashboard.xlsx",
                "Excel Workbook (*.xlsx)",
            )
        )

        if not selected_path:
            return

        output_path = Path(selected_path)

        if output_path.suffix.lower() != ".xlsx":
            output_path = output_path.with_suffix(
                ".xlsx"
            )

        self.export_button.setDisabled(True)

        self.flow_controller.export_excel(
            output_path
        )

    def _on_export_completed(
        self,
        file_path: str,
    ) -> None:
        self.export_button.setEnabled(
            self._dashboard_data is not None
        )

        self.status_label.setText(
            f"Đã xuất báo cáo OEE: {file_path}"
        )

        QMessageBox.information(
            self,
            "Xuất Excel thành công",
            "Đã xuất báo cáo OEE:\n"
            f"{file_path}",
        )

    def _render_summary(
        self,
        summary,
    ) -> None:
        """
        Compatibility wrapper cho code cũ.
        """

        self.kpi_panel.set_summary(summary)

    def _on_export_failed(
        self,
        message: str,
    ) -> None:
        self.export_button.setEnabled(
            self._dashboard_data is not None
            and self.export_service is not None
        )

        self.status_label.setText(
            message or "Xuất Excel thất bại."
        )

        QMessageBox.critical(
            self,
            "Xuất Excel thất bại",
            message or "Không thể xuất dữ liệu OEE Dashboard.",
        )
        
    @staticmethod
    def _number(value: Any) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _integer(value: Any) -> int:
        try:
            return int(round(float(value or 0)))
        except (TypeError, ValueError):
            return 0

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QLabel#pageTitle { font-size: 22px; font-weight: 700; }
            QFrame#filterPanel, QFrame#kpiCard {
                border: 1px solid #d7dce2;
                border-radius: 8px;
                background: palette(base);
            }
            QLabel#kpiCardTitle { font-size: 12px; font-weight: 600; }
            QLabel#kpiCardValue { font-size: 24px; font-weight: 700; }
            QLabel#statusLabel { padding-top: 4px; }
            QPushButton { min-height: 30px; padding: 4px 14px; }
            QLineEdit, QComboBox, QDateEdit { min-height: 28px; }
            QTableWidget { gridline-color: #d7dce2; }
            QHeaderView::section { font-weight: 600; padding: 6px; }
            """
        )



