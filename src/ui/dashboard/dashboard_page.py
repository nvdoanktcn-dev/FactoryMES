from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.services.dashboard import (
    DashboardFacadeService,
    DashboardRequest,
)
from src.ui.dashboard.dashboard_chart_panel import (
    DashboardChartPanel,
)
from src.ui.dashboard.dashboard_controller import (
    DashboardController,
)
from src.ui.dashboard.dashboard_kpi_panel import (
    DashboardKPIPanel,
)
from src.ui.dashboard.dashboard_status_panel import (
    DashboardStatusPanel,
)
from src.ui.dashboard.dashboard_table_panel import (
    DashboardTablePanel,
)
from src.ui.dashboard.dashboard_toolbar import (
    DashboardToolbar,
)


class DashboardPage(QWidget):
    """
    FactoryMES Dashboard Page.

    Luồng:
        DashboardToolbar
            ↓
        DashboardRequest
            ↓
        DashboardController
            ↓
        DashboardFacadeService
            ↓
        DashboardResponse
            ↓
        KPI / Charts / Tables / Status
    """

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName(
            "FactoryDashboardPage"
        )

        self.title_label = QLabel(
            "FACTORY MES DASHBOARD"
        )

        self.subtitle_label = QLabel(
            "Manufacturing performance overview"
        )

        self.toolbar = DashboardToolbar()

        self.kpi_panel = DashboardKPIPanel()
        self.chart_panel = DashboardChartPanel()
        self.table_panel = DashboardTablePanel()
        self.status_panel = DashboardStatusPanel()

        self.controller = DashboardController(
            page=self,
            facade_service=DashboardFacadeService(),
        )

        self.scroll_area = QScrollArea()
        self.content_widget = QWidget()

        self._build_ui()
        self._connect_events()
        self._apply_style()
        self._load_lookup_data()
        self._has_loaded_once = False
        self.refresh_dashboard()

    def on_page_activated(self):
        """
        Được gọi mỗi khi người dùng chuyển sang
        tab Dashboard, để dữ liệu luôn cập nhật.
        """

        self.refresh_dashboard()

    # ==========================================================
    # UI
    # ==========================================================

    def _build_ui(self):
        root_layout = QVBoxLayout(self)

        root_layout.setContentsMargins(
            12,
            12,
            12,
            12,
        )

        root_layout.setSpacing(10)

        self.title_label.setAlignment(
            Qt.AlignCenter
        )

        self.title_label.setStyleSheet(
            "font-size:24px;"
            "font-weight:bold;"
            "color:#263238;"
        )

        self.subtitle_label.setAlignment(
            Qt.AlignCenter
        )

        self.subtitle_label.setStyleSheet(
            "font-size:12px;"
            "color:#78909C;"
        )

        content_layout = QVBoxLayout(
            self.content_widget
        )

        content_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        content_layout.setSpacing(10)

        content_layout.addWidget(
            self.kpi_panel
        )

        content_layout.addWidget(
            self.chart_panel
        )

        content_layout.addWidget(
            self.table_panel
        )

        content_layout.addWidget(
            self.status_panel
        )

        self.scroll_area.setWidgetResizable(
            True
        )

        self.scroll_area.setFrameShape(
            QScrollArea.NoFrame
        )

        self.scroll_area.setWidget(
            self.content_widget
        )

        root_layout.addWidget(
            self.title_label
        )

        root_layout.addWidget(
            self.subtitle_label
        )

        root_layout.addWidget(
            self.toolbar
        )

        root_layout.addWidget(
            self.scroll_area,
            1,
        )

    def _apply_style(self):
        self.setStyleSheet("""
            QWidget#FactoryDashboardPage {
                background: #F4F6F8;
            }

            QGroupBox {
                font-size: 13px;
                font-weight: bold;
                color: #37474F;
                border: 1px solid #CFD8DC;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 6px;
                background: #FFFFFF;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
            }
        """)

    # ==========================================================
    # Events
    # ==========================================================

    def _connect_events(self):
        self.toolbar.refresh_requested.connect(
            self.refresh_dashboard
        )

        self.toolbar.filters_changed.connect(
            self.on_filters_changed
        )

        self.toolbar.auto_refresh_changed.connect(
            self.on_auto_refresh_changed
        )

    def on_filters_changed(
        self,
        request,
    ):
        """
        Chỉ lưu request mới.

        Không tự refresh mỗi lần người dùng
        thay đổi một ComboBox.
        """

        if isinstance(
            request,
            DashboardRequest,
        ):
            self.controller.current_request = (
                request
            )

    def on_auto_refresh_changed(
        self,
        enabled,
        interval_seconds,
    ):
        status_text = (
            "enabled"
            if enabled
            else "disabled"
        )

        self.status_panel.dashboard_status.set_status(
            "ONLINE",
            (
                f"Auto refresh {status_text}. "
                f"Interval: {interval_seconds}s."
            ),
        )

    # ==========================================================
    # Refresh
    # ==========================================================

    def refresh_dashboard(
        self,
        request=None,
    ):
        try:
            if request is None:
                request = (
                    self.toolbar.get_request()
                )

            if isinstance(
                request,
                dict,
            ):
                request = DashboardRequest(
                    **request
                )

            if not isinstance(
                request,
                DashboardRequest,
            ):
                raise TypeError(
                    "Dashboard refresh requires "
                    "DashboardRequest."
                )

            self.set_loading(True)

            return self.controller.refresh(
                request
            )

        except Exception as error:
            self.handle_refresh_error(
                error
            )

            return None

        finally:
            self.set_loading(False)

    def refresh_without_cache(self):
        """
        Bỏ qua cache và tải dữ liệu mới.
        """

        try:
            request = (
                self.toolbar.get_request()
            )

            self.controller.current_request = (
                request
            )

            self.set_loading(True)

            return self.controller.force_refresh()

        except Exception as error:
            self.handle_refresh_error(
                error
            )

            return None

        finally:
            self.set_loading(False)

    def invalidate_dashboard_cache(self):
        self.controller.invalidate_cache()

    # ==========================================================
    # Loading / Error
    # ==========================================================

    def set_loading(
        self,
        loading,
    ):
        self.toolbar.set_loading(
            loading
        )

        self.chart_panel.set_loading(
            loading
        )

        self.table_panel.set_loading(
            loading
        )

        self.status_panel.set_loading(
            loading
        )

        self.kpi_panel.setEnabled(
            not loading
        )

    def handle_refresh_error(
        self,
        error,
    ):
        message = str(error)

        self.status_panel.set_error(
            message
        )

        QMessageBox.warning(
            self,
            "Dashboard Error",
            message,
        )

    # ==========================================================
    # Lookup data
    # ==========================================================

    def _load_lookup_data(self):
        self._load_machine_lookup()
        self._load_work_order_lookup()
        self._load_employee_lookup()
        self._load_product_lookup()

    def _load_machine_lookup(self):
        try:
            from src.services.machine_service import (
                MachineService,
            )

            records = self._load_service_records(
                service=MachineService(),
                methods=[
                    "search_machines",
                    "get_all",
                    "get_all_machines",
                ],
            )

            self.toolbar.set_machines(
                records
            )

        except Exception:
            self.toolbar.set_machines([])

    def _load_work_order_lookup(self):
        try:
            from src.services.work_order_service import (
                WorkOrderService,
            )

            records = self._load_service_records(
                service=WorkOrderService(),
                methods=[
                    "search",
                    "get_all",
                    "get_all_work_orders",
                ],
            )

            self.toolbar.set_work_orders(
                records
            )

        except Exception:
            self.toolbar.set_work_orders([])

    def _load_employee_lookup(self):
        try:
            from src.services.employee_service import (
                EmployeeService,
            )

            records = self._load_service_records(
                service=EmployeeService(),
                methods=[
                    "search_employees",
                    "get_all",
                    "get_all_employees",
                ],
            )

            self.toolbar.set_employees(
                records
            )

        except Exception:
            self.toolbar.set_employees([])

    def _load_product_lookup(self):
        try:
            from src.services.product_service import (
                ProductService,
            )

            records = self._load_service_records(
                service=ProductService(),
                methods=[
                    "search_products",
                    "get_all",
                    "get_all_products",
                ],
            )

            self.toolbar.set_products(
                records
            )

        except Exception:
            self.toolbar.set_products([])

    @staticmethod
    def _load_service_records(
        service,
        methods,
    ):
        for method_name in methods:
            method = getattr(
                service,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:
                if method_name.startswith(
                    "search"
                ):
                    records = method("")
                else:
                    records = method()

                return list(
                    records or []
                )

            except TypeError:
                continue

        return []