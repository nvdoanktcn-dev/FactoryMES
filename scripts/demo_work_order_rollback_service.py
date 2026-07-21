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
        module_name = str(
            record.module or ""
        ).strip().upper()

        status = str(
            record.status or ""
        ).strip().upper()

        if module_name != "WORK_ORDER":
            continue

        if status != "SUCCESS":
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
                "Work Order import found."
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
        "Work Order rollback test passed."
    )

finally:
    session.close()