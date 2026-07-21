from src.database.session import get_session
from src.services.production_order_generator import (
    ProductionOrderGenerator,
)


session = get_session()

try:
    generator = ProductionOrderGenerator(
        session=session
    )

    result = generator.generate(
        "WO202607001",
        auto_commit=False,
    )

    print(
        "Work Order:",
        result["work_order_no"],
    )

    print(
        "Routing Count:",
        result["routing_count"],
    )

    print(
        "Created:",
        result["created_count"],
    )

    print(
        "Skipped:",
        result["skipped_count"],
    )

    print(
        "Last Operation:",
        result["last_operation_no"],
    )

    for order in result["created"]:
        print(
            order.work_order_no,
            order.operation_no,
            order.operation_name,
            order.process_type,
            order.planned_start,
            order.planned_finish,
            order.remark,
        )

    assert result["routing_count"] > 0

    assert (
        result["created_count"]
        + result["skipped_count"]
        == result["routing_count"]
    )

    session.rollback()

    print(
        "Production Order Generator test passed."
    )

finally:
    session.close()