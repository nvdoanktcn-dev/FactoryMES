from __future__ import annotations

from abc import ABC
from abc import abstractmethod


class BaseTransactionManager(ABC):
    """
    Base class cho Transaction Manager.
    """

    @abstractmethod
    def begin(self):
        ...

    @abstractmethod
    def commit(self):
        ...

    @abstractmethod
    def rollback(self):
        ...

    @abstractmethod
    def in_transaction(self) -> bool:
        ...