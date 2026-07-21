from src.ui.pages.product_page import ProductPage
from src.ui.pages.machine_page import MachinePage
from src.ui.pages.employee_page import EmployeePage
from src.ui.pages.routing_page import RoutingPage
from src.ui.pages.work_order_page import WorkOrderPage
from src.ui.pages.production_page import ProductionPage
from src.ui.pages.master_import_page import MasterImportPage


PAGE_REGISTRY = {
    "Product": ProductPage,
    "Machine": MachinePage,
    "Employee": EmployeePage,
    "Routing": RoutingPage,
    "Work Order": WorkOrderPage,
    "Production": ProductionPage,
    "Master Import": MasterImportPage,
}