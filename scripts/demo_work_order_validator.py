from datetime import date

from src.database.session import get_session
from src.validator.work_order_validator import (
    WorkOrderValidator,
)


def main() -> None:
    session = get_session()

    try:
        validator = WorkOrderValidator(
            session=session,
        )

        data = {
            "work_order_no": "WO001",
            "product_code": "P001",
            "plan_qty": 100,
            "completed_qty": 0,
            "ng_qty": 0,
            "start_date": date(2026, 7, 1),
            "due_date": date(2026, 7, 31),
            "finish_date": None,
            "status": "PLANNED",
            "priority": "NORMAL",
            "remark": "",
        }

        validator.validate(
            data,
            allow_existing=True,
        )

        print("WorkOrderValidator test passed.")

    finally:
        session.rollback()
        session.close()


if __name__ == "__main__":
    main()