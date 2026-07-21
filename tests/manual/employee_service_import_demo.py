from src.database.session import get_session
from src.services.employee_service import (
    EmployeeService,
)


session = get_session()

try:
    service = EmployeeService(
        session=session
    )

    employee, action = service.save_employee(
        {
            "employee_code": "TEST-E001",
            "employee_name": "Test Employee",
            "department": "CNC",
            "position": "Operator",
            "shift": "DAY",
            "status": "ACTIVE",
            "remark": "Transaction test",
        }
    )

    print(
        employee.employee_code,
        action,
    )

    assert employee.employee_code == (
        "TEST-E001"
    )

    assert action in {
        "created",
        "updated",
    }

    session.rollback()

    print(
        "EmployeeService transaction test passed."
    )

finally:
    session.close()