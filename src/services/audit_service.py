from __future__ import annotations

import json

from src.database.session import get_session
from src.models.audit_log import AuditLog


class AuditService:
    def __init__(
        self,
        session=None,
        *,
        auto_commit=True,
    ):
        self._owns_session = session is None
        self.session = session or get_session()
        self.auto_commit = bool(auto_commit)

    def write(
        self,
        table_name,
        record_id,
        action,
        old_value=None,
        new_value=None,
        username="System",
    ):
        log = AuditLog(
            table_name=table_name,
            record_id=record_id,
            action=action,
            old_value=self._serialize(old_value),
            new_value=self._serialize(new_value),
            username=str(username or "System"),
        )
        self.session.add(log)
        self.session.flush()
        if self.auto_commit:
            self.session.commit()
        return log

    def get_by_id(self, audit_id):
        try:
            normalized_id = int(audit_id)
        except (TypeError, ValueError):
            return None
        return self.session.get(AuditLog, normalized_id)

    def get_recent(
        self,
        *,
        table_name=None,
        limit=100,
    ):
        try:
            normalized_limit = max(1, int(limit))
        except (TypeError, ValueError):
            normalized_limit = 100
        query = self.session.query(AuditLog)
        if table_name:
            query = query.filter(
                AuditLog.table_name
                == str(table_name)
            )
        return (
            query
            .order_by(
                AuditLog.created_at.desc(),
                AuditLog.id.desc(),
            )
            .limit(normalized_limit)
            .all()
        )

    def close(self):
        if self._owns_session:
            self.session.close()

    @staticmethod
    def _serialize(value):
        if value is None:
            return None
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
        )
