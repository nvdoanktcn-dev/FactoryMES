from __future__ import annotations

from collections.abc import Iterator

from src.execution.downtime import (
    DowntimeEvent,
    DowntimeReason,
)
from src.execution.exceptions import (
    DowntimeEventNotFoundError,
    DuplicateDowntimeEventError,
    InvalidDowntimeEventError,
)


class DowntimeTracker:
    """Quản lý và tổng hợp các sự kiện dừng máy."""

    def __init__(self) -> None:
        self._events: dict[
            str,
            DowntimeEvent,
        ] = {}

    def add(
        self,
        event: DowntimeEvent,
    ) -> None:
        self._validate_event(event)

        key = self._build_key(event)

        if key in self._events:
            raise DuplicateDowntimeEventError(
                f"Downtime event already exists: {key}."
            )

        self._validate_overlap(event)

        self._events[key] = event

    def get(
        self,
        machine_code: str,
        start_time,
        end_time,
    ) -> DowntimeEvent:
        key = self._build_key_from_values(
            machine_code=machine_code,
            start_time=start_time,
            end_time=end_time,
        )

        try:
            return self._events[key]
        except KeyError as exc:
            raise DowntimeEventNotFoundError(
                f"Downtime event not found: {key}."
            ) from exc

    def remove(
        self,
        machine_code: str,
        start_time,
        end_time,
    ) -> DowntimeEvent:
        key = self._build_key_from_values(
            machine_code=machine_code,
            start_time=start_time,
            end_time=end_time,
        )

        try:
            return self._events.pop(key)
        except KeyError as exc:
            raise DowntimeEventNotFoundError(
                f"Downtime event not found: {key}."
            ) from exc

    def find_by_machine(
        self,
        machine_code: str,
    ) -> tuple[DowntimeEvent, ...]:
        normalized = self._normalize_required(
            machine_code,
            "machine_code",
        )

        return tuple(
            event
            for event in self._sorted_events()
            if event.machine_code == normalized
        )

    def find_by_work_order(
        self,
        work_order_code: str,
    ) -> tuple[DowntimeEvent, ...]:
        normalized = self._normalize_required(
            work_order_code,
            "work_order_code",
        )

        return tuple(
            event
            for event in self._sorted_events()
            if event.work_order_code == normalized
        )

    def find_by_reason(
        self,
        reason: DowntimeReason,
    ) -> tuple[DowntimeEvent, ...]:
        normalized_reason = self._normalize_reason(
            reason
        )

        return tuple(
            event
            for event in self._sorted_events()
            if event.reason is normalized_reason
        )

    def find_planned(
        self,
    ) -> tuple[DowntimeEvent, ...]:
        return tuple(
            event
            for event in self._sorted_events()
            if event.is_planned
        )

    def find_unplanned(
        self,
    ) -> tuple[DowntimeEvent, ...]:
        return tuple(
            event
            for event in self._sorted_events()
            if event.is_unplanned
        )

    @property
    def total_events(self) -> int:
        return len(self._events)

    @property
    def total_minutes(self) -> float:
        return sum(
            event.duration_minutes
            for event in self._events.values()
        )

    @property
    def planned_minutes(self) -> float:
        return sum(
            event.duration_minutes
            for event in self._events.values()
            if event.is_planned
        )

    @property
    def unplanned_minutes(self) -> float:
        return sum(
            event.duration_minutes
            for event in self._events.values()
            if event.is_unplanned
        )

    def total_minutes_by_machine(
        self,
        machine_code: str,
    ) -> float:
        return sum(
            event.duration_minutes
            for event in self.find_by_machine(
                machine_code
            )
        )

    def total_minutes_by_reason(
        self,
        reason: DowntimeReason,
    ) -> float:
        return sum(
            event.duration_minutes
            for event in self.find_by_reason(
                reason
            )
        )

    def clear(self) -> None:
        self._events.clear()

    def __len__(self) -> int:
        return len(self._events)

    def __iter__(self) -> Iterator[DowntimeEvent]:
        return iter(
            self._sorted_events()
        )

    def __contains__(
        self,
        event: object,
    ) -> bool:
        if not isinstance(event, DowntimeEvent):
            return False

        return self._build_key(event) in self._events

    def _validate_overlap(
        self,
        new_event: DowntimeEvent,
    ) -> None:
        for current_event in self._events.values():
            if (
                current_event.machine_code
                != new_event.machine_code
            ):
                continue

            overlaps = (
                new_event.start_time
                < current_event.end_time
                and new_event.end_time
                > current_event.start_time
            )

            if overlaps:
                raise InvalidDowntimeEventError(
                    "Downtime events for the same "
                    "machine must not overlap."
                )

    def _sorted_events(
        self,
    ) -> tuple[DowntimeEvent, ...]:
        return tuple(
            sorted(
                self._events.values(),
                key=lambda event: (
                    event.start_time,
                    event.machine_code,
                ),
            )
        )

    @classmethod
    def _build_key(
        cls,
        event: DowntimeEvent,
    ) -> str:
        return cls._build_key_from_values(
            machine_code=event.machine_code,
            start_time=event.start_time,
            end_time=event.end_time,
        )

    @classmethod
    def _build_key_from_values(
        cls,
        machine_code: str,
        start_time,
        end_time,
    ) -> str:
        machine = cls._normalize_required(
            machine_code,
            "machine_code",
        )

        return (
            f"{machine}|"
            f"{start_time.isoformat()}|"
            f"{end_time.isoformat()}"
        )

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

    @staticmethod
    def _validate_event(
        event: DowntimeEvent,
    ) -> None:
        if not isinstance(event, DowntimeEvent):
            raise InvalidDowntimeEventError(
                "event must be a DowntimeEvent instance."
            )