from __future__ import annotations

from src.services.master_import.schema.base_schema import (
    FieldSchema,
    ImportSchema,
)


ROUTING_SCHEMA = ImportSchema(
    module_name="ROUTING",
    allow_extra_columns=False,
    fields=[
        FieldSchema(
            name="Product Code",
            required=True,
            data_type=str,
        ),
        FieldSchema(
            name="Operation No",
            required=True,
            data_type=str,
        ),
        FieldSchema(
            name="Operation Name",
            required=True,
            data_type=str,
            max_length=100,
        ),
        FieldSchema(
            name="Process Type",
            required=True,
            data_type=str,
            allowed_values=[
                "CNC",
                "ROBOT",
                "MANUAL",
                "INSPECTION",
                "OTHER",
            ],
        ),
        FieldSchema(
            name="Machine Type",
            required=False,
            data_type=str,
        ),
        FieldSchema(
            name="Standard Cycle Time (Sec)",
            required=True,
            data_type=float,
            minimum=0.000001,
        ),
        FieldSchema(
            name="Standard Output (PCS/H)",
            required=False,
            data_type=float,
            minimum=0,
        ),
        FieldSchema(
            name="Standard Operator Count",
            required=False,
            data_type=float,
            default=1.0,
            minimum=0.000001,
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