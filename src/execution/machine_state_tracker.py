from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime

from src.execution.exceptions import (
    DuplicateMachineError,
    InvalidMachineStateError,
    InvalidMachineTransitionError,
    MachineNotFoundError,
)
from src.execution.machine_state import MachineState


@dataclass(frozen=True)
class MachineStateChange:
    machine_code: str
    previous_state: MachineState | None
    current_state: MachineState
    changed_at: datetime
    reason: str = ""

    def __post_init__(self) -> None:
        machine_code = str(self.machine_code).strip().upper()

        if not machine_code:
            raise InvalidMachineStateError(
                "machine_code must not be empty."
            )

        if not isinstance(self.current_state, MachineState):
            raise InvalidMachineStateError(
                "current_state must be a MachineState."
            )

        if (
            self.previous_state is not None
            and not isinstance(
                self.previous_state,
                MachineState,
            )
        ):
            raise InvalidMachineStateError(
                "previous_state must be a MachineState or None."
            )

        if not isinstance(self.changed_at, datetime):
            raise InvalidMachineStateError(
                "changed_at must be a datetime."
            )

        object.__setattr__(
            self,
            "machine_code",
            machine_code,
        )
        object.__setattr__(
            self,
            "reason",
            str(self.reason).strip(),
        )


class MachineStateTracker:
    """Quản lý trạng thái hiện tại và lịch sử trạng thái máy."""

    _ALLOWED_TRANSITIONS: dict[
        MachineState,
        set[MachineState],
    ] = {
        MachineState.OFFLINE: {
            MachineState.IDLE,
            MachineState.MAINTENANCE,
        },
        MachineState.IDLE: {
            MachineState.RUNNING,
            MachineState.OFFLINE,
            MachineState.DOWNTIME,
            MachineState.MAINTENANCE,
        },
        MachineState.RUNNING: {
            MachineState.IDLE,
            MachineState.PAUSED,
            MachineState.DOWNTIME,
            MachineState.MAINTENANCE,
        },
        MachineState.PAUSED: {
            MachineState.RUNNING,
            MachineState.IDLE,
            MachineState.DOWNTIME,
            MachineState.MAINTENANCE,
        },
        MachineState.DOWNTIME: {
            MachineState.IDLE,
            MachineState.MAINTENANCE,
            MachineState.OFFLINE,
        },
        MachineState.MAINTENANCE: {
            MachineState.IDLE,
            MachineState.DOWNTIME,
            MachineState.OFFLINE,
        },
    }

    def __init__(self) -> None:
        self._states: dict[str, MachineState] = {}
        self._histories: dict[
            str,
            list[MachineStateChange],
        ] = {}

    def register(
        self,
        machine_code: str,
        initial_state: MachineState = MachineState.OFFLINE,
        *,
        changed_at: datetime | None = None,
        reason: str = "",
    ) -> MachineStateChange:
        machine = self._normalize_machine_code(
            machine_code
        )
        state = self._normalize_state(
            initial_state
        )

        if machine in self._states:
            raise DuplicateMachineError(
                f"Machine already registered: {machine}."
            )

        change = MachineStateChange(
            machine_code=machine,
            previous_state=None,
            current_state=state,
            changed_at=changed_at or datetime.now(),
            reason=reason,
        )

        self._states[machine] = state
        self._histories[machine] = [change]

        return change

    def unregister(
        self,
        machine_code: str,
    ) -> MachineState:
        machine = self._require_machine(
            machine_code
        )

        state = self._states.pop(machine)
        self._histories.pop(machine)

        return state

    def get_state(
        self,
        machine_code: str,
    ) -> MachineState:
        machine = self._require_machine(
            machine_code
        )
        return self._states[machine]

    def transition(
        self,
        machine_code: str,
        new_state: MachineState,
        *,
        changed_at: datetime | None = None,
        reason: str = "",
    ) -> MachineStateChange:
        machine = self._require_machine(
            machine_code
        )
        target_state = self._normalize_state(
            new_state
        )
        current_state = self._states[machine]

        if target_state is current_state:
            raise InvalidMachineTransitionError(
                f"Machine {machine} is already "
                f"in state {current_state.value}."
            )

        allowed_states = self._ALLOWED_TRANSITIONS[
            current_state
        ]

        if target_state not in allowed_states:
            raise InvalidMachineTransitionError(
                f"Invalid machine transition: "
                f"{current_state.value} -> "
                f"{target_state.value}."
            )

        timestamp = changed_at or datetime.now()
        history = self._histories[machine]

        if (
            history
            and timestamp < history[-1].changed_at
        ):
            raise InvalidMachineTransitionError(
                "changed_at must not be earlier "
                "than the latest state change."
            )

        change = MachineStateChange(
            machine_code=machine,
            previous_state=current_state,
            current_state=target_state,
            changed_at=timestamp,
            reason=reason,
        )

        self._states[machine] = target_state
        history.append(change)

        return change

    def find_by_state(
        self,
        state: MachineState,
    ) -> tuple[str, ...]:
        normalized_state = self._normalize_state(
            state
        )

        return tuple(
            sorted(
                machine
                for machine, current_state
                in self._states.items()
                if current_state is normalized_state
            )
        )

    def get_history(
        self,
        machine_code: str,
    ) -> tuple[MachineStateChange, ...]:
        machine = self._require_machine(
            machine_code
        )

        return tuple(
            self._histories[machine]
        )

    def get_last_change(
        self,
        machine_code: str,
    ) -> MachineStateChange:
        history = self.get_history(
            machine_code
        )
        return history[-1]

    def count_by_state(
        self,
        state: MachineState,
    ) -> int:
        return len(
            self.find_by_state(state)
        )

    @property
    def total_machines(self) -> int:
        return len(self._states)

    @property
    def active_machines(self) -> tuple[str, ...]:
        return self.find_by_state(
            MachineState.RUNNING
        )

    @property
    def available_machines(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                machine
                for machine, state
                in self._states.items()
                if state.is_available
            )
        )

    @property
    def stopped_machines(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                machine
                for machine, state
                in self._states.items()
                if state.is_stopped
            )
        )

    def clear(self) -> None:
        self._states.clear()
        self._histories.clear()

    def __len__(self) -> int:
        return len(self._states)

    def __contains__(
        self,
        machine_code: object,
    ) -> bool:
        if not isinstance(machine_code, str):
            return False

        normalized = machine_code.strip().upper()
        return normalized in self._states

    def __iter__(
        self,
    ) -> Iterator[str]:
        return iter(
            sorted(self._states)
        )

    def _require_machine(
        self,
        machine_code: str,
    ) -> str:
        machine = self._normalize_machine_code(
            machine_code
        )

        if machine not in self._states:
            raise MachineNotFoundError(
                f"Machine not found: {machine}."
            )

        return machine

    @staticmethod
    def _normalize_machine_code(
        machine_code: str,
    ) -> str:
        machine = str(
            machine_code
        ).strip().upper()

        if not machine:
            raise InvalidMachineStateError(
                "machine_code must not be empty."
            )

        return machine

    @staticmethod
    def _normalize_state(
        state: MachineState,
    ) -> MachineState:
        if isinstance(state, MachineState):
            return state

        try:
            return MachineState(
                str(state).strip().upper()
            )
        except ValueError as exc:
            raise InvalidMachineStateError(
                f"Invalid machine state: {state}."
            ) from exc