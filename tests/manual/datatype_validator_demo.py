import pandas as pd

from src.services.master_import.schema import (
    SchemaRegistry,
)

from src.services.master_import.validation import (
    DataTypeValidator,
    ValidationResult,
)

schema = SchemaRegistry.get(
    "PRODUCT"
)

df = pd.DataFrame(
    [
        {
            "Product Code": "P001",
            "Product Name": "ABC",
            "Material": "ADC12",
            "Unit": "PCS",
            "Cycle Time (Sec)": 35,
            "Standard Output (PCS/H)": 80,
            "Status": "ACTIVE",
        },
        {
            "Product Code": "P002",
            "Product Name": "ABC",
            "Material": "ADC12",
            "Unit": "BOX",
            "Cycle Time (Sec)": -2,
            "Standard Output (PCS/H)": "ABC",
            "Status": "RUNNING",
        },
    ]
)

validator = DataTypeValidator(
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
        error.code,
        error.message,
    )