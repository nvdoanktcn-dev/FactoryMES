from tests.base_db_test import DatabaseTestCase

from src.services.production_assignment_service import (
    ProductionAssignmentService,
)

from src.services.production_execution_service import (
    ProductionExecutionService,
)

from src.services.production_downtime_service import (
    ProductionDowntimeService,
)


class BaseServiceTest(
    DatabaseTestCase
):

    def setUp(self):

        super().setUp()

        self.assignment_service = (
            ProductionAssignmentService(
                session=self.session
            )
        )

        self.execution_service = (
            ProductionExecutionService(
                session=self.session
            )
        )

        self.downtime_service = (
            ProductionDowntimeService(
                session=self.session
            )
        )