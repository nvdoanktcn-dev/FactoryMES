import hashlib
import json
from datetime import date, datetime


HASH_FIELDS = [
    "work_order_no",
    "product_code",
    "op_no",
    "machine_code",
    "employee_code",
    "shift",
    "start_time",
    "finish_time",
    "run_time_sec",
    "ok_qty",
    "ng_qty",
]


def _normalize_value(value):
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")

    if isinstance(value, date):
        return value.isoformat()

    if value is None:
        return ""

    if isinstance(value, float):
        return round(value, 6)

    return value


def create_production_record_hash(data):
    if not isinstance(data, dict):
        raise ValueError("Production data must be a dictionary.")

    payload = {
        field: _normalize_value(data.get(field))
        for field in HASH_FIELDS
    }

    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()