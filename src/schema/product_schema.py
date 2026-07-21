class ProductSchema:
    """
    Định nghĩa cấu trúc dữ liệu chuẩn cho Product Master Import.

    Schema chỉ chứa quy tắc dữ liệu.
    Schema không đọc Excel và không truy cập database.
    """

    REQUIRED_COLUMNS = [
        "Product Code",
        "Product Name",
    ]

    OPTIONAL_COLUMNS = [
        "Product Name VI",
        "Product Name CN",
        "Customer",
        "Material",
        "Unit",
        "Status",
        "Remark",
    ]

    COLUMN_MAPPING = {
        # Product Code
        "Product Code": "Product Code",
        "Mã sản phẩm": "Product Code",
        "Mã hàng": "Product Code",
        "Mã SP": "Product Code",
        "产品编码": "Product Code",
        "产品代码": "Product Code",

        # Product Name
        "Product Name": "Product Name",
        "Tên sản phẩm": "Product Name",
        "Tên hàng": "Product Name",
        "Tên SP": "Product Name",
        "产品名称": "Product Name",

        # Vietnamese name
        "Product Name VI": "Product Name VI",
        "Product Name VN": "Product Name VI",
        "Tên sản phẩm VI": "Product Name VI",
        "Tên tiếng Việt": "Product Name VI",

        # Chinese name
        "Product Name CN": "Product Name CN",
        "Tên sản phẩm CN": "Product Name CN",
        "Tên tiếng Trung": "Product Name CN",
        "中文名称": "Product Name CN",

        # Customer
        "Customer": "Customer",
        "Khách hàng": "Customer",
        "客户": "Customer",
        "客户名称": "Customer",

        # Material
        "Material": "Material",
        "Vật liệu": "Material",
        "Nguyên liệu": "Material",
        "材料": "Material",

        # Unit
        "Unit": "Unit",
        "Đơn vị": "Unit",
        "ĐVT": "Unit",
        "单位": "Unit",

        # Status
        "Status": "Status",
        "Trạng thái": "Status",
        "状态": "Status",

        # Remark
        "Remark": "Remark",
        "Ghi chú": "Remark",
        "备注": "Remark",
    }

    VALID_STATUSES = {
        "ACTIVE",
        "INACTIVE",
    }

    STATUS_MAPPING = {
        "ACTIVE": "ACTIVE",
        "HOẠT ĐỘNG": "ACTIVE",
        "ĐANG HOẠT ĐỘNG": "ACTIVE",
        "启用": "ACTIVE",
        "有效": "ACTIVE",
        "1": "ACTIVE",

        "INACTIVE": "INACTIVE",
        "NGỪNG HOẠT ĐỘNG": "INACTIVE",
        "KHÔNG HOẠT ĐỘNG": "INACTIVE",
        "停用": "INACTIVE",
        "无效": "INACTIVE",
        "0": "INACTIVE",
    }

    DEFAULT_UNIT = "PCS"
    DEFAULT_STATUS = "ACTIVE"

    @classmethod
    def normalize_status(cls, value):
        text = str(value or "").strip().upper()

        if not text:
            return cls.DEFAULT_STATUS

        normalized = cls.STATUS_MAPPING.get(text, text)

        if normalized not in cls.VALID_STATUSES:
            raise ValueError(
                f"Invalid Product Status: {value}. "
                "Allowed values: ACTIVE, INACTIVE."
            )

        return normalized

    @classmethod
    def validate_data(cls, data):
        product_code = str(
            data.get("product_code", "")
        ).strip()

        product_name = str(
            data.get("product_name", "")
        ).strip()

        if not product_code:
            raise ValueError("Product Code is required.")

        if not product_name:
            raise ValueError("Product Name is required.")

        if len(product_code) > 50:
            raise ValueError(
                "Product Code cannot exceed 50 characters."
            )

        if len(product_name) > 200:
            raise ValueError(
                "Product Name cannot exceed 200 characters."
            )

        status = data.get(
            "status",
            cls.DEFAULT_STATUS,
        )

        if status not in cls.VALID_STATUSES:
            raise ValueError(
                f"Invalid Product Status: {status}."
            )

        return True