import pandas as pd

from src.services.master_import.validation import (
    HeaderValidator,
    ValidationResult,
)

df = pd.DataFrame(
    columns=[
        "Product Code",
        "Product Name",
        "Customer",
        "ABC",
    ]
)

validator = HeaderValidator(
    required_headers=[
        "Product Code",
        "Product Name",
        "Customer",
        "Material",
    ]
)

result = ValidationResult()

validator.validate(
    df,
    result,
)

print()

print(
    "Success:",
    result.success
)

print(
    "Errors:",
    len(result.errors)
)

for error in result.errors:

    print(error.code)

    print(error.message)

    print()