from __future__ import annotations

import json

from src.database.session import (
    get_session,
)
from src.models.import_detail import (
    ImportDetail,
)
from src.repository.import_detail_repository import (
    ImportDetailRepository,
)


class ImportDetailService:
    """
    Ghi và đọc chi tiết của một lần Master Import.
    """

    ACTION_INSERT = "INSERT"
    ACTION_UPDATE = "UPDATE"
    ACTION_DELETE = "DELETE"

    def __init__(
        self,
        session=None,
        auto_commit=False,
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
            ImportDetailRepository(
                self.session
            )
        )

    def record_insert(
        self,
        *,
        log_id,
        module,
        entity_key,
        new_data,
    ):
        return self._create_detail(
            log_id=log_id,
            module=module,
            action=self.ACTION_INSERT,
            entity_key=entity_key,
            old_data=None,
            new_data=new_data,
        )

    def record_update(
        self,
        *,
        log_id,
        module,
        entity_key,
        old_data,
        new_data,
    ):
        return self._create_detail(
            log_id=log_id,
            module=module,
            action=self.ACTION_UPDATE,
            entity_key=entity_key,
            old_data=old_data,
            new_data=new_data,
        )

    def record_delete(
        self,
        *,
        log_id,
        module,
        entity_key,
        old_data,
    ):
        return self._create_detail(
            log_id=log_id,
            module=module,
            action=self.ACTION_DELETE,
            entity_key=entity_key,
            old_data=old_data,
            new_data=None,
        )

    def get_by_log_id(
        self,
        log_id,
        reverse=False,
    ):
        if reverse:
            return (
                self.repository
                .get_by_log_id_reverse(
                    log_id
                )
            )

        return self.repository.get_by_log_id(
            log_id
        )

    def _create_detail(
        self,
        *,
        log_id,
        module,
        action,
        entity_key,
        old_data,
        new_data,
    ):
        detail = ImportDetail(
            log_id=int(log_id),
            module=self._normalize_text(
                module,
                upper=True,
            ),
            action=self._normalize_text(
                action,
                upper=True,
            ),
            entity_key=self._normalize_text(
                entity_key,
                upper=False,
            ),
            old_json=self._to_json(
                old_data
            ),
            new_json=self._to_json(
                new_data
            ),
        )

        self.repository.add(
            detail
        )

        if self.auto_commit:
            self.session.commit()

        return detail

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def close(self):
        if self._owns_session:
            self.session.close()

    @staticmethod
    def _to_json(
        value,
    ):
        if value is None:
            return None

        return json.dumps(
            value,
            ensure_ascii=False,
            default=str,
        )

    @staticmethod
    def from_json(
        value,
    ):
        if not value:
            return None

        return json.loads(
            value
        )

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