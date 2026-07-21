from dataclasses import dataclass

import pandas as pd

from src.services.master_import.import_engine import (
    ImportContext,
)
from src.services.master_import.importers import (
    GenericMasterImporter,
)


@dataclass
class TestEntity:
    code: str
    name: str


class TestMapper:
    def from_dataframe(
        self,
        dataframe,
    ):
        return [
            TestEntity(
                code=str(row["Code"]),
                name=str(row["Name"]),
            )
            for _, row in dataframe.iterrows()
        ]


class TestService:
    def __init__(self):
        self.storage = {}

    def get_by_code(
        self,
        code,
    ):
        return self.storage.get(
            code
        )

    def save(
        self,
        data,
    ):
        code = data["code"]

        action = (
            "updated"
            if code in self.storage
            else "created"
        )

        entity = TestEntity(
            code=code,
            name=data["name"],
        )

        self.storage[code] = entity

        return entity, action


service = TestService()

importer = GenericMasterImporter(
    module_name="TEST",
    mapper=TestMapper(),
    service=service,
    save_method=service.save,
    get_method=service.get_by_code,
    entity_key_getter=(
        lambda entity: entity.code
    ),
    entity_to_service_data=(
        lambda entity: {
            "code": entity.code,
            "name": entity.name,
        }
    ),
    database_entity_to_dict=(
        lambda entity: (
            None
            if entity is None
            else {
                "code": entity.code,
                "name": entity.name,
            }
        )
    ),
)

dataframe = pd.DataFrame(
    [
        {
            "Code": "T001",
            "Name": "Test 1",
        },
        {
            "Code": "T002",
            "Name": "Test 2",
        },
    ]
)

context = ImportContext(
    module_name="TEST",
    dataframe=dataframe,
)

result = importer.import_data(
    context
)

assert result.success
assert result.inserted_rows == 2
assert result.updated_rows == 0

result = importer.import_data(
    context
)

assert result.success
assert result.inserted_rows == 0
assert result.updated_rows == 2

print(
    "GenericMasterImporter test passed."
)