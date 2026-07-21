import pandas as pd

from src.schema.product_schema import ProductSchema


class ProductMapper:
    """
    Chuyển dữ liệu Product Master đã chuẩn hóa
    thành dictionary dùng bởi ProductService.
    """

    @classmethod
    def from_row(cls, row):
        if row is None:
            raise ValueError("Product row is required.")

        product_name = cls.clean_text(
            row.get("Product Name")
        )

        product_name_vi = cls.clean_text(
            row.get("Product Name VI")
        )

        product_name_cn = cls.clean_text(
            row.get("Product Name CN")
        )

        if not product_name_vi:
            product_name_vi = product_name

        data = {
            "product_code": cls.clean_text(
                row.get("Product Code")
            ).upper(),

            "product_name": product_name,

            "product_name_vi": product_name_vi,

            "product_name_cn": product_name_cn,

            "customer": cls.clean_text(
                row.get("Customer")
            ),

            "material": cls.clean_text(
                row.get("Material")
            ),

            "unit": (
                cls.clean_text(
                    row.get("Unit")
                ).upper()
                or ProductSchema.DEFAULT_UNIT
            ),

            "status": ProductSchema.normalize_status(
                row.get("Status")
            ),

            "remark": cls.clean_text(
                row.get("Remark")
            ),
        }

        ProductSchema.validate_data(data)

        return data

    @classmethod
    def from_dataframe_row(cls, row):
        """
        Giữ tương thích với code cũ.
        """
        return cls.from_row(row)

    @classmethod
    def from_dataframe(cls, dataframe):
        if dataframe is None:
            raise ValueError("DataFrame is required.")

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