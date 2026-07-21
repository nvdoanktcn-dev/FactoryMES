from abc import ABC
from abc import abstractmethod


class ReferenceRepository(ABC):

    @abstractmethod
    def exists(
        self,
        category: str,
        value: str,
    ) -> bool:
        ...