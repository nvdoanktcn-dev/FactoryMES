from tests.factories.production_execution_factory import (
    ProductionExecutionFactory,
)

from src.services.production_ng_service import (
    ProductionNGService,
)


class ProductionNGFactory:

    @classmethod
    def create_processing(
        cls,
        session,
        execution=None,
        *,
        reason_code="DIMENSION",
        quantity=3,
        recorded_at="2026-07-20 10:00",
        employee_code="EMP001",
        remark="Processing NG Factory",
    ):
        if execution is None:
            execution = (
                ProductionExecutionFactory
                .create_running(session)
            )

        service = ProductionNGService(
            session=session
        )

        record = service.record_ng(
            execution_id=execution.id,
            ng_type=ProductionNGService.TYPE_PROCESSING,
            reason_code=reason_code,
            quantity=quantity,
            recorded_at=recorded_at,
            employee_code=employee_code,
            remark=remark,
        )

        session.flush()

        return record

    @classmethod
    def create_blank(
        cls,
        session,
        execution=None,
        *,
        reason_code="CASTING_DEFECT",
        quantity=2,
        recorded_at="2026-07-20 10:15",
        employee_code="EMP001",
        remark="Blank NG Factory",
    ):
        if execution is None:
            execution = (
                ProductionExecutionFactory
                .create_running(session)
            )

        service = ProductionNGService(
            session=session
        )

        record = service.record_ng(
            execution_id=execution.id,
            ng_type=ProductionNGService.TYPE_BLANK,
            reason_code=reason_code,
            quantity=quantity,
            recorded_at=recorded_at,
            employee_code=employee_code,
            remark=remark,
        )

        session.flush()

        return record

    @classmethod
    def create_cancelled(
        cls,
        session,
        execution=None,
        *,
        ng_type=ProductionNGService.TYPE_PROCESSING,
        reason_code="SCRATCH",
        quantity=1,
    ):
        if execution is None:
            execution = (
                ProductionExecutionFactory
                .create_running(session)
            )

        service = ProductionNGService(
            session=session
        )

        record = service.record_ng(
            execution_id=execution.id,
            ng_type=ng_type,
            reason_code=reason_code,
            quantity=quantity,
            recorded_at="2026-07-20 10:30",
        )

        session.flush()

        service.cancel_ng(
            record.id
        )

        session.flush()

        return record
