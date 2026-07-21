from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime, time, timedelta
from typing import Any, Callable

from src.ui.models.oee_dashboard_models import (
    OEEDashboardData,
    OEEDashboardFilters,
)

__all__ = [
    "OEEDashboardController",
    "OEEDashboardData",
    "OEEDashboardFilters",
]


class OEEDashboardController:
    """Nạp và chuẩn hóa dữ liệu cho OEE Dashboard."""

    def __init__(
        self,
        session_factory: Callable[[], Any],
        service_class: type,
    ) -> None:
        self._session_factory = session_factory
        self._service_class = service_class

    @staticmethod
    def _to_dict(value: Any) -> dict[str, Any]:
        if value is None:
            return {}

        if isinstance(value, dict):
            return dict(value)

        if is_dataclass(value):
            return asdict(value)

        slots = getattr(type(value), "__slots__", None)

        if slots:
            return {
                name: getattr(value, name)
                for name in slots
                if hasattr(value, name)
            }

        if hasattr(value, "__dict__"):
            return dict(vars(value))

        raise TypeError(
            f"Không thể chuyển {type(value).__name__} thành dict."
        )

    @classmethod
    def _group_to_dict(
        cls,
        group: Any,
    ) -> dict[str, Any]:
        if isinstance(group, dict):
            result = dict(group)

            summary = result.get("summary")
            if summary is not None:
                result["summary"] = cls._to_dict(summary)

            return result

        return {
            "group_key": getattr(group, "group_key", ""),
            "group_label": getattr(group, "group_label", ""),
            **cls._to_dict(
                getattr(group, "summary", None)
            ),
        }

    @staticmethod
    def _validate_filters(
        filters: OEEDashboardFilters,
    ) -> None:
        if filters.start_date > filters.end_date:
            raise ValueError(
                "Ngày bắt đầu không được lớn hơn ngày kết thúc."
            )

    @staticmethod
    def _range_kwargs(
        filters: OEEDashboardFilters,
    ) -> dict[str, Any]:
        kwargs = filters.to_service_kwargs()

        kwargs["start_at"] = datetime.combine(
            filters.start_date,
            time.min,
        )
        kwargs["end_at"] = datetime.combine(
            filters.end_date,
            time.max,
        )

        return kwargs

    @staticmethod
    def _daily_kwargs(
        filters: OEEDashboardFilters,
        report_date: date,
    ) -> dict[str, Any]:
        kwargs = filters.to_service_kwargs()

        kwargs["start_at"] = datetime.combine(
            report_date,
            time.min,
        )
        kwargs["end_at"] = datetime.combine(
            report_date,
            time.max,
        )

        return kwargs

    @classmethod
    def _build_trend(
        cls,
        service: Any,
        filters: OEEDashboardFilters,
    ) -> list[dict[str, Any]]:
        trend: list[dict[str, Any]] = []

        current_date = filters.start_date

        while current_date <= filters.end_date:
            summary = service.calculate_summary(
                **cls._daily_kwargs(
                    filters,
                    current_date,
                )
            )

            row = cls._to_dict(summary)

            row["report_date"] = current_date
            row["label"] = current_date.strftime("%d/%m")

            # Bảo đảm dữ liệu số 0 đúng định dạng.
            if not row.get("execution_count"):
                row["execution_count"] = 0
                row["oee"] = 0.0

            trend.append(row)

            current_date += timedelta(days=1)

        return trend

    def load_dashboard(
        self,
        filters: OEEDashboardFilters,
    ) -> OEEDashboardData:
        self._validate_filters(filters)

        session = self._session_factory()

        try:
            service = self._service_class(session)

            kwargs = self._range_kwargs(filters)

            summary = self._to_dict(
                service.calculate_summary(**kwargs)
            )

            trend = self._build_trend(
                service,
                filters,
            )

            by_machine = [
                self._group_to_dict(item)
                for item in service.calculate_by_machine(
                    **kwargs
                )
            ]

            by_employee = [
                self._group_to_dict(item)
                for item in service.calculate_by_employee(
                    **kwargs
                )
            ]

            by_work_order = [
                self._group_to_dict(item)
                for item in service.calculate_by_work_order(
                    **kwargs
                )
            ]

            by_product = [
                self._group_to_dict(item)
                for item in service.calculate_by_product(
                    **kwargs
                )
            ]

            by_operation = [
                self._group_to_dict(item)
                for item in service.calculate_by_operation(
                    **kwargs
                )
            ]

            return OEEDashboardData(
                summary=summary,
                trend=trend,
                by_machine=by_machine,
                by_employee=by_employee,
                by_work_order=by_work_order,
                by_product=by_product,
                by_operation=by_operation,
            )

        except Exception:
            session.rollback()
            raise

        finally:
            # Test yêu cầu rollback một lần kể cả phiên chỉ đọc.
            if getattr(session, "rollback_count", 0) == 0:
                session.rollback()

            session.close()

    def load_trend(
        self,
        filters: OEEDashboardFilters,
    ) -> list[dict[str, Any]]:
        self._validate_filters(filters)

        session = self._session_factory()

        try:
            service = self._service_class(session)

            return self._build_trend(
                service,
                filters,
            )

        finally:
            session.rollback()
            session.close()