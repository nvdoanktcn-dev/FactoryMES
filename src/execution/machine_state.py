from enum import Enum


class MachineState(str, Enum):
    OFFLINE = "OFFLINE"
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    DOWNTIME = "DOWNTIME"
    MAINTENANCE = "MAINTENANCE"

    @property
    def is_available(self) -> bool:
        return self in {
            MachineState.IDLE,
            MachineState.RUNNING,
            MachineState.PAUSED,
        }

    @property
    def is_active(self) -> bool:
        return self is MachineState.RUNNING

    @property
    def is_stopped(self) -> bool:
        return self in {
            MachineState.OFFLINE,
            MachineState.DOWNTIME,
            MachineState.MAINTENANCE,
        }