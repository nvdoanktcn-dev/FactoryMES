from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.orm import Session

from src.framework.exception import NotFoundError, ValidationError
from src.framework.validator import BaseValidator
from src.models.stock_in import StockIn
from src.repository.stock_in_repository import StockInRepository
from src.services.base_service import SessionOwnedService
from src.services.item_catalog_lookup import (
    normalize_item_type,
    validate_item_reference,
)


class StockInService(SessionOwnedService):
    """
    Service quản lý phiếu Nhập kho (StockIn).
    """

    def __init__(
        self,
        session: Session | None = None,
        repository: StockInRepository | None = None,
    ) -> None:
        if repository is not None:
            super().__init__(
                session=getattr(repository, "session", None)
            )
            self._owns_session = False
            self.repository = repository
            return

        super().__init__(session=session)

        self.repository = StockInRepository(
            self.require_session()
        )

    # ==========================================================
    # Query
    # ==========================================================

    def get_all_stock_in(self):
        return self.repository.get_all()

    def get_stock_in(self, stock_in_id):
        return self.repository.get_by_id(stock_in_id)

    def search_stock_in(self, keyword):
        records = self.get_all_stock_in()

        text = str(keyword or "").strip().lower()

        if not text:
            return records

        return [
            record
            for record in records
            if (
                text in str(record.item_code or "").lower()
                or text in str(record.supplier or "").lower()
                or text in str(record.remark or "").lower()
            )
        ]

    # ==========================================================
    # Create
    # ==========================================================
    def create_stock_in(
        self,
        data,
    ):
        normalized = self._normalize_data(
            data
        )
        
        self._validate(normalized)

        self.logger.info(
            "Create StockIn: %s",
            normalized["item_code"],
        )

        item_type = normalized.pop(
            "item_type",
            None,
        )

        validate_item_reference(
            self.session,
            item_type,
            normalized["item_code"],
        )

        record = StockIn(
            **normalized
        )

        try:
            self.session.add(record)
            self.session.flush()
            self.session.commit()
            self.session.refresh(record)

            return record

        except Exception:
            self.session.rollback()
            raise
    # ==========================================================
    # Update
    # ==========================================================

    def update_stock_in(self, stock_in_id, data):
        record = self.repository.get_by_id(stock_in_id)

        if record is None:
            raise NotFoundError(
                f"StockIn not found: {stock_in_id}"
            )

        normalized = self._normalize_data(data)

        self._validate(normalized)

        item_type = normalized.pop("item_type")

        validate_item_reference(
            self.session,
            item_type,
            normalized["item_code"],
        )

        for field, value in normalized.items():
            setattr(record, field, value)

        self.log_info(f"Update StockIn: {stock_in_id}")

        self.repository.update()

        self.session.commit()

        return record

    # ==========================================================
    # Delete
    # ==========================================================

    def delete_stock_in(self, stock_in_id):
        record = self.repository.get_by_id(stock_in_id)

        if record is None:
            raise NotFoundError(
                f"StockIn not found: {stock_in_id}"
            )

        self.log_warning(f"Delete StockIn: {stock_in_id}")

        deleted = self.repository.delete(record)

        self.session.commit()
        return deleted

    # ==========================================================
    # Validation and normalization
    # ==========================================================

    @staticmethod
    def _validate(normalized):
        BaseValidator.required(
            normalized["item_code"], "Item Code"
        )
        BaseValidator.required(
            normalized["stock_in_date"], "Stock In Date"
        )

        if normalized["qty"] < 0:
            raise ValidationError("Qty must not be negative.")

    @classmethod
    def _normalize_data(cls, data):
        data = dict(data or {})

        return {
            "stock_in_date": cls._parse_date(
                data.get("stock_in_date")
            ),
            "item_type": normalize_item_type(
                data.get("item_type")
            ),
            "item_code": str(
                data.get("item_code") or ""
            ).strip().upper(),
            "qty": cls._parse_float(data.get("qty")),
            "supplier": cls._clean_optional_text(
                data.get("supplier")
            ),
            "remark": cls._clean_optional_text(
                data.get("remark")
            ),
        }

    @staticmethod
    def _clean_optional_text(value):
        text = str(value or "").strip()
        return text or None

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
