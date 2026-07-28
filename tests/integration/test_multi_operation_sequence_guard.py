from __future__ import annotations

from datetime import datetime

from tests.base.database_test_case import DatabaseTestCase

from src.services.production_order_service import (
    ProductionOrderService,
)


class TestMultiOperationSequenceGuard(DatabaseTestCase):
    """Verify Production Orders must run in operation sequence."""

    WORK_ORDER_NO = "WO-INT-SEQ-001"
    PRODUCT_CODE = "INT-SEQ-001"

    def setUp(self):
        super().setUp()

        self.service = ProductionOrderService(
            session=self.session,
        )

        self.op10 = self._create_order(
            operation_no=10,
            operation_name="CNC Roughing",
        )
        self.op20 = self._create_order(
            operation_no=20,
            operation_name="Robot Welding",
        )
        self.op30 = self._create_order(
            operation_no=30,
            operation_name="Final Inspection",
        )

        self.session.flush()

    def _create_order(
        self,
        *,
        operation_no,
        operation_name,
    ):
        return self.service.create_production_order(
            {
                "work_order_no": self.WORK_ORDER_NO,
                "product_code": self.PRODUCT_CODE,
                "operation_no": operation_no,
                "operation_name": operation_name,
                "process_type": "CNC",
                "machine_type": "CNC",
                "plan_qty": 100,
                "completed_qty": 0,
                "ng_qty": 0,
                "status": "PLANNED",
                "planned_start": datetime(
                    2026,
                    7,
                    28,
                    8 + operation_no // 10,
                    0,
                ),
                "planned_finish": datetime(
                    2026,
                    7,
                    28,
                    9 + operation_no // 10,
                    0,
                ),
                "remark": (
                    "Sequence guard integration test"
                ),
            }
        )

    def _release_all(self):
        for operation_no in (10, 20, 30):
            self.service.release(
                self.WORK_ORDER_NO,
                operation_no,
            )

        self.session.flush()

    def test_operations_must_start_in_sequence(self):
        self._release_all()

        # OP20 cannot start while OP10 is only RELEASED.
        with self.assertRaisesRegex(
            ValueError,
            (
                r"Previous operation OP10 "
                r"must be COMPLETED before starting OP20"
            ),
        ):
            self.service.start(
                self.WORK_ORDER_NO,
                20,
                actual_start=datetime(
                    2026,
                    7,
                    28,
                    9,
                    0,
                ),
            )

        self.session.flush()

        persisted_op20 = self.service.get_production_order(
            self.WORK_ORDER_NO,
            20,
        )

        self.assertEqual(
            persisted_op20.status,
            "RELEASED",
        )
        self.assertIsNone(
            persisted_op20.actual_start,
        )

        # OP10 is the first operation and may start.
        op10 = self.service.start(
            self.WORK_ORDER_NO,
            10,
            actual_start=datetime(
                2026,
                7,
                28,
                8,
                0,
            ),
        )

        self.assertEqual(
            op10.status,
            "IN_PROGRESS",
        )

        # OP20 is still blocked while OP10 is IN_PROGRESS.
        with self.assertRaisesRegex(
            ValueError,
            (
                r"Previous operation OP10 "
                r"must be COMPLETED before starting OP20"
            ),
        ):
            self.service.start(
                self.WORK_ORDER_NO,
                20,
                actual_start=datetime(
                    2026,
                    7,
                    28,
                    9,
                    0,
                ),
            )

        # Complete OP10.
        op10 = self.service.complete(
            self.WORK_ORDER_NO,
            10,
            completed_qty=98,
            ng_qty=2,
            actual_finish=datetime(
                2026,
                7,
                28,
                9,
                0,
            ),
        )

        self.assertEqual(
            op10.status,
            "COMPLETED",
        )

        # OP20 may now start.
        op20 = self.service.start(
            self.WORK_ORDER_NO,
            20,
            actual_start=datetime(
                2026,
                7,
                28,
                9,
                0,
            ),
        )

        self.assertEqual(
            op20.status,
            "IN_PROGRESS",
        )

        # OP30 remains blocked while OP20 is IN_PROGRESS.
        with self.assertRaisesRegex(
            ValueError,
            (
                r"Previous operation OP20 "
                r"must be COMPLETED before starting OP30"
            ),
        ):
            self.service.start(
                self.WORK_ORDER_NO,
                30,
                actual_start=datetime(
                    2026,
                    7,
                    28,
                    11,
                    0,
                ),
            )

        # Complete OP20.
        op20 = self.service.complete(
            self.WORK_ORDER_NO,
            20,
            completed_qty=97,
            ng_qty=3,
            actual_finish=datetime(
                2026,
                7,
                28,
                11,
                0,
            ),
        )

        self.assertEqual(
            op20.status,
            "COMPLETED",
        )

        # OP30 may now start.
        op30 = self.service.start(
            self.WORK_ORDER_NO,
            30,
            actual_start=datetime(
                2026,
                7,
                28,
                11,
                0,
            ),
        )

        self.session.flush()

        self.assertEqual(
            op30.status,
            "IN_PROGRESS",
        )

        persisted_orders = (
            self.service.get_by_work_order(
                self.WORK_ORDER_NO
            )
        )

        self.assertEqual(
            [
                order.operation_no
                for order in persisted_orders
            ],
            [10, 20, 30],
        )
        self.assertEqual(
            [
                order.status
                for order in persisted_orders
            ],
            [
                "COMPLETED",
                "COMPLETED",
                "IN_PROGRESS",
            ],
        )