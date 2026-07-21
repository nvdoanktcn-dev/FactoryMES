class BaseController:
    def __init__(self, service):
        self.service = service

    def get_all(self):
        return self.service.get_all()

    def get_by_id(self, item_id):
        return self.service.get_by_id(item_id)

    def create(self, data):
        return self.service.create(data)

    def update(self, item_id, data):
        return self.service.update(item_id, data)

    def delete(self, item_id):
        return self.service.delete(item_id)