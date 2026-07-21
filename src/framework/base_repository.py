class BaseRepository:

    def __init__(self, session, model):
        self.session = session
        self.model = model

    def get_all(self):
        return self.session.query(self.model).all()

    def get_by_id(self, id):
        return self.session.get(self.model, id)

    def add(self, obj):
        self.session.add(obj)
        self.session.commit()
        return obj

    def update(self):
        self.session.commit()

    def delete(self, obj):
        self.session.delete(obj)
        self.session.commit()