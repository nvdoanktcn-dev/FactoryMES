from __future__ import annotations

import uuid

from tests.base.integration_test_case import IntegrationTestCase

from src.services.production_batch_service import (
    ProductionBatchService,
)


class TestProductionBatchService(IntegrationTestCase):

    def setUp(self) -> None:
        super().setUp()

        try:
            self.service = ProductionBatchService(
                session=self.session
            )
        except TypeError:
            self.service = ProductionBatchService()

        unique = uuid.uuid4().hex[:12]

        self.file_name = f"CNC_TEST_{unique}.xlsx"
        self.file_hash = f"test-hash-{unique}"

    def test_create_batch(self) -> None:
        batch = self.service.create(
            import_type="CNC",
            file_name=self.file_name,
            file_hash=self.file_hash,
            imported_by="UnitTest",
        )

        self.session.flush()

        self.assertIsNotNone(batch)
        self.assertTrue(batch.batch_no)
        self.assertEqual(batch.file_name, self.file_name)
        self.assertEqual(batch.file_hash, self.file_hash)

    def test_mark_processing(self) -> None:
        batch = self._create_batch()

        result = self.service.mark_processing(
            batch.batch_no
        )

        self.session.flush()

        updated = result or batch

        self.assertEqual(
            str(updated.status).upper(),
            "PROCESSING",
        )

    def test_complete_batch(self) -> None:
        batch = self._create_batch()

        self.service.mark_processing(
            batch.batch_no
        )

        result = self.service.complete(
            batch_no=batch.batch_no,
            total_rows=10,
            success_rows=8,
            failed_rows=2,
        )

        self.session.flush()

        completed = result or batch

        self.assertEqual(
            str(completed.status).upper(),
            "COMPLETED_WITH_ERRORS",
        )
        self.assertEqual(completed.total_rows, 10)
        self.assertEqual(completed.success_rows, 8)
        self.assertEqual(completed.failed_rows, 2)

    def test_complete_with_errors_sets_completed_with_errors(self):
        batch = self._create_batch()

        self.service.mark_processing(batch.batch_no)

        completed = self.service.complete(
            batch_no=batch.batch_no,
            total_rows=100,
            success_rows=98,
            failed_rows=2,
        )

        completed = completed or batch

        self.assertEqual(
            str(completed.status).upper(),
            "COMPLETED_WITH_ERRORS",
        )

    def test_complete_all_success(self) -> None:
        batch = self._create_batch()

        self.service.mark_processing(
            batch.batch_no
        )

        completed = self.service.complete(
            batch_no=batch.batch_no,
            total_rows=10,
            success_rows=10,
            failed_rows=0,
        )

        self.session.flush()

        completed = completed or batch

        self.assertEqual(completed.total_rows, 10)
        self.assertEqual(completed.success_rows, 10)
        self.assertEqual(completed.failed_rows, 0)

    def _create_batch(self):
        batch = self.service.create(
            import_type="CNC",
            file_name=self.file_name,
            file_hash=self.file_hash,
            imported_by="UnitTest",
        )

        self.session.flush()
        return batch


if __name__ == "__main__":
    import unittest

    unittest.main(verbosity=2)