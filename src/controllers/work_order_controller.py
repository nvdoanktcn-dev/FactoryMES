from src.services.work_order_service import WorkOrderService
from src.engine.routing_engine import RoutingEngine
from src.engine.routing_engine import RoutingEngine


class WorkOrderController:
    def __init__(self):
        self.service = WorkOrderService()

    def get_all(self):
        return self.service.get_all()

    def get_by_no(self, work_order_no):
        return self.service.get_by_no(work_order_no)

    def search(self, keyword):
        return self.service.search(keyword)

    def create(self, data):
        return self.service.create(data)

    def update(self, work_order_no, data):
        return self.service.update(work_order_no, data)

    def change_status(self, work_order_no, new_status):
        return self.service.change_status(work_order_no, new_status)

    def update_progress(self, work_order_no, ok_qty=0, ng_qty=0):
        return self.service.update_progress(work_order_no, ok_qty, ng_qty)

    def close(self, work_order_no):
        return self.service.close(work_order_no)
        
    def release(self, work_order_no):
        return self.routing_engine.release_work_order(work_order_no)    

    def release(self, work_order_no):
        return self.routing_engine.release_work_order(work_order_no)