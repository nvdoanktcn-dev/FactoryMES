from __future__ import annotations

from src.models.production_assignment_history import ProductionAssignmentHistory
from src.repository.base_repository import BaseRepository


class ProductionAssignmentHistoryRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(session=session, model=ProductionAssignmentHistory)

    def get_by_assignment_id(self, assignment_id):
        return (self.session.query(ProductionAssignmentHistory)
                .filter(ProductionAssignmentHistory.assignment_id == int(assignment_id))
                .order_by(ProductionAssignmentHistory.changed_at.desc(),
                          ProductionAssignmentHistory.id.desc())
                .all())

    def get_by_production_order_id(self, production_order_id):
        return (self.session.query(ProductionAssignmentHistory)
                .filter(ProductionAssignmentHistory.production_order_id == int(production_order_id))
                .order_by(ProductionAssignmentHistory.changed_at.desc(),
                          ProductionAssignmentHistory.id.desc())
                .all())
