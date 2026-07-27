from __future__ import annotations

from collections.abc import Callable
from typing import Optional

from PySide6.QtWidgets import (
    QLabel,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.ui.dashboard.dashboard_page import DashboardPage
from src.ui.pages.master_import_page import MasterImportPage
from src.ui.pages.production_assignment_page import (
    ProductionAssignmentPage,
)
from src.ui.pages.production_downtime_page import (
    ProductionDowntimePage,
)
from src.ui.pages.production_execution_page import (
    ProductionExecutionPage,
)
from src.ui.pages.production_ng_page import (
    ProductionNGPage,
)
from src.ui.pages.production_page import (
    ProductionPage,
)


PageFactory = Callable[[], QWidget]


class NavigationManager:
    """
    Quản lý đăng ký và điều hướng các trang của FactoryMES.

    Kiến trúc Lazy Loading:

    - build_pages() chỉ đăng ký factory.
    - Page chỉ được tạo khi người dùng điều hướng lần đầu.
    - Mỗi page chỉ tồn tại một instance trong suốt vòng đời ứng dụng.
    - Controller và resource được đóng khi ứng dụng kết thúc.
    """

    def __init__(
        self,
        stack: QStackedWidget,
        dashboard_controller=None,
        allowed_pages=None,
    ) -> None:
        if stack is None:
            raise ValueError(
                "NavigationManager requires a QStackedWidget."
            )

        self.stack = stack
        self.dashboard_controller = dashboard_controller

        self.allowed_pages = (
            None
            if allowed_pages is None
            else set(allowed_pages)
        )

        # Các page đã được khởi tạo.
        self.pages: dict[str, QWidget] = {}

        # Danh sách factory của các page.
        self.page_factories: dict[
            str,
            PageFactory,
        ] = {}

    # ==========================================================
    # Registration
    # ==========================================================

    def register_factory(
        self,
        page_name: str,
        factory: PageFactory,
    ) -> None:
        """
        Đăng ký factory tạo page.

        Factory không được gọi tại thời điểm đăng ký.
        """

        normalized_name = self._normalize_page_name(
            page_name
        )

        if not callable(factory):
            raise TypeError(
                f"Factory for page "
                f"'{normalized_name}' must be callable."
            )

        self.page_factories[
            normalized_name
        ] = factory

    def unregister_factory(
        self,
        page_name: str,
    ) -> None:
        """
        Xóa factory và page đã tạo tương ứng.
        """

        normalized_name = self._normalize_page_name(
            page_name
        )

        self.page_factories.pop(
            normalized_name,
            None,
        )

        self.remove_page(
            normalized_name
        )

    def register_placeholder(
        self,
        page_name: str,
        title: str,
    ) -> None:
        """
        Đăng ký một trang placeholder.
        """

        def create_placeholder() -> QWidget:
            page = QWidget()

            layout = QVBoxLayout(
                page
            )

            label = QLabel(
                str(title or page_name)
            )

            label.setStyleSheet(
                """
                QLabel {
                    font-size: 28px;
                    font-weight: bold;
                    padding: 24px;
                }
                """
            )

            layout.addWidget(
                label
            )

            layout.addStretch()

            return page

        self.register_factory(
            page_name,
            create_placeholder,
        )

    # ==========================================================
    # Page factory definitions
    # ==========================================================

    def build_pages(self) -> None:
        """
        Đăng ký toàn bộ page của FactoryMES.

        Không khởi tạo QWidget, Service hoặc Session tại đây.
        """

        # Import cục bộ để giảm chi phí import lúc startup.
        from src.ui.pages.employee_page import (
            EmployeePage,
        )
        from src.ui.pages.machine_page import (
            MachinePage,
        )
        from src.ui.pages.oee_dashboard_page import (
            OEEDashboardPage,
        )
        from src.ui.pages.product_page import (
            ProductPage,
        )
        from src.ui.pages.routing_page import (
            RoutingPage,
        )
        from src.ui.pages.work_order_page import (
            WorkOrderPage,
        )
        from src.ui.pages.cnc_page import (
            CNCPage,
        )
        from src.ui.pages.robot_module_page import (
            RobotModulePage,
        )
        from src.ui.pages.inventory_page import (
            InventoryPage,
        )
        from src.ui.pages.reporting_page import (
            ReportingPage,
        )
        from src.ui.pages.production_inventory_reconciliation_page import (
            ProductionInventoryReconciliationPage,
        )

        self.page_factories.clear()

        self.register_factory(
            "Dashboard",
            self._create_dashboard_page,
        )

        self.register_factory(
            "Master Import",
            MasterImportPage,
        )

        self.register_factory(
            "Product",
            ProductPage,
        )

        self.register_factory(
            "Machine",
            MachinePage,
        )

        self.register_factory(
            "Employee",
            EmployeePage,
        )

        self.register_factory(
            "Routing",
            RoutingPage,
        )

        self.register_factory(
            "Work Order",
            WorkOrderPage,
        )

        self.register_factory(
            "CNC",
            CNCPage,
        )

        self.register_factory(
            "Robot",
            RobotModulePage,
        )

        self.register_factory(
            "Inventory",
            InventoryPage,
        )

        self.register_factory(
            "Machine Utilization Report",
            ReportingPage,
        )

        self.register_factory(
            "Production Inventory Reconciliation",
            ProductionInventoryReconciliationPage,
        )

        self.register_factory(
            "Production",
            ProductionPage,
        )

        self.register_factory(
            "Production Assignment",
            ProductionAssignmentPage,
        )

        self.register_factory(
            "Production Execution",
            ProductionExecutionPage,
        )

        self.register_factory(
            "Production Downtime",
            ProductionDowntimePage,
        )

        self.register_factory(
            "Production NG",
            ProductionNGPage,
        )

        self.register_factory(
            "OEE Dashboard",
            lambda: self._create_oee_dashboard_page(
                OEEDashboardPage
            ),
        )

        if self.allowed_pages is not None:
            self.page_factories = {
                name: factory
                for name, factory
                in self.page_factories.items()
                if name in self.allowed_pages
            }

    # ==========================================================
    # ==========================================================

    def _create_dashboard_page(
        self,
    ) -> QWidget:
        """
        Tạo DashboardPage.

        Nếu MainWindow truyền DashboardController vào thì sử dụng
        controller đó; nếu không, DashboardPage tự tạo controller.
        """

        if self.dashboard_controller is None:
            return DashboardPage()

        try:
            return DashboardPage(
                controller=self.dashboard_controller
            )

        except TypeError:
            page = DashboardPage()

            if hasattr(
                page,
                "controller",
            ):
                page.controller = (
                    self.dashboard_controller
                )

            return page

    @staticmethod
    def _create_oee_dashboard_page(
        page_class,
    ) -> QWidget:
        """
        Tạo OEE Dashboard với controller thực tế.

        Nếu controller thực tế chưa sẵn sàng thì dùng controller
        tương thích để giao diện vẫn mở được.
        """

        try:
            from src.database.database import (
                SessionLocal,
            )
            from src.ui.controllers.oee_dashboard_controller import (
                OEEDashboardController,
            )

            controller = (
                OEEDashboardController(
                    session_factory=SessionLocal
                )
            )

            return page_class(
                controller=controller
            )

        except Exception:
            from src.ui.models.oee_dashboard_models import (
                OEEDashboardData,
            )

            class OEECompatibleController:
                def load_dashboard(
                    self,
                    filters,
                ):
                    del filters

                    return OEEDashboardData(
                        summary={
                            "execution_count": 0
                        },
                        by_machine=[],
                        by_employee=[],
                        by_work_order=[],
                        by_product=[],
                        by_operation=[],
                    )

                def close(self) -> None:
                    return None

            return page_class(
                controller=(
                    OEECompatibleController()
                )
            )

    # ==========================================================
    # Query methods
    # ==========================================================

    def has_page(
        self,
        page_name: str,
    ) -> bool:
        """
        Kiểm tra page đã đăng ký hay chưa.

        Bao gồm cả page đã tạo và factory chưa được gọi.
        """

        normalized_name = self._normalize_page_name(
            page_name
        )

        return (
            normalized_name in self.pages
            or normalized_name
            in self.page_factories
        )

    def is_page_created(
        self,
        page_name: str,
    ) -> bool:
        """
        Kiểm tra page đã được khởi tạo hay chưa.
        """

        normalized_name = self._normalize_page_name(
            page_name
        )

        return normalized_name in self.pages

    def page_names(
        self,
    ) -> tuple[str, ...]:
        """
        Trả về các page đã đăng ký theo thứ tự.
        """

        return tuple(
            self.page_factories.keys()
        )

    def current_page_name(
        self,
    ) -> Optional[str]:
        """
        Trả về tên page đang hiển thị.
        """

        current_widget = (
            self.stack.currentWidget()
        )

        if current_widget is None:
            return None

        for page_name, page in (
            self.pages.items()
        ):
            if page is current_widget:
                return page_name

        return None

    def get_page(
        self,
        page_name: str,
    ) -> Optional[QWidget]:
        """
        Lấy page đã tạo.

        Không tự tạo page mới.
        """

        normalized_name = self._normalize_page_name(
            page_name
        )

        return self.pages.get(
            normalized_name
        )

    # ==========================================================
    # Page creation
    # ==========================================================

    def get_or_create_page(
        self,
        page_name: str,
    ) -> QWidget:
        """
        Trả về page nếu đã tồn tại.

        Nếu chưa tồn tại thì gọi factory để tạo.
        """

        normalized_name = self._normalize_page_name(
            page_name
        )

        existing_page = self.pages.get(
            normalized_name
        )

        if existing_page is not None:
            return existing_page

        factory = self.page_factories.get(
            normalized_name
        )

        if factory is None:
            raise KeyError(
                f"Page '{normalized_name}' "
                "is not registered."
            )

        try:
            page = factory()

        except Exception as error:
            raise RuntimeError(
                f"Cannot create page "
                f"'{normalized_name}': {error}"
            ) from error

        if not isinstance(
            page,
            QWidget,
        ):
            raise TypeError(
                f"Factory for page "
                f"'{normalized_name}' "
                "must return QWidget."
            )

        return self._register_page(
            normalized_name,
            page,
        )

    def _register_page(
        self,
        page_name: str,
        page: QWidget,
    ) -> QWidget:
        """
        Đưa page đã tạo vào QStackedWidget.
        """

        existing_page = self.pages.get(
            page_name
        )

        if (
            existing_page is not None
            and existing_page is not page
        ):
            self._dispose_page(
                existing_page
            )

            self.stack.removeWidget(
                existing_page
            )

            existing_page.deleteLater()

        self.pages[
            page_name
        ] = page

        if self.stack.indexOf(
            page
        ) < 0:
            self.stack.addWidget(
                page
            )

        return page

    # ==========================================================
    # Navigation
    # ==========================================================

    def navigate(
        self,
        page_name: str,
    ) -> QWidget:
        """
        Mở page theo tên.

        Page sẽ được lazy-load ở lần điều hướng đầu tiên.
        """

        normalized_name = self._normalize_page_name(
            page_name
        )

        page = self.get_or_create_page(
            normalized_name
        )

        self.stack.setCurrentWidget(
            page
        )

        self._activate_page(
            normalized_name,
            page,
        )

        return page

    @staticmethod
    def _activate_page(
        page_name: str,
        page: QWidget,
    ) -> None:
        """
        Gọi callback khi page được kích hoạt.
        """

        del page_name

        activated_method = getattr(
            page,
            "on_page_activated",
            None,
        )

        if callable(
            activated_method
        ):
            activated_method()

    # ==========================================================
    # Remove and reload
    # ==========================================================

    def reload_page(
        self,
        page_name: str,
    ) -> QWidget:
        """
        Hủy page hiện tại và tạo lại từ factory.
        """

        normalized_name = self._normalize_page_name(
            page_name
        )

        self.remove_page(
            normalized_name
        )

        return self.navigate(
            normalized_name
        )

    def remove_page(
        self,
        page_name: str,
    ) -> None:
        """
        Xóa một page đã được tạo.
        """

        normalized_name = self._normalize_page_name(
            page_name
        )

        page = self.pages.pop(
            normalized_name,
            None,
        )

        if page is None:
            return

        self._dispose_page(
            page
        )

        self.stack.removeWidget(
            page
        )

        page.deleteLater()

    # ==========================================================
    # Lifecycle
    # ==========================================================

    def close_all_pages(
        self,
    ) -> None:
        """
        Đóng resource của tất cả page đã được tạo.

        Page chưa từng được mở sẽ không tồn tại và không cần đóng.
        """

        pages = list(
            self.pages.values()
        )

        self.pages.clear()

        for page in pages:
            self._dispose_page(
                page
            )

            self.stack.removeWidget(
                page
            )

            page.deleteLater()

    @classmethod
    def _dispose_page(
        cls,
        page: QWidget,
    ) -> None:
        """
        Giải phóng controller/service/resource của một page.

        Thứ tự ưu tiên:

        1. page.close_resources()
        2. page.controller.close()
        3. page.service.close()
        """

        close_resources = getattr(
            page,
            "close_resources",
            None,
        )

        if callable(
            close_resources
        ):
            try:
                close_resources()
            except Exception:
                pass

            return

        controller = getattr(
            page,
            "controller",
            None,
        )

        cls._safe_close(
            controller
        )

        service = getattr(
            page,
            "service",
            None,
        )

        cls._safe_close(
            service
        )

        services = getattr(
            page,
            "services",
            None,
        )

        if isinstance(
            services,
            dict,
        ):
            for item in (
                services.values()
            ):
                cls._safe_close(
                    item
                )

        elif isinstance(
            services,
            (list, tuple, set),
        ):
            for item in services:
                cls._safe_close(
                    item
                )

    @staticmethod
    def _safe_close(
        resource,
    ) -> None:
        """
        Đóng resource nếu resource có phương thức close().
        """

        if resource is None:
            return

        close_method = getattr(
            resource,
            "close",
            None,
        )

        if not callable(
            close_method
        ):
            return

        try:
            close_method()

        except Exception:
            # Không chặn quá trình shutdown vì lỗi đóng một resource.
            pass

    # ==========================================================
    # Helpers
    # ==========================================================

    @staticmethod
    def _normalize_page_name(
        page_name: str,
    ) -> str:
        normalized_name = str(
            page_name or ""
        ).strip()

        if not normalized_name:
            raise ValueError(
                "Page name is required."
            )

        return normalized_name
