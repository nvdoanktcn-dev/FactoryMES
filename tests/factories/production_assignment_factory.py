from __future__ import annotations

from datetime import datetime

from src.models.production_order import ProductionOrder
from src.services.production_assignment_service import (
    ProductionAssignmentService,
)
from tests.factories.production_order_factory import (
    ProductionOrderFactory,
)


class ProductionAssignmentFactory:
    """
    Factory tạo ProductionAssignment phục vụ integration test.

    Factory dùng ProductionAssignmentService để dữ liệu test
    đi qua cùng validation và audit history như dữ liệu thực tế.
    """

    DEFAULT_PLANNED_START = "2026-07-20 08:00"
    DEFAULT_PLANNED_FINISH = "2026-07-20 20:00"

    @staticmethod
    def get_production_order(session):
        """
        Lấy ProductionOrder đầu tiên đang có trong database test.

        Nếu chưa có ProductionOrder nào (test chạy độc lập, database
        test trống), tự tạo một ProductionOrder tối thiểu để test
        không phụ thuộc vào dữ liệu để lại từ test khác.
        """
        production_order = (
            session.query(ProductionOrder)
            .order_by(ProductionOrder.id.asc())
            .first()
        )

        if production_order is None:
            production_order = ProductionOrderFactory.create(
                session
            )

        return production_order

    @classmethod
    def create(
        cls,
        session,
        *,
        production_order=None,
        production_order_id=None,
        machine_code=None,
        employee_code=None,
        shift=None,
        planned_start=DEFAULT_PLANNED_START,
        planned_finish=DEFAULT_PLANNED_FINISH,
        status="DRAFT",
        assigned_at=None,
        released_at=None,
        actual_start=None,
        actual_finish=None,
        remark="Factory assignment",
    ):
        """
        Tạo một ProductionAssignment với dữ liệu tùy chỉnh.

        production_order hoặc production_order_id có thể được truyền vào.
        Nếu không truyền, factory lấy ProductionOrder đầu tiên trong DB.
        """
        if production_order_id is None:
            if production_order is None:
                production_order = cls.get_production_order(
                    session
                )

            production_order_id = production_order.id

        service = ProductionAssignmentService(
            session=session
        )

        assignment = service.create_assignment(
            {
                "production_order_id": production_order_id,
                "machine_code": machine_code,
                "employee_code": employee_code,
                "shift": shift,
                "planned_start": planned_start,
                "planned_finish": planned_finish,
                "status": status,
                "assigned_at": assigned_at,
                "released_at": released_at,
                "actual_start": actual_start,
                "actual_finish": actual_finish,
                "remark": remark,
            }
        )

        session.flush()

        return assignment

    @classmethod
    def create_draft(
        cls,
        session,
        **overrides,
    ):
        """
        Tạo assignment ở trạng thái DRAFT.
        """
        return cls.create(
            session,
            status="DRAFT",
            **overrides,
        )

    @classmethod
    def create_released(
        cls,
        session,
        *,
        released_at=None,
        **overrides,
    ):
        """
        Tạo assignment ở trạng thái RELEASED.

        Phương thức này dùng để dựng fixture trạng thái.
        Test riêng cho release() phải bắt đầu từ create_draft().
        """
        return cls.create(
            session,
            status="RELEASED",
            released_at=(
                released_at
                or datetime(2026, 7, 20, 7, 50)
            ),
            **overrides,
        )

    @classmethod
    def create_in_progress(
        cls,
        session,
        *,
        released_at=None,
        actual_start=None,
        **overrides,
    ):
        """
        Tạo assignment ở trạng thái IN_PROGRESS.
        """
        return cls.create(
            session,
            status="IN_PROGRESS",
            released_at=(
                released_at
                or datetime(2026, 7, 20, 7, 50)
            ),
            actual_start=(
                actual_start
                or datetime(2026, 7, 20, 8, 0)
            ),
            **overrides,
        )

    @classmethod
    def create_on_hold(
        cls,
        session,
        *,
        released_at=None,
        actual_start=None,
        **overrides,
    ):
        """
        Tạo assignment ở trạng thái ON_HOLD.
        """
        return cls.create(
            session,
            status="ON_HOLD",
            released_at=(
                released_at
                or datetime(2026, 7, 20, 7, 50)
            ),
            actual_start=(
                actual_start
                or datetime(2026, 7, 20, 8, 0)
            ),
            **overrides,
        )

    @classmethod
    def create_completed(
        cls,
        session,
        *,
        released_at=None,
        actual_start=None,
        actual_finish=None,
        **overrides,
    ):
        """
        Tạo assignment ở trạng thái COMPLETED.
        """
        return cls.create(
            session,
            status="COMPLETED",
            released_at=(
                released_at
                or datetime(2026, 7, 20, 7, 50)
            ),
            actual_start=(
                actual_start
                or datetime(2026, 7, 20, 8, 0)
            ),
            actual_finish=(
                actual_finish
                or datetime(2026, 7, 20, 12, 0)
            ),
            **overrides,
        )

    @classmethod
    def create_cancelled(
        cls,
        session,
        **overrides,
    ):
        """
        Tạo assignment ở trạng thái CANCELLED.
        """
        return cls.create(
            session,
            status="CANCELLED",
            **overrides,
        )