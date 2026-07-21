
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, Numeric

from src.database.session import SessionLocal
from src.models.production_assignment import ProductionAssignment
from src.models.production_execution import ProductionExecution
from src.models.production_order import ProductionOrder
from src.services.oee_calculation_service import OEECalculationService


TEST_PREFIX = "OEE_TEST"


def _assert_close(
    actual,
    expected,
    tolerance=0.01,
):
    if abs(float(actual) - float(expected)) > tolerance:
        raise AssertionError(
            (
                f"Expected {expected}, "
                f"received {actual}."
            )
        )


def _default_column_value(
    column,
    *,
    unique_token,
):
    """
    Sinh giá trị an toàn cho các cột bắt buộc chưa được truyền.

    Hàm này giúp test tương thích với các phiên bản model có thêm
    trường bắt buộc nhưng không ảnh hưởng đến logic OEE.
    """

    python_type = None

    try:
        python_type = column.type.python_type
    except (AttributeError, NotImplementedError):
        python_type = None

    column_name = str(column.name or "").lower()

    if python_type is bool or isinstance(column.type, Boolean):
        return True

    if (
        python_type is int
        or isinstance(column.type, Integer)
    ):
        return 1

    if (
        python_type is float
        or isinstance(column.type, Float)
    ):
        return 0.0

    if (
        python_type is Decimal
        or isinstance(column.type, Numeric)
    ):
        return Decimal("0")

    if (
        python_type is datetime
        or isinstance(column.type, DateTime)
    ):
        return datetime.now()

    if (
        python_type is not None
        and python_type.__name__ == "date"
    ) or isinstance(column.type, Date):
        return datetime.now().date()

    if "status" in column_name:
        return "ACTIVE"

    if "unit" in column_name:
        return "PCS"

    if "name" in column_name:
        return f"{TEST_PREFIX}_{unique_token}"

    if "code" in column_name:
        return f"T{unique_token}"[:30]

    if column.unique:
        return f"{TEST_PREFIX}_{unique_token}"

    return f"{TEST_PREFIX}_{unique_token}"


def _build_model(
    model_class,
    **overrides,
):
    """
    Tạo ORM object dựa trên metadata SQLAlchemy.

    Các field đã truyền được ưu tiên. Các field bắt buộc khác được
    điền tự động để test không phụ thuộc quá chặt vào từng phiên bản
    model.
    """

    unique_token = uuid4().hex[:10].upper()
    values = dict(overrides)

    for column in model_class.__table__.columns:
        if column.primary_key and column.autoincrement:
            continue

        if column.name in values:
            continue

        if column.default is not None:
            continue

        if column.server_default is not None:
            continue

        if column.nullable:
            continue

        values[column.name] = _default_column_value(
            column,
            unique_token=unique_token,
        )

    valid_column_names = {
        column.name
        for column in model_class.__table__.columns
    }

    values = {
        key: value
        for key, value in values.items()
        if key in valid_column_names
    }

    return model_class(
        **values
    )


def _set_first_existing(
    obj,
    field_names,
    value,
):
    """
    Gán field đầu tiên tồn tại trong model.

    Nếu model chưa có field cycle time, vẫn gán dynamic attribute.
    OEECalculationService có thể đọc attribute này trong cùng session.
    """

    for field_name in field_names:
        if hasattr(obj, field_name):
            setattr(
                obj,
                field_name,
                value,
            )
            return field_name

    field_name = field_names[0]
    setattr(
        obj,
        field_name,
        value,
    )
    return field_name


