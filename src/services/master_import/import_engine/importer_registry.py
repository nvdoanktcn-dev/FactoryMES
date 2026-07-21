from __future__ import annotations

from collections.abc import Iterable

from .base_importer import (
    BaseImporter,
)
from .import_exception import (
    ImporterNotFoundError,
)


class ImporterRegistry:
    """
    Registry quản lý Importer theo module.
    """

    def __init__(
        self,
        importers: Iterable[
            BaseImporter
        ] | None = None,
    ):
        self._importers: dict[
            str,
            BaseImporter,
        ] = {}

        for importer in importers or []:
            self.register(
                importer
            )

    def register(
        self,
        importer: BaseImporter,
        replace: bool = False,
    ):
        if not isinstance(
            importer,
            BaseImporter,
        ):
            raise TypeError(
                "Importer must inherit "
                "from BaseImporter."
            )

        module_name = (
            importer
            .normalized_module_name()
        )

        if not module_name:
            raise ValueError(
                "Importer module name "
                "cannot be empty."
            )

        if (
            module_name in self._importers
            and not replace
        ):
            raise KeyError(
                (
                    f"Importer already registered "
                    f"for module '{module_name}'."
                )
            )

        self._importers[
            module_name
        ] = importer

        return importer

    def unregister(
        self,
        module_name,
    ):
        key = self._normalize(
            module_name
        )

        return self._importers.pop(
            key,
            None,
        )

    def get(
        self,
        module_name,
    ) -> BaseImporter:
        key = self._normalize(
            module_name
        )

        importer = self._importers.get(
            key
        )

        if importer is None:
            raise ImporterNotFoundError(
                (
                    "No importer registered for "
                    f"module '{key}'."
                )
            )

        return importer

    def contains(
        self,
        module_name,
    ) -> bool:
        return (
            self._normalize(
                module_name
            )
            in self._importers
        )

    def modules(self) -> list[str]:
        return list(
            self._importers.keys()
        )

    def importers(
        self,
    ) -> list[BaseImporter]:
        return list(
            self._importers.values()
        )

    def clear(self):
        self._importers.clear()

    def __len__(self):
        return len(
            self._importers
        )

    @staticmethod
    def _normalize(
        module_name,
    ) -> str:
        normalized = str(
            module_name or ""
        ).strip().upper()

        if not normalized:
            raise ValueError(
                "Module name is required."
            )

        return normalized