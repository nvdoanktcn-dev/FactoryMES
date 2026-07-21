from src.models.production_order import ProductionOrder
from src.services.production_assignment_service import (
    ProductionAssignmentService,
)


class ProductionAssignmentFactory:
    """Tạo ProductionAssignment phục vụ integration test."""

    @staticmethod
    def get_production_order(session):
        production_order = (
            session.query(ProductionOrder)
            .order_by(ProductionOrder.id.asc())
            .first()
        )

        if production_order is None:
            raise AssertionError(
                "Không tìm thấy ProductionOrder để tạo Assignment test."
            )

        return production_order

    @classmethod
    def create(
        cls,
        session,
        *,
        production_order=None,
        machine_code=None,
        employee_code=None,
        shift=None,
        planned_start="2026-07-20 08:00",
        planned_finish="2026-07-20 20:00",
        status="DRAFT",
        remark="Factory assignment",
    ):
        if production_order is None:
            production_order = cls.get_production_order(session)

        service = ProductionAssignmentService(session=session)

        assignment = service.create_assignment(
            {
                "production_order_id": production_order.id,
                "machine_code": machine_code,
                "employee_code": employee_code,
                "shift": shift,
                "planned_start": planned_start,
                "planned_finish": planned_finish,
                "status": status,
                "remark": remark,
            }
        )

        session.flush()
        return assignment