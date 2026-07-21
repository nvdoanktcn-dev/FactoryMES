from __future__ import annotations

from src.models.production_execution import (
    ProductionExecution,
)
from src.repository.base_repository import (
    BaseRepository,
)


class ProductionExecutionRepository(
    BaseRepository
):
    def __init__(
        self,
        session,
    ):
        super().__init__(
            session=session,
            model=ProductionExecution,
        )

    def get_by_id(
        self,
        execution_id,
    ):
        try:
            normalized_id = int(
                execution_id
            )
        except (TypeError, ValueError):
            return None

        return (
            self.session
            .query(ProductionExecution)
            .filter(
                ProductionExecution.id
                == normalized_id
            )
            .first()
        )

    def get_by_assignment_id(
        self,
        assignment_id,
    ):
        return (
            self.session
            .query(ProductionExecution)
            .filter(
                ProductionExecution.assignment_id
                == int(assignment_id)
            )
            .order_by(
                ProductionExecution.start_time.asc(),
                ProductionExecution.id.asc(),
            )
            .all()
        )

    def get_running_by_assignment_id(
        self,
        assignment_id,
    ):
        return (
            self.session
            .query(ProductionExecution)
            .filter(
                ProductionExecution.assignment_id
                == int(assignment_id),
                ProductionExecution.status
                == "RUNNING",
            )
            .first()
        )

    def get_running(self):
        return (
            self.session
            .query(ProductionExecution)
            .filter(
                ProductionExecution.status
                == "RUNNING"
            )
            .order_by(
                ProductionExecution.start_time.asc()
            )
            .all()
        )