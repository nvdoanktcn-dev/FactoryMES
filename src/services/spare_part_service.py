from __future__ import annotations

from sqlalchemy.orm import Session

from src.framework.exception import DuplicateError, NotFoundError
from src.framework.validator import BaseValidator
from src.models.spare_part import SparePart
from src.repository.spare_part_repository import SparePartRepository
from src.services.base_service import SessionOwnedService


class SparePartService(SessionOwnedService):
    """
    Service quản lý danh mục Phụ tùng (Spare Part) — Giai đoạn 4.
    """

    STATUS_ACTIVE = "ACTIVE"
    STATUS_STOPPED = "STOPPED"

    # "Sắp hết" (low stock) là trạng thái TÍNH TOÁN động từ
    # InventoryBalanceService (so sánh tồn thực tế với min_stock), KHÔNG
    # phải trạng thái lưu trong danh mục - lưu nó ở đây sẽ nhanh chóng
    # lỗi thời ngay khi có phiếu Nhập/Xuất mới.
    VALID_STATUS = {
        STATUS_ACTIVE,
        STATUS_STOPPED,
    }

    def __init__(
        self,
        session: Session | None = None,
        repository: SparePartRepository | None = None,
    ) -> None:
        if repository is not None:
            super().__init__(
                session=getattr(repository, "session", None)
            )
            self._owns_session = False
            self.repository = repository
            return

        super().__init__(session=session)

        self.repository = SparePartRepository(
            self.require_session()
        )

    # ==========================================================
    # Query
    # ==========================================================

    def get_all_spare_parts(self):
        return self.repository.get_all()

    def get_spare_part(self, part_code):
        code = self._normalize_code(part_code)

        if not code:
            return None

        return self.repository.get_by_code(code)

    def get_by_code(self, part_code):
        return self.get_spare_part(part_code)

    def search_spare_parts(self, keyword):
        parts = self.get_all_spare_parts()

        text = str(keyword or "").strip().lower()

        if not text:
            return parts

        return [
            part
            for part in parts
            if (
                text in str(part.part_code or "").lower()
                or text in str(part.part_name or "").lower()
                or text in str(part.category or "").lower()
                or text in str(part.location or "").lower()
                or text in str(part.status or "").lower()
            )
        ]

    # ==========================================================
    # Create
    # ==========================================================

    def create_spare_part(self, data):
        normalized = self._normalize_data(data)

        part_code = normalized["part_code"]
        part_name = normalized["part_name"]

        self._validate_spare_part(
            part_code=part_code,
            part_name=part_name,
        )

        if self.repository.exists(part_code):
            raise DuplicateError(
                f"Spare Part already exists: {part_code}"
            )

        part = SparePart(**normalized)

        self.log_info(f"Create SparePart: {part_code}")

        created = self.repository.add(part)

        # Giai đoạn 4 (Warehouse nâng cao, 2026-07-25): commit ngay,
        # cùng lý do như ToolService.create_tool() - SparePart vừa tạo
        # phải thấy được ngay từ StockIn/StockOut (Service/Session
        # khác) trong cùng phiên làm việc, không chờ tới khi close().
        self.commit()

        return created

    # ==========================================================
    # Update
    # ==========================================================

    def update_spare_part(self, part_code, data):
        code = self._normalize_code(part_code)

        part = self.repository.get_by_code(code)

        if part is None:
            raise NotFoundError(f"Spare Part not found: {code}")

        normalized = self._normalize_data(
            {**dict(data or {}), "part_code": code}
        )

        self._validate_spare_part(
            part_code=code,
            part_name=normalized["part_name"],
        )

        part.part_name = normalized["part_name"]
        part.category = normalized["category"]
        part.location = normalized["location"]
        part.unit = normalized["unit"]
        part.min_stock = normalized["min_stock"]
        part.status = normalized["status"]
        part.remark = normalized["remark"]

        self.log_info(f"Update SparePart: {code}")

        self.repository.update()

        self.commit()

        return part

    # ==========================================================
    # Deactivate
    # ==========================================================

    def delete_spare_part(self, part_code):
        code = self._normalize_code(part_code)

        part = self.repository.get_by_code(code)

        if part is None:
            raise NotFoundError(f"Spare Part not found: {code}")

        part.status = self.STATUS_STOPPED

        self.log_warning(f"Stopped SparePart: {code}")

        self.repository.update()

        self.commit()

        return part

    # ==========================================================
    # Validation and normalization
    # ==========================================================

    @staticmethod
    def _validate_spare_part(part_code, part_name):
        BaseValidator.required(part_code, "Part Code")
        BaseValidator.required(part_name, "Part Name")
        BaseValidator.max_length(part_code, "Part Code", 30)
        BaseValidator.max_length(part_name, "Part Name", 100)

    @classmethod
    def _normalize_data(cls, data):
        data = dict(data or {})

        return {
            "part_code": cls._normalize_code(
                data.get("part_code")
            ),
            "part_name": cls._clean_text(
                data.get("part_name")
            ),
            "category": cls._clean_optional_text(
                data.get("category")
            ),
            "location": cls._clean_optional_text(
                data.get("location")
            ),
            "unit": cls._clean_optional_text(
                data.get("unit")
            ),
            "min_stock": cls._parse_float(
                data.get("min_stock")
            ),
            "status": cls._normalize_status(
                data.get("status")
            ),
            "remark": cls._clean_optional_text(
                data.get("remark")
            ),
        }

    @staticmethod
    def _normalize_code(value):
        return str(value or "").strip().upper()

    @staticmethod
    def _clean_text(value):
        return str(value or "").strip()

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

    @classmethod
    def _normalize_status(cls, value):
        status = str(value or cls.STATUS_ACTIVE).strip().upper()

        if status not in cls.VALID_STATUS:
            raise ValueError(f"Invalid Spare Part Status: {status}")

        return status
