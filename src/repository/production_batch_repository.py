from sqlalchemy import desc

from src.repository.base_repository import BaseRepository
from src.models.production_batch import ProductionBatch


class ProductionBatchRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(session, ProductionBatch)

    def get_by_batch_no(self, batch_no):
        return (
            self.session.query(ProductionBatch)
            .filter(ProductionBatch.batch_no == batch_no)
            .first()
        )

    def get_by_file_hash(self, file_hash):
        return (
            self.session.query(ProductionBatch)
            .filter(ProductionBatch.file_hash == file_hash)
            .first()
        )

    def get_latest(self):
        return (
            self.session.query(ProductionBatch)
            .order_by(desc(ProductionBatch.id))
            .first()
        )

    def get_by_status(self, status):
        return (
            self.session.query(ProductionBatch)
            .filter(ProductionBatch.status == status)
            .order_by(desc(ProductionBatch.imported_at))
            .all()
        )