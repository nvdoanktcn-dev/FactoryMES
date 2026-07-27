from datetime import date
from types import SimpleNamespace

import pytest

from src.services.finished_inventory_receipt_audit_service import (
    FinishedInventoryReceiptAuditService,
)


class InventoryRepository:
    def __init__(self, records=()):
        self.records = {
            item.inventory_id: item
            for item in records
        }
        self.next_id = 100

    def get_by_id(self, record_id):
        return self.records.get(record_id)

    def add(self, record):
        if record.inventory_id is None:
            record.inventory_id = self.next_id
            self.next_id += 1
        self.records[record.inventory_id] = record
        return record

    def update(self):
        return None

    def delete(self, record):
        self.records.pop(record.inventory_id)
        return record


class AuditService:
    def __init__(self):
        self.records = []

    def write(self, **values):
        record = SimpleNamespace(
            id=len(self.records) + 1,
            **values,
        )
        self.records.append(record)
        return record

    def get_by_id(self, audit_id):
        return next(
            (
                item
                for item in self.records
                if item.id == audit_id
            ),
            None,
        )

    def get_recent(self, table_name, limit=100):
        return [
            item
            for item in reversed(self.records)
            if item.table_name == table_name
        ][:limit]


def inventory(qty=40):
    return SimpleNamespace(
        inventory_id=7,
        inventory_date=date(2026, 7, 27),
        work_order="WO-1",
        product_code="P-1",
        qty=qty,
    )


def make_service(record=None):
    repository = InventoryRepository(
        [record] if record is not None else []
    )
    audit = AuditService()
    service = FinishedInventoryReceiptAuditService(
        session=object(),
        inventory_repository=repository,
        audit_service=audit,
    )
    return service, repository, audit


def test_create_audit_rollback_deletes_unchanged_record():
    record = inventory()
    service, repository, audit = make_service(record)
    log = service.record_create(
        record,
        source="PENDING_RECEIPT",
    )

    result = service.rollback(log.id)

    assert repository.get_by_id(7) is None
    assert result["action"] == "CREATE"
    assert audit.records[-1].action == "ROLLBACK"


def test_update_audit_restores_old_snapshot():
    record = inventory(qty=40)
    service, repository, _audit = make_service(record)
    old_data = service.snapshot(record)
    record.qty = 60
    log = service.record_update(record, old_data)

    service.rollback(log.id)

    assert repository.get_by_id(7).qty == 40


def test_rollback_is_blocked_after_record_changes():
    record = inventory()
    service, _repository, _audit = make_service(record)
    log = service.record_create(record)
    record.qty = 41

    with pytest.raises(
        ValueError,
        match="changed after this audit",
    ):
        service.rollback(log.id)


def test_same_audit_cannot_be_rolled_back_twice():
    record = inventory()
    service, _repository, _audit = make_service(record)
    log = service.record_create(record)
    service.rollback(log.id)

    with pytest.raises(
        ValueError,
        match="already been rolled back",
    ):
        service.rollback(log.id)
