from __future__ import annotations

from abc import ABC
from abc import abstractmethod


class BaseRepository(ABC):
    """
    Base Repository.
    """

    @abstractmethod
    def insert_batch(
        self,
        entities,
    ):
        ...

    @abstractmethod
    def update_batch(
        self,
        entities,
    ):
        ...

    @abstractmethod
    def delete_batch(
        self,
        entities,
    ):
        ...

    @abstractmethod
    def exists(
        self,
        key,
    ):
        ...