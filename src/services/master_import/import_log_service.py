from __future__ import annotations

from pathlib import Path

from src.database.session import get_session
from src.models.import_log import ImportLog
from src.repository.import_log_repository import (
    ImportLogRepository,
)


class ImportLogService:
    """
    Ghi và đọc lịch sử Master Import.
    """

    def __init__(
        self,
        session=None,
        auto_commit=True,
    ):
        self._owns_session = (
            session is None
        )

        self.session = (
            session
            or get_session()
        )

        self.auto_commit = bool(
            auto_commit
        )

        self.repository = (
            ImportLogRepository(
                self.session
            )
        )

    def create_log(
        self,
        *,
        module,
        file_path,
        sheet_name=None,
        user_name=None,
        total_rows=0,
        inserted_rows=0,
        updated_rows=0,
        failed_rows=0,
        duration=0.0,
        status="SUCCESS",
        message="",
    ):
        log = ImportLog(
            module=self._normalize_text(
                module,
                upper=True,
            ),
            file_name=Path(
                str(file_path or "")
            ).name,
            sheet_name=(
                self._optional_text(
                    sheet_name
                )
            ),
            user_name=(
                self._optional_text(
                    user_name
                )
            ),
            total_rows=self._to_int(
                total_rows
            ),
            inserted_rows=self._to_int(
                inserted_rows
            ),
            updated_rows=self._to_int(
                updated_rows
            ),
            failed_rows=self._to_int(
                failed_rows
            ),
            duration=self._to_float(
                duration
            ),
            status=self._normalize_text(
                status or "SUCCESS",
                upper=True,
            ),
            message=self._optional_text(
                message
            ),
        )

        self.repository.add(
            log
        )

        if self.auto_commit:
            self.session.commit()

        return log

    def get_recent(
        self,
        limit=100,
    ):
        return self.repository.get_recent(
            limit=limit
        )

    def to_history_rows(
        self,
        records,
    ):
        rows = []

        for record in records or []:
            rows.append(
                {
                    "id": record.id,
                    "time": (
                        record.import_time
                        .strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        if record.import_time
                        else ""
                    ),
                    "module": (
                        record.module or ""
                    ),
                    "file": (
                        record.file_name or ""
                    ),
                    "rows": (
                        record.total_rows or 0
                    ),
                    "success": (
                        (record.inserted_rows or 0)
                        + (record.updated_rows or 0)
                    ),
                    "failed": (
                        record.failed_rows or 0
                    ),
                    "duration": (
                        f"{float(record.duration or 0):.3f}s"
                    ),
                    "status": (
                        record.status or ""
                    ),
                    "message": (
                        record.message or ""
                    ),
                }
            )

        return rows

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def close(self):
        if self._owns_session:
            self.session.close()

    @staticmethod
    def _normalize_text(
        value,
        upper=False,
    ):
        text = str(
            value or ""
        ).strip()

        if upper:
            text = text.upper()

        return text

    @staticmethod
    def _optional_text(
        value,
    ):
        text = str(
            value or ""
        ).strip()

        return text or None

    @staticmethod
    def _to_int(
        value,
    ):
        try:
            return int(
                value or 0
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0

    @staticmethod
    def _to_float(
        value,
    ):
        try:
            return float(
                value or 0.0
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    def update_log(
        self,
        log_id,
        *,
        total_rows=None,
        inserted_rows=None,
        updated_rows=None,
        failed_rows=None,
        duration=None,    
        status=None,
        message=None,
    ):
        values = {}

        if total_rows is not None:
                values["total_rows"] = self._to_int(
                total_rows
            )

        if inserted_rows is not None:
            values["inserted_rows"] = self._to_int(
                inserted_rows
            )

        if updated_rows is not None:
            values["updated_rows"] = self._to_int(
                updated_rows
            )

        if failed_rows is not None:
            values["failed_rows"] = self._to_int(
                failed_rows
            )

        if duration is not None:
            values["duration"] = self._to_float(
                duration
            )

        if status is not None:
            values["status"] = self._normalize_text(
                status,
                upper=True,
            )

        if message is not None:
            values["message"] = self._optional_text(
                message
            )

        record = self.repository.update_log(
            log_id,
            **values,
        )

        if self.auto_commit:
            self.session.commit()

        return record

    def get_by_id(
        self,
        log_id,
    ):
        return self.repository.get_by_log_id(
            log_id
        )