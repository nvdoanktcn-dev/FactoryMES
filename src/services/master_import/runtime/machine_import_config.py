from __future__ import annotations


def machine_entity_key(
    entity,
) -> str:
    return str(
        entity.machine_code or ""
    ).strip().upper()


def machine_entity_to_service_data(
    entity,
) -> dict:
    return {
        "machine_code": str(
            entity.machine_code or ""
        ).strip().upper(),

        "machine_name": str(
            entity.machine_name or ""
        ).strip(),

        "machine_type": (
            str(
                entity.machine_type or ""
            ).strip().upper()
            or None
        ),

        "line": (
            str(
                entity.line or ""
            ).strip()
            or None
        ),

        "location": (
            str(
                entity.location or ""
            ).strip()
            or None
        ),

        "brand": (
            str(
                entity.brand or ""
            ).strip()
            or None
        ),

        "model": (
            str(
                entity.model or ""
            ).strip()
            or None
        ),

        "serial_number": (
            str(
                entity.serial_number or ""
            ).strip()
            or None
        ),

        "status": (
            str(
                entity.status or "RUNNING"
            ).strip().upper()
            or "RUNNING"
        ),
    }


def database_machine_to_dict(
    machine,
):
    if machine is None:
        return None

    return {
        "machine_code": machine.machine_code,
        "machine_name": machine.machine_name,
        "machine_type": machine.machine_type,
        "line": machine.line,
        "location": machine.location,
        "brand": machine.brand,
        "model": machine.model,
        "serial_number": machine.serial_number,
        "status": machine.status,
    }