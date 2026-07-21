from __future__ import annotations

from abc import ABC
from abc import abstractmethod

import pandas as pd


class BaseMapper(ABC):
    """
    Base class cho tất cả Mapper.
    """

    @abstractmethod
    def from_row(
        self,
        row: pd.Series,
    ):
        """
        Chuyển một dòng DataFrame thành Entity.
        """

    def from_dataframe(
        self,
        dataframe: pd.DataFrame,
    ):
        entities = []

        for _, row in dataframe.iterrows():

            entities.append(
                self.from_row(row)
            )

        return entities