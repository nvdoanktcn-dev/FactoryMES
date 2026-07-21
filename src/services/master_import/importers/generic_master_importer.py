from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.services.master_import.import_engine import (
    BaseImporter,
    ImportContext,
    ImportResult,
)


class GenericMasterImporter(BaseImporter):
    """
    Importer dùng chung cho các Master Data.

    Các thành phần được truyền vào:
    - module_name
    - mapper
    - service
    - save_method
    - get_method
    - entity_key_getter
    - entity_to_service_data
    - database_entity_to_dict
    - ImportDetailService
    """

    def __init__(
        self,
        *,
        module_name: str,
        mapper,
        service,
        save_method: Callable[[dict], tuple],
        get_method: Callable[[str], Any],
        entity_key_getter: Callable[[Any], str],
        entity_to_service_data: Callable[[Any], dict],
        database_entity_to_dict: Callable[[Any], dict | None],
        import_detail_service=None,
    ):
        normalized_module = str(
            module_name or ""
        ).strip().upper()

        if not normalized_module:
            raise ValueError(
                "GenericMasterImporter.module_name is required."
            )

        if mapper is None:
            raise ValueError(
                "GenericMasterImporter.mapper is required."
            )

        if service is None:
            raise ValueError(
                "GenericMasterImporter.service is required."
            )

        if not callable(save_method):
            raise TypeError(
                "save_method must be callable."
            )

        if not callable(get_method):
            raise TypeError(
                "get_method must be callable."
            )

        if not callable(entity_key_getter):
            raise TypeError(
                "entity_key_getter must be callable."
            )

        if not callable(entity_to_service_data):
            raise TypeError(
                "entity_to_service_data must be callable."
            )

        if not callable(database_entity_to_dict):
            raise TypeError(
                "database_entity_to_dict must be callable."
            )

        self._module_name = normalized_module
        self.mapper = mapper
        self.service = service
        self.save_method = save_method
        self.get_method = get_method
        self.entity_key_getter = entity_key_getter
        self.entity_to_service_data = (
            entity_to_service_data
        )
        self.database_entity_to_dict = (
            database_entity_to_dict
        )
        self.import_detail_service = (
            import_detail_service
        )

    @property
    def module_name(self) -> str:
        return self._module_name

    def import_data(
        self,
        context: ImportContext,
    ) -> ImportResult:
        self.validate_context(
            context
        )

        result = ImportResult(
            success=True,
            module_name=context.module_name,
            total_rows=context.total_rows,
        )

        entities = self.mapper.from_dataframe(
            context.dataframe
        )

        if not entities:
            result.add_warning(
                (
                    f"No {self.module_name} "
                    "records to import."
                )
            )
            return result.finalize()

        if context.validate_only:
            result.skipped_rows = len(
                entities
            )

            result.add_message(
                (
                    "Validation-only mode: "
                    f"{len(entities)} "
                    f"{self.module_name} record(s) checked."
                )
            )

            return result.finalize()

        if context.dry_run:
            result.skipped_rows = len(
                entities
            )

            result.add_message(
                (
                    "Dry-run mode: "
                    f"{len(entities)} "
                    f"{self.module_name} record(s) mapped."
                )
            )

            return result.finalize()

        metadata = context.metadata or {}

        log_id = metadata.get(
            "import_log_id"
        )

        for row_index, entity in enumerate(
            entities,
            start=2,
        ):
            entity_key = self._normalize_entity_key(
                self.entity_key_getter(
                    entity
                )
            )

            try:
                existing_entity = self.get_method(
                    entity_key
                )

                old_data = (
                    self.database_entity_to_dict(
                        existing_entity
                    )
                )

                service_data = (
                    self.entity_to_service_data(
                        entity
                    )
                )

                saved_entity, action = (
                    self.save_method(
                        service_data
                    )
                )

                action = str(
                    action or ""
                ).strip().lower()

                new_data = (
                    self.database_entity_to_dict(
                        saved_entity
                    )
                )

                if action == "created":
                    result.inserted_rows += 1

                    self._record_insert(
                        log_id=log_id,
                        entity_key=entity_key,
                        new_data=new_data,
                    )

                elif action == "updated":
                    result.updated_rows += 1

                    self._record_update(
                        log_id=log_id,
                        entity_key=entity_key,
                        old_data=old_data,
                        new_data=new_data,
                    )

                else:
                    result.skipped_rows += 1

                    result.add_warning(
                        (
                            f"Row {row_index}: "
                            f"unknown action '{action}' "
                            f"for '{entity_key}'."
                        )
                    )

                result.add_detail(
                    {
                        "row": row_index,
                        "entity_key": entity_key,
                        "action": action,
                        "success": True,
                    }
                )

            except Exception as error:
                result.failed_rows += 1

                result.add_detail(
                    {
                        "row": row_index,
                        "entity_key": entity_key,
                        "action": "failed",
                        "success": False,
                        "error": str(error),
                    }
                )

                result.add_error(
                    (
                        f"Row {row_index}, "
                        f"{self.module_name} "
                        f"'{entity_key}': {error}"
                    )
                )

                # Dừng để ImportEngine rollback toàn bộ file.
                raise

        result.add_message(
            (
                f"{self.module_name} import completed: "
                f"{result.inserted_rows} inserted, "
                f"{result.updated_rows} updated, "
                f"{result.failed_rows} failed."
            )
        )

        return result.finalize()

    def _record_insert(
        self,
        *,
        log_id,
        entity_key,
        new_data,
    ):
        if (
            self.import_detail_service is None
            or log_id is None
        ):
            return

        self.import_detail_service.record_insert(
            log_id=log_id,
            module=self.module_name,
            entity_key=entity_key,
            new_data=new_data,
        )

    def _record_update(
        self,
        *,
        log_id,
        entity_key,
        old_data,
        new_data,
    ):
        if (
            self.import_detail_service is None
            or log_id is None
        ):
            return

        self.import_detail_service.record_update(
            log_id=log_id,
            module=self.module_name,
            entity_key=entity_key,
            old_data=old_data,
            new_data=new_data,
        )

    @staticmethod
    def _normalize_entity_key(
        value,
    ) -> str:
        key = str(
            value or ""
        ).strip().upper()

        if not key:
            raise ValueError(
                "Import entity key is empty."
            )

        return key