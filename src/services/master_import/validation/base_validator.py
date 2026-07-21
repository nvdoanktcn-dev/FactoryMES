from abc import ABC
from abc import abstractmethod

from .validation_result import ValidationResult


class BaseValidator(ABC):
    """
    Base class của tất cả validator.
    """

    @abstractmethod
    def validate(
        self,
        dataframe,
        result: ValidationResult,
    ):
        ...