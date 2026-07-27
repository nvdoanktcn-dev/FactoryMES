from __future__ import annotations

from datetime import date
from pathlib import Path
from time import perf_counter

import pytest

from src.models.finished_inventory import FinishedInventory
from src.services.finished_inventory_import_history_service import (
    FinishedInventoryImportHistoryService,
)
from tests.base.base_database_test import BaseDatabaseTest


class TestFinishedInventoryImportHistory(
    BaseDatabaseTest
):
    def setUp(self):
        super().setUp()
        self.service = (
            FinishedInventoryImportHistoryService(
                session=self.session
            )
        )
        self.import_file = (
            Path(__file__).parent
            / (
                "_finished_inventory_history_"
                f"{self._testMethodName}.xlsx"
            )
        )
        self.import_file.write_bytes(
            (
                "FactoryMES finished inventory history "
                f"{self._testMethodName}"
            ).encode("utf-8")
        )

    def tearDown(self):
        self.import_file.unlink(
            missing_ok=True
        )
        super().tearDown()

    def _create_completed_import(self):
        log = self.service.begin_import(
            self.import_file,
            total_rows=1,
        )
        record = FinishedInventory(
            inventory_date=date(2026, 7, 27),
            work_order="WO-HISTORY-1",
            product_code="P-HISTORY-1",
            qty=10,
        )
        self.session.add(record)
        self.session.flush()
        self.service.record_created(
            log.id,
            record,
        )
        self.service.complete_import(
            log.id,
            total=1,
            created=1,
            skipped=0,
            failed=0,
            started_at=perf_counter(),
        )
        return log, record.inventory_id

    def test_same_file_is_blocked_after_completed_import(
        self,
    ):
        log, _ = self._create_completed_import()

        duplicate = self.service.find_duplicate(
            self.import_file
        )

        assert duplicate.id == log.id
        with pytest.raises(
            ValueError,
            match="already imported",
        ):
            self.service.assert_not_imported(
                self.import_file
            )

    def test_rollback_deletes_unchanged_imported_rows(
        self,
    ):
        log, inventory_id = (
            self._create_completed_import()
        )

        result = self.service.rollback_import(
            log.id
        )

        assert result["deleted_rows"] == 1
        assert (
            self.session.get(
                FinishedInventory,
                inventory_id,
            )
            is None
        )
        self.session.refresh(log)
        assert log.status == "ROLLED_BACK"

    def test_rollback_is_blocked_when_row_changed(
        self,
    ):
        log, inventory_id = (
            self._create_completed_import()
        )
        record = self.session.get(
            FinishedInventory,
            inventory_id,
        )
        record.qty = 99
        self.session.commit()

        with pytest.raises(
            ValueError,
            match="changed after import",
        ):
            self.service.rollback_import(log.id)

        assert (
            self.session.get(
                FinishedInventory,
                inventory_id,
            )
            is not None
        )
        self.session.refresh(log)
        assert log.status == "SUCCESS"

    def test_rolled_back_file_can_be_imported_again(
        self,
    ):
        log, _ = self._create_completed_import()
        self.service.rollback_import(log.id)

        assert (
            self.service.find_duplicate(
                self.import_file
            )
            is None
        )
