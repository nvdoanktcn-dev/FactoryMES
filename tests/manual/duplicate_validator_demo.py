import pandas as pd

from src.services.master_import.schema import (
    SchemaRegistry,
)

from src.services.master_import.validation import (
    DuplicateValidator,
    ValidationResult,
)

schema = SchemaRegistry.get(
    "PRODUCT"
)

df = pd.DataFrame(
    [
        {
            "Product Code": "P001",
        },
        {
            "Product Code": "P002",
        },
        {
            "Product Code": "P001",
        },
        {
            "Product Code": "P003",
        },
        {
            "Product Code": "P002",
        },
    ]
)

validator = DuplicateValidator(
    schema
)

result = ValidationResult()

validator.validate(
    df,
    result,
)

print(
    "Success:",
    result.success
)

print(
    "Errors:",
    len(result.errors)
)

for error in result.errors:

    print(
        error.row,
        error.column,
        error.value,
    )