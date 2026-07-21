import pandas as pd

from src.services.master_import.mappers import (
    ProductMapper,
)

df = pd.DataFrame(
    [
        {
            "Product Code": "P001",
            "Product Name": "Housing",
            "Customer": "Toyota",
            "Material": "ADC12",
            "Unit": "PCS",
            "Cycle Time (Sec)": 45,
            "Standard Output (PCS/H)": 80,
            "Status": "ACTIVE",
        }
    ]
)

mapper = ProductMapper()

products = mapper.from_dataframe(
    df
)

print(products[0])

print(products[0].to_dict())

print("Mapper OK")