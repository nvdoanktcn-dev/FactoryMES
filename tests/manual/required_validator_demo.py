import pandas as pd

from src.services.master_import.schema import (
    SchemaRegistry,
)

from src.services.master_import.validation import (
    RequiredFieldValidator,
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
            "Status": "ACTIVE",
        },
        {
            "Product Code": "",
            "Product Name": "DEF",
            "Material": "ADC12",
            "Unit": "PCS",
            "Cycle Time (Sec)": 28,
            "Status": "ACTIVE",
        },
        {
            "Product Code": "P003",
            "Product Name": "",
            "Material": "",
            "Unit": "PCS",
            "Cycle Time (Sec)": 40,
            "Status": "ACTIVE",
        },
    ]
)

validator = RequiredFieldValidator(
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
        error.message,
    )