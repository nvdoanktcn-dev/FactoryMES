from __future__ import annotations

from src.services.master_import.schema.base_schema import (
    FieldSchema,
    ImportSchema,
)


WORK_ORDER_SCHEMA = ImportSchema(
    module_name="WORK_ORDER",
    allow_extra_columns=False,
    fields=[
        FieldSchema(
            name="Work Order No",
            required=True,
            data_type=str,
            unique=True,
            max_length=50,
        ),
        FieldSchema(
            name="Product Code",
            required=True,
            data_type=str,
            max_length=50,
        ),
        FieldSchema(
            name="Plan Qty",
            required=True,
            data_type=int,
            minimum=1,
        ),
        FieldSchema(
            name="Start Date",
            required=True,
        ),
        FieldSchema(
            name="Due Date",
            required=True,
        ),
        FieldSchema(
            name="Priority",
            required=False,
            data_type=str,
            default="NORMAL",
            allowed_values=[
                "LOW",
                "NORMAL",
                "HIGH",
                "URGENT",
            ],
        ),
        FieldSchema(
            name="Status",
            required=False,
            data_type=str,
            default="PLANNED",
            allowed_values=[
                "PLANNED",
                "RELEASED",
                "IN_PROGRESS",
                "ON_HOLD",
                "COMPLETED",
                "CANCELLED",
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