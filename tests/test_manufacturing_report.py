from datetime import date, datetime
from types import SimpleNamespace

from openpyxl import load_workbook

from src.services.manufacturing_analytics_service import (
    ManufacturingAnalyticsService,
)
from src.services.manufacturing_report_export_service import (
    ManufacturingReportExportService,
)
from src.services.production_history_service import (
    ProductionHistoryService,
)


def _record(
    *,
    record_id,
    day,
    work_order,
    product,
    operation,
    machine,
    ok_qty,
    ng_qty=0,
    runtime=3600,
):
    return SimpleNamespace(
        id=record_id,
        start_time=datetime.combine(
            day,
            datetime.min.time(),
        ),
        work_order_no=work_order,
        product_code=product,
        op_no=operation,
        machine_code=machine,
        employee_code="E001",
        shift="DAY",
        status="COMPLETED",
        run_time_sec=runtime,
        downtime_min=0,
        ok_qty=ok_qty,
        ng_qty=ng_qty,
    )


def _history_service():
    # The tested aggregation helpers do not access the repository/session.
    return ProductionHistoryService.__new__(
        ProductionHistoryService
    )


def test_final_output_summary_keeps_all_runtime():
    service = _history_service()
    records = [
        _record(
            record_id=1,
            day=date(2026, 7, 1),
            work_order="WO-1",
            product="P-1",
            operation="OP1",
            machine="BL01",
            ok_qty=100,
            runtime=3600,
        ),
        _record(
            record_id=2,
            day=date(2026, 7, 2),
            work_order="WO-1",
            product="P-1",
            operation="OP2",
            machine="BL02",
            ok_qty=90,
            ng_qty=2,
            runtime=7200,
        ),
    ]

    summary = service.build_final_output_summary(
        records
    )

    assert summary["runtime_hour"] == 3
    assert summary["ok_qty"] == 90
    assert summary["ng_qty"] == 2
    assert summary["total_qty"] == 92


def test_daily_final_output_is_selected_before_grouping():
    service = _history_service()
    records = [
        _record(
            record_id=1,
            day=date(2026, 7, 1),
            work_order="WO-1",
            product="P-1",
            operation="OP1",
            machine="BL01",
            ok_qty=100,
        ),
        _record(
            record_id=2,
            day=date(2026, 7, 2),
            work_order="WO-1",
            product="P-1",
            operation="OP2",
            machine="BL02",
            ok_qty=90,
        ),
    ]

    daily = service.group_by_date(
        records,
        final_output_only=True,
    )

    assert daily[0]["runtime_hour"] == 1
    assert daily[0]["total_qty"] == 0
    assert daily[1]["runtime_hour"] == 1
    assert daily[1]["total_qty"] == 90


def test_machine_group_code_conventions():
    service = ManufacturingAnalyticsService

    assert service._machine_group_for_code("BL01") == "CNC"
    assert service._machine_group_for_code("BR11") == "ROBOT"
    assert service._machine_group_for_code("ASK03") == "ROBOT"
    assert service._machine_group_for_code("OTHER") == "OTHER"


def test_export_creates_expected_workbook(tmp_path):
    report = {
        "period": {
            "start_date": date(2026, 7, 1),
            "end_date": date(2026, 7, 31),
        },
        "filters": {
            "machine_group": "CNC",
        },
        "summary": {
            "record_count": 2,
            "runtime_hour": 3,
            "ok_qty": 90,
            "ng_qty": 2,
            "total_qty": 92,
            "yield_percent": 97.83,
        },
        "machine": [{
            "machine_code": "BL01",
            "record_count": 1,
            "runtime_hour": 1,
            "utilization_percent": 100,
        }],
        "daily": [],
        "employee": [],
        "product": [],
        "work_order": [],
    }

    target = (
        ManufacturingReportExportService()
        .export(
            report,
            tmp_path / "report.xlsx",
        )
    )

    workbook = load_workbook(
        target,
        data_only=True,
    )

    assert workbook.sheetnames == [
        "Summary",
        "Machine Utilization",
        "Daily",
        "Employee Efficiency",
        "By Product",
        "By Work Order",
    ]
    assert (
        workbook["Machine Utilization"]["A2"].value
        == "BL01"
    )
