from __future__ import annotations


def employee_entity_key(
    entity,
) -> str:
    return str(
        entity.employee_code or ""
    ).strip().upper()


def employee_entity_to_service_data(
    entity,
) -> dict:
    return {
        "employee_code": str(
            entity.employee_code or ""
        ).strip().upper(),

        "employee_name": str(
            entity.employee_name or ""
        ).strip(),

        "department": (
            str(
                entity.department or ""
            ).strip()
            or None
        ),

        "position": (
            str(
                entity.position or ""
            ).strip()
            or None
        ),

        "shift": (
            str(
                entity.shift or ""
            ).strip().upper()
            or None
        ),

        "status": (
            str(
                entity.status or "ACTIVE"
            ).strip().upper()
            or "ACTIVE"
        ),

        "remark": (
            str(
                entity.remark or ""
            ).strip()
            or None
        ),
    }


def database_employee_to_dict(
    employee,
):
    if employee is None:
        return None

    return {
        "employee_code": (
            employee.employee_code
        ),
        "employee_name": (
            employee.employee_name
        ),
        "department": (
            employee.department
        ),
        "position": (
            employee.position
        ),
        "shift": (
            employee.shift
        ),
        "status": (
            employee.status
        ),
        "remark": (
            employee.remark
        ),
    }