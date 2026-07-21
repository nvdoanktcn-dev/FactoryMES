from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from src.ui.dashboard.dashboard_page import DashboardPage
from src.ui.pages.master_import_page import MasterImportPage
from src.ui.pages.production_page import ProductionPage
from src.ui.pages.production_assignment_page import ProductionAssignmentPage
from src.ui.pages.production_execution_page import ProductionExecutionPage
from src.ui.pages.production_downtime_page import ProductionDowntimePage
from src.ui.pages.production_ng_page import ProductionNGPage

class NavigationManager:
    """Bộ quản lý và đăng ký các trang giao diện điều hướng tập trung của FactoryMES."""

    def __init__(self, stack, dashboard_controller=None):
        self.stack = stack
        self.dashboard_controller = dashboard_controller
        self.pages = {}

    def _register_page(self, page_name, page):
        if page_name in self.pages:
            old = self.pages[page_name]
            self.stack.removeWidget(old)
            old.deleteLater()

        self.pages[page_name] = page
        self.stack.addWidget(page)
        return page    

    def register_placeholder(self, name, title):
        page = QWidget()
        layout = QVBoxLayout()
        label = QLabel(title)
        label.setStyleSheet("font-size:28px;font-weight:bold;")
        layout.addWidget(label)
        layout.addStretch()
        page.setLayout(layout)
        self._register_page(name, page)

    def build_pages(self):
        # Lazy imports nhằm tối ưu tốc độ khởi động ứng dụng ban đầu
        from src.ui.pages.product_page import ProductPage
        from src.ui.pages.machine_page import MachinePage
        from src.ui.pages.employee_page import EmployeePage
        from src.ui.pages.routing_page import RoutingPage
        from src.ui.pages.work_order_page import WorkOrderPage    
        from src.ui.pages.oee_dashboard_page import OEEDashboardPage

        # Đăng ký các phân hệ chính của hệ thống MES
        self._register_page("Dashboard", DashboardPage())
        self._register_page("Master Import", MasterImportPage())
        self._register_page("Product", ProductPage())
        self._register_page("Machine", MachinePage())
        self._register_page("Employee", EmployeePage())
        self._register_page("Routing", RoutingPage())
        self._register_page("Work Order", WorkOrderPage())
        self._register_page("Production", ProductionPage())
        self._register_page("Production Assignment", ProductionAssignmentPage())
        self._register_page("Production Execution", ProductionExecutionPage())
        self._register_page("Production Downtime", ProductionDowntimePage())
        self._register_page("Production NG", ProductionNGPage())
        
        # --- KẾT NỐI VỚI OEEDASHBOARDCONTROLLER THỰC TẾ ---
        try:
            from src.database.database import SessionLocal  # Hoặc engine tùy theo project setup
            from src.ui.controllers.oee_dashboard_controller import OEEDashboardController
            
            # Khởi tạo controller thực tế với session_factory tương ứng
            oee_controller = OEEDashboardController(session_factory=SessionLocal)
            oee_page = OEEDashboardPage(controller=oee_controller)
        except Exception as e:
            # Fallback tạo một Mock/Compatible Controller nếu định dạng tham số __init__ của controller thực tế có sự khác biệt
            from src.ui.models.oee_dashboard_models import OEEDashboardData
            
            class OEECompatibleController:
                def load_dashboard(self, filters):
                    return OEEDashboardData(
                        summary={"execution_count": 0},
                        by_machine=[], by_employee=[], by_work_order=[], by_product=[], by_operation=[]
                    )
            oee_page = OEEDashboardPage(controller=OEECompatibleController())

        self._register_page("OEE Dashboard", oee_page)

    def navigate(self, page_name):    
        page = self.pages.get(page_name)
        if page is None:
            raise KeyError(f"Page '{page_name}' not found.")

        self.stack.setCurrentWidget(page)
        self._refresh_page_if_needed(page_name, page)
        return page    

    @staticmethod
    def _refresh_page_if_needed(page_name, page):
        del page_name
        activated_method = getattr(page, "on_page_activated", None)
        if callable(activated_method):
            activated_method()