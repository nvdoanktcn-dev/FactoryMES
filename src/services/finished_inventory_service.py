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


class FinishedInventoryService(SessionOwnedService):
    """
    Service quản lý Tồn kho thành phẩm (FinishedInventory).
    """

    def __init__(
        self,
        session: Session | None = None,
        repository: FinishedInventoryRepository | None = None,
    ) -> None:
        if repository is not None:
            super().__init__(
                session=getattr(repository, "session", None)
            )
            self._owns_session = False
            self.repository = repository
            return

        super().__init__(session=session)

        self.repository = FinishedInventoryRepository(
            self.require_session()
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

    # ==========================================================
    # Create
    # ==========================================================

    def create_inventory(self, data):
        normalized = self._normalize_data(data)

        self._validate(normalized)

        record = FinishedInventory(**normalized)

        self.log_info(
            "Create FinishedInventory: "
            f"{normalized['work_order']} / "
            f"{normalized['product_code']}"
        )

        return self.repository.add(record)

    # ==========================================================
    # Update
    # ==========================================================

    def update_inventory(self, inventory_id, data):
        record = self.repository.get_by_id(inventory_id)

        if record is None:
            raise NotFoundError(
                f"FinishedInventory not found: {inventory_id}"
            )

        normalized = self._normalize_data(data)

        self._validate(normalized)

        for field, value in normalized.items():
            setattr(record, field, value)

        self.log_info(
            f"Update FinishedInventory: {inventory_id}"
        )

        self.repository.update()

        return record

    # ==========================================================
    # Delete
    # ==========================================================

    def delete_inventory(self, inventory_id):
        record = self.repository.get_by_id(inventory_id)

        if record is None:
            raise NotFoundError(
                f"FinishedInventory not found: {inventory_id}"
            )

        self.log_warning(
            f"Delete FinishedInventory: {inventory_id}"
        )

        return self.repository.delete(record)

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
