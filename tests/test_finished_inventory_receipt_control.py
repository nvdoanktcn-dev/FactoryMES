from types import SimpleNamespace

import pytest

from src.framework.exception import ValidationError
from src.services.finished_inventory_receipt_control_service import (
    FinishedInventoryReceiptControlService,
)


class Repository:
    def __init__(self, records):
        self.records = list(records)

    def get_all(self):
        return list(self.records)


class WorkOrders(Repository):
    def get_by_no(self, number):
        return next(
            (
                item
                for item in self.records
                if item.work_order_no == number
            ),
            None,
        )


class ProductionOrders(Repository):
    def get_by_work_order(self, number):
        return [
            item
            for item in self.records
            if item.work_order_no == number
        ]


class ProductionLogs(Repository):
    def get_by_work_order(self, number):
        return [
            item
            for item in self.records
            if item.work_order_no == number
        ]


def make_service(inventory=()):
    return FinishedInventoryReceiptControlService(
        work_order_repository=WorkOrders([
            SimpleNamespace(
                work_order_no="WO-1",
                product_code="P-1",
            )
        ]),
        production_order_repository=ProductionOrders([
            SimpleNamespace(
                work_order_no="WO-1",
                product_code="P-1",
                operation_no=10,
                status="COMPLETED",
            ),
            SimpleNamespace(
                work_order_no="WO-1",
                product_code="P-1",
                operation_no=20,
                status="COMPLETED",
            ),
        ]),
        production_log_repository=ProductionLogs([
            SimpleNamespace(
                work_order_no="WO-1",
                product_code="P-1",
                op_no="10",
                ok_qty=100,
                status="COMPLETED",
            ),
            SimpleNamespace(
                work_order_no="WO-1",
                product_code="P-1",
                op_no="20",
                ok_qty=80,
                status="COMPLETED",
            ),
        ]),
        finished_inventory_repository=Repository(inventory),
    )


def test_capacity_uses_only_final_operation_output():
    service = make_service([
        SimpleNamespace(
            inventory_id=1,
            work_order="WO-1",
            product_code="P-1",
            qty=30,
        )
    ])

    capacity = service.get_capacity("WO-1", "P-1")

    assert capacity["final_operation"] == 20
    assert capacity["final_op_qty"] == 80
    assert capacity["received_qty"] == 30
    assert capacity["available_qty"] == 50


def test_over_receipt_is_blocked():
    service = make_service([
        SimpleNamespace(
            inventory_id=1,
            work_order="WO-1",
            product_code="P-1",
            qty=30,
        )
    ])

    with pytest.raises(
        ValidationError,
        match="exceeds Final OP availability",
    ):
        service.validate_receipt({
            "work_order": "WO-1",
            "product_code": "P-1",
            "qty": 51,
        })


def test_edit_excludes_current_inventory_record():
    service = make_service([
        SimpleNamespace(
            inventory_id=7,
            work_order="WO-1",
            product_code="P-1",
            qty=60,
        )
    ])

    capacity = service.validate_receipt(
        {
            "work_order": "WO-1",
            "product_code": "P-1",
            "qty": 70,
        },
        exclude_inventory_id=7,
    )

    assert capacity["available_qty"] == 80
    assert capacity["remaining_qty"] == 10


def test_reserved_import_rows_are_included():
    service = make_service()

    with pytest.raises(ValidationError):
        service.validate_receipt(
            {
                "work_order": "WO-1",
                "product_code": "P-1",
                "qty": 31,
            },
            reserved_qty=50,
        )
