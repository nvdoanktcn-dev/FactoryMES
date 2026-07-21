from src.services.master_import.schema import (
    MACHINE_SCHEMA,
    PRODUCT_SCHEMA,
)


def check_schema(
    schema,
):
    assert schema.module_name
    assert isinstance(
        schema.headers,
        list,
    )
    assert isinstance(
        schema.required_headers,
        list,
    )
    assert isinstance(
        schema.optional_headers,
        list,
    )
    assert isinstance(
        schema.unique_fields,
        list,
    )
    assert isinstance(
        schema.field_map,
        dict,
    )

    assert schema.headers == (
        schema.all_columns
    )

    for field_name in (
        schema.unique_fields
    ):
        field_schema = schema.get_field(
            field_name
        )

        assert field_schema is not None
        assert field_schema.unique is True


check_schema(
    PRODUCT_SCHEMA
)

check_schema(
    MACHINE_SCHEMA
)

assert "Product Code" in (
    PRODUCT_SCHEMA.unique_fields
)

assert "Machine Code" in (
    MACHINE_SCHEMA.unique_fields
)

print(
    "ImportSchema compatibility test passed."
)