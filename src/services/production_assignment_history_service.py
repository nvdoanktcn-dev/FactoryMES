from __future__ import annotations

import json
from datetime import date, datetime

from src.models.production_assignment_history import ProductionAssignmentHistory
from src.repository.production_assignment_history_repository import ProductionAssignmentHistoryRepository


class ProductionAssignmentHistoryService:
    def __init__(self, session):
        if session is None:
            raise ValueError("SQLAlchemy session is required.")
        self.session = session
        self.repository = ProductionAssignmentHistoryRepository(session)

    def record(self, *, assignment, action, old_data=None, new_data=None,
               changed_by="FactoryMES User", remark=None):
        old_data = dict(old_data or {})
        new_data = dict(new_data or {})
        history = ProductionAssignmentHistory(
            assignment_id=int(assignment.id),
            production_order_id=int(assignment.production_order_id),
            action=str(action or "").strip().upper(),
            old_status=old_data.get("status"),
            new_status=new_data.get("status"),
            old_machine_code=old_data.get("machine_code"),
            new_machine_code=new_data.get("machine_code"),
            old_employee_code=old_data.get("employee_code"),
            new_employee_code=new_data.get("employee_code"),
            old_shift=old_data.get("shift"),
            new_shift=new_data.get("shift"),
            old_data_json=self._to_json(old_data),
            new_data_json=self._to_json(new_data),
            changed_by=str(changed_by or "FactoryMES User").strip(),
            remark=str(remark).strip() if remark else None,
        )
        return self.repository.add(history)

    def get_by_assignment_id(self, assignment_id):
        return self.repository.get_by_assignment_id(assignment_id)

    def get_by_production_order_id(self, production_order_id):
        return self.repository.get_by_production_order_id(production_order_id)

    @staticmethod
    def assignment_to_dict(assignment):
        if assignment is None:
            return {}
        return {
            "id": assignment.id,
            "production_order_id": assignment.production_order_id,
            "machine_code": assignment.machine_code,
            "employee_code": assignment.employee_code,
            "shift": assignment.shift,
            "planned_start": assignment.planned_start,
            "planned_finish": assignment.planned_finish,
            "status": assignment.status,
            "assigned_at": assignment.assigned_at,
            "released_at": assignment.released_at,
            "actual_start": assignment.actual_start,
            "actual_finish": assignment.actual_finish,
            "remark": assignment.remark,
        }

    @classmethod
    def _to_json(cls, data):
        return json.dumps(data, ensure_ascii=False, default=cls._json_default)

    @staticmethod
    def _json_default(value):
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return str(value)
