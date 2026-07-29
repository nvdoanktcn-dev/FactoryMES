from __future__ import annotations

from sqlalchemy import func

from src.models.stock_in import StockIn
from src.models.stock_out import StockOut
from src.services.base_service import SessionOwnedService
from src.services.item_catalog_lookup import (
    ITEM_TYPE_LABELS,
    ITEM_TYPE_PRODUCT,
    ITEM_TYPE_SPARE_PART,
    ITEM_TYPE_TOOL,
)


class InventoryBalanceService(SessionOwnedService):
    """
    Tồn kho thực sự (Giai đoạn 4 — Warehouse nâng cao, 2026-07-25).

    Đây là service CHỈ ĐỌC (read-only reporting): tồn kho không được
    lưu như một bảng riêng (tránh lệch dữ liệu / phải đồng bộ thủ công)
    mà được TÍNH TOÁN động mỗi lần gọi:

        balance = tổng Nhập (StockIn) - tổng Xuất (StockOut)

    theo từng cặp (item_type, item_code), sau đó ghép tên + min_stock
    từ đúng danh mục (Product/Tool/SparePart) dựa trên item_type.
    """

    def __init__(self, session=None, repository=None) -> None:
        del repository  # không dùng repository - service tự truy vấn

        super().__init__(session=session)

    # ==========================================================
    # Query
    # ==========================================================

    def get_balances(self):
        session = self.require_session()

        stock_in_rows = (
            session.query(
                StockIn.item_type,
                StockIn.item_code,
                func.coalesce(func.sum(StockIn.qty), 0.0),
            )
            .group_by(StockIn.item_type, StockIn.item_code)
            .all()
        )

        stock_out_rows = (
            session.query(
                StockOut.item_type,
                StockOut.item_code,
                func.coalesce(func.sum(StockOut.qty), 0.0),
            )
            .group_by(StockOut.item_type, StockOut.item_code)
            .all()
        )

        totals = {}

        for item_type, item_code, total_in in stock_in_rows:
            key = self._key(item_type, item_code)

            entry = totals.setdefault(
                key, {"total_in": 0.0, "total_out": 0.0}
            )

            entry["total_in"] += float(total_in or 0)

        for item_type, item_code, total_out in stock_out_rows:
            key = self._key(item_type, item_code)

            entry = totals.setdefault(
                key, {"total_in": 0.0, "total_out": 0.0}
            )

            entry["total_out"] += float(total_out or 0)

        balances = []

        for (item_type, item_code), entry in totals.items():
            total_in = entry["total_in"]
            total_out = entry["total_out"]
            balance = total_in - total_out

            catalog_record = self._lookup_catalog(
                item_type, item_code
            )

            min_stock = self._catalog_min_stock(catalog_record)

            balances.append(
                {
                    "item_type": item_type,
                    "item_type_label": ITEM_TYPE_LABELS.get(
                        item_type, item_type
                    ),
                    "item_code": item_code,
                    "item_name": self._catalog_name(
                        item_type, catalog_record
                    ),
                    "min_stock": min_stock,
                    "total_in": total_in,
                    "total_out": total_out,
                    "balance": balance,
                    "is_low_stock": self._is_low_stock(
                        min_stock, balance
                    ),
                }
            )

        balances.sort(
            key=lambda row: (row["item_type"], row["item_code"])
        )

        return balances

    def search_balances(self, keyword):
        balances = self.get_balances()

        text = str(keyword or "").strip().lower()

        if not text:
            return balances

        return [
            row
            for row in balances
            if (
                text in str(row["item_code"]).lower()
                or text in str(row["item_name"]).lower()
                or text in str(row["item_type_label"]).lower()
            )
        ]

    # ==========================================================
    # Catalog lookup
    # ==========================================================

    def _lookup_catalog(self, item_type, item_code):
        if item_type == ITEM_TYPE_PRODUCT:
            from src.services.product_service import ProductService

            return ProductService(
                session=self.session
            ).get_by_code(item_code)

        if item_type == ITEM_TYPE_TOOL:
            from src.services.tool_service import ToolService

            return ToolService(
                session=self.session
            ).get_by_code(item_code)

        if item_type == ITEM_TYPE_SPARE_PART:
            from src.services.spare_part_service import (
                SparePartService,
            )

            return SparePartService(
                session=self.session
            ).get_by_code(item_code)

        return None

    @staticmethod
    def _catalog_name(item_type, record):
        if record is None:
            return ""

        if item_type == ITEM_TYPE_PRODUCT:
            return getattr(record, "product_name", "") or ""

        if item_type == ITEM_TYPE_TOOL:
            return getattr(record, "tool_name", "") or ""

        if item_type == ITEM_TYPE_SPARE_PART:
            return getattr(record, "part_name", "") or ""

        return ""

    @staticmethod
    def _catalog_min_stock(record):
        if record is None:
            return 0.0

        return float(getattr(record, "min_stock", 0) or 0)

    @staticmethod
    def _is_low_stock(min_stock, balance):
        if min_stock <= 0:
            return False

        return balance < min_stock

    @staticmethod
    def _key(item_type, item_code):
        return (
            str(item_type or "OTHER").strip().upper(),
            str(item_code or "").strip().upper(),
        )
