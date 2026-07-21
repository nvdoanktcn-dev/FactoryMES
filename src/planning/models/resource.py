from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MachineResource:
    """
    Một nhóm máy hoặc một máy tham gia sản xuất.
    """

    machine_group: str

    available_machines: int

    target_oee: float = 0.85

    efficiency: float = 1.0