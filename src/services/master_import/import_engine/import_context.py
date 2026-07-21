from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass(slots=True)
class ImportContext:
    """
    Ngữ cảnh đầu vào của Import Engine.
    """

    module_name: str

    dataframe: pd.DataFrame

    user: str = ""

    validate_only: bool = False

    dry_run: bool = False

    batch_size: int = 200

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self):
        self.module_name = str(
            self.module_name or ""
        ).strip().upper()

        self.user = str(
            self.user or ""
        ).strip()

        if not self.module_name:
            raise ValueError(
                "Import module name is required."
            )

        if not isinstance(
            self.dataframe,
            pd.DataFrame,
        ):
            raise TypeError(
                "Import dataframe must be "
                "a pandas DataFrame."
            )

        try:
            self.batch_size = int(
                self.batch_size
            )

        except (
            TypeError,
            ValueError,
        ) as error:
            raise TypeError(
                "Import batch size must be "
                "an integer."
            ) from error

        if self.batch_size <= 0:
            raise ValueError(
                "Import batch size must be "
                "greater than zero."
            )

    @property
    def total_rows(self) -> int:
        return len(
            self.dataframe
        )

    @property
    def is_empty(self) -> bool:
        return self.dataframe.empty