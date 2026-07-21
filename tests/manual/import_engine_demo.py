import pandas as pd

from src.services.master_import.import_engine import (
    BaseImporter,
    ImportContext,
    ImportEngine,
    ImportResult,
    ImporterRegistry,
)


class ProductImporter(
    BaseImporter,
):

    @property
    def module_name(self):
        return "PRODUCT"

    def import_data(
        self,
        context,
    ):

        self.validate_context(
            context
        )

        return ImportResult(
            success=True,
            module_name="PRODUCT",
            total_rows=context.total_rows,
            inserted_rows=context.total_rows,
        )


registry = ImporterRegistry()

registry.register(
    ProductImporter()
)

engine = ImportEngine(
    registry
)

context = ImportContext(
    module_name="PRODUCT",
    dataframe=pd.DataFrame(
        [
            {
                "Product Code": "P001"
            },
            {
                "Product Code": "P002"
            },
        ]
    ),
)

result = engine.execute(
    context
)

print()

print(
    result.success
)

print(
    result.inserted_rows
)

print(
    round(
        result.duration,
        6,
    )
)

print()

print(
    "ImportEngine OK"
)