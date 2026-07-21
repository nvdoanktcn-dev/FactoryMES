from __future__ import annotations

from src.models.import_log import ImportLog
from src.repository.base_repository import (
    BaseRepository,
)


class ImportLogRepository(
    BaseRepository
):
    def __init__(
        self,
        session,
    ):
        super().__init__(
            session=session,
            model=ImportLog,
        )

    def get_recent(
        self,
        limit=100,
    ):
        try:
            normalized_limit = max(
                1,
                int(limit),
            )
        except (
            TypeError,
            ValueError,
        ):
            normalized_limit = 100

        return (
            self.session
            .query(ImportLog)
            .order_by(
                ImportLog.import_time.desc(),
                ImportLog.id.desc(),
            )
            .limit(normalized_limit)
            .all()
        )

    def get_by_log_id(
        self,
        log_id,
    ):
        return self.get_by_id(
            log_id
        )

    def update_log(
        self,
        log_id,
        **values,
    ):
        record = self.get_by_log_id(
            log_id
        )

        if record is None:
            raise ValueError(
                f"Import Log not found: {log_id}"
            )

        for field_name, value in values.items():
            if hasattr(
                record,
                field_name,
            ):
                setattr(
                    record,
                    field_name,
                    value,
                )

        self.session.flush()

        return record