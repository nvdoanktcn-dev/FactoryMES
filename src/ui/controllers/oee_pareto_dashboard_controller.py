from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Callable, Iterable, Mapping, Sequence

from sqlalchemy.orm import Session

from src.database.session import SessionLocal
from src.services.oee_pareto_service import (
    OEEParetoService,
    ParetoFilter,
    ParetoResult,
)
from src.ui.controllers.oee_dashboard_controller import (
    OEEDashboardFilters,
)


RecordLoader = Callable[[Session], Iterable[object]]


@dataclass(frozen=True, slots=True)
class OEEParetoDashboardData:
    """
    Kết quả Pareto dùng cho OEE Dashboard.
    """

    downtime: ParetoResult
    ng: ParetoResult


class OEEParetoDashboardController:
    """
    Controller tải dữ liệu Pareto Downtime và Pareto NG.

    Thiết kế:
    - Tự quản lý SQLAlchemy Session.
    - Có thể inject record loader để kiểm thử độc lập.
    - Mặc định đọc ProductionDowntime và ProductionNG.
    - Chuẩn hóa model SQLAlchemy thành dictionary trước khi
      chuyển cho OEEParetoService.
    - Dùng chung bộ lọc với OEEDashboardFilters.
    """

    def __init__(
        self,
        session_factory: Callable[[], Session] = SessionLocal,
        pareto_service: OEEParetoService | None = None,
        downtime_loader: RecordLoader | None = None,
        ng_loader: RecordLoader | None = None,
        maximum_items: int = 10,
        focus_threshold: float = 80.0,
    ) -> None:
        if maximum_items < 1:
            raise ValueError(
                "maximum_items must be greater than or equal to 1."
            )

        if not 0 < focus_threshold <= 100:
            raise ValueError(
                "focus_threshold must be greater than 0 and at most 100."
            )

        self._session_factory = session_factory
        self._pareto_service = (
            pareto_service
            if pareto_service is not None
            else OEEParetoService()
        )
        self._downtime_loader = (
            downtime_loader
            if downtime_loader is not None
            else self._default_downtime_loader
        )
        self._ng_loader = (
            ng_loader
            if ng_loader is not None
            else self._default_ng_loader
        )
        self._maximum_items = maximum_items
        self._focus_threshold = focus_threshold

    def load_all(
        self,
        filters: OEEDashboardFilters,
    ) -> OEEParetoDashboardData:
        """
        Tải đồng thời Downtime Pareto và NG Pareto trong một session.
        """

        normalized_filter = self._build_pareto_filter(
            filters
        )
        session = self._session_factory()

        try:
            downtime_records = self._normalize_downtime_records(
                self._downtime_loader(session)
            )
            ng_records = self._normalize_ng_records(
                self._ng_loader(session)
            )

            result = OEEParetoDashboardData(
                downtime=self._pareto_service.build_downtime_pareto(
                    downtime_records,
                    filters=normalized_filter,
                    maximum_items=self._maximum_items,
                    focus_threshold=self._focus_threshold,
                ),
                ng=self._pareto_service.build_ng_pareto(
                    ng_records,
                    filters=normalized_filter,
                    maximum_items=self._maximum_items,
                    focus_threshold=self._focus_threshold,
                ),
            )

            session.rollback()
            return result

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    def load_downtime_pareto(
        self,
        filters: OEEDashboardFilters,
    ) -> ParetoResult:
        return self._load_single(
            filters=filters,
            loader=self._downtime_loader,
            normalizer=self._normalize_downtime_records,
            builder=self._pareto_service.build_downtime_pareto,
        )

    def load_ng_pareto(
        self,
        filters: OEEDashboardFilters,
    ) -> ParetoResult:
        return self._load_single(
            filters=filters,
            loader=self._ng_loader,
            normalizer=self._normalize_ng_records,
            builder=self._pareto_service.build_ng_pareto,
        )

    def _load_single(
        self,
        *,
        filters: OEEDashboardFilters,
        loader: RecordLoader,
        normalizer: Callable[
            [Iterable[object]],
            list[dict[str, Any]],
        ],
        builder: Callable[..., ParetoResult],
    ) -> ParetoResult:
        normalized_filter = self._build_pareto_filter(
            filters
        )
        session = self._session_factory()

        try:
            records = normalizer(
                loader(session)
            )
            result = builder(
                records,
                filters=normalized_filter,
                maximum_items=self._maximum_items,
                focus_threshold=self._focus_threshold,
            )

            session.rollback()
            return result

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    @staticmethod
    def _build_pareto_filter(
        filters: OEEDashboardFilters,
    ) -> ParetoFilter:
        normalized = filters.normalized()

        return ParetoFilter(
            start_date=normalized.start_date,
            end_date=normalized.end_date,
            machine_codes=OEEParetoDashboardController._single_code(
                normalized.machine_code
            ),
            employee_codes=OEEParetoDashboardController._single_code(
                normalized.employee_code
            ),
            work_order_codes=OEEParetoDashboardController._single_code(
                normalized.work_order_no
            ),
            product_codes=OEEParetoDashboardController._single_code(
                normalized.product_code
            ),
        ).normalized()

    @staticmethod
    def _single_code(
        value: object | None,
    ) -> tuple[str, ...]:
        if value is None:
            return ()

        text = str(value).strip()

        return (text,) if text else ()

    @classmethod
    def _normalize_downtime_records(
        cls,
        records: Iterable[object],
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []

        for record in records:
            raw = cls._record_to_mapping(record)

            normalized.append(
                {
                    **raw,
                    "reason": cls._first_value(
                        raw,
                        (
                            "reason",
                            "reason_name",
                            "downtime_reason",
                            "reason_code",
                        ),
                    ),
                    "duration_minutes": cls._first_value(
                        raw,
                        (
                            "duration_minutes",
                            "downtime_minutes",
                            "minutes",
                            "duration",
                        ),
                    ),
                    "production_date": cls._first_date_value(
                        raw,
                        (
                            "production_date",
                            "record_date",
                            "event_date",
                            "date",
                            "start_time",
                            "started_at",
                            "created_at",
                        ),
                    ),
                    "machine_code": cls._first_value(
                        raw,
                        (
                            "machine_code",
                            "device_code",
                            "machine",
                        ),
                    ),
                    "employee_code": cls._first_value(
                        raw,
                        (
                            "employee_code",
                            "operator_code",
                            "employee",
                            "operator",
                        ),
                    ),
                    "work_order_code": cls._first_value(
                        raw,
                        (
                            "work_order_code",
                            "work_order_no",
                            "work_order",
                            "production_order_code",
                        ),
                    ),
                    "product_code": cls._first_value(
                        raw,
                        (
                            "product_code",
                            "product",
                            "item_code",
                        ),
                    ),
                }
            )

        return normalized

    @classmethod
    def _normalize_ng_records(
        cls,
        records: Iterable[object],
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []

        for record in records:
            raw = cls._record_to_mapping(record)

            normalized.append(
                {
                    **raw,
                    "reason": cls._first_value(
                        raw,
                        (
                            "reason",
                            "reason_name",
                            "ng_reason",
                            "defect_reason",
                            "defect_type",
                            "reason_code",
                            "ng_type",
                        ),
                    ),
                    "quantity": cls._first_value(
                        raw,
                        (
                            "quantity",
                            "ng_quantity",
                            "defect_quantity",
                            "count",
                        ),
                    ),
                    "production_date": cls._first_date_value(
                        raw,
                        (
                            "production_date",
                            "record_date",
                            "event_date",
                            "date",
                            "recorded_at",
                            "created_at",
                        ),
                    ),
                    "machine_code": cls._first_value(
                        raw,
                        (
                            "machine_code",
                            "device_code",
                            "machine",
                        ),
                    ),
                    "employee_code": cls._first_value(
                        raw,
                        (
                            "employee_code",
                            "operator_code",
                            "employee",
                            "operator",
                        ),
                    ),
                    "work_order_code": cls._first_value(
                        raw,
                        (
                            "work_order_code",
                            "work_order_no",
                            "work_order",
                            "production_order_code",
                        ),
                    ),
                    "product_code": cls._first_value(
                        raw,
                        (
                            "product_code",
                            "product",
                            "item_code",
                        ),
                    ),
                }
            )

        return normalized

    @staticmethod
    def _record_to_mapping(
        record: object,
    ) -> dict[str, Any]:
        if isinstance(record, Mapping):
            return dict(record)

        table = getattr(
            record,
            "__table__",
            None,
        )

        if table is not None:
            return {
                column.name: getattr(
                    record,
                    column.name,
                    None,
                )
                for column in table.columns
            }

        if hasattr(
            record,
            "__dict__",
        ):
            return {
                key: value
                for key, value in vars(record).items()
                if not key.startswith("_")
            }

        field_names = (
            "reason",
            "reason_name",
            "reason_code",
            "duration_minutes",
            "downtime_minutes",
            "quantity",
            "ng_quantity",
            "ng_type",
            "production_date",
            "record_date",
            "start_time",
            "recorded_at",
            "created_at",
            "machine_code",
            "employee_code",
            "work_order_code",
            "work_order_no",
            "product_code",
        )

        result = {
            field_name: getattr(
                record,
                field_name,
            )
            for field_name in field_names
            if hasattr(
                record,
                field_name,
            )
        }

        if result:
            return result

        raise TypeError(
            (
                "Unsupported Pareto record type: "
                f"{type(record).__name__}"
            )
        )

    @staticmethod
    def _first_value(
        source: Mapping[str, Any],
        field_names: Sequence[str],
    ) -> Any:
        for field_name in field_names:
            value = source.get(
                field_name
            )

            if value is not None:
                return value

        return None

    @classmethod
    def _first_date_value(
        cls,
        source: Mapping[str, Any],
        field_names: Sequence[str],
    ) -> date | datetime | str | None:
        value = cls._first_value(
            source,
            field_names,
        )

        if value is None:
            return None

        if isinstance(
            value,
            (date, datetime),
        ):
            return value

        text = str(value).strip()

        return text or None

    @staticmethod
    def _default_downtime_loader(
        session: Session,
    ) -> Iterable[object]:
        from src.models.production_downtime import (
            ProductionDowntime,
        )

        return (
            session.query(
                ProductionDowntime
            )
            .all()
        )

    @staticmethod
    def _default_ng_loader(
        session: Session,
    ) -> Iterable[object]:
        from src.models.production_ng import (
            ProductionNG,
        )

        return (
            session.query(
                ProductionNG
            )
            .all()
        )
