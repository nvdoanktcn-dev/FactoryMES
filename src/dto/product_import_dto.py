from dataclasses import dataclass


@dataclass(slots=True)
class ProductImportDTO:
    """
    DTO dùng trong Product Import.

    Không thao tác database.
    Chỉ truyền dữ liệu giữa Importer và Service.
    """

    product_code: str
    product_name: str

    product_name_vi: str = ""
    product_name_cn: str = ""

    product_type: str = ""

    unit: str = "PCS"

    status: str = "ACTIVE"

    remark: str = ""