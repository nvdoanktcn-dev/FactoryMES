from src.services.machine_service import MachineService


class MachineController:
    def __init__(self):
        self.service = MachineService()

    def get_all_machines(self):
        return self.service.get_all_machines()

    def get_machine(self, machine_code):
        return self.service.get_machine(machine_code)

    def search_machines(self, keyword):
        return self.service.search_machines(keyword)

    def create_machine(self, data):
        return self.service.create_machine(data)

    def update_machine(self, machine_code, data):
        return self.service.update_machine(machine_code, data)

    def delete_machine(self, machine_code):
        return self.service.delete_machine(machine_code)

    def get_by_code(self, machine_code):
        return self.get_machine(machine_code)