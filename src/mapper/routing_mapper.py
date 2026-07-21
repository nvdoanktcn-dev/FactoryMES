import pandas as pd

from src.schema.routing_schema import RoutingSchema


class RoutingMapper:
    """
    Chuyển một dòng Routing Master đã chuẩn hóa
    thành dictionary dùng bởi RoutingService.
    """

    @classmethod
    def from_row(cls, row):
        if row is None:
            raise ValueError(
                "Routing row is required."
            )

        product_code = cls.clean_text(
            row.get("Product Code")
        ).upper()

        op_no = RoutingSchema.normalize_op(
            row.get("OP No")
        )

        machine_code = cls.clean_text(
            row.get("Machine Code")
        ).upper()

        machine_type = (
            RoutingSchema.normalize_machine_type(
                row.get("Machine Type"),
                machine_code,
            )
        )

        cycle_time_sec = cls.to_float(
            row.get("Cycle Time Sec"),
            field_name="Cycle Time Sec",
        )

        standard_output_hour = cls.to_float(
            row.get("Standard Output Hour"),
            field_name="Standard Output Hour",
        )

        # Nếu file không có sản lượng chuẩn/giờ,
        # tự tính từ Cycle Time.
        if (
            standard_output_hour <= 0
            and cycle_time_sec > 0
        ):
            standard_output_hour = round(
                3600 / cycle_time_sec,
                4,
            )

        data = {
            "product_code": product_code,

            "op_no": op_no,

            "sequence": cls.to_int(
                row.get("Sequence"),
                field_name="Sequence",
            ),

            "op_name": cls.clean_text(
                row.get("OP Name")
            ),

            "process_type": cls.clean_text(
                row.get("Process Type")
            ).upper(),

            "machine_type": machine_type,

            "machine_code": machine_code,

            "cycle_time_sec": cycle_time_sec,

            "setup_time_min": cls.to_float(
                row.get("Setup Time Min"),
                field_name="Setup Time Min",
            ),

            "standard_output_hour":
                standard_output_hour,

            "status": RoutingSchema.normalize_status(
                row.get("Status")
            ),

            "remark": cls.clean_text(
                row.get("Remark")
            ),
        }

        RoutingSchema.validate_data(data)

        return data

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

    @staticmethod
    def to_int(value, field_name="Value"):
        if value is None or pd.isna(value):
            return 0

        try:
            return int(float(value))

        except (TypeError, ValueError) as error:
            raise ValueError(
                f"{field_name} must be an integer: {value}"
            ) from error

    @staticmethod
    def to_float(value, field_name="Value"):
        if value is None or pd.isna(value) or value == "":
            return 0.0

        try:
            return float(value)

        except (TypeError, ValueError) as error:
            raise ValueError(
                f"{field_name} must be numeric: {value}"
            ) from error