def _create_test_data(
    session,
):
    token = uuid4().hex[:8].upper()

    work_order_no = (
        f"{TEST_PREFIX}_WO_{token}"
    )
    product_code = (
        f"{TEST_PREFIX}_P_{token}"
    )
    machine_code = (
        f"TBL{token[:5]}"
    )
    employee_code = (
        f"TE{token[:6]}"
    )

    production_order = _build_model(
        ProductionOrder,
        work_order_no=work_order_no,
        product_code=product_code,
        operation_no=20,
        operation_name="OEE Test Operation",
        status="RELEASED",
    )

    # 54 giây/PCS = 0.9 phút/PCS.
    # 150 PCS × 0.9 phút = 135 ideal runtime minutes.
    _set_first_existing(
        production_order,
        OEECalculationService.CYCLE_TIME_SECOND_FIELDS,
        54.0,
    )

    session.add(
        production_order
    )
    session.flush()

    assignment = _build_model(
        ProductionAssignment,
        production_order_id=production_order.id,
        machine_code=machine_code,
        employee_code=employee_code,
        shift="DAY",
        status="COMPLETED",
        planned_start=datetime(
            2099,
            1,
            10,
            8,
            0,
            0,
        ),
        planned_finish=datetime(
            2099,
            1,
            10,
            20,
            0,
            0,
        ),
    )

    session.add(
        assignment
    )
    session.flush()

    execution_1 = _build_model(
        ProductionExecution,
        assignment_id=assignment.id,
        status="STOPPED",
        start_time=datetime(
            2099,
            1,
            10,
            8,
            0,
            0,
        ),
        end_time=datetime(
            2099,
            1,
            10,
            9,
            40,
            0,
        ),
    )

    _set_first_existing(
        execution_1,
        OEECalculationService.RUNTIME_FIELDS,
        90.0,
    )
    _set_first_existing(
        execution_1,
        OEECalculationService.DOWNTIME_FIELDS,
        10.0,
    )
    _set_first_existing(
        execution_1,
        OEECalculationService.OK_QTY_FIELDS,
        90,
    )
    _set_first_existing(
        execution_1,
        OEECalculationService.TOTAL_NG_FIELDS,
        10,
    )
    _set_first_existing(
        execution_1,
        OEECalculationService.PROCESSING_NG_FIELDS,
        7,
    )
    _set_first_existing(
        execution_1,
        OEECalculationService.BLANK_NG_FIELDS,
        3,
    )

    execution_2 = _build_model(
        ProductionExecution,
        assignment_id=assignment.id,
        status="COMPLETED",
        start_time=datetime(
            2099,
            1,
            10,
            10,
            0,
            0,
        ),
        end_time=datetime(
            2099,
            1,
            10,
            11,
            0,
            0,
        ),
    )

    _set_first_existing(
        execution_2,
        OEECalculationService.RUNTIME_FIELDS,
        45.0,
    )
    _set_first_existing(
        execution_2,
        OEECalculationService.DOWNTIME_FIELDS,
        15.0,
    )
    _set_first_existing(
        execution_2,
        OEECalculationService.OK_QTY_FIELDS,
        48,
    )
    _set_first_existing(
        execution_2,
        OEECalculationService.TOTAL_NG_FIELDS,
        2,
    )
    _set_first_existing(
        execution_2,
        OEECalculationService.PROCESSING_NG_FIELDS,
        2,
    )
    _set_first_existing(
        execution_2,
        OEECalculationService.BLANK_NG_FIELDS,
        0,
    )

    session.add_all(
        [
            execution_1,
            execution_2,
        ]
    )
    session.flush()

    return SimpleNamespace(
        production_order=production_order,
        assignment=assignment,
        executions=[
            execution_1,
            execution_2,
        ],
        work_order_no=work_order_no,
        product_code=product_code,
        machine_code=machine_code,
        employee_code=employee_code,
        operation_no=20,
        start_at=datetime(
            2099,
            1,
            10,
            0,
            0,
            0,
        ),
        end_at=datetime(
            2099,
            1,
            10,
            23,
            59,
            59,
        ),
    )


def _test_summary(
    service,
    data,
):
    summary = service.calculate_summary(
        start_at=data.start_at,
        end_at=data.end_at,
        machine_code=data.machine_code,
        employee_code=data.employee_code,
        shift="DAY",
        work_order_no=data.work_order_no,
        product_code=data.product_code,
        operation_no=data.operation_no,
    )

    assert summary.execution_count == 2
    _assert_close(
        summary.runtime_minutes,
        135.0,
    )
    _assert_close(
        summary.downtime_minutes,
        25.0,
    )
    _assert_close(
        summary.planned_minutes,
        160.0,
    )

    assert summary.ok_quantity == 138
    assert summary.ng_quantity == 12
    assert summary.total_quantity == 150

    _assert_close(
        summary.ideal_runtime_minutes,
        135.0,
    )
    _assert_close(
        summary.availability,
        84.38,
    )
    _assert_close(
        summary.performance,
        100.0,
    )
    _assert_close(
        summary.quality,
        92.0,
    )
    _assert_close(
        summary.oee,
        77.63,
    )

    print(
        "\nOEE Summary"
    )
    print(
        f"  Executions   : {summary.execution_count}"
    )
    print(
        f"  Planned Min  : {summary.planned_minutes}"
    )
    print(
        f"  Runtime Min  : {summary.runtime_minutes}"
    )
    print(
        f"  Downtime Min : {summary.downtime_minutes}"
    )
    print(
        f"  OK Qty       : {summary.ok_quantity}"
    )
    print(
        f"  NG Qty       : {summary.ng_quantity}"
    )
    print(
        f"  Availability : {summary.availability}%"
    )
    print(
        f"  Performance  : {summary.performance}%"
    )
    print(
        f"  Quality      : {summary.quality}%"
    )
    print(
        f"  OEE          : {summary.oee}%"
    )


