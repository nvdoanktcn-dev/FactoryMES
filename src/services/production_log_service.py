from sqlalchemy.exc import IntegrityError

from src.database.session import get_session
from src.framework.base_service import BaseService
from src.framework.exception import NotFoundError, ValidationError
from src.models.production_log import ProductionLog
from src.repository.production_log_repository import ProductionLogRepository


class ProductionLogService(BaseService):
    def __init__(self):
        super().__init__()

        self.session = get_session()
        self.repository = ProductionLogRepository(self.session)

    def get_all(self):
        return self.repository.get_all()

    def get_by_id(self, log_id):
        return self.repository.get_by_id(log_id)

    def get_by_record_hash(self, record_hash):
        return self.repository.get_by_record_hash(record_hash)

    def get_by_work_order(self, work_order_no):
        return self.repository.get_by_work_order(work_order_no)

    def get_by_machine(self, machine_code):
        return self.repository.get_by_machine(machine_code)

    def get_by_employee(self, employee_code):
        return self.repository.get_by_employee(employee_code)

    def create(self, data):
        record_hash = data.get("record_hash")

        if not record_hash:
            raise ValidationError(
                "Production record_hash is required."
            )

        existing = self.repository.get_by_record_hash(record_hash)

        if existing is not None:
            raise ValidationError(
                "Duplicate production record detected."
            )

        log = ProductionLog(**data)

        try:
            self.log_info(
                f"Create Production Log: "
                f"{log.work_order_no} - {log.op_no}"
            )

            return self.repository.add(log)

        except IntegrityError as error:
            self.session.rollback()

            raise ValidationError(
                "Duplicate production record detected."
            ) from error

        except Exception:
            self.session.rollback()
            raise

    def update(self, log_id, data):
        log = self.repository.get_by_id(log_id)

        if log is None:
            raise NotFoundError(
                f"Production Log not found: {log_id}"
            )

        protected_fields = {
            "id",
            "record_hash",
        }

        for key, value in data.items():
            if key in protected_fields:
                continue

            if hasattr(log, key):
                setattr(log, key, value)

        self.repository.update()
        return log