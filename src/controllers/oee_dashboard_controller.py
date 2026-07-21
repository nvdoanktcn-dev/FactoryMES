from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime, time
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence

from sqlalchemy.orm import Session

from src.database.session import SessionLocal
from src.services.oee_calculation_service import OEECalculationService


@dataclass(slots=True)
class OEEDashboardFilters:
    """
    Bộ lọc dùng chung cho OEE Dashboard.

    start_date và end_date có thể truyền date hoặc datetime.
    Khi là date:
    - start_date được chuyển thành 00:00:00
    - end_date được chuyển thành 23:59:59.999999
    """

    start_date: date | datetime
    end_date: date | datetime

    machine_code: str | None = None
    employee_code: str | None = None
    shift: str | None = None
    work_order_no: str | None = None
    product_code: str | None = None
    operation_no: int | str | None = None

    def normalized(self) -> "OEEDashboardFilters":
        start_at = self._to_start_datetime(
            self.start_date
        )
        end_at = self._to_end_datetime(
            self.end_date
        )

        if end_at < start_at:
            raise ValueError(
                "End date must be greater than or equal to start date."
            )

        return OEEDashboardFilters(
            start_date=start_at,
            end_date=end_at,
            machine_code=self._clean_text(
                self.machine_code
            ),
            employee_code=self._clean_text(
                self.employee_code
            ),
            shift=self._clean_text(
                self.shift
            ),
            work_order_no=self._clean_text(
                self.work_order_no
            ),
            product_code=self._clean_text(
                self.product_code
            ),
            operation_no=self._clean_operation_no(
                self.operation_no
            ),
        )

    def to_service_kwargs(self) -> dict[str, Any]:
        normalized = self.normalized()

        kwargs: dict[str, Any] = {
            "start_at": normalized.start_date,
            "end_at": normalized.end_date,
        }

        optional_values = {
            "machine_code": normalized.machine_code,
            "employee_code": normalized.employee_code,
            "shift": normalized.shift,
            "work_order_no": normalized.work_order_no,
            "product_code": normalized.product_code,
            "operation_no": normalized.operation_no,
        }

        for key, value in optional_values.items():
            if value is not None:
                kwargs[key] = value

        return kwargs

    @staticmethod
    def _to_start_datetime(
        value: date | datetime,
    ) -> datetime:
        if isinstance(value, datetime):
            return value

        return datetime.combine(
            value,
            time.min,
        )

    @staticmethod
    def _to_end_datetime(
        value: date | datetime,
    ) -> datetime:
        if isinstance(value, datetime):
            return value

        return datetime.combine(
            value,
            time.max,
        )

    @staticmethod
    def _clean_text(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = str(value).strip()

        if not cleaned:
            return None

        if cleaned.upper() in {
            "ALL",
            "TẤT CẢ",
            "TAT CA",
        }:
            return None

        return cleaned

    @staticmethod
    def _clean_operation_no(
        value: int | str | None,
    ) -> int | str | None:
        if value is None:
            return None

        if isinstance(value, int):
            return value

        cleaned = str(value).strip().upper()

        if not cleaned or cleaned in {
            "ALL",
            "TẤT CẢ",
            "TAT CA",
        }:
            return None

        if cleaned.startswith("OP"):
            cleaned = cleaned[2:].strip()

        if cleaned.isdigit():
            return int(cleaned)

        return cleaned


@dataclass(slots=True)
class OEEDashboardData:
    """
    Dữ liệu hoàn chỉnh trả về cho OEE Dashboard UI.
    """

    summary: dict[str, Any] = field(
        default_factory=dict
    )
    by_machine: list[dict[str, Any]] = field(
        default_factory=list
    )
    by_employee: list[dict[str, Any]] = field(
        default_factory=list
    )
    by_work_order: list[dict[str, Any]] = field(
        default_factory=list
    )
    by_product: list[dict[str, Any]] = field(
        default_factory=list
    )
    by_operation: list[dict[str, Any]] = field(
        default_factory=list
    )


class OEEDashboardController:
    """
    Controller trung gian giữa OEE Dashboard UI và
    OEECalculationService.

    Controller tự quản lý SQLAlchemy Session cho mỗi lần load.
    Vì vậy UI không cần tự commit hoặc rollback.
    """

    def __init__(
        self,
        session_factory: Callable[[], Session] = SessionLocal,
        service_class: type[OEECalculationService] = (
            OEECalculationService
        ),
    ) -> None:
        self._session_factory = session_factory
        self._service_class = service_class

    def load_dashboard(
        self,
        filters: OEEDashboardFilters,
    ) -> OEEDashboardData:
        """
        Tải toàn bộ KPI và các bảng breakdown trong một session.
        """

        kwargs = filters.to_service_kwargs()
        session = self._session_factory()

        try:
            service = self._service_class(
                session=session
            )

            result = OEEDashboardData(
                summary=self._normalize_summary(
                    service.calculate_summary(
                        **kwargs
                    )
                ),
                by_machine=self._normalize_groups(
                    service.calculate_by_machine(
                        **kwargs
                    )
                ),
                by_employee=self._normalize_groups(
                    service.calculate_by_employee(
                        **kwargs
                    )
                ),
                by_work_order=self._normalize_groups(
                    service.calculate_by_work_order(
                        **kwargs
                    )
                ),
                by_product=self._normalize_groups(
                    service.calculate_by_product(
                        **kwargs
                    )
                ),
                by_operation=self._normalize_groups(
                    service.calculate_by_operation(
                        **kwargs
                    )
                ),
            )

            session.rollback()
            return result

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    def load_summary(
        self,
        filters: OEEDashboardFilters,
    ) -> dict[str, Any]:
        return self._load_single(
            filters=filters,
            loader_name="calculate_summary",
            normalizer=self._normalize_summary,
        )

    def load_by_machine(
        self,
        filters: OEEDashboardFilters,
    ) -> list[dict[str, Any]]:
        return self._load_single(
            filters=filters,
            loader_name="calculate_by_machine",
            normalizer=self._normalize_groups,
        )

    def load_by_employee(
        self,
        filters: OEEDashboardFilters,
    ) -> list[dict[str, Any]]:
        return self._load_single(
            filters=filters,
            loader_name="calculate_by_employee",
            normalizer=self._normalize_groups,
        )

    def load_by_work_order(
        self,
        filters: OEEDashboardFilters,
    ) -> list[dict[str, Any]]:
        return self._load_single(
            filters=filters,
            loader_name="calculate_by_work_order",
            normalizer=self._normalize_groups,
        )

    def load_by_product(
        self,
        filters: OEEDashboardFilters,
    ) -> list[dict[str, Any]]:
        return self._load_single(
            filters=filters,
            loader_name="calculate_by_product",
            normalizer=self._normalize_groups,
        )

    def load_by_operation(
        self,
        filters: OEEDashboardFilters,
    ) -> list[dict[str, Any]]:
        return self._load_single(
            filters=filters,
            loader_name="calculate_by_operation",
            normalizer=self._normalize_groups,
        )

    def _load_single(
        self,
        *,
        filters: OEEDashboardFilters,
        loader_name: str,
        normalizer: Callable[[Any], Any],
    ) -> Any:
        kwargs = filters.to_service_kwargs()
        session = self._session_factory()

        try:
            service = self._service_class(
                session=session
            )
            loader = getattr(
                service,
                loader_name,
            )
            raw_result = loader(
                **kwargs
            )

            session.rollback()
            return normalizer(
                raw_result
            )

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    @classmethod
    def _normalize_summary(
        cls,
        summary: Any,
    ) -> dict[str, Any]:
        raw = cls._to_mapping(
            summary
        )

        normalized = {
            "execution_count": cls._to_int(
                raw.get(
                    "execution_count",
                    0,
                )
            ),
            "planned_minutes": cls._to_float(
                raw.get(
                    "planned_minutes",
                    0,
                )
            ),
            "runtime_minutes": cls._to_float(
                raw.get(
                    "runtime_minutes",
                    0,
                )
            ),
            "downtime_minutes": cls._to_float(
                raw.get(
                    "downtime_minutes",
                    0,
                )
            ),
            "ideal_runtime_minutes": cls._to_float(
                raw.get(
                    "ideal_runtime_minutes",
                    0,
                )
            ),
            "ok_quantity": cls._to_int(
                raw.get(
                    "ok_quantity",
                    0,
                )
            ),
            "processing_ng_quantity": cls._to_int(
                raw.get(
                    "processing_ng_quantity",
                    raw.get(
                        "processing_ng",
                        0,
                    ),
                )
            ),
            "blank_ng_quantity": cls._to_int(
                raw.get(
                    "blank_ng_quantity",
                    raw.get(
                        "blank_ng",
                        0,
                    ),
                )
            ),
            "ng_quantity": cls._to_int(
                raw.get(
                    "ng_quantity",
                    raw.get(
                        "total_ng_quantity",
                        0,
                    ),
                )
            ),
            "total_quantity": cls._to_int(
                raw.get(
                    "total_quantity",
                    0,
                )
            ),
            "availability": cls._to_float(
                raw.get(
                    "availability",
                    0,
                )
            ),
            "performance": cls._to_float(
                raw.get(
                    "performance",
                    0,
                )
            ),
            "quality": cls._to_float(
                raw.get(
                    "quality",
                    0,
                )
            ),
            "oee": cls._to_float(
                raw.get(
                    "oee",
                    0,
                )
            ),
        }

        # Giữ lại các field bổ sung từ service nếu có.
        for key, value in raw.items():
            if key not in normalized:
                normalized[key] = value

        return normalized

    @classmethod
    def _normalize_groups(
        cls,
        groups: Iterable[Any] | None,
    ) -> list[dict[str, Any]]:
        if groups is None:
            return []

        normalized: list[dict[str, Any]] = []

        for item in groups:
            raw = cls._to_mapping(
                item
            )

            group_key = raw.get(
                "group_key",
                raw.get(
                    "key",
                    raw.get(
                        "code",
                        "",
                    ),
                ),
            )
            group_label = raw.get(
                "group_label",
                raw.get(
                    "label",
                    raw.get(
                        "name",
                        group_key,
                    ),
                ),
            )

            summary_source = raw.get(
                "summary"
            )

            if summary_source is None:
                summary_source = raw

            summary = cls._normalize_summary(
                summary_source
            )

            row = {
                "group_key": (
                    ""
                    if group_key is None
                    else str(group_key)
                ),
                "group_label": (
                    ""
                    if group_label is None
                    else str(group_label)
                ),
                **summary,
            }

            normalized.append(
                row
            )

        return normalized

    @staticmethod
    def _to_mapping(
        value: Any,
    ) -> dict[str, Any]:
        if value is None:
            return {}

        if isinstance(value, Mapping):
            return dict(value)

        if is_dataclass(value):
            return asdict(value)

        if hasattr(
            value,
            "_asdict",
        ):
            return dict(
                value._asdict()
            )

        if hasattr(
            value,
            "__dict__",
        ):
            return {
                key: item
                for key, item in vars(value).items()
                if not key.startswith("_")
            }

        raise TypeError(
            (
                "Unsupported OEE result type: "
                f"{type(value).__name__}"
            )
        )

    @staticmethod
    def _to_float(
        value: Any,
    ) -> float:
        if value in {
            None,
            "",
        }:
            return 0.0

        return round(
            float(value),
            2,
        )

    @staticmethod
    def _to_int(
        value: Any,
    ) -> int:
        if value in {
            None,
            "",
        }:
            return 0

        return int(
            round(
                float(value)
            )
        )
