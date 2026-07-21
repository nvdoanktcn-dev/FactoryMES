from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from src.planning.exceptions import PlanningError


class InvalidResourceError(PlanningError):
    """Dữ liệu tài nguyên máy không hợp lệ."""


class ResourceNotFoundError(PlanningError):
    """Không tìm thấy nhóm tài nguyên máy."""


@dataclass(frozen=True, slots=True)
class MachineResource:
    """
    Năng lực tài nguyên hiện có của một nhóm máy.

    Attributes:
        machine_group:
            Mã nhóm máy, ví dụ CNC, ROBOT hoặc ASK.

        available_machines:
            Tổng số máy có thể sử dụng để lập kế hoạch.

        target_oee:
            OEE mục tiêu trong khoảng (0, 1].

        efficiency:
            Hệ số hiệu suất bổ sung trong khoảng (0, 1].
            Giá trị 1.0 nghĩa là không điều chỉnh thêm.
    """

    machine_group: str
    available_machines: int
    target_oee: float = 0.85
    efficiency: float = 1.0

    def __post_init__(self) -> None:
        normalized_group = self.machine_group.strip().upper()

        if not normalized_group:
            raise InvalidResourceError(
                "machine_group must not be empty."
            )

        if isinstance(self.available_machines, bool):
            raise InvalidResourceError(
                "available_machines must be an integer."
            )

        if not isinstance(self.available_machines, int):
            raise InvalidResourceError(
                "available_machines must be an integer."
            )

        if self.available_machines <= 0:
            raise InvalidResourceError(
                "available_machines must be greater than zero."
            )

        self._validate_ratio(
            name="target_oee",
            value=self.target_oee,
        )
        self._validate_ratio(
            name="efficiency",
            value=self.efficiency,
        )

        # Chuẩn hóa để CNC, cnc và " CNC " được coi là cùng một nhóm.
        object.__setattr__(
            self,
            "machine_group",
            normalized_group,
        )

    @staticmethod
    def _validate_ratio(
        name: str,
        value: float,
    ) -> None:
        if isinstance(value, bool):
            raise InvalidResourceError(
                f"{name} must be a finite number."
            )

        try:
            numeric_value = float(value)
        except (TypeError, ValueError) as exc:
            raise InvalidResourceError(
                f"{name} must be a finite number."
            ) from exc

        if not isfinite(numeric_value):
            raise InvalidResourceError(
                f"{name} must be a finite number."
            )

        if not 0 < numeric_value <= 1:
            raise InvalidResourceError(
                f"{name} must be greater than zero "
                "and less than or equal to one."
            )


@dataclass(frozen=True, slots=True)
class ResourceGap:
    """
    Chênh lệch giữa số máy cần và số máy hiện có.
    """

    machine_group: str
    required: int
    available: int
    shortage: int

    def __post_init__(self) -> None:
        normalized_group = self.machine_group.strip().upper()

        if not normalized_group:
            raise InvalidResourceError(
                "machine_group must not be empty."
            )

        for field_name, value in (
            ("required", self.required),
            ("available", self.available),
            ("shortage", self.shortage),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise InvalidResourceError(
                    f"{field_name} must be an integer."
                )

            if value < 0:
                raise InvalidResourceError(
                    f"{field_name} must not be negative."
                )

        expected_shortage = max(
            0,
            self.required - self.available,
        )

        if self.shortage != expected_shortage:
            raise InvalidResourceError(
                "shortage must equal "
                "max(0, required - available)."
            )

        object.__setattr__(
            self,
            "machine_group",
            normalized_group,
        )

    @classmethod
    def calculate(
        cls,
        machine_group: str,
        required: int,
        available: int,
    ) -> ResourceGap:
        """
        Tạo ResourceGap và tự động tính số máy thiếu.
        """

        return cls(
            machine_group=machine_group,
            required=required,
            available=available,
            shortage=max(0, required - available),
        )

    @property
    def has_shortage(self) -> bool:
        return self.shortage > 0


@dataclass(frozen=True, slots=True)
class ResourcePool:
    """
    Danh sách tài nguyên máy được lập chỉ mục theo machine_group.
    """

    resources: tuple[MachineResource, ...]

    def __post_init__(self) -> None:
        try:
            normalized_resources = tuple(self.resources)
        except TypeError as exc:
            raise InvalidResourceError(
                "resources must be an iterable of MachineResource."
            ) from exc

        resource_groups: set[str] = set()

        for resource in normalized_resources:
            if not isinstance(resource, MachineResource):
                raise InvalidResourceError(
                    "Every resource must be a MachineResource."
                )

            if resource.machine_group in resource_groups:
                raise InvalidResourceError(
                    "Duplicate machine group: "
                    f"{resource.machine_group}."
                )

            resource_groups.add(resource.machine_group)

        object.__setattr__(
            self,
            "resources",
            normalized_resources,
        )

    def get(
        self,
        machine_group: str,
    ) -> MachineResource:
        normalized_group = self._normalize_group(
            machine_group
        )

        for resource in self.resources:
            if resource.machine_group == normalized_group:
                return resource

        raise ResourceNotFoundError(
            f"Machine resource not found: {normalized_group}."
        )

    def find(
        self,
        machine_group: str,
    ) -> MachineResource | None:
        """
        Tra cứu an toàn. Trả về None nếu không tìm thấy.
        """

        normalized_group = self._normalize_group(
            machine_group
        )

        for resource in self.resources:
            if resource.machine_group == normalized_group:
                return resource

        return None

    def contains(
        self,
        machine_group: str,
    ) -> bool:
        return self.find(machine_group) is not None

    def available_count(
        self,
        machine_group: str,
    ) -> int:
        return self.get(machine_group).available_machines

    def evaluate_gap(
        self,
        machine_group: str,
        required: int,
    ) -> ResourceGap:
        if isinstance(required, bool) or not isinstance(required, int):
            raise InvalidResourceError(
                "required must be an integer."
            )

        if required < 0:
            raise InvalidResourceError(
                "required must not be negative."
            )

        resource = self.get(machine_group)

        return ResourceGap.calculate(
            machine_group=resource.machine_group,
            required=required,
            available=resource.available_machines,
        )

    def as_dict(self) -> dict[str, MachineResource]:
        return {
            resource.machine_group: resource
            for resource in self.resources
        }

    def __len__(self) -> int:
        return len(self.resources)

    def __iter__(self):
        return iter(self.resources)

    @staticmethod
    def _normalize_group(
        machine_group: str,
    ) -> str:
        if not isinstance(machine_group, str):
            raise InvalidResourceError(
                "machine_group must be a string."
            )

        normalized_group = machine_group.strip().upper()

        if not normalized_group:
            raise InvalidResourceError(
                "machine_group must not be empty."
            )

        return normalized_group