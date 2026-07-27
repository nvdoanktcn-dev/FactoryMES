from __future__ import annotations

from datetime import date, datetime, timedelta

import pandas as pd

from src.importer.master_base_importer import (
    MasterBaseImporter,
    MasterImportResult,
)
from src.repository.work_order_repository import (
    WorkOrderRepository,
)
from src.services.finished_inventory_service import (
    FinishedInventoryService,
)


class FinishedInventoryImporter(MasterBaseImporter):
    """Import daily finished-inventory receipts from Excel or CSV."""

    REQUIRED_COLUMNS = [
        "inventory_date",
        "work_order",
        "product_code",
        "qty",
    ]

    COLUMN_MAPPING = {
        "inventory_date": "inventory_date",
        "Inventory Date": "inventory_date",
        "Date": "inventory_date",
        "Ngày": "inventory_date",
        "Ngày nhập kho": "inventory_date",
        "work_order": "work_order",
        "Work Order": "work_order",
        "Work Order No": "work_order",
        "Công lệnh": "work_order",
        "Mã công lệnh": "work_order",
        "product_code": "product_code",
        "Product": "product_code",
        "Product Code": "product_code",
        "Mã sản phẩm": "product_code",
        "Mã hàng": "product_code",
        "qty": "qty",
        "Qty": "qty",
        "Quantity": "qty",
        "Số lượng": "qty",
        "Số lượng nhập": "qty",
        "Số lượng nhập kho": "qty",
    }

    def __init__(
        self,
        service=None,
        work_order_repository=None,
    ) -> None:
        self._owns_service = service is None
        self.service = (
            service
            or FinishedInventoryService()
        )
        session = getattr(
            getattr(
                self.service,
                "repository",
                None,
            ),
            "session",
            None,
        )
        self.work_order_repository = (
            work_order_repository
            or WorkOrderRepository(session)
        )
        self._seen_keys = set()

    def preview(self, filename):
        self._seen_keys.clear()
        return super().preview(filename)

    def import_file(self, filename):
        preview = self.preview(filename)
        dataframe = preview["dataframe"]
        self._seen_keys.clear()
        result = MasterImportResult()

        for index, row in dataframe.iterrows():
            excel_row = index + 2
            try:
                self.validate_row(row, excel_row)
                action = self.save_record(
                    self.map_row(row)
                )
                if action == "created":
                    result.add_created()
                elif action == "updated":
                    result.add_updated()
                else:
                    result.add_skipped()
                result.add_valid()
            except Exception as error:
                result.add_error(
                    excel_row,
                    str(error),
                )

        result.finish(len(dataframe))
        return result

    def validate_row(
        self,
        row,
        row_number,
    ) -> None:
        del row_number
        data = self.map_row(row)
        if data["inventory_date"] is None:
            raise ValueError(
                "Inventory Date is required or invalid."
            )
        if not data["work_order"]:
            raise ValueError(
                "Work Order is required."
            )
        if not data["product_code"]:
            raise ValueError(
                "Product Code is required."
            )
        if data["qty"] <= 0:
            raise ValueError(
                "Qty must be greater than zero."
            )

        work_order = (
            self.work_order_repository.get_by_no(
                data["work_order"]
            )
        )
        if work_order is None:
            raise ValueError(
                "Work Order does not exist: "
                f"{data['work_order']}"
            )
        expected_product = self.clean_text(
            getattr(
                work_order,
                "product_code",
                "",
            )
        ).upper()
        if expected_product != data["product_code"]:
            raise ValueError(
                f"Work Order {data['work_order']} "
                "belongs to Product "
                f"{expected_product}, not "
                f"{data['product_code']}."
            )

        key = self._record_key(data)
        if key in self._seen_keys:
            raise ValueError(
                "Duplicate row in import file."
            )
        self._seen_keys.add(key)

    def map_row(self, row) -> dict:
        return {
            "inventory_date": self._to_date(
                row.get("inventory_date")
            ),
            "work_order": self.clean_text(
                row.get("work_order")
            ).upper(),
            "product_code": self.clean_text(
                row.get("product_code")
            ).upper(),
            "qty": self.to_int(
                row.get("qty"),
            ),
        }

    def save_record(self, data) -> str:
        if self.service.has_exact_inventory(
            data
        ):
            return "skipped"
        self.service.create_inventory(data)
        return "created"

    def close(self) -> None:
        if self._owns_service:
            self.service.close()

    @staticmethod
    def _record_key(data):
        return (
            data["inventory_date"],
            data["work_order"],
            data["product_code"],
            data["qty"],
        )

    @staticmethod
    def _to_date(value):
        if value is None or pd.isna(value):
            return None
        if isinstance(value, date) and not isinstance(
            value,
            datetime,
        ):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, (int, float)):
            serial = float(value)
            if not 1 <= serial <= 100_000:
                return None
            return (
                date(1899, 12, 30)
                + timedelta(days=int(serial))
            )
        try:
            parsed = pd.to_datetime(
                str(value).strip(),
                dayfirst=True,
                errors="raise",
            )
        except (TypeError, ValueError):
            return None
        return parsed.date()
