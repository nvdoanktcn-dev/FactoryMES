from sqlalchemy import desc

from src.repository.base_repository import BaseRepository
from src.models.production_log import ProductionLog
from datetime import datetime, time, timedelta


class ProductionLogRepository(BaseRepository):
    """
    Repository truy cập dữ liệu ProductionLog.
    """

    def __init__(self, session):
        super().__init__(session, ProductionLog)

    def get_by_record_hash(self, record_hash):
        return (
            self.session.query(ProductionLog)
            .filter(
                ProductionLog.record_hash == record_hash
            )
            .first()
        )

    def get_by_work_order(self, work_order_no):
        work_order_no = str(
            work_order_no or ""
        ).strip().upper()

        return (
            self.session.query(ProductionLog)
            .filter(
                ProductionLog.work_order_no
                == work_order_no
            )
            .order_by(
                ProductionLog.start_time,
                ProductionLog.id,
            )
            .all()
        )


    def get_by_machine(self, machine_code):
        machine_code = str(
            machine_code or ""
        ).strip().upper()

        return (
            self.session.query(ProductionLog)
            .filter(
                ProductionLog.machine_code
                == machine_code
            )
            .order_by(
                desc(ProductionLog.start_time),
                desc(ProductionLog.id),
            )
            .all()
        )

    def get_by_employee(self, employee_code):
        employee_code = str(
            employee_code or ""
        ).strip().upper()

        return (
            self.session.query(ProductionLog)
            .filter(
                ProductionLog.employee_code
                == employee_code
            )
            .order_by(
                desc(ProductionLog.start_time),
                desc(ProductionLog.id),
            )
            .all()
        )

    def get_running(self):
        return (
            self.session.query(ProductionLog)
            .filter(
                ProductionLog.status == "RUNNING"
            )
            .order_by(
                ProductionLog.start_time,
                ProductionLog.id,
            )
            .all()
        )

    def get_completed(self):
        return (
            self.session.query(ProductionLog)
            .filter(
                ProductionLog.status == "COMPLETED"
            )
            .order_by(
                desc(ProductionLog.start_time),
                desc(ProductionLog.id),
            )
            .all()
        )

    def get_by_date_range(
        self,
        start_date,
        end_date,
        machine_code=None,
    ):
        """
        Lấy Production Log theo ngày bắt đầu sản xuất.

        end_date được tính bao gồm toàn bộ ngày cuối.
        """
        start_datetime = datetime.combine(
            start_date,
            time.min,
        )

        end_datetime = datetime.combine(
            end_date + timedelta(days=1),
            time.min,
        )

        query = (
            self.session.query(ProductionLog)
            .filter(
                ProductionLog.start_time >= start_datetime,
                ProductionLog.start_time < end_datetime,
            )
        )

        if machine_code:
            machine_code = str(
                machine_code
            ).strip().upper()

            query = query.filter(
                ProductionLog.machine_code
                == machine_code
            )

        return (
            query
            .order_by(
                ProductionLog.start_time,
                ProductionLog.id,
            )
            .all()
        )

    def get_by_machine_date(
        self,
        machine_code,
        production_date,
    ):
        return self.get_by_date_range(
            start_date=production_date,
            end_date=production_date,
            machine_code=machine_code,
        )