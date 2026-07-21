from __future__ import annotations

from src.services.master_import.import_engine import (
    BaseImporter,
    ImportContext,
    ImportResult,
)
from src.services.master_import.mappers import (
    ProductMapper,
)
from src.services.product_service import (
    ProductService,
)


class ProductImporter(BaseImporter):
    """
    Import Product Master into SQLite.

    Responsibilities:
    - Map DataFrame rows to Product entities.
    - Call ProductService to create or update products.
    - Record ImportDetail for INSERT and UPDATE actions.
    - Never commit or rollback directly.
    """

    MODULE_NAME = "PRODUCT"

    def __init__(
        self,
        repository=None,
        product_service=None,
        mapper=None,
        import_detail_service=None,
    ):
        if product_service is None:
            if repository is not None:
                product_service = ProductService(repository=repository)
            else:
                product_service = ProductService()

        self.product_service = product_service
        self.mapper = mapper or ProductMapper()
        self.import_detail_service = import_detail_service
    @property
    def module_name(self) -> str:
        return self.MODULE_NAME

    def import_data(
        self,
        context: ImportContext,
    ) -> ImportResult:
        self.validate_context(
            context
        )

        print("=" * 70)
        print("PRODUCT IMPORTER START")
        print("module_name       =", context.module_name)
        print("total_rows        =", context.total_rows)
        print("metadata          =", context.metadata)
        print(
            "detail_service    =",
            self.import_detail_service,
        )
        print(
            "product_session   =",
            id(self.product_service.session),
        )
        print(
            "detail_session    =",
            (
                id(self.import_detail_service.session)
                if self.import_detail_service is not None
                else None
            ),
        )
        print("=" * 70)

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
                "No Product records to import."
            )
            return result.finalize()

        if context.validate_only:
            result.skipped_rows = len(
                entities
            )
            result.add_message(
                (
                    "Validation-only mode: "
                    f"{len(entities)} Product "
                    "record(s) checked."
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
                    f"{len(entities)} Product "
                    "record(s) mapped."
                )
            )
            return result.finalize()

        log_id = context.metadata.get(
            "import_log_id"
        )

        for row_index, entity in enumerate(
            entities,
            start=2,
        ):
            product_code = str(
                entity.product_code or ""
            ).strip().upper()

            try:
                existing_product = (
                    self.product_service
                    .get_product(
                        product_code
                    )
                )

                old_data = (
                    self._database_product_to_dict(
                        existing_product
                    )
                )

                service_data = (
                    self._entity_to_service_data(
                        entity
                    )
                )

                product, action = (
                    self.product_service
                    .save_product(
                        service_data
                    )
                )

                new_data = (
                    self._database_product_to_dict(
                        product
                    )
                )

                if action == "created":
                    result.inserted_rows += 1

                    if (
                        self.import_detail_service
                        is not None
                        and log_id is not None
                    ):
                        self.import_detail_service.record_insert(
                            log_id=log_id,
                            module=context.module_name,
                            entity_key=product_code,
                            new_data=new_data,
                        )

                elif action == "updated":
                    result.updated_rows += 1

                    if (
                        self.import_detail_service
                        is not None
                        and log_id is not None
                    ):
                        self.import_detail_service.record_update(
                            log_id=log_id,
                            module=context.module_name,
                            entity_key=product_code,
                            old_data=old_data,
                            new_data=new_data,
                        )

                else:
                    result.skipped_rows += 1
                    result.add_warning(
                        (
                            f"Row {row_index}: "
                            f"unknown Product action "
                            f"'{action}'."
                        )
                    )

                result.add_detail(
                    {
                        "row": row_index,
                        "product_code": product_code,
                        "action": action,
                        "success": True,
                    }
                )

            except Exception as error:
                result.failed_rows += 1

                result.add_detail(
                    {
                        "row": row_index,
                        "product_code": product_code,
                        "action": "failed",
                        "success": False,
                        "error": str(error),
                    }
                )

                result.add_error(
                    (
                        f"Row {row_index}, "
                        f"Product '{product_code}': "
                        f"{error}"
                    )
                )

                raise

        result.add_message(
            (
                "Product import completed: "
                f"{result.inserted_rows} inserted, "
                f"{result.updated_rows} updated, "
                f"{result.failed_rows} failed."
            )
        )

        return result.finalize()

    @staticmethod
    def _entity_to_service_data(
        entity,
    ) -> dict:
        return {
            "product_code": str(
                entity.product_code or ""
            ).strip().upper(),
            "product_name_vi": str(
                entity.product_name or ""
            ).strip(),
            "product_name_cn": None,
            "customer": (
                str(
                    entity.customer or ""
                ).strip()
                or None
            ),
            "material": (
                str(
                    entity.material or ""
                ).strip()
                or None
            ),
            "unit": (
                str(
                    entity.unit or "PCS"
                ).strip().upper()
                or "PCS"
            ),
            "status": (
                str(
                    entity.status or "ACTIVE"
                ).strip().upper()
                or "ACTIVE"
            ),
        }

    @staticmethod
    def _database_product_to_dict(
        product,
    ):
        if product is None:
            return None

        return {
            "product_code": product.product_code,
            "product_name_vi": product.product_name_vi,
            "product_name_cn": product.product_name_cn,
            "customer": product.customer,
            "material": product.material,
            "unit": product.unit,
            "status": product.status,
        }
