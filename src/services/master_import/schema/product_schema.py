from src.services.master_import.schema.base_schema import (
    FieldSchema,
    ImportSchema,
)


PRODUCT_SCHEMA = ImportSchema(
    module_name="PRODUCT",
    allow_extra_columns=False,
    fields=[
        FieldSchema(
            name="Product Code",
            required=True,
            data_type=str,
            unique=True,
        ),
        FieldSchema(
            name="Product Name",
            required=True,
            data_type=str,
        ),
        FieldSchema(
            name="Customer",
            required=False,
            data_type=str,
        ),
        FieldSchema(
            name="Drawing No",
            required=False,
            data_type=str,
        ),
        FieldSchema(
            name="Revision",
            required=False,
            data_type=str,
        ),
        FieldSchema(
            name="Material",
            required=True,
            data_type=str,
        ),
        FieldSchema(
            name="Unit",
            required=True,
            data_type=str,
            allowed_values=[
                "PCS",
                "KG",
                "SET",
            ],
        ),
        FieldSchema(
            name="Cycle Time (Sec)",
            required=True,
            data_type=float,
            minimum=0.000001,
        ),
        FieldSchema(
            name="Standard Output (PCS/H)",
            required=True,
            data_type=float,
            minimum=0,
        ),
        FieldSchema(
            name="Product Group",
            required=False,
            data_type=str,
        ),
        FieldSchema(
            name="Status",
            required=True,
            data_type=str,
            allowed_values=[
                "ACTIVE",
                "INACTIVE",
            ],
        ),
        FieldSchema(
            name="Remark",
            required=False,
            data_type=str,
        ),
    ],
)