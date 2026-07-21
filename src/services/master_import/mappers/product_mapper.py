from __future__ import annotations

from src.domain.entities import Product

from .base_mapper import BaseMapper


class ProductMapper(BaseMapper):

    def from_row(
        self,
        row,
    ):

        return Product(

            product_code=str(
                row["Product Code"]
            ).strip(),

            product_name=str(
                row["Product Name"]
            ).strip(),

            customer=str(
                row.get(
                    "Customer",
                    "",
                )
            ).strip(),

            drawing_no=str(
                row.get(
                    "Drawing No",
                    "",
                )
            ).strip(),

            revision=str(
                row.get(
                    "Revision",
                    "",
                )
            ).strip(),

            material=str(
                row.get(
                    "Material",
                    "",
                )
            ).strip(),

            unit=str(
                row.get(
                    "Unit",
                    "PCS",
                )
            ).strip(),

            cycle_time=float(
                row.get(
                    "Cycle Time (Sec)",
                    0,
                )
            ),

            standard_output=float(
                row.get(
                    "Standard Output (PCS/H)",
                    0,
                )
            ),

            product_group=str(
                row.get(
                    "Product Group",
                    "",
                )
            ).strip(),

            status=str(
                row.get(
                    "Status",
                    "ACTIVE",
                )
            ).upper(),

            remark=str(
                row.get(
                    "Remark",
                    "",
                )
            ).strip(),
        )