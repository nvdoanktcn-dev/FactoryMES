from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class RankingItem:
    name: str
    value: float
    percent: float
    cumulative_percent: float
    rank: int


class RankingService:
    """
    Generic ranking engine.

    Có thể dùng cho:

        NG
        Downtime
        Alarm
        Runtime
        Operator
        Machine
    """

    @staticmethod
    def build(
        rows: Iterable[Any],
        *,
        key: str = "name",
        value: str = "value",
        descending: bool = True,
    ) -> tuple[RankingItem, ...]:

        data: list[tuple[str, float]] = []

        for row in rows:

            if isinstance(row, dict):
                name = str(row.get(key, ""))

                try:
                    qty = float(row.get(value, 0))
                except Exception:
                    qty = 0.0

            else:
                name = str(getattr(row, key, ""))

                try:
                    qty = float(
                        getattr(
                            row,
                            value,
                            0,
                        )
                    )
                except Exception:
                    qty = 0.0

            if not isfinite(qty):
                qty = 0.0

            data.append((name, max(qty, 0.0)))

        data.sort(
            key=lambda x: x[1],
            reverse=descending,
        )

        total = sum(
            value
            for _, value in data
        )

        cumulative = 0.0

        result: list[RankingItem] = []

        previous_qty = None
        current_rank = 0

        for index, (name, qty) in enumerate(
            data,
            start=1,
        ):
            if previous_qty is None or qty != previous_qty:
                current_rank = index
                previous_qty = qty

            percent = (
                qty / total * 100
                if total
                else 0.0
            )

            cumulative += percent

            result.append(
                RankingItem(
                    name=name,
                    value=qty,
                    percent=percent,
                    cumulative_percent=min(
                        cumulative,
                        100.0,
                    ),
                    rank=current_rank,
                )
            )

        return tuple(result)
