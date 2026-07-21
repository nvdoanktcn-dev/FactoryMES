import pandas as pd

from src.services.master_import.import_engine import (
    ImportContext,
)
from src.services.master_import.importers import (
    ProductImporter,
)
from src.services.product_service import (
    ProductService,
)


dataframe = pd.DataFrame(
    [
        {
            "Product Code": "IMP-P001",
            "Product Name": "Import Housing A",
            "Customer": "TOYOTA",
            "Drawing No": "DWG-IMP-001",
            "Revision": "A",
            "Material": "ADC12",
            "Unit": "PCS",
            "Cycle Time (Sec)": 45,
            "Standard Output (PCS/H)": 80,
            "Product Group": "Casting",
            "Status": "ACTIVE",
            "Remark": "SQLite test",
        },
        {
            "Product Code": "IMP-P002",
            "Product Name": "Import Bracket B",
            "Customer": "HONDA",
            "Drawing No": "DWG-IMP-002",
            "Revision": "A",
            "Material": "AL6061",
            "Unit": "PCS",
            "Cycle Time (Sec)": 38,
            "Standard Output (PCS/H)": 95,
            "Product Group": "Machining",
            "Status": "ACTIVE",
            "Remark": "SQLite test",
        },
    ]
)

context = ImportContext(
    module_name="PRODUCT",
    dataframe=dataframe,
    user="test",
)

importer = ProductImporter()

result = importer.import_data(
    context
)

print("=" * 70)
print("PRODUCT SQLITE IMPORT")
print("=" * 70)
print("Success:", result.success)
print("Inserted:", result.inserted_rows)
print("Updated:", result.updated_rows)
print("Failed:", result.failed_rows)
print("Messages:", result.messages)

service = ProductService()

for product_code in (
    "IMP-P001",
    "IMP-P002",
):
    product = service.get_product(
        product_code
    )

    assert product is not None

    print(
        product.product_code,
        product.product_name_vi,
        product.customer,
        product.material,
        product.status,
    )

print()
print(
    "Product SQLite import test passed."
)