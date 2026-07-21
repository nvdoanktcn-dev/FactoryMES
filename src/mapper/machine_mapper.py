import pandas as pd

from src.schema.machine_schema import MachineSchema


class MachineMapper:
    """
    Chuyển một dòng Machine Master đã chuẩn hóa
    thành dictionary dùng bởi MachineService.

    Mapper không truy cập database.
    """

    @classmethod
    def from_row(cls, row):
        if row is None:
            raise ValueError(
                "Machine row is required."
            )

        machine_code = cls.clean_text(
            row.get("Machine Code")
        ).upper()

        machine_name = cls.clean_text(
            row.get("Machine Name")
        )

        machine_type_value = cls.clean_text(
            row.get("Machine Type")
        )

        if machine_type_value:
            machine_type = (
                MachineSchema.normalize_machine_type(
                    machine_type_value
                )
            )
        else:
            machine_type = (
                MachineSchema.infer_machine_type(
                    machine_code
                )
            )

        data = {
            "machine_code": machine_code,

            "machine_name": machine_name,

            "machine_type": machine_type,

            "department": cls.clean_text(
                row.get("Department")
            ),

            "status": MachineSchema.normalize_status(
                row.get("Status")
            ),

            "remark": cls.clean_text(
                row.get("Remark")
            ),
        }

        MachineSchema.validate_data(data)

        return data

    @classmethod
    def from_dataframe_row(cls, row):
        """
        Alias để tương thích với các module cũ.
        """
        return cls.from_row(row)

    @classmethod
    def from_dataframe(cls, dataframe):
        if dataframe is None:
            raise ValueError(
                "DataFrame is required."
            )

        records = []
        errors = []

        for index, row in dataframe.iterrows():
            excel_row = index + 2

            try:
                records.append({
                    "excel_row": excel_row,
                    "data": cls.from_row(row),
                })

            except Exception as error:
                errors.append({
                    "row": excel_row,
                    "message": str(error),
                })

        return records, errors

    @staticmethod
    def clean_text(value):
        if value is None or pd.isna(value):
            return ""

        text = str(value).strip()

        if text.lower() in {
            "nan",
            "none",
            "nat",
        }:
            return ""

        return " ".join(text.split())