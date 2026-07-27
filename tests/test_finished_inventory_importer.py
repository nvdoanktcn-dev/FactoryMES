from datetime import date
from types import SimpleNamespace

import pandas as pd

from src.importer.finished_inventory_importer import (
    FinishedInventoryImporter,
)


class FakeInventoryService:
    def __init__(self, existing=None):
        self.existing = set(existing or [])
        self.created = []

    def has_exact_inventory(self, data):
        return (
            data["inventory_date"],
            data["work_order"],
            data["product_code"],
            data["qty"],
        ) in self.existing

    def create_inventory(self, data):
        self.created.append(dict(data))
        return SimpleNamespace(**data)


class FakeWorkOrderRepository:
    def __init__(self):
        self.records = {
            "WO-1": SimpleNamespace(
                work_order_no="WO-1",
                product_code="P-1",
            ),
        }

    def get_by_no(self, number):
        return self.records.get(number)


def _importer(existing=None):
    return FinishedInventoryImporter(
        service=FakeInventoryService(
            existing=existing
        ),
        work_order_repository=(
            FakeWorkOrderRepository()
        ),
    )


def _frame(**overrides):
    row = {
        "Ngày nhập kho": "27/07/2026",
        "Mã công lệnh": "wo-1",
        "Mã sản phẩm": "p-1",
        "Số lượng nhập kho": 80,
    }
    row.update(overrides)
    return pd.DataFrame([row])


def _use_frame(importer, dataframe):
    importer.load_file = (
        lambda filename: dataframe
    )
    return importer


def test_preview_accepts_vietnamese_columns():
    importer = _use_frame(
        _importer(),
        _frame(),
    )

    preview = importer.preview("inventory.xlsx")

    assert preview["result"].valid == 1
    assert preview["result"].invalid == 0
    mapped = importer.map_row(
        preview["dataframe"].iloc[0]
    )
    assert mapped == {
        "inventory_date":
            date(2026, 7, 27),
        "work_order": "WO-1",
        "product_code": "P-1",
        "qty": 80,
    }


def test_preview_rejects_work_order_product_mismatch():
    importer = _use_frame(
        _importer(),
        _frame(**{
            "Mã sản phẩm": "P-2",
        }),
    )

    result = importer.preview(
        "inventory.xlsx"
    )["result"]

    assert result.invalid == 1
    assert "belongs to Product P-1" in (
        result.errors[0]["message"]
    )


def test_preview_rejects_duplicate_rows_in_file():
    dataframe = pd.concat(
        [_frame(), _frame()],
        ignore_index=True,
    )
    importer = _use_frame(
        _importer(),
        dataframe,
    )

    result = importer.preview(
        "inventory.xlsx"
    )["result"]

    assert result.valid == 1
    assert result.invalid == 1
    assert (
        result.errors[0]["message"]
        == "Duplicate row in import file."
    )


def test_import_creates_valid_inventory():
    importer = _use_frame(
        _importer(),
        _frame(),
    )

    result = importer.import_file(
        "inventory.xlsx"
    )

    assert result.created == 1
    assert result.invalid == 0
    assert importer.service.created[0][
        "qty"
    ] == 80


def test_import_skips_existing_exact_inventory():
    key = (
        date(2026, 7, 27),
        "WO-1",
        "P-1",
        80,
    )
    importer = _use_frame(
        _importer(existing={key}),
        _frame(),
    )

    result = importer.import_file(
        "inventory.xlsx"
    )

    assert result.created == 0
    assert result.skipped == 1
    assert importer.service.created == []
