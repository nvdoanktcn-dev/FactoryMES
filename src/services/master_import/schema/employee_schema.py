from __future__ import annotations

from src.services.master_import.schema.base_schema import (
    FieldSchema,
    ImportSchema,
)


EMPLOYEE_SCHEMA = ImportSchema(
    module_name="EMPLOYEE",
    allow_extra_columns=False,
    fields=[
        FieldSchema(
            name="Employee Code",
            required=True,
            data_type=str,
            unique=True,
            max_length=30,
        ),
        FieldSchema(
            name="Employee Name",
            required=True,
            data_type=str,
            max_length=100,
        ),
        FieldSchema(
            name="Department",
            required=False,
            data_type=str,
            max_length=50,
        ),
        FieldSchema(
            name="Position",
            required=False,
            data_type=str,
            max_length=50,
        ),
        FieldSchema(
            name="Shift",
            required=False,
            data_type=str,
            allowed_values=[
                "DAY",
                "NIGHT",
                "ROTATING",
                "OFFICE",
            ],
        ),
        FieldSchema(
            name="Status",
            required=True,
            data_type=str,
            default="ACTIVE",
            allowed_values=[
                "ACTIVE",
                "INACTIVE",
            ],
        ),
        FieldSchema(
            name="Remark",
            required=False,
            data_type=str,
            max_length=255,
        ),
    ],
)