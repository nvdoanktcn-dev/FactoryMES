from __future__ import annotations

from sqlalchemy import func

from src.models.production_ng import ProductionNG
from src.repository.base_repository import BaseRepository


class ProductionNGRepository(BaseRepository):
    def __init__(
        self,
        session,
    ):
        super().__init__(
            session=session,
            model=ProductionNG,
        )

    def get_by_id(
        self,
        ng_id,
    ):
        try:
            normalized_id = int(ng_id)
        except (TypeError, ValueError):
            return None

        return (
            self.session
            .query(ProductionNG)
            .filter(
                ProductionNG.id == normalized_id
            )
            .first()
        )

    def get_by_execution_id(
        self,
        execution_id,
    ):
        return (
            self.session
            .query(ProductionNG)
            .filter(
                ProductionNG.execution_id
                == int(execution_id),
                ProductionNG.status == "ACTIVE",
            )
            .order_by(
                ProductionNG.recorded_at.asc(),
                ProductionNG.id.asc(),
            )
            .all()
        )

    def get_by_type(
        self,
        ng_type,
    ):
        normalized_type = str(
            ng_type or ""
        ).strip().upper()

        return (
            self.session
            .query(ProductionNG)
            .filter(
                ProductionNG.ng_type
                == normalized_type,
                ProductionNG.status == "ACTIVE",
            )
            .order_by(
                ProductionNG.recorded_at.desc()
            )
            .all()
        )

    def sum_quantity_by_execution_id(
        self,
        execution_id,
    ) -> int:
        result = (
            self.session
            .query(
                func.coalesce(
                    func.sum(
                        ProductionNG.quantity
                    ),
                    0,
                )
            )
            .filter(
                ProductionNG.execution_id
                == int(execution_id),
                ProductionNG.status == "ACTIVE",
            )
            .scalar()
        )

        return int(result or 0)

    def sum_quantity_by_execution_type(
        self,
        execution_id,
        ng_type,
    ) -> int:
        normalized_type = str(
            ng_type or ""
        ).strip().upper()

        result = (
            self.session
            .query(
                func.coalesce(
                    func.sum(
                        ProductionNG.quantity
                    ),
                    0,
                )
            )
            .filter(
                ProductionNG.execution_id
                == int(execution_id),
                ProductionNG.ng_type
                == normalized_type,
                ProductionNG.status == "ACTIVE",
            )
            .scalar()
        )

        return int(result or 0)