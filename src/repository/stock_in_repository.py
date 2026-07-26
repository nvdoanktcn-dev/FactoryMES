from __future__ import annotations

from src.models.stock_in import StockIn
from src.repository.base_repository import BaseRepository


class StockInRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(
            session=session,
            model=StockIn,
        )

    def get_by_id(self, stock_in_id):
        try:
            normalized_id = int(stock_in_id)
        except (TypeError, ValueError):
            return None

        return (
            self.session
            .query(StockIn)
            .filter(
                StockIn.stock_in_id == normalized_id
            )
            .first()
        )

    def get_all(self):
        return (
            self.session
            .query(StockIn)
            .order_by(
                StockIn.stock_in_date.desc().nullslast(),
                StockIn.stock_in_id.desc(),
            )
            .all()
        )
