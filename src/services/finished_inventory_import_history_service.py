from __future__ import annotations

import hashlib
import json
from pathlib import Path
from time import perf_counter

from src.database.session import get_session
from src.repository.finished_inventory_repository import (
    FinishedInventoryRepository,
)
from src.repository.import_log_repository import (
    ImportLogRepository,
)
from src.services.master_import.import_detail_service import (
    ImportDetailService,
)
from src.services.master_import.import_log_service import (
    ImportLogService,
)
from src.services.finished_inventory_receipt_audit_service import (
    FinishedInventoryReceiptAuditService,
)


class FinishedInventoryImportHistoryService:
    MODULE = "FINISHED_INVENTORY"
    STATUS_SUCCESS = "SUCCESS"
    STATUS_PARTIAL = "PARTIAL"
    STATUS_ROLLED_BACK = "ROLLED_BACK"

    def __init__(self, session=None):
        self._owns_session = session is None
        self.session = session or get_session()
        self.log_repository = ImportLogRepository(
            self.session
        )
        self.inventory_repository = (
            FinishedInventoryRepository(
                self.session
            )
        )
        self.log_service = ImportLogService(
            session=self.session,
            auto_commit=False,
        )
        self.detail_service = ImportDetailService(
            session=self.session,
            auto_commit=False,
        )
        self.receipt_audit_service = (
            FinishedInventoryReceiptAuditService(
                session=self.session,
                inventory_repository=self.inventory_repository,
            )
        )

    @staticmethod
    def file_fingerprint(file_path):
        digest = hashlib.sha256()

        with Path(file_path).open("rb") as stream:
            for chunk in iter(
                lambda: stream.read(1024 * 1024),
                b"",
            ):
                digest.update(chunk)

        return "SHA256:" + digest.hexdigest().upper()

    def find_duplicate(self, file_path):
        return (
            self.log_repository
            .get_completed_by_fingerprint(
                self.MODULE,
                self.file_fingerprint(file_path),
            )
        )

    def assert_not_imported(self, file_path):
        existing = self.find_duplicate(file_path)

        if existing is None:
            return

        imported_at = (
            existing.import_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            if existing.import_time
            else ""
        )
        raise ValueError(
            "This exact file was already imported "
            f"(log #{existing.id}, {imported_at})."
        )

    def begin_import(
        self,
        file_path,
        total_rows,
        user_name=None,
    ):
        self.assert_not_imported(file_path)
        return self.log_service.create_log(
            module=self.MODULE,
            file_path=file_path,
            sheet_name=self.file_fingerprint(
                file_path
            ),
            user_name=user_name,
            total_rows=total_rows,
            status="PENDING",
            message="Import in progress.",
        )

    def record_created(self, log_id, record):
        snapshot = self.snapshot(record)
        self.detail_service.record_insert(
            log_id=log_id,
            module=self.MODULE,
            entity_key=str(record.inventory_id),
            new_data=snapshot,
        )

    def complete_import(
        self,
        log_id,
        *,
        total,
        created,
        skipped,
        failed,
        started_at,
    ):
        status = (
            self.STATUS_SUCCESS
            if int(failed or 0) == 0
            else self.STATUS_PARTIAL
        )
        duration = max(
            0.0,
            perf_counter() - float(started_at),
        )
        message = (
            f"Created: {int(created or 0)}; "
            f"Skipped: {int(skipped or 0)}; "
            f"Failed: {int(failed or 0)}."
        )
        log = self.log_service.update_log(
            log_id,
            total_rows=total,
            inserted_rows=created,
            # Finished Inventory import never updates records.
            # This field stores skipped rows for this module.
            updated_rows=skipped,
            failed_rows=failed,
            duration=duration,
            status=status,
            message=message,
        )
        self.session.commit()
        return log

    def get_recent(self, limit=100):
        return (
            self.log_repository
            .get_recent_by_module(
                self.MODULE,
                limit=limit,
            )
        )

    def rollback_import(
        self,
        log_id,
        *,
        username="System",
    ):
        log = self.log_repository.get_by_log_id(
            log_id
        )

        if log is None:
            raise ValueError(
                f"Import Log not found: {log_id}"
            )
        if str(log.module or "").upper() != self.MODULE:
            raise ValueError(
                "The selected log is not a "
                "Finished Inventory import."
            )

        status = str(log.status or "").upper()
        if status == self.STATUS_ROLLED_BACK:
            raise ValueError(
                "This import has already been rolled back."
            )
        if status not in {
            self.STATUS_SUCCESS,
            self.STATUS_PARTIAL,
        }:
            raise ValueError(
                "Only completed imports can be rolled back. "
                f"Current status: {status}"
            )

        details = self.detail_service.get_by_log_id(
            log_id,
            reverse=True,
        )
        if not details:
            raise ValueError(
                "No created records were stored for this import."
            )

        records = []

        # Validation pass: do not mutate anything until every row is safe.
        for detail in details:
            if str(detail.action or "").upper() != "INSERT":
                raise ValueError(
                    "Rollback contains an unsupported "
                    f"action: {detail.action}"
                )

            try:
                inventory_id = int(detail.entity_key)
            except (TypeError, ValueError) as error:
                raise ValueError(
                    "Invalid inventory key in import history: "
                    f"{detail.entity_key}"
                ) from error

            record = self.inventory_repository.get_by_id(
                inventory_id
            )
            if record is None:
                raise ValueError(
                    "Rollback blocked: Finished Inventory "
                    f"#{inventory_id} no longer exists."
                )

            expected = self._from_json(detail.new_json)
            current = self.snapshot(record)

            if current != expected:
                raise ValueError(
                    "Rollback blocked: Finished Inventory "
                    f"#{inventory_id} was changed after import."
                )

            records.append(record)

        try:
            for record in records:
                old_data = self.snapshot(record)
                self.inventory_repository.delete(record)
                self.receipt_audit_service.record_delete(
                    record,
                    old_data,
                    source="ROLLBACK",
                    username=username,
                )

            message = (
                "Rollback completed: "
                f"{len(records)} imported row(s) deleted."
            )
            self.log_service.update_log(
                log_id,
                status=self.STATUS_ROLLED_BACK,
                message=message,
            )
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

        return {
            "log_id": int(log_id),
            "deleted_rows": len(records),
            "message": message,
        }

    @staticmethod
    def snapshot(record):
        return {
            "inventory_id": int(record.inventory_id),
            "inventory_date": (
                record.inventory_date.isoformat()
                if record.inventory_date
                else None
            ),
            "work_order": str(
                record.work_order or ""
            ),
            "product_code": str(
                record.product_code or ""
            ),
            "qty": int(record.qty or 0),
        }

    @staticmethod
    def _from_json(value):
        parsed = json.loads(value or "{}")
        return dict(parsed or {})

    def rollback_session(self):
        self.session.rollback()

    def close(self):
        if self._owns_session:
            self.session.close()
