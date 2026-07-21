import pandas as pd

from src.services.master_import.schema import (
    SchemaRegistry,
)
from src.services.master_import.validation import (
    HeaderValidator,
    ValidationResult,
)


schema = SchemaRegistry.get(
    "PRODUCT"
)

dataframe = pd.DataFrame(
    columns=[
        "Product Code",
        "Product Name",
        "Customer",
        "Drawing No",
        "Revision",
        "Material",
        "Unit",
        "Cycle Time (Sec)",
        "Standard Output (PCS/H)",
        "Product Group",
        "Status",
        "Remark",
    ]
)

validator = HeaderValidator(
    schema
)

result = ValidationResult()

validator.validate(
    dataframe,
    result,
)

print(
    "Module:",
    schema.module_name,
)

print(
    "Headers:",
    schema.headers,
)

print(
    "Required:",
    schema.required_headers,
)

print(
    "Unique:",
    schema.unique_fields,
)

print(
    "Success:",
    result.success,
)

print(
    "Errors:",
    len(result.errors),
)