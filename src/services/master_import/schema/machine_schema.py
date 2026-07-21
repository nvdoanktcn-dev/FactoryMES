from __future__ import annotations

from src.services.master_import.schema.base_schema import (
    FieldSchema,
    ImportSchema,
)


MACHINE_SCHEMA = ImportSchema(
    module_name="MACHINE",
    allow_extra_columns=False,
    fields=[
        FieldSchema(
            name="Machine Code",
            required=True,
            data_type=str,
            unique=True,
            max_length=30,
        ),
        FieldSchema(
            name="Machine Name",
            required=True,
            data_type=str,
            max_length=100,
        ),
        FieldSchema(
            name="Machine Type",
            required=True,
            data_type=str,
            allowed_values=[
                "CNC",
                "ROBOT",
            ],
        ),
        FieldSchema(
            name="Line",
            required=False,
            data_type=str,
        ),
        FieldSchema(
            name="Location",
            required=False,
            data_type=str,
        ),
        FieldSchema(
            name="Brand",
            required=False,
            data_type=str,
        ),
        FieldSchema(
            name="Model",
            required=False,
            data_type=str,
        ),
        FieldSchema(
            name="Serial Number",
            required=False,
            data_type=str,
        ),
        FieldSchema(
            name="Status",
            required=True,
            data_type=str,
            default="RUNNING",
            allowed_values=[
                "RUNNING",
                "STOPPED",
                "MAINTENANCE",
                "INACTIVE",
            ],
        ),
    ],
)