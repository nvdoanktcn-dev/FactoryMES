import pandas as pd

from src.services.master_import.import_engine import (
    BaseImporter,
    ImportContext,
    ImportResult,
    ImporterNotFoundError,
    ImporterRegistry,
)


class FakeProductImporter(
    BaseImporter
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
            module_name=(
                context.module_name
            ),
            total_rows=(
                context.total_rows
            ),
            inserted_rows=(
                context.total_rows
            ),
        )


dataframe = pd.DataFrame(
    [
        {
            "Product Code": "P001",
        },
        {
            "Product Code": "P002",
        },
    ]
)

context = ImportContext(
    module_name="product",
    dataframe=dataframe,
    user="admin",
    batch_size=100,
)

registry = ImporterRegistry()

registry.register(
    FakeProductImporter()
)

importer = registry.get(
    "PRODUCT"
)

result = importer.import_data(
    context
)

print(
    "Registered modules:",
    registry.modules(),
)

print(
    "Context rows:",
    context.total_rows,
)

print(
    "Import success:",
    result.success,
)

print(
    "Inserted rows:",
    result.inserted_rows,
)

assert registry.contains(
    "PRODUCT"
)

assert context.module_name == (
    "PRODUCT"
)

assert result.inserted_rows == 2

try:
    registry.get(
        "MACHINE"
    )

except ImporterNotFoundError:
    print(
        "Missing importer test passed."
    )

else:
    raise AssertionError(
        "ImporterNotFoundError expected."
    )

print(
    "Import Engine Core test passed."
)