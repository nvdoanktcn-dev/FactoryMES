from __future__ import annotations


def routing_entity_key(
    entity,
) -> str:
    product_code = str(
        entity.product_code or ""
    ).strip().upper()

    operation_no = int(
        entity.operation_no
    )

    return (
        f"{product_code}|{operation_no}"
    )


def routing_entity_to_service_data(
    entity,
) -> dict:
    return {
        "product_code": str(
            entity.product_code or ""
        ).strip().upper(),

        "operation_no": int(
            entity.operation_no
        ),

        "operation_name": str(
            entity.operation_name or ""
        ).strip(),

        "process_type": str(
            entity.process_type or ""
        ).strip().upper(),

        "machine_type": (
            str(
                entity.machine_type or ""
            ).strip().upper()
            or None
        ),

        "standard_cycle_time_sec": float(
            entity.standard_cycle_time_sec
            or 0.0
        ),

        "standard_output_pcs_hour": float(
            entity.standard_output_pcs_hour
            or 0.0
        ),

        "standard_operator_count": float(
            entity.standard_operator_count
            or 1.0
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


def database_routing_to_dict(
    routing,
):
    if routing is None:
        return None

    return {
        "product_code": routing.product_code,
        "operation_no": routing.operation_no,
        "operation_name": routing.operation_name,
        "process_type": routing.process_type,
        "machine_type": routing.machine_type,
        "standard_cycle_time_sec": (
            routing.standard_cycle_time_sec
        ),
        "standard_output_pcs_hour": (
            routing.standard_output_pcs_hour
        ),
        "standard_operator_count": (
            routing.standard_operator_count
        ),
        "status": routing.status,
        "remark": routing.remark,
    }