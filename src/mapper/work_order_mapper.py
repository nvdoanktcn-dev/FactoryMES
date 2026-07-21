from datetime import date, datetime

import pandas as pd

from src.schema.work_order_schema import WorkOrderSchema


class WorkOrderMapper:
    """
    Chuyển một dòng Work Order Master đã chuẩn hóa
    thành dictionary dùng bởi WorkOrderService.

    Mapper không truy cập database.
    """

    @classmethod
    def from_row(cls, row):
        if row is None:
            raise ValueError(
                "Work Order row is required."
            )

        data = {
            "work_order_no": cls.clean_text(
                row.get("Work Order No")
            ).upper(),

            "product_code": cls.clean_text(
                row.get("Product Code")
            ).upper(),

            "plan_qty": cls.to_int(
                row.get("Plan Qty"),
                field_name="Plan Qty",
            ),

            "completed_qty": cls.to_int(
                row.get("Completed Qty"),
                field_name="Completed Qty",
                default=0,
            ),

            "ng_qty": cls.to_int(
                row.get("NG Qty"),
                field_name="NG Qty",
                default=0,
            ),

            "start_date": cls.to_date(
                row.get("Start Date"),
                field_name="Start Date",
            ),

            "due_date": cls.to_date(
                row.get("Due Date"),
                field_name="Due Date",
            ),

            "finish_date": cls.to_date(
                row.get("Finish Date"),
                field_name="Finish Date",
            ),

            "status": WorkOrderSchema.normalize_status(
                row.get("Status")
            ),

            "priority": WorkOrderSchema.normalize_priority(
                row.get("Priority")
            ),

            "remark": cls.clean_text(
                row.get("Remark")
            ),
        }

        WorkOrderSchema.validate_data(data)

        return data

    @classmethod
    def from_dataframe_row(cls, row):
        """
        Alias để tương thích với các module cũ.
        """
        return cls.from_row(row)

    @classmethod
    def from_dataframe(cls, dataframe):
        """
        Chuyển toàn bộ DataFrame thành danh sách record chuẩn.

        Returns:
            records:
                [
                    {
                        "excel_row": 2,
                        "data": {...}
                    }
                ]

            errors:
                [
                    {
                        "row": 3,
                        "message": "..."
                    }
                ]
        """
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
    def to_int(
        value,
        field_name="Value",
        default=0,
    ):
        if value is None or pd.isna(value):
            return default

        if isinstance(value, str):
            text = value.strip()

            if not text:
                return default

            text = text.replace(",", "")
            text = text.replace(" ", "")

            value = text

        try:
            number = int(float(value))

        except (TypeError, ValueError) as error:
            raise ValueError(
                f"{field_name} must be an integer: {value}"
            ) from error

        return number

    @staticmethod
    def to_date(
        value,
        field_name="Date",
    ):
        """
        Chuyển ngày Excel/String/Timestamp về datetime.date.

        Hỗ trợ rõ ràng:
        - YYYY-MM-DD
        - DD/MM/YYYY
        - DD-MM-YYYY
        - Excel datetime
        """
        if value is None or pd.isna(value):
            return None

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        if isinstance(value, pd.Timestamp):
            return value.date()

        text = str(value).strip()

        if not text or text.lower() in {
            "nan",
            "none",
            "nat",
        }:
            return None

        explicit_formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d",
            "%Y/%m/%d %H:%M:%S",
            "%d/%m/%Y",
            "%d/%m/%Y %H:%M:%S",
            "%d-%m-%Y",
            "%d-%m-%Y %H:%M:%S",
            "%d.%m.%Y",
        ]

        for date_format in explicit_formats:
            try:
                return datetime.strptime(
                    text,
                    date_format,
                ).date()

            except ValueError:
                continue

        parsed = pd.to_datetime(
            text,
            errors="coerce", 
        )

        if pd.isna(parsed):
            raise ValueError(
                f"{field_name} is invalid: {value}"
            )

        return parsed.date()