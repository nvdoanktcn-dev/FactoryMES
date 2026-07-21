from __future__ import annotations

from src.models.routing import Routing
from src.repository.base_repository import BaseRepository


class RoutingRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(
            session=session,
            model=Routing,
        )

    def get_by_product_operation(
        self,
        product_code,
        operation_no,
    ):
        code = str(
            product_code or ""
        ).strip().upper()

        try:
            operation = int(
                operation_no
            )
        except (TypeError, ValueError):
            return None

        if not code:
            return None

        return (
            self.session
            .query(Routing)
            .filter(
                Routing.product_code == code,
                Routing.operation_no == operation,
            )
            .first()
        )

    def get_by_product(
        self,
        product_code,
    ):
        code = str(
            product_code or ""
        ).strip().upper()

        if not code:
            return []

        return (
            self.session
            .query(Routing)
            .filter(
                Routing.product_code == code
            )
            .order_by(
                Routing.operation_no.asc()
            )
            .all()
        )

    def exists(
        self,
        product_code,
        operation_no,
    ):
        return (
            self.get_by_product_operation(
                product_code,
                operation_no,
            )
            is not None
        )

    def get_last_operation(
        self,
        product_code,
    ):
        code = str(
            product_code or ""
        ).strip().upper()

        if not code:
            return None

        return (
            self.session
            .query(Routing)
            .filter(
                Routing.product_code == code,
                Routing.status == "ACTIVE",
            )
            .order_by(
                Routing.operation_no.desc()
            )
            .first()
        )