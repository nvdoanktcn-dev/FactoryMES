from .reference_repository import (
    ReferenceRepository,
)


class InMemoryReferenceRepository(
    ReferenceRepository
):

    def __init__(self):

        self.tables = {

            "PRODUCT_GROUP": {

                "Casting",

                "Machining",

                "CNC",

                "Gear",

            },

            "CUSTOMER": {

                "TOYOTA",

                "HONDA",

                "YAMAHA",

            },

        }

    def exists(
        self,
        category,
        value,
    ):

        return (
            str(value).strip()
            in self.tables.get(
                category,
                set(),
            )
        )