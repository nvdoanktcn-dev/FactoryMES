import pandas as pd

from src.repositories.product_repository import (
    ProductRepository,
)
from src.services.master_import.import_engine import (
    ImportContext,
)
from src.services.master_import.importers import (
    ProductImporter,
)


repository = ProductRepository()

importer = ProductImporter(
    repository=repository
)

dataframe = pd.DataFrame(
    [
        {
            "Product Code": "P001",
            "Product Name": "Housing A",
            "Customer": "TOYOTA",
            "Drawing No": "DWG-001",
            "Revision": "A",
            "Material": "ADC12",
            "Unit": "PCS",
            "Cycle Time (Sec)": 45,
            "Standard Output (PCS/H)": 80,
            "Product Group": "Casting",
            "Status": "ACTIVE",
            "Remark": "",
        },
        {
            "Product Code": "P002",
            "Product Name": "Bracket B",
            "Customer": "HONDA",
            "Drawing No": "DWG-002",
            "Revision": "B",
            "Material": "AL6061",
            "Unit": "PCS",
            "Cycle Time (Sec)": 38,
            "Standard Output (PCS/H)": 95,
            "Product Group": "Machining",
            "Status": "ACTIVE",
            "Remark": "",
        },
    ]
)

context = ImportContext(
    module_name="PRODUCT",
    dataframe=dataframe,
)

first_result = importer.import_data(
    context
)

print("=" * 70)
print("FIRST IMPORT")
print("=" * 70)
print(
    "Success:",
    first_result.success,
)
print(
    "Inserted:",
    first_result.inserted_rows,
)
print(
    "Updated:",
    first_result.updated_rows,
)
print(
    "Repository count:",
    len(repository.get_all()),
)

assert first_result.success
assert first_result.inserted_rows == 2
assert first_result.updated_rows == 0
assert len(repository.get_all()) == 2


updated_dataframe = pd.DataFrame(
    [
        {
            "Product Code": "P001",
            "Product Name": "Housing A Updated",
            "Customer": "TOYOTA",
            "Drawing No": "DWG-001",
            "Revision": "B",
            "Material": "ADC12",
            "Unit": "PCS",
            "Cycle Time (Sec)": 42,
            "Standard Output (PCS/H)": 85,
            "Product Group": "Casting",
            "Status": "ACTIVE",
            "Remark": "Updated",
        },
        {
            "Product Code": "P003",
            "Product Name": "Cover C",
            "Customer": "YAMAHA",
            "Drawing No": "DWG-003",
            "Revision": "A",
            "Material": "S45C",
            "Unit": "PCS",
            "Cycle Time (Sec)": 60,
            "Standard Output (PCS/H)": 60,
            "Product Group": "CNC",
            "Status": "ACTIVE",
            "Remark": "",
        },
    ]
)

second_context = ImportContext(
    module_name="PRODUCT",
    dataframe=updated_dataframe,
)

second_result = importer.import_data(
    second_context
)

print()
print("=" * 70)
print("SECOND IMPORT")
print("=" * 70)
print(
    "Success:",
    second_result.success,
)
print(
    "Inserted:",
    second_result.inserted_rows,
)
print(
    "Updated:",
    second_result.updated_rows,
)
print(
    "Repository count:",
    len(repository.get_all()),
)

assert second_result.success
assert second_result.inserted_rows == 1
assert second_result.updated_rows == 1
assert len(repository.get_all()) == 3

updated_product = repository.get(
    "P001"
)

assert (
    updated_product.product_name
    == "Housing A Updated"
)

print()
print(
    "ProductImporter test passed."
)