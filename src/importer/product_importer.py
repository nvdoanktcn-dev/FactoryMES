from src.importer.master_base_importer import (
    MasterBaseImporter,
)
from src.mapper.product_mapper import ProductMapper
from src.schema.product_schema import ProductSchema
from src.services.product_service import ProductService


class ProductImporter(MasterBaseImporter):
    """
    Import Product Master từ Excel hoặc CSV.

    Pipeline:

        File
        -> MasterBaseImporter
        -> ProductSchema
        -> ProductMapper
        -> ProductService.save_product()
        -> tb_product
    """

    REQUIRED_COLUMNS = ProductSchema.REQUIRED_COLUMNS
    COLUMN_MAPPING = ProductSchema.COLUMN_MAPPING

    def __init__(self):
        super().__init__()
        self.product_service = ProductService()

    def clean_dataframe(self, dataframe):
        """
        Chuẩn hóa các cột text của Product.
        """
        df = dataframe.copy()

        text_columns = [
            "Product Code",
            "Product Name",
            "Product Name VI",
            "Product Name CN",
            "Customer",
            "Material",
            "Unit",
            "Status",
            "Remark",
        ]

        for column in text_columns:
            if column not in df.columns:
                continue

            df[column] = df[column].map(
                self.clean_text
            )

        if "Product Code" in df.columns:
            df["Product Code"] = (
                df["Product Code"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

        if "Unit" in df.columns:
            df["Unit"] = df["Unit"].map(
                lambda value: (
                    self.clean_text(value).upper()
                    or ProductSchema.DEFAULT_UNIT
                )
            )

        if "Status" in df.columns:
            df["Status"] = df["Status"].map(
                ProductSchema.normalize_status
            )

        return df

    def validate_row(self, row, row_number):
        """
        Kiểm tra một dòng Product trước khi import.
        """
        product_code = self.require_value(
            row.get("Product Code"),
            "Product Code",
        ).upper()

        product_name = self.require_value(
            row.get("Product Name"),
            "Product Name",
        )

        if len(product_code) > 30:
            raise ValueError(
                "Product Code cannot exceed "
                "30 characters."
            )

        if len(product_name) > 200:
            raise ValueError(
                "Product Name cannot exceed "
                "200 characters."
            )

        ProductSchema.normalize_status(
            row.get("Status")
        )

        return True

    def map_row(self, row):
        """
        Mapping Excel row thành dictionary chuẩn.
        """
        return ProductMapper.from_row(row)

    def save_record(self, data):
        """
        Upsert Product qua ProductService.
        """
        _, action = self.product_service.save_product(
            data
        )

        return action