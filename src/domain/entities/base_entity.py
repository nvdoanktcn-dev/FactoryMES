from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass


@dataclass(slots=True)
class BaseEntity:
    """
    Base Entity của toàn bộ Domain.
    """

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(
        cls,
        data: dict,
    ):
        return cls(**data)