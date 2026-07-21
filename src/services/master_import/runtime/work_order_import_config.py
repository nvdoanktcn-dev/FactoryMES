from __future__ import annotations


def work_order_entity_key(
    entity,
) -> str:
    return str(
        entity.work_order_no or ""
    ).strip().upper()


def work_order_entity_to_service_data(
    entity,
) -> dict:
    return {
        "work_order_no": str(
            entity.work_order_no or ""
        ).strip().upper(),

        "product_code": str(
            entity.product_code or ""
        ).strip().upper(),

        "plan_qty": int(
            entity.plan_qty
        ),

        "start_date": entity.start_date,

        "due_date": entity.due_date,

        "priority": (
            str(
                entity.priority or "NORMAL"
            ).strip().upper()
            or "NORMAL"
        ),

        "status": (
            str(
                entity.status or "PLANNED"
            ).strip().upper()
            or "PLANNED"
        ),

        "remark": (
            str(
                entity.remark or ""
            ).strip()
            or None
        ),
    }


def database_work_order_to_dict(
    work_order,
):
    if work_order is None:
        return None

    return {
        "work_order_no": (
            work_order.work_order_no
        ),
        "product_code": (
            work_order.product_code
        ),
        "plan_qty": (
            work_order.plan_qty
        ),
        "start_date": (
            work_order.start_date
        ),
        "due_date": (
            work_order.due_date
        ),
        "priority": (
            work_order.priority
        ),
        "status": (
            work_order.status
        ),
        "remark": (
            work_order.remark
        ),
    }