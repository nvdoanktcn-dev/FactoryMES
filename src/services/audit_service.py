import json

from src.database.session import get_session
from src.models.audit_log import AuditLog


class AuditService:

    def __init__(self):
        self.session = get_session()

    def write(
        self,
        table_name,
        record_id,
        action,
        old_value=None,
        new_value=None,
        username="System"
    ):

        log = AuditLog(
            table_name=table_name,
            record_id=record_id,
            action=action,
            old_value=json.dumps(old_value, ensure_ascii=False) if old_value else None,
            new_value=json.dumps(new_value, ensure_ascii=False) if new_value else None,
            username=username,
        )

        self.session.add(log)
        self.session.commit()