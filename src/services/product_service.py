from src.database.session import get_session
from src.framework.constants import (
    STATUS_ACTIVE,
    STATUS_INACTIVE,
)
from src.framework.exception import (
    DuplicateError,
    NotFoundError,
)
from src.framework.validator import BaseValidator
from src.models.product import Product
from src.repository.product_repository import ProductRepository
from src.utils.logger import get_logger


class ProductService:
    """
    Nghiệp vụ Product Master.

    Các API cũ được giữ nguyên để tương thích với UI.
    Hàm save_product() được bổ sung cho Master Import.
    """

    def __init__(self, session=None, repository=None):
        self.logger = get_logger("ProductService")

        if repository is not None:
            # Compatibility mode: dùng repository được truyền từ bên ngoài
            self.repository = repository
            self.session = getattr(repository, "session", None)
            self._owns_session = False
        else:
            self._owns_session = session is None
            self.session = session or get_session()
            self.repository = ProductRepository(self.session)

    # ==========================================================
    # Query
    # ==========================================================

    def get_all_products(self):
        return self.repository.get_all()

    def get_product(self, product_code):
        product_code = self._normalize_code(product_code)
        if not product_code:
            return None
        return self.repository.get_by_code(product_code)

    def get_by_code(self, product_code):
        """
        Alias chuẩn cho các module mới.
        """
        return self.get_product(product_code)

    def search_products(self, keyword):
        """
        LƯU Ý: Khuyên khích nên chuyển logic filter keyword này xuống ProductRepository 
        để sử dụng query SQL `LIKE` thay vì tải toàn bộ DB lên RAM.
        """
        products = self.get_all_products()
        if not keyword:
            return products

        keyword = str(keyword).strip().lower()

        return [
            product
            for product in products
            if keyword in (product.product_code or "").lower()
            or keyword in (product.product_name_vi or "").lower()
            or keyword in (product.product_name_cn or "").lower()
            or keyword in (product.customer or "").lower()
            or keyword in (product.material or "").lower()
        ]

    # ==========================================================
    # Create
    # ==========================================================

    def create_product(
        self,
        product_code,
        product_name_vi,
        product_name_cn=None,
        customer=None,
        material=None,
        unit="PCS",
        status=STATUS_ACTIVE,
    ):
        product_code = self._normalize_code(product_code)
        product_name_vi = self._clean_text(product_name_vi)
        product_name_cn = self._clean_optional_text(product_name_cn)
        customer = self._clean_optional_text(customer)
        material = self._clean_optional_text(material)
        unit = self._normalize_unit(unit)
        status = self._normalize_status(status)

        self._validate_product(
            product_code=product_code,
            product_name_vi=product_name_vi,
        )

        existing_product = self.repository.get_by_code(product_code)
        if existing_product:
            raise DuplicateError(f"Product already exists: {product_code}")

        product = Product(
            product_code=product_code,
            product_name_vi=product_name_vi,
            product_name_cn=product_name_cn,
            customer=customer,
            material=material,
            unit=unit,
            status=status,
        )

        self.logger.info(f"Create Product: {product_code}")
        return self.repository.add(product)

    # ==========================================================
    # Update
    # ==========================================================

    def update_product(self, product_code, data):
        product_code = self._normalize_code(product_code)

        product = self.repository.get_by_code(product_code)
        if product is None:
            raise NotFoundError(f"Product not found: {product_code}")

        product_name_vi = self._clean_text(
            data.get("product_name_vi") or data.get("product_name")
        )

        self._validate_product(
            product_code=product_code,
            product_name_vi=product_name_vi,
        )

        product.product_name_vi = product_name_vi
        product.product_name_cn = self._clean_optional_text(data.get("product_name_cn"))
        product.customer = self._clean_optional_text(data.get("customer"))
        product.material = self._clean_optional_text(data.get("material"))
        product.unit = self._normalize_unit(data.get("unit"))
        product.status = self._normalize_status(data.get("status"))

        self.logger.info(f"Update Product: {product_code}")
        self.repository.update() # Giả định repository.update() lưu trạng thái của session
        return product

    # ==========================================================
    # Upsert for Import (Tối ưu hóa tránh trùng lặp query)
    # ==========================================================

    def save_product(self, data):
        """
        Tạo mới hoặc cập nhật Product (Tối ưu hóa tránh gọi lặp DB).
        """
        if not isinstance(data, dict):
            raise ValueError("Product data must be a dictionary.")

        product_code = self._normalize_code(data.get("product_code"))
        product_name_vi = self._clean_text(
            data.get("product_name_vi") or data.get("product_name")
        )

        # Validate dữ liệu trước
        self._validate_product(
            product_code=product_code,
            product_name_vi=product_name_vi,
        )

        normalized_data = {
            "product_name_vi": product_name_vi,
            "product_name_cn": self._clean_optional_text(data.get("product_name_cn")),
            "customer": self._clean_optional_text(data.get("customer")),
            "material": self._clean_optional_text(data.get("material")),
            "unit": self._normalize_unit(data.get("unit")),
            "status": self._normalize_status(data.get("status")),
        }

        existing_product = self.repository.get_by_code(product_code)

        if existing_product is None:
            # Tạo mới trực tiếp bằng Object để tránh bị gọi hàm get_by_code() một lần nữa bên trong create_product
            product = Product(
                product_code=product_code,
                **normalized_data
            )
            self.logger.info(f"Import - Create Product: {product_code}")
            action = "created"
            self.repository.add(product)
        else:
            # Cập nhật trực tiếp lên thực thể cũ tìm thấy
            existing_product.product_name_vi = normalized_data["product_name_vi"]
            existing_product.product_name_cn = normalized_data["product_name_cn"]
            existing_product.customer = normalized_data["customer"]
            existing_product.material = normalized_data["material"]
            existing_product.unit = normalized_data["unit"]
            existing_product.status = normalized_data["status"]
            
            self.logger.info(f"Import - Update Product: {product_code}")
            action = "updated"
            self.repository.update()
            product = existing_product

        return product, action

    # ==========================================================
    # Delete
    # ==========================================================

    def delete_product(self, product_code):
        product_code = self._normalize_code(product_code)
        product = self.repository.get_by_code(product_code)

        if product is None:
            raise NotFoundError(f"Product not found: {product_code}")

        # Soft delete
        product.status = STATUS_INACTIVE
        self.logger.warning(f"Inactive Product: {product_code}")
        self.repository.update()

        return product

    # ==========================================================
    # Validation and normalization
    # ==========================================================

    @staticmethod
    def _validate_product(product_code, product_name_vi):
        BaseValidator.required(product_code, "Product Code")
        BaseValidator.required(product_name_vi, "Vietnamese Name")
        BaseValidator.max_length(product_code, "Product Code", 30)
        BaseValidator.max_length(product_name_vi, "Vietnamese Name", 200)

    @staticmethod
    def _normalize_code(value):
        return str(value or "").strip().upper()

    @staticmethod
    def _clean_text(value):
        return str(value or "").strip()

    @staticmethod
    def _clean_optional_text(value):
        text = str(value or "").strip()
        return text or None

    @staticmethod
    def _normalize_unit(value):
        return str(value or "PCS").strip().upper() or "PCS"

    @staticmethod
    def _normalize_status(value):
        status = str(value or STATUS_ACTIVE).strip().upper()
        if status not in {STATUS_ACTIVE, STATUS_INACTIVE}:
            raise ValueError(f"Invalid Product Status: {status}")
        return status

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def close(self):
        if self._owns_session:
            self.session.close()