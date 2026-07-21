import pandas as pd

from src.schema.employee_schema import (
    EmployeeSchema,
)


class EmployeeMapper:

    @classmethod
    def from_row(cls, row):

        data = {

            "employee_code":

            cls.clean(
                row.get("Employee Code")
            ).upper(),

            "employee_name":

            cls.clean(
                row.get("Employee Name")
            ),

            "department":

            cls.clean(
                row.get("Department")
            ),

            "position":

            cls.clean(
                row.get("Position")
            ),

            "status":

            EmployeeSchema.normalize_status(
                row.get("Status")
            ),
        }

        EmployeeSchema.validate_data(
            data
        )

        return data

    @staticmethod
    def clean(value):

        if value is None:
            return ""

        if pd.isna(value):
            return ""

        return str(value).strip()