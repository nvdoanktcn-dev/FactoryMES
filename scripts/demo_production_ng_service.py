from src.database.session import get_session
from src.models.production_execution import (
    ProductionExecution,
)
from src.services.production_ng_service import (
    ProductionNGService,
)


session = get_session()

try:
    execution = (
        session
        .query(ProductionExecution)
        .filter(
            ProductionExecution.status.in_(
                [
                    "RUNNING",
                    "STOPPED",
                    "COMPLETED",
                ]
            )
        )
        .order_by(
            ProductionExecution.id.asc()
        )
        .first()
    )

    if execution is None:
        raise RuntimeError(
            "No eligible Production Execution found."
        )

    service = ProductionNGService(
        session=session
    )

    processing_record = service.record_ng(
        execution.id,
        "PROCESSING",
        "DIMENSION",
        3,
        employee_code="E001",
        remark="Processing NG test",
    )

    blank_record = service.record_ng(
        execution.id,
        "BLANK",
        "CASTING_DEFECT",
        2,
        employee_code="E001",
        remark="Blank NG test",
    )

    session.flush()

    print(
        processing_record.id,
        processing_record.ng_type,
        processing_record.quantity,
    )

    print(
        blank_record.id,
        blank_record.ng_type,
        blank_record.quantity,
    )

    print(
        "Total NG:",
        execution.ng_qty,
    )

    print(
        "Processing NG:",
        execution.processing_ng_qty,
    )

    print(
        "Blank NG:",
        execution.blank_ng_qty,
    )

    assert execution.ng_qty == 5
    assert execution.processing_ng_qty == 3
    assert execution.blank_ng_qty == 2

    service.cancel_ng(
        processing_record.id
    )

    session.flush()

    assert execution.ng_qty == 2
    assert execution.processing_ng_qty == 0
    assert execution.blank_ng_qty == 2

    session.rollback()

    print(
        "ProductionNGService transaction test passed."
    )

finally:
    session.close()