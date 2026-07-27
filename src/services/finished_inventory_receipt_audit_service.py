from __future__ import annotations

import json

from src.models.finished_inventory import FinishedInventory
from src.repository.finished_inventory_repository import (
    FinishedInventoryRepository,
)
from src.services.audit_service import AuditService


class FinishedInventoryReceiptAuditService:
    TABLE_NAME = "tb_finished_inventory"
    SUPPORTED_ACTIONS = {"CREATE", "UPDATE", "DELETE"}

    def __init__(
        self,
        session,
        *,
        inventory_repository=None,
        receipt_control_service=None,
        audit_service=None,
    ):
        self.session = session
        self.inventory_repository = (
            inventory_repository
            or FinishedInventoryRepository(session)
        )
        self.receipt_control_service = (
            receipt_control_service
        )
        self.audit_service = (
            audit_service
            or AuditService(
                session=session,
                auto_commit=False,
            )
        )

    def record_create(
        self,
        record,
        *,
        source="MANUAL",
        username="System",
    ):
        return self._write(
            record_id=record.inventory_id,
            action="CREATE",
            new_data=self.snapshot(record),
            source=source,
            username=username,
        )

    def record_update(
        self,
        record,
        old_data,
        *,
        source="MANUAL",
        username="System",
    ):
        return self._write(
            record_id=record.inventory_id,
            action="UPDATE",
            old_data=old_data,
            new_data=self.snapshot(record),
            source=source,
            username=username,
        )

    def record_delete(
        self,
        record,
        old_data,
        *,
        source="MANUAL",
        username="System",
    ):
        return self._write(
            record_id=record.inventory_id,
            action="DELETE",
            old_data=old_data,
            source=source,
            username=username,
        )

    def get_recent(self, limit=100):
        return self.audit_service.get_recent(
            table_name=self.TABLE_NAME,
            limit=limit,
        )

    def rollback(
        self,
        audit_id,
        *,
        username="System",
    ) -> dict:
        audit = self.audit_service.get_by_id(audit_id)
        if audit is None:
            raise ValueError(
                f"Audit Log not found: {audit_id}"
            )
        if str(audit.table_name or "") != self.TABLE_NAME:
            raise ValueError(
                "The selected audit does not belong to "
                "Finished Inventory."
            )

        action = str(audit.action or "").upper()
        if action not in self.SUPPORTED_ACTIONS:
            raise ValueError(
                f"Audit action cannot be rolled back: {action}"
            )
        if self._was_rolled_back(audit.id):
            raise ValueError(
                "This audit has already been rolled back."
            )

        old_data = self._payload_data(audit.old_value)
        new_data = self._payload_data(audit.new_value)
        record = self.inventory_repository.get_by_id(
            audit.record_id
        )

        if action == "CREATE":
            self._require_current(record, new_data)
            self.inventory_repository.delete(record)
            result_record_id = audit.record_id
            result_data = None

        elif action == "UPDATE":
            self._require_current(record, new_data)
            self._validate_restore(
                old_data,
                exclude_inventory_id=record.inventory_id,
            )
            self._apply(record, old_data)
            self.inventory_repository.update()
            result_record_id = record.inventory_id
            result_data = self.snapshot(record)

        else:
            if record is not None:
                raise ValueError(
                    "Rollback blocked: the deleted inventory "
                    "ID is currently in use."
                )
            self._validate_restore(old_data)
            restored = FinishedInventory(
                **self._model_values(old_data)
            )
            self.inventory_repository.add(restored)
            result_record_id = restored.inventory_id
            result_data = self.snapshot(restored)

        self.audit_service.write(
            table_name=self.TABLE_NAME,
            record_id=result_record_id,
            action="ROLLBACK",
            old_value={
                "source": "ROLLBACK",
                "rolled_back_audit_id": int(audit.id),
                "data": new_data,
            },
            new_value={
                "source": "ROLLBACK",
                "rolled_back_audit_id": int(audit.id),
                "data": result_data,
            },
            username=username,
        )
        return {
            "audit_id": int(audit.id),
            "action": action,
            "record_id": result_record_id,
            "message": (
                f"Rollback completed for {action} "
                f"audit #{audit.id}."
            ),
        }

    def snapshot(self, record):
        return {
            "inventory_id": int(record.inventory_id),
            "inventory_date": (
                record.inventory_date.isoformat()
                if record.inventory_date
                else None
            ),
            "work_order": str(record.work_order or ""),
            "product_code": str(
                record.product_code or ""
            ),
            "qty": int(record.qty or 0),
        }

    def _write(
        self,
        *,
        record_id,
        action,
        old_data=None,
        new_data=None,
        source,
        username,
    ):
        return self.audit_service.write(
            table_name=self.TABLE_NAME,
            record_id=record_id,
            action=action,
            old_value=(
                self._payload(source, old_data)
                if old_data is not None
                else None
            ),
            new_value=(
                self._payload(source, new_data)
                if new_data is not None
                else None
            ),
            username=username,
        )

    def _validate_restore(
        self,
        data,
        *,
        exclude_inventory_id=None,
    ):
        if self.receipt_control_service is None:
            return
        self.receipt_control_service.validate_receipt(
            data,
            exclude_inventory_id=exclude_inventory_id,
        )

    def _was_rolled_back(self, audit_id):
        for item in self.get_recent(1000):
            if str(item.action or "").upper() != "ROLLBACK":
                continue
            for raw_value in (
                item.old_value,
                item.new_value,
            ):
                payload = self._json(raw_value)
                if payload.get(
                    "rolled_back_audit_id"
                ) == int(audit_id):
                    return True
        return False

    def _require_current(self, record, expected):
        if record is None:
            raise ValueError(
                "Rollback blocked: Finished Inventory "
                "record no longer exists."
            )
        if self.snapshot(record) != expected:
            raise ValueError(
                "Rollback blocked: Finished Inventory "
                "record changed after this audit."
            )

    @staticmethod
    def _apply(record, data):
        values = (
            FinishedInventoryReceiptAuditService
            ._model_values(data)
        )
        for field, value in values.items():
            setattr(record, field, value)

    @staticmethod
    def _model_values(data):
        from datetime import date

        raw_date = data.get("inventory_date")
        return {
            "inventory_date": (
                date.fromisoformat(raw_date)
                if isinstance(raw_date, str)
                else raw_date
            ),
            "work_order": str(
                data.get("work_order") or ""
            ),
            "product_code": str(
                data.get("product_code") or ""
            ),
            "qty": int(data.get("qty") or 0),
        }

    @staticmethod
    def _payload(source, data):
        return {
            "source": str(
                source or "MANUAL"
            ).strip().upper(),
            "data": dict(data or {}),
        }

    @staticmethod
    def _payload_data(value):
        payload = (
            FinishedInventoryReceiptAuditService
            ._json(value)
        )
        return dict(payload.get("data") or {})

    @staticmethod
    def _json(value):
        if isinstance(value, dict):
            return value
        try:
            return dict(json.loads(value or "{}") or {})
        except (TypeError, ValueError):
            return {}
