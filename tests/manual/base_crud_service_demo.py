from types import SimpleNamespace

from src.framework.base_crud_service import (
    BaseCRUDService,
)


class DemoRepository:
    def __init__(self):
        self.session = None

        self.records = [
            SimpleNamespace(
                code="D001",
                name="Demo One",
                status="ACTIVE",
            ),
            SimpleNamespace(
                code="D002",
                name="Demo Two",
                status="INACTIVE",
            ),
        ]

    def get_all(self):
        return self.records


class DemoService(BaseCRUDService):
    ENTITY_NAME = "Demo"

    def __init__(self):
        super().__init__(
            repository=DemoRepository()
        )

    def search_fields(self):
        return [
            "code",
            "name",
            "status",
        ]

    def get_by_key(self, key):
        key = self.normalize_code(key)

        for record in self.repository.records:
            if (
                self.normalize_code(
                    record.code
                )
                == key
            ):
                return record

        return None

    def create(self, data):
        self.require_dict(data)

        code = self.normalize_code(
            data.get("code")
        )

        name = self.normalize_text(
            data.get("name")
        )

        self.require_unique(code)

        record = SimpleNamespace(
            code=code,
            name=name,
            status=self.normalize_status(
                data.get("status")
            ),
        )

        self.repository.records.append(
            record
        )

        return record

    def update(self, key, data):
        self.require_dict(data)

        record = self.require_record(key)

        record.name = self.normalize_text(
            data.get("name")
        )

        record.status = (
            self.normalize_status(
                data.get("status")
            )
        )

        return record

    def delete(self, key):
        record = self.require_record(key)

        record.status = "INACTIVE"

        return record


service = DemoService()

print("=" * 70)
print("BASE CRUD SERVICE")
print("=" * 70)

records = service.get_all()

assert len(records) == 2
assert service.exists("D001")
assert not service.exists("D999")


search_result = service.search(
    "two"
)

assert len(search_result) == 1
assert search_result[0].code == "D002"


created = service.create({
    "code": "d003",
    "name": "Demo Three",
    "status": "active",
})

assert created.code == "D003"
assert created.status == "ACTIVE"
assert service.exists("D003")


updated = service.update(
    "D003",
    {
        "name": "Demo Three Updated",
        "status": "ACTIVE",
    },
)

assert (
    updated.name
    == "Demo Three Updated"
)


deleted = service.delete(
    "D003"
)

assert deleted.status == "INACTIVE"


try:
    service.create({
        "code": "D001",
        "name": "Duplicate",
    })

except ValueError as error:
    print(
        "Duplicate validation:",
        error,
    )

else:
    raise AssertionError(
        "Duplicate validation did not run."
    )


print(
    "Records:",
    len(service.get_all()),
)

print(
    "Search ACTIVE:",
    len(service.search("active")),
)

print()
print(
    "BaseCRUDService test passed."
)