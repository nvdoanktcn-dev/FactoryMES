class Status:
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class MachineStatus:
    RUNNING = "RUNNING"
    STOP = "STOP"
    MAINTENANCE = "MAINTENANCE"


class Shift:
    DAY = "DAY"
    NIGHT = "NIGHT"
    ADMIN = "ADMIN"


class MachineType:
    CNC = "CNC"
    ROBOT = "ROBOT"
    CMM = "CMM"
    LASER = "LASER"
    OTHER = "OTHER"


# ===== Compatibility =====
STATUS_ACTIVE = Status.ACTIVE
STATUS_INACTIVE = Status.INACTIVE

MACHINE_RUNNING = MachineStatus.RUNNING
MACHINE_STOP = MachineStatus.STOP
MACHINE_MAINTENANCE = MachineStatus.MAINTENANCE