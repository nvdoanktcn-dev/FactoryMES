from src.models.plan_history import PlanHistory
from src.repository.base_repository import BaseRepository


class PlanHistoryRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(session, PlanHistory)