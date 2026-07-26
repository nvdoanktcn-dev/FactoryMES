from __future__ import annotations

from src.models.stock_out import StockOut
from src.repository.base_repository import BaseRepository


class StockOutRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(
            session=session,
            model=StockOut,
        )

    def get_by_id(self, stock_out_id):
        try:
            normalized_id = int(stock_out_id)
        except (TypeError, ValueError):
            return None

        return (
            self.session
            .query(StockOut)
            .filter(
                StockOut.stock_out_id == normalized_id
            )
            .first()
        )

    def get_all(self):
        return (
            self.session
            .query(StockOut)
            .order_by(
                StockOut.stock_out_date.desc().nullslast(),
                StockOut.stock_out_id.desc(),
            )
            .all()
        )
