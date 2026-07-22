from datetime import datetime
import unittest

from tests.base_db_test import DatabaseTestCase
from tests.factories.production_execution_factory import (
    ProductionExecutionFactory,
)
from tests.factories.production_ng_factory import (
    ProductionNGFactory,
)

from src.framework.exception import NotFoundError
from src.models.production_execution import (
    ProductionExecution,
)
from src.models.production_ng import (
    ProductionNG,
)
from src.services.production_ng_service import (
    ProductionNGService,
)


class TestProductionNGService(DatabaseTestCase):

    def setUp(self):
        super().setUp()

        self.service = ProductionNGService(
            session=self.session
        )

    def create_running_execution(self):
        return (
            ProductionExecutionFactory
            .create_running(
                self.session
            )
        )

    def test_record_processing_ng(self):
        execution = self.create_running_execution()

        record = self.service.record_ng(
            execution_id=execution.id,
            ng_type="processing",
            reason_code="dimension",
            quantity=3,
            recorded_at="2026-07-20 10:00",
            employee_code=" emp001 ",
            remark=" Dimension error ",
        )

        self.session.flush()

        self.assertIsNotNone(
            record.id
        )
        self.assertEqual(
            record.execution_id,
            execution.id,
        )
        self.assertEqual(
            record.ng_type,
            ProductionNGService.TYPE_PROCESSING,
        )
        self.assertEqual(
            record.reason_code,
            "DIMENSION",
        )
        self.assertEqual(
            record.quantity,
            3,
        )
        self.assertEqual(
            record.employee_code,
            "EMP001",
        )
        self.assertEqual(
            record.remark,
            "Dimension error",
        )
        self.assertEqual(
            record.status,
            "ACTIVE",
        )

    def test_record_blank_ng(self):
        execution = self.create_running_execution()

        record = self.service.record_ng(
            execution_id=execution.id,
            ng_type="blank",
            reason_code="casting_defect",
            quantity=2,
        )

        self.session.flush()

        self.assertEqual(
            record.ng_type,
            ProductionNGService.TYPE_BLANK,
        )
        self.assertEqual(
            record.reason_code,
            "CASTING_DEFECT",
        )
        self.assertEqual(
            record.quantity,
            2,
        )

    def test_record_ng_uses_current_datetime_when_omitted(self):
        execution = self.create_running_execution()

        before = datetime.now()

        record = self.service.record_ng(
            execution_id=execution.id,
            ng_type="PROCESSING",
            reason_code="BURR",
            quantity=1,
        )

        after = datetime.now()

        self.assertIsNotNone(
            record.recorded_at
        )
        self.assertGreaterEqual(
            record.recorded_at,
            before,
        )
        self.assertLessEqual(
            record.recorded_at,
            after,
        )

    def test_record_ng_for_completed_execution(self):
        execution = (
            ProductionExecutionFactory
            .create_completed(
                self.session
            )
        )

        record = self.service.record_ng(
            execution_id=execution.id,
            ng_type="PROCESSING",
            reason_code="SCRATCH",
            quantity=4,
        )

        self.session.flush()

        self.assertIsNotNone(
            record.id
        )
        self.assertEqual(
            record.execution_id,
            execution.id,
        )

    def test_record_ng_rejects_cancelled_execution(self):
        execution = self.create_running_execution()
        execution.status = "CANCELLED"

        self.session.flush()

        with self.assertRaisesRegex(
            ValueError,
            "NG can only be recorded",
        ):
            self.service.record_ng(
                execution_id=execution.id,
                ng_type="PROCESSING",
                reason_code="BURR",
                quantity=1,
            )

    def test_record_ng_invalid_execution_id(self):
        with self.assertRaisesRegex(
            ValueError,
            "Invalid Execution ID",
        ):
            self.service.record_ng(
                execution_id="ABC",
                ng_type="PROCESSING",
                reason_code="BURR",
                quantity=1,
            )

    def test_record_ng_execution_not_found(self):
        with self.assertRaises(
            NotFoundError
        ):
            self.service.record_ng(
                execution_id=999999999,
                ng_type="PROCESSING",
                reason_code="BURR",
                quantity=1,
            )

    def test_record_ng_invalid_type(self):
        execution = self.create_running_execution()

        with self.assertRaisesRegex(
            ValueError,
            "Invalid NG Type",
        ):
            self.service.record_ng(
                execution_id=execution.id,
                ng_type="UNKNOWN",
                reason_code="BURR",
                quantity=1,
            )

    def test_record_ng_invalid_reason(self):
        execution = self.create_running_execution()

        with self.assertRaisesRegex(
            ValueError,
            "Invalid NG Reason",
        ):
            self.service.record_ng(
                execution_id=execution.id,
                ng_type="PROCESSING",
                reason_code="UNKNOWN",
                quantity=1,
            )

    def test_record_ng_zero_quantity(self):
        execution = self.create_running_execution()

        with self.assertRaisesRegex(
            ValueError,
            "greater than zero",
        ):
            self.service.record_ng(
                execution_id=execution.id,
                ng_type="PROCESSING",
                reason_code="BURR",
                quantity=0,
            )

    def test_record_ng_negative_quantity(self):
        execution = self.create_running_execution()

        with self.assertRaisesRegex(
            ValueError,
            "greater than zero",
        ):
            self.service.record_ng(
                execution_id=execution.id,
                ng_type="PROCESSING",
                reason_code="BURR",
                quantity=-2,
            )

    def test_record_ng_invalid_quantity(self):
        execution = self.create_running_execution()

        with self.assertRaisesRegex(
            ValueError,
            "Invalid NG Quantity",
        ):
            self.service.record_ng(
                execution_id=execution.id,
                ng_type="PROCESSING",
                reason_code="BURR",
                quantity="invalid",
            )

    def test_record_ng_invalid_datetime(self):
        execution = self.create_running_execution()

        with self.assertRaisesRegex(
            ValueError,
            "Invalid datetime value",
        ):
            self.service.record_ng(
                execution_id=execution.id,
                ng_type="PROCESSING",
                reason_code="BURR",
                quantity=1,
                recorded_at="not-a-date",
            )

    def test_get_records_by_execution(self):
        execution = self.create_running_execution()

        first = ProductionNGFactory.create_processing(
            self.session,
            execution,
            quantity=3,
            recorded_at="2026-07-20 10:00",
        )

        second = ProductionNGFactory.create_blank(
            self.session,
            execution,
            quantity=2,
            recorded_at="2026-07-20 10:15",
        )

        records = self.service.get_by_execution_id(
            execution.id
        )

        self.assertEqual(
            len(records),
            2,
        )
        self.assertEqual(
            records[0].id,
            first.id,
        )
        self.assertEqual(
            records[1].id,
            second.id,
        )

    def test_get_total_processing_and_blank_ng(self):
        execution = self.create_running_execution()

        ProductionNGFactory.create_processing(
            self.session,
            execution,
            quantity=4,
        )

        ProductionNGFactory.create_processing(
            self.session,
            execution,
            quantity=3,
            reason_code="SCRATCH",
            recorded_at="2026-07-20 10:10",
        )

        ProductionNGFactory.create_blank(
            self.session,
            execution,
            quantity=2,
        )

        self.assertEqual(
            self.service.get_processing_ng(
                execution.id
            ),
            7,
        )
        self.assertEqual(
            self.service.get_blank_ng(
                execution.id
            ),
            2,
        )
        self.assertEqual(
            self.service.get_total_ng(
                execution.id
            ),
            9,
        )

    def test_record_ng_synchronizes_execution(self):
        execution = self.create_running_execution()

        ProductionNGFactory.create_processing(
            self.session,
            execution,
            quantity=5,
        )

        ProductionNGFactory.create_blank(
            self.session,
            execution,
            quantity=2,
        )

        self.session.refresh(
            execution
        )

        self.assertEqual(
            execution.processing_ng_qty,
            5,
        )
        self.assertEqual(
            execution.blank_ng_qty,
            2,
        )
        self.assertEqual(
            execution.ng_qty,
            7,
        )

    def test_update_ng(self):
        execution = self.create_running_execution()

        record = ProductionNGFactory.create_processing(
            self.session,
            execution,
            quantity=3,
        )

        updated = self.service.update_ng(
            record.id,
            ng_type="BLANK",
            reason_code="MATERIAL_DEFECT",
            quantity=6,
            recorded_at="2026-07-20 11:00",
            employee_code=" emp002 ",
            remark=" Updated remark ",
        )

        self.session.flush()

        self.assertEqual(
            updated.ng_type,
            "BLANK",
        )
        self.assertEqual(
            updated.reason_code,
            "MATERIAL_DEFECT",
        )
        self.assertEqual(
            updated.quantity,
            6,
        )
        self.assertEqual(
            updated.employee_code,
            "EMP002",
        )
        self.assertEqual(
            updated.remark,
            "Updated remark",
        )
        self.assertEqual(
            updated.recorded_at,
            datetime(
                2026,
                7,
                20,
                11,
                0,
            ),
        )

        self.session.refresh(
            execution
        )

        self.assertEqual(
            execution.processing_ng_qty,
            0,
        )
        self.assertEqual(
            execution.blank_ng_qty,
            6,
        )
        self.assertEqual(
            execution.ng_qty,
            6,
        )

    def test_update_ng_not_found(self):
        with self.assertRaises(
            NotFoundError
        ):
            self.service.update_ng(
                999999999,
                ng_type="PROCESSING",
                reason_code="BURR",
                quantity=1,
            )

    def test_update_cancelled_ng_rejected(self):
        execution = self.create_running_execution()

        record = ProductionNGFactory.create_cancelled(
            self.session,
            execution,
        )

        with self.assertRaisesRegex(
            ValueError,
            "Only ACTIVE NG record can be edited",
        ):
            self.service.update_ng(
                record.id,
                ng_type="PROCESSING",
                reason_code="BURR",
                quantity=2,
            )

    def test_cancel_ng(self):
        execution = self.create_running_execution()

        record = ProductionNGFactory.create_processing(
            self.session,
            execution,
            quantity=5,
        )

        cancelled = self.service.cancel_ng(
            record.id
        )

        self.session.flush()
        self.session.refresh(
            execution
        )

        self.assertEqual(
            cancelled.status,
            "CANCELLED",
        )
        self.assertEqual(
            execution.processing_ng_qty,
            0,
        )
        self.assertEqual(
            execution.blank_ng_qty,
            0,
        )
        self.assertEqual(
            execution.ng_qty,
            0,
        )
        self.assertEqual(
            self.service.get_total_ng(
                execution.id
            ),
            0,
        )

    def test_cancel_ng_not_found(self):
        with self.assertRaises(
            NotFoundError
        ):
            self.service.cancel_ng(
                999999999
            )

    def test_cancel_ng_twice_rejected(self):
        execution = self.create_running_execution()

        record = ProductionNGFactory.create_processing(
            self.session,
            execution,
        )

        self.service.cancel_ng(
            record.id
        )

        with self.assertRaisesRegex(
            ValueError,
            "Only ACTIVE NG record can be cancelled",
        ):
            self.service.cancel_ng(
                record.id
            )

    def test_cancelled_record_not_returned_by_execution_query(self):
        execution = self.create_running_execution()

        active_record = (
            ProductionNGFactory
            .create_processing(
                self.session,
                execution,
                quantity=3,
            )
        )

        cancelled_record = (
            ProductionNGFactory
            .create_cancelled(
                self.session,
                execution,
                quantity=2,
            )
        )

        records = self.service.get_by_execution_id(
            execution.id
        )

        record_ids = {
            record.id
            for record in records
        }

        self.assertIn(
            active_record.id,
            record_ids,
        )
        self.assertNotIn(
            cancelled_record.id,
            record_ids,
        )

    def test_optional_values_become_none(self):
        execution = self.create_running_execution()

        record = self.service.record_ng(
            execution_id=execution.id,
            ng_type="PROCESSING",
            reason_code="OTHER",
            quantity=1,
            employee_code="   ",
            remark="   ",
        )

        self.assertIsNone(
            record.employee_code
        )
        self.assertIsNone(
            record.remark
        )

    def test_get_record_invalid_id_returns_none(self):
        self.assertIsNone(
            self.service.get_record(
                "INVALID"
            )
        )

    def test_get_all_records_contains_created_record(self):
        execution = self.create_running_execution()

        record = ProductionNGFactory.create_processing(
            self.session,
            execution,
        )

        records = self.service.get_all_records()

        record_ids = {
            item.id
            for item in records
        }

        self.assertIn(
            record.id,
            record_ids,
        )

   
