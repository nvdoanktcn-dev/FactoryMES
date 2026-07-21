from src.database.session import get_session
from src.models.production_order import (
    ProductionOrder,
)
from src.services.production_assignment_service import (
    ProductionAssignmentService,
)


session = get_session()

try:
    production_orders = (
        session
        .query(ProductionOrder)
        .order_by(
            ProductionOrder.id.asc()
        )
        .limit(2)
        .all()
    )

    if not production_orders:
        raise RuntimeError(
            "No Production Order found."
        )

    first_order = production_orders[0]

    second_order = (
        production_orders[1]
        if len(production_orders) > 1
        else production_orders[0]
    )

    service = ProductionAssignmentService(
        session=session
    )

    first = service.create_assignment(
        {
            "production_order_id": (
                first_order.id
            ),
            "machine_code": "BL01",
            "employee_code": "E001",
            "shift": "DAY",
            "planned_start": (
                "2026-07-20 08:00"
            ),
            "planned_finish": (
                "2026-07-20 12:00"
            ),
            "status": "DRAFT",
            "remark": "Conflict test 1",
        }
    )

    session.flush()

    second = service.create_assignment(
        {
            "production_order_id": (
                second_order.id
            ),
            "machine_code": "BL02",
            "employee_code": "E001",
            "shift": "DAY",
            "planned_start": (
                "2026-07-20 09:00"
            ),
            "planned_finish": (
                "2026-07-20 11:00"
            ),
            "status": "DRAFT",
            "remark": "Conflict test 2",
        }
    )

    session.flush()

    print(
        "Both DRAFT assignments created:",
        first.id,
        second.id,
    )

    # Assignment đầu tiên chưa xung đột với Assignment RELEASED nào.
    service.release(
        first.id
    )

    print(
        "First assignment released."
    )

    try:
        service.release(
            second.id
        )

    except ValueError as error:
        print(
            "Expected conflict:"
        )
        print(
            error
        )

        assert (
            "Resource conflict detected"
            in str(error)
        )

    else:
        raise AssertionError(
            (
                "Second assignment should "
                "have been rejected."
            )
        )

    session.rollback()

    print(
        "Resource Conflict Service test passed."
    )

finally:
    session.close()