from tests.factories.production_assignment_factory import (
    ProductionAssignmentFactory,
)

from src.services.production_execution_service import (
    ProductionExecutionService,
)


class ProductionExecutionFactory:

    @classmethod
    def create_running(
        cls,
        session,
        assignment=None,
        start_time="2026-07-20 08:00",
        remark="Factory Execution",
    ):

        if assignment is None:

            assignment = (
                ProductionAssignmentFactory.create(
                    session,
                    status="IN_PROGRESS",
                )
            )

        service = ProductionExecutionService(
            session=session
        )

        execution = service.start_execution(
            assignment.id,
            start_time=start_time,
            remark=remark,
        )

        session.flush()

        return execution

    @classmethod
    def create_completed(
        cls,
        session,
        assignment=None,
    ):

        execution = cls.create_running(
            session,
            assignment,
        )

        service = ProductionExecutionService(
            session=session
        )

        execution = service.stop_execution(

            execution.id,

            ok_qty=100,

            ng_qty=2,

            processing_ng_qty=1,

            blank_ng_qty=1,

            downtime_minutes=10,

            end_time="2026-07-20 12:00",

            complete=True,
        )

        session.flush()

        return execution