import pandas as pd

from src.importer.master_base_importer import (
    MasterBaseImporter,
)


class DemoImporter(MasterBaseImporter):
    REQUIRED_COLUMNS = [
        "Code",
        "Name",
    ]

    COLUMN_MAPPING = {
        "Mã": "Code",
        "Tên": "Name",
        "Status": "Status",
    }

    def validate_row(self, row, row_number):
        self.require_value(
            row.get("Code"),
            "Code",
        )

        self.require_value(
            row.get("Name"),
            "Name",
        )

    def map_row(self, row):
        return {
            "code": self.clean_text(
                row.get("Code")
            ).upper(),
            "name": self.clean_text(
                row.get("Name")
            ),
            "status": self.clean_text(
                row.get("Status")
            ).upper() or "ACTIVE",
        }

    def save_record(self, data):
        print("SAVE:", data)
        return "created"


dataframe = pd.DataFrame([
    {
        "Mã": " p001 ",
        "Tên": "Sản phẩm A",
        "Status": "active",
    },
    {
        "Mã": "P002",
        "Tên": "Sản phẩm B",
        "Status": "",
    },
])

importer = DemoImporter()

prepared = importer.prepare_dataframe(dataframe)
importer.validate_columns(prepared)

for index, row in prepared.iterrows():
    importer.validate_row(row, index + 2)
    print(importer.map_row(row))

print("MasterBaseImporter test passed.")