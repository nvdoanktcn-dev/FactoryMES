from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.execution.exceptions import (
    InvalidDowntimeEventError,
)


class DowntimeReason(str, Enum):
    WAIT_OPERATOR = "WAIT_OPERATOR"
    WAIT_MATERIAL = "WAIT_MATERIAL"
    WAIT_ORDER = "WAIT_ORDER"
    CHANGE_MODEL = "CHANGE_MODEL"
    MAINTENANCE = "MAINTENANCE"
    REPAIR = "REPAIR"
    POWER_LOSS = "POWER_LOSS"
    PROGRAMMING = "PROGRAMMING"

    @property
    def is_planned(self) -> bool:
        return self in {
            DowntimeReason.CHANGE_MODEL,
            DowntimeReason.MAINTENANCE,
            DowntimeReason.PROGRAMMING,
        }

    @property
    def is_unplanned(self) -> bool:
        return not self.is_planned


@dataclass(frozen=True)
class DowntimeEvent:
    machine_code: str
    work_order_code: str
    reason: DowntimeReason
    start_time: datetime
    end_time: datetime
    note: str = ""

    def __post_init__(self) -> None:
        machine_code = self._normalize_required(
            self.machine_code,
            "machine_code",
        )
        work_order_code = self._normalize_required(
            self.work_order_code,
            "work_order_code",
        )

        reason = self._normalize_reason(
            self.reason
        )

        if not isinstance(self.start_time, datetime):
            raise InvalidDowntimeEventError(
                "start_time must be a datetime instance."
            )

        if not isinstance(self.end_time, datetime):
            raise InvalidDowntimeEventError(
                "end_time must be a datetime instance."
            )

        if self.end_time <= self.start_time:
            raise InvalidDowntimeEventError(
                "end_time must be later than start_time."
            )

        note = str(self.note).strip()

        object.__setattr__(
            self,
            "machine_code",
            machine_code,
        )
        object.__setattr__(
            self,
            "work_order_code",
            work_order_code,
        )
        object.__setattr__(
            self,
            "reason",
            reason,
        )
        object.__setattr__(
            self,
            "note",
            note,
        )

    @property
    def duration_minutes(self) -> float:
        duration = self.end_time - self.start_time

        return duration.total_seconds() / 60

    @property
    def is_planned(self) -> bool:
        return self.reason.is_planned

    @property
    def is_unplanned(self) -> bool:
        return self.reason.is_unplanned

    @staticmethod
    def _normalize_required(
        value: str,
        field_name: str,
    ) -> str:
        normalized = str(value).strip().upper()

        if not normalized:
            raise InvalidDowntimeEventError(
                f"{field_name} must not be empty."
            )

        return normalized

    @staticmethod
    def _normalize_reason(
        reason: DowntimeReason,
    ) -> DowntimeReason:
        if isinstance(reason, DowntimeReason):
            return reason

        try:
            return DowntimeReason(
                str(reason).strip().upper()
            )
        except ValueError as exc:
            raise InvalidDowntimeEventError(
                f"Invalid downtime reason: {reason}."
            ) from exc