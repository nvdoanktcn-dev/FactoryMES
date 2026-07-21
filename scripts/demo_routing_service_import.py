from src.database.session import get_session
from src.services.routing_service import (
    RoutingService,
)


session = get_session()

try:
    service = RoutingService(
        session=session
    )

    routing, action = service.save_routing(
        {
            "product_code": "TEST-P001",
            "operation_no": "OP10",
            "operation_name": "CNC Turning",
            "process_type": "CNC",
            "machine_type": "CNC",
            "standard_cycle_time_sec": 45,
            "standard_output_pcs_hour": 80,
            "standard_operator_count": 1,
            "status": "ACTIVE",
            "remark": "Transaction test",
        }
    )

    print(
        routing.product_code,
        routing.operation_no,
        action,
    )

    assert routing.product_code == (
        "TEST-P001"
    )

    assert routing.operation_no == 10

    assert action in {
        "created",
        "updated",
    }

    session.rollback()

    print(
        "RoutingService transaction test passed."
    )

finally:
    session.close()