def _assert_single_group(
    results,
    expected_key,
):
    assert len(results) == 1

    result = results[0]

    assert result.group_key == expected_key
    assert result.summary.execution_count == 2
    assert result.summary.total_quantity == 150

    _assert_close(
        result.summary.oee,
        77.63,
    )


def _test_grouping(
    service,
    data,
):
    common = {
        "start_at": data.start_at,
        "end_at": data.end_at,
    }

    by_machine = service.calculate_by_machine(
        **common,
        machine_code=data.machine_code,
    )
    _assert_single_group(
        by_machine,
        data.machine_code,
    )

    by_employee = service.calculate_by_employee(
        **common,
        employee_code=data.employee_code,
    )
    _assert_single_group(
        by_employee,
        data.employee_code,
    )

    by_work_order = service.calculate_by_work_order(
        **common,
        work_order_no=data.work_order_no,
    )
    _assert_single_group(
        by_work_order,
        data.work_order_no,
    )

    by_product = service.calculate_by_product(
        **common,
        product_code=data.product_code,
    )
    _assert_single_group(
        by_product,
        data.product_code,
    )

    by_operation = service.calculate_by_operation(
        **common,
        operation_no=data.operation_no,
    )
    _assert_single_group(
        by_operation,
        "OP20",
    )

    print(
        "\nGrouping tests passed:"
    )
    print(
        "  Machine"
    )
    print(
        "  Employee"
    )
    print(
        "  Work Order"
    )
    print(
        "  Product"
    )
    print(
        "  Operation"
    )


def _test_cancelled_exclusion(
    session,
    service,
    data,
):
    cancelled_execution = _build_model(
        ProductionExecution,
        assignment_id=data.assignment.id,
        status="CANCELLED",
        start_time=datetime(
            2099,
            1,
            10,
            12,
            0,
            0,
        ),
        end_time=datetime(
            2099,
            1,
            10,
            13,
            40,
            0,
        ),
    )

    _set_first_existing(
        cancelled_execution,
        OEECalculationService.RUNTIME_FIELDS,
        90.0,
    )
    _set_first_existing(
        cancelled_execution,
        OEECalculationService.DOWNTIME_FIELDS,
        10.0,
    )
    _set_first_existing(
        cancelled_execution,
        OEECalculationService.OK_QTY_FIELDS,
        100,
    )
    _set_first_existing(
        cancelled_execution,
        OEECalculationService.TOTAL_NG_FIELDS,
        0,
    )

    session.add(
        cancelled_execution
    )
    session.flush()

    summary = service.calculate_summary(
        start_at=data.start_at,
        end_at=data.end_at,
        machine_code=data.machine_code,
    )

    # CANCELLED không được cộng vào kết quả.
    assert summary.execution_count == 2
    assert summary.total_quantity == 150

    print(
        "\nCancelled execution exclusion passed."
    )


def run_test():
    session = SessionLocal()
    transaction = session.begin_nested()

    try:
        print(
            "Create OEE transaction test data..."
        )

        data = _create_test_data(
            session
        )

        service = OEECalculationService(
            session=session
        )

        _test_summary(
            service,
            data,
        )

        _test_grouping(
            service,
            data,
        )

        _test_cancelled_exclusion(
            session,
            service,
            data,
        )

        print(
            "\nOEE Calculation Service test passed."
        )

    finally:
        if transaction.is_active:
            transaction.rollback()

        session.rollback()
        session.close()

        print(
            "Transaction rolled back."
        )


if __name__ == "__main__":
    run_test()
