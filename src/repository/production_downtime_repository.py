from __future__ import annotations

from src.models.production_downtime import (
    ProductionDowntime,
)
from src.repository.base_repository import (
    BaseRepository,
)


class ProductionDowntimeRepository(
    BaseRepository
):
    def __init__(
        self,
        session,
    ):
        super().__init__(
            session=session,
            model=ProductionDowntime,
        )

    def get_by_id(
        self,
        downtime_id,
    ):
        try:
            normalized_id = int(
                downtime_id
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

        return (
            self.session
            .query(ProductionDowntime)
            .filter(
                ProductionDowntime.id
                == normalized_id
            )
            .first()
        )

    def get_by_execution_id(
        self,
        execution_id,
    ):
        return (
            self.session
            .query(ProductionDowntime)
            .filter(
                ProductionDowntime.execution_id
                == int(execution_id)
            )
            .order_by(
                ProductionDowntime.start_time.asc(),
                ProductionDowntime.id.asc(),
            )
            .all()
        )

    def get_open_by_execution_id(
        self,
        execution_id,
    ):
        return (
            self.session
            .query(ProductionDowntime)
            .filter(
                ProductionDowntime.execution_id
                == int(execution_id),
                ProductionDowntime.status
                == "OPEN",
            )
            .first()
        )

    def get_open_events(self):
        return (
            self.session
            .query(ProductionDowntime)
            .filter(
                ProductionDowntime.status
                == "OPEN"
            )
            .order_by(
                ProductionDowntime.start_time.asc()
            )
            .all()
        )

    def sum_duration_by_execution_id(
        self,
        execution_id,
    ) -> float:
        events = self.get_by_execution_id(
            execution_id
        )

        return sum(
            float(
                event.duration_minutes
                or 0.0
            )
            for event in events
            if str(
                event.status or ""
            ).upper() == "CLOSED"
        )