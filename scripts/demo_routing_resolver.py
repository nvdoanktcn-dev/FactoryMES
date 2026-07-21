from src.database.session import get_session
from src.engine.routing_resolver import RoutingResolver


WORK_ORDER_NO = "WO001"


def main() -> None:
    session = get_session()

    try:
        resolver = RoutingResolver(
            session=session,
        )

        last_operation = resolver.get_last_operation(
            WORK_ORDER_NO
        )

        print("Last OP:", last_operation.op_no)
        print("Sequence:", last_operation.sequence)

        result = resolver.calculate_completed_quantity(
            WORK_ORDER_NO
        )

        print("Completed result:")

        for key, value in result.items():
            print(f"{key}: {value}")

        print("\nOperation summary:")

        summary = resolver.get_operation_summary(
            WORK_ORDER_NO
        )

        for op_no, values in summary.items():
            print(op_no, values)

    finally:
        session.rollback()
        session.close()


if __name__ == "__main__":
    main()