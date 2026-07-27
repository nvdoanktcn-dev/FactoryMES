from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.orm import Session

from src.framework.exception import NotFoundError, ValidationError
from src.framework.validator import BaseValidator
from src.models.finished_inventory import FinishedInventory
from src.repository.finished_inventory_repository import (
    FinishedInventoryRepository,
)
from src.services.base_service import SessionOwnedService
from src.services.finished_inventory_receipt_control_service import (
    FinishedInventoryReceiptControlService,
)
from src.services.finished_inventory_receipt_audit_service import (
    FinishedInventoryReceiptAuditService,
)


class FinishedInventoryService(SessionOwnedService):
    """
    Service quản lý Tồn kho thành phẩm (FinishedInventory).
    """

    def __init__(
        self,
        session: Session | None = None,
        repository: FinishedInventoryRepository | None = None,
        receipt_control_service=None,
        receipt_audit_service=None,
    ) -> None:
        if repository is not None:
            super().__init__(
                session=getattr(repository, "session", None)
            )
            self._owns_session = False
            self.repository = repository
            self.receipt_control_service = (
                receipt_control_service
            )
            self.receipt_audit_service = (
                receipt_audit_service
            )
            return

        super().__init__(session=session)

        self.repository = FinishedInventoryRepository(
            self.require_session()
        )
        self.receipt_control_service = (
            receipt_control_service
            or FinishedInventoryReceiptControlService(
                session=self.require_session(),
                finished_inventory_repository=(
                    self.repository
                ),
            )
        )
        self.receipt_audit_service = (
            receipt_audit_service
            or FinishedInventoryReceiptAuditService(
                session=self.require_session(),
                inventory_repository=self.repository,
                receipt_control_service=(
                    self.receipt_control_service
                ),
            )
        )

    # ==========================================================
    # Query
    # ==========================================================

    def get_all_inventory(self):
        return self.repository.get_all()

    def get_inventory(self, inventory_id):
        return self.repository.get_by_id(inventory_id)

    def search_inventory(self, keyword):
        records = self.get_all_inventory()

        text = str(keyword or "").strip().lower()

        if not text:
            return records

        return [
            record
            for record in records
            if (
                text in str(record.work_order or "").lower()
                or text in str(record.product_code or "").lower()
            )
        ]

    def has_exact_inventory(self, data) -> bool:
        normalized = self._normalize_data(data)

        self._validate(normalized)

        return (
            self.repository.find_exact(
                **normalized
            )
            is not None
        )

    # ==========================================================
    # Create
    # ==========================================================

    def create_inventory(
        self,
        data,
        *,
        source="MANUAL",
        username="System",
    ):
        normalized = self._normalize_data(data)

        self._validate(normalized)
        self._validate_receipt(normalized)

        record = FinishedInventory(**normalized)

        self.log_info(
            "Create FinishedInventory: "
            f"{normalized['work_order']} / "
            f"{normalized['product_code']}"
        )

        record = self.repository.add(record)
        if self.receipt_audit_service is not None:
            self.receipt_audit_service.record_create(
                record,
                source=source,
                username=username,
            )
        return record

    # ==========================================================
    # Update
    # ==========================================================

    def update_inventory(
        self,
        inventory_id,
        data,
        *,
        source="MANUAL",
        username="System",
    ):
        record = self.repository.get_by_id(inventory_id)

        if record is None:
            raise NotFoundError(
                f"FinishedInventory not found: {inventory_id}"
            )

        old_data = (
            self.receipt_audit_service.snapshot(record)
            if self.receipt_audit_service is not None
            else None
        )
        normalized = self._normalize_data(data)

        self._validate(normalized)
        self._validate_receipt(
            normalized,
            exclude_inventory_id=inventory_id,
        )

        for field, value in normalized.items():
            setattr(record, field, value)

        self.log_info(
            f"Update FinishedInventory: {inventory_id}"
        )

        self.repository.update()
        if self.receipt_audit_service is not None:
            self.receipt_audit_service.record_update(
                record,
                old_data,
                source=source,
                username=username,
            )

        return record

    # ==========================================================
    # Delete
    # ==========================================================

    def delete_inventory(
        self,
        inventory_id,
        *,
        source="MANUAL",
        username="System",
    ):
        record = self.repository.get_by_id(inventory_id)

        if record is None:
            raise NotFoundError(
                f"FinishedInventory not found: {inventory_id}"
            )

        old_data = (
            self.receipt_audit_service.snapshot(record)
            if self.receipt_audit_service is not None
            else None
        )
        self.log_warning(
            f"Delete FinishedInventory: {inventory_id}"
        )

        deleted = self.repository.delete(record)
        if self.receipt_audit_service is not None:
            self.receipt_audit_service.record_delete(
                record,
                old_data,
                source=source,
                username=username,
            )
        return deleted

    def get_receipt_capacity(
        self,
        work_order,
        product_code,
        *,
        exclude_inventory_id=None,
    ):
        if self.receipt_control_service is None:
            return None
        return self.receipt_control_service.get_capacity(
            work_order,
            product_code,
            exclude_inventory_id=exclude_inventory_id,
        )

    def get_receipt_audit_history(self, limit=100):
        if self.receipt_audit_service is None:
            return []
        return self.receipt_audit_service.get_recent(
            limit=limit
        )

    def rollback_receipt_audit(
        self,
        audit_id,
        *,
        username="System",
    ):
        if self.receipt_audit_service is None:
            raise ValueError(
                "Receipt audit is unavailable."
            )
        return self.receipt_audit_service.rollback(
            audit_id,
            username=username,
        )

    def get_pending_receipts(self):
        if self.receipt_control_service is None:
            return []
        return (
            self.receipt_control_service
            .get_pending_receipts()
        )

    def _validate_receipt(
        self,
        data,
        *,
        exclude_inventory_id=None,
    ):
        if self.receipt_control_service is None:
            return None
        return (
            self.receipt_control_service
            .validate_receipt(
                data,
                exclude_inventory_id=(
                    exclude_inventory_id
                ),
            )
        )

    # ==========================================================
    # Validation and normalization
    # ==========================================================

    @staticmethod
    def _validate(normalized):
        BaseValidator.required(
            normalized["work_order"], "Work Order"
        )
        BaseValidator.required(
            normalized["product_code"], "Product Code"
        )
        BaseValidator.required(
            normalized["inventory_date"], "Inventory Date"
        )

        if normalized["qty"] < 0:
            raise ValidationError("Qty must not be negative.")

    @classmethod
    def _normalize_data(cls, data):
        data = dict(data or {})

        return {
            "inventory_date": cls._parse_date(
                data.get("inventory_date")
            ),
            "work_order": str(
                data.get("work_order") or ""
            ).strip().upper(),
            "product_code": str(
                data.get("product_code") or ""
            ).strip().upper(),
            "qty": int(cls._parse_float(data.get("qty"))),
        }

    @staticmethod
    def _parse_float(value):
        if value in (None, ""):
            return 0.0

        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _parse_date(value):
        if value in (None, ""):
            return None

        if isinstance(value, date) and not isinstance(
            value, datetime
        ):
            return value

        if isinstance(value, datetime):
            return value.date()

        try:
            return datetime.strptime(
                str(value)[:10], "%Y-%m-%d"
            ).date()
        except ValueError:
            return None
