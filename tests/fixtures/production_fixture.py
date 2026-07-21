from dataclasses import dataclass

from tests.factories.production_assignment_factory import (
    ProductionAssignmentFactory,
)

from tests.factories.production_execution_factory import (
    ProductionExecutionFactory,
)

from tests.factories.production_downtime_factory import (
    ProductionDowntimeFactory,
)


@dataclass
class ProductionFixture:

    assignment: object

    execution: object

    downtime: object

    @classmethod
    def create(cls, session):

        assignment = (
            ProductionAssignmentFactory.create(
                session,
                status="IN_PROGRESS",
            )
        )

        execution = (
            ProductionExecutionFactory.create_running(
                session,
                assignment,
            )
        )

        downtime = (
            ProductionDowntimeFactory.create_open(
                session,
                execution,
            )
        )

        return cls(

            assignment,

            execution,

            downtime,

        )