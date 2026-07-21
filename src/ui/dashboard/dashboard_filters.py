from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True, slots=True)
class OEEDashboardFilters:
    start_date: date
    end_date: date

    machine_code: str | None = None
    employee_code: str | None = None
    shift: str | None = None
    work_order_no: str | None = None
    product_code: str |None = None
    operation_no: str | None = None

    def __post_init__(self):
        if self.start_date > self.end_date:
            raise ValueError(
                "Ngày bắt đầu không được lớn hơn ngày kết thúc."
            )

    @staticmethod
    def _normalize(value):
        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        if value.lower() in (
            "tất cả",
            "tat ca",
            "all",
        ):
            return None

        return value

    def to_service_kwargs(self):
        kwargs = {
            "start_date": self.start_date,
            "end_date": self.end_date,
        }

        for name in (
            "machine_code",
            "employee_code",
            "shift",
            "work_order_no",
            "product_code",
            "operation_no",
        ):
            value = self._normalize(
                getattr(self, name)
            )

            if value is not None:
                kwargs[name] = value

        return kwargs