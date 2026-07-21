from src.database.session import get_session
from src.services.master_import.import_detail_service import (
    ImportDetailService,
)
from src.services.master_import.import_log_service import (
    ImportLogService,
)
from src.services.master_import.rollback_service import (
    RollbackService,
)


session = get_session()

try:
    log_service = ImportLogService(
        session=session,
        auto_commit=False,
    )

    detail_service = ImportDetailService(
        session=session,
        auto_commit=False,
    )

    target = None

    for record in log_service.get_recent(
        limit=100
    ):
        if str(
            record.module or ""
        ).strip().upper() != "ROUTING":
            continue

        if str(
            record.status or ""
        ).strip().upper() != "SUCCESS":
            continue

        details = detail_service.get_by_log_id(
            record.id
        )

        if details:
            target = record
            break

    if target is None:
        raise RuntimeError(
            (
                "No rollback-ready SUCCESS "
                "Routing import found."
            )
        )

    print(
        "Rollback target:",
        target.id,
        target.file_name,
        target.status,
    )

    result = RollbackService(
        session=session
    ).rollback_import(
        target.id
    )

    print(result)

    refreshed = log_service.get_by_id(
        target.id
    )

    assert refreshed is not None
    assert refreshed.status == "ROLLED_BACK"

    print(
        "Routing rollback test passed."
    )

finally:
    session.close()