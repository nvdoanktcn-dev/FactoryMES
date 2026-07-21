from src.services.master_import.schema.machine_schema import (
    MACHINE_SCHEMA,
)
from src.services.master_import.schema.product_schema import (
    PRODUCT_SCHEMA,
)
from src.services.master_import.schema.employee_schema import (
    EMPLOYEE_SCHEMA,
)
from src.services.master_import.schema.routing_schema import (
    ROUTING_SCHEMA,
)
from src.services.master_import.schema.work_order_schema import (
    WORK_ORDER_SCHEMA,
)


class SchemaRegistry:
    """
    Quản lý ImportSchema theo module.
    """

    _schemas = {
        PRODUCT_SCHEMA.module_name: PRODUCT_SCHEMA,
        MACHINE_SCHEMA.module_name: MACHINE_SCHEMA,
        EMPLOYEE_SCHEMA.module_name: EMPLOYEE_SCHEMA,
        ROUTING_SCHEMA.module_name: ROUTING_SCHEMA,
        WORK_ORDER_SCHEMA.module_name: WORK_ORDER_SCHEMA,
    }

    @classmethod
    def get(
        cls,
        module_name,
    ):
        normalized = str(
            module_name or ""
        ).strip().upper()

        schema = cls._schemas.get(
            normalized
        )

        if schema is None:
            raise KeyError(
                f"Import schema not found: {normalized}"
            )

        return schema

    @classmethod
    def register(
        cls,
        schema,
    ):
        cls._schemas[
            schema.module_name
        ] = schema

    @classmethod
    def modules(cls):
        return list(
            cls._schemas.keys()
        )