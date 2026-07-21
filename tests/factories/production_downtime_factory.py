from tests.factories.production_execution_factory import (
    ProductionExecutionFactory,
)

from src.services.production_downtime_service import (
    ProductionDowntimeService,
)


class ProductionDowntimeFactory:

    @classmethod
    def create_open(

        cls,

        session,

        execution=None,

        reason="WAIT_MATERIAL",

    ):

        if execution is None:

            execution = (
                ProductionExecutionFactory
                .create_running(session)
            )

        service = ProductionDowntimeService(
            session=session
        )

        event = service.start_downtime(

            execution.id,

            reason,

            start_time="2026-07-20 09:00",

            remark="Factory",

        )

        session.flush()

        return event

    @classmethod
    def create_closed(

        cls,

        session,

        execution=None,

    ):

        event = cls.create_open(
            session,
            execution,
        )

        service = ProductionDowntimeService(
            session=session
        )

        event = service.stop_downtime(

            event.id,

            end_time="2026-07-20 09:30",

        )

        session.flush()

        return event