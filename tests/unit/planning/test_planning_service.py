import unittest

from src.planning import (
    Operation,
    PlanningRequest,
    PlanningService,
    Routing,
)


class TestPlanningService(unittest.TestCase):

    def setUp(self):
        self.service = PlanningService()

    def test_create_plan(self):

        routing = Routing(
            product_code="P001",
            operations=[
                Operation(
                    op_code="OP10",
                    sequence=10,
                    machine_group="CNC",
                    cycle_time_sec=20,
                ),
                Operation(
                    op_code="OP20",
                    sequence=20,
                    machine_group="ROBOT",
                    cycle_time_sec=40,
                ),
            ],
        )

        request = PlanningRequest(
            routing=routing,
            demand_qty=1200,
            available_minutes=600,
        )

        result = self.service.analyze(
            request
        )

        self.assertEqual(
            result.total_required_machines,
            2,
        )

        self.assertEqual(
            len(result.operation_plans),
            2,
        )

        self.assertGreater(
            result.estimated_runtime_minutes,
            0,
        )