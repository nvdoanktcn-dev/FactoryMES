from __future__ import annotations

from src.models.finished_inventory import FinishedInventory
from src.repository.base_repository import BaseRepository


class FinishedInventoryRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(
            session=session,
            model=FinishedInventory,
        )

    def get_by_id(self, inventory_id):
        try:
            normalized_id = int(inventory_id)
        except (TypeError, ValueError):
            return None

        return (
            self.session
            .query(FinishedInventory)
            .filter(
                FinishedInventory.inventory_id == normalized_id
            )
            .first()
        )

    def get_all(self):
        return (
            self.session
            .query(FinishedInventory)
            .order_by(
                FinishedInventory.inventory_date.desc().nullslast(),
                FinishedInventory.inventory_id.desc(),
            )
            .all()
        )
