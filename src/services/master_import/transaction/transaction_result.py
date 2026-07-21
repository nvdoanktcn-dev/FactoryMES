from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TransactionResult:
    """
    Kết quả của transaction.
    """

    success: bool = True

    message: str = ""

    duration: float = 0.0