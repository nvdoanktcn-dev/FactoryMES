from __future__ import annotations

from abc import ABC, abstractmethod

from .import_context import (
    ImportContext,
)
from .import_result import (
    ImportResult,
)


class BaseImporter(ABC):
    """
    Base class cho mọi Master Data Importer.
    """

    @property
    @abstractmethod
    def module_name(self) -> str:
        """
        Module mà Importer xử lý.
        Ví dụ: PRODUCT, MACHINE.
        """

    def supports(
        self,
        module_name,
    ) -> bool:
        return (
            self.normalized_module_name()
            == str(
                module_name or ""
            ).strip().upper()
        )

    def normalized_module_name(
        self,
    ) -> str:
        return str(
            self.module_name or ""
        ).strip().upper()

    def validate_context(
        self,
        context: ImportContext,
    ):
        if not isinstance(
            context,
            ImportContext,
        ):
            raise TypeError(
                "Importer requires ImportContext."
            )

        if not self.supports(
            context.module_name
        ):
            raise ValueError(
                (
                    f"Importer '{self.module_name}' "
                    "does not support module "
                    f"'{context.module_name}'."
                )
            )

        if context.is_empty:
            raise ValueError(
                "Import dataframe is empty."
            )

    @abstractmethod
    def import_data(
        self,
        context: ImportContext,
    ) -> ImportResult:
        """
        Thực thi import.

        Importer không tự commit hoặc rollback.
        TransactionManager sẽ xử lý transaction.
        """