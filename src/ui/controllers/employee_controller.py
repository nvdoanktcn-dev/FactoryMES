from src.services.employee_service import EmployeeService


class EmployeeController:
    def __init__(self):
        self.service = EmployeeService()

    def get_all(self):
        return self.service.get_all()

    def get_by_code(self, employee_code):
        return self.service.get_by_code(employee_code)

    def search(self, keyword):
        return self.service.search(keyword)

    def create(self, data):
        return self.service.create(data)