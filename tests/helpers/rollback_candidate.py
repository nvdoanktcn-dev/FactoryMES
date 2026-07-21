from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def find_rollback_candidate(
    records: Iterable[Any],
    *,
    module_name: str,
    detail_service: Any,
) -> Any | None:
    expected_module = str(module_name or "").strip().upper()

    for record in records:
        module = str(
            getattr(record, "module", "") or ""
        ).strip().upper()

        status = str(
            getattr(record, "status", "") or ""
        ).strip().upper()

        if module != expected_module:
            continue

        if status != "SUCCESS":
            continue

        details = detail_service.get_by_log_id(
            record.id
        )

        if details:
            return record

    return None