from abc import abstractmethod


class BaseCRUDService:
    """
    Service nền dùng chung cho Master Data.

    Lớp này không giả định cấu trúc khóa của từng model.
    Service con cần triển khai các phương thức nghiệp vụ cụ thể.

    API chuẩn:
        get_all()
        get_by_key(key)
        search(keyword)
        create(data)
        update(key, data)
        delete(key)
        exists(key)
    """

    ENTITY_NAME = "Record"

    def __init__(
        self,
        repository,
        session=None,
    ):
        if repository is None:
            raise ValueError(
                "Repository is required."
            )

        self.repository = repository

        self.session = (
            session
            or getattr(
                repository,
                "session",
                None,
            )
        )

    # ==========================================================
    # Query
    # ==========================================================

    def get_all(self):
        """
        Trả về toàn bộ bản ghi.
        """
        if not hasattr(
            self.repository,
            "get_all",
        ):
            raise AttributeError(
                f"{self.repository.__class__.__name__} "
                "does not provide get_all()."
            )

        return self.repository.get_all()

    @abstractmethod
    def get_by_key(self, key):
        """
        Lấy một bản ghi theo khóa nghiệp vụ.
        """

    def exists(self, key):
        """
        Kiểm tra bản ghi có tồn tại hay không.
        """
        return self.get_by_key(key) is not None

    def search(self, keyword):
        """
        Search mặc định.

        Service con nên override search_fields()
        hoặc override trực tiếp search().
        """
        records = self.get_all()

        keyword = self._normalize_search_keyword(
            keyword
        )

        if not keyword:
            return records

        fields = self.search_fields()

        if not fields:
            return records

        return [
            record
            for record in records
            if self._record_matches(
                record,
                fields,
                keyword,
            )
        ]

    def search_fields(self):
        """
        Danh sách tên thuộc tính được dùng để tìm kiếm.

        Ví dụ:
            return [
                "product_code",
                "product_name_vi",
            ]
        """
        return []

    # ==========================================================
    # CRUD
    # ==========================================================

    @abstractmethod
    def create(self, data):
        """
        Tạo bản ghi mới từ dictionary.
        """

    @abstractmethod
    def update(self, key, data):
        """
        Cập nhật bản ghi theo khóa nghiệp vụ.
        """

    @abstractmethod
    def delete(self, key):
        """
        Xóa hoặc deactivate bản ghi.
        """

    # ==========================================================
    # Transaction helpers
    # ==========================================================

    def commit(self):
        if self.session is None:
            return

        self.session.commit()

    def rollback(self):
        if self.session is None:
            return

        self.session.rollback()

    def flush(self):
        if self.session is None:
            return

        self.session.flush()

    def safe_commit(self):
        try:
            self.commit()

        except Exception:
            self.rollback()
            raise

    # ==========================================================
    # Validation helpers
    # ==========================================================

    def require_record(
        self,
        key,
        error_class=ValueError,
    ):
        record = self.get_by_key(key)

        if record is None:
            raise error_class(
                f"{self.ENTITY_NAME} not found: "
                f"{self.format_key(key)}"
            )

        return record

    def require_unique(
        self,
        key,
        error_class=ValueError,
    ):
        if self.exists(key):
            raise error_class(
                f"{self.ENTITY_NAME} already exists: "
                f"{self.format_key(key)}"
            )

    @staticmethod
    def require_dict(data):
        if not isinstance(data, dict):
            raise ValueError(
                "Data must be a dictionary."
            )

        return data

    # ==========================================================
    # Normalization
    # ==========================================================

    @staticmethod
    def normalize_code(value):
        return str(
            value or ""
        ).strip().upper()

    @staticmethod
    def normalize_text(value):
        if value is None:
            return ""

        text = str(value).strip()

        if text.lower() in {
            "none",
            "nan",
            "nat",
        }:
            return ""

        return " ".join(
            text.split()
        )

    @classmethod
    def normalize_optional_text(
        cls,
        value,
    ):
        text = cls.normalize_text(value)
        return text or None

    @staticmethod
    def normalize_status(
        value,
        default="ACTIVE",
    ):
        return str(
            value or default
        ).strip().upper()

    @staticmethod
    def normalize_non_negative_int(
        value,
        field_name="Value",
    ):
        try:
            number = int(
                float(value or 0)
            )

        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                f"{field_name} must be an integer: "
                f"{value}"
            ) from error

        if number < 0:
            raise ValueError(
                f"{field_name} cannot be negative."
            )

        return number

    @staticmethod
    def normalize_positive_int(
        value,
        field_name="Value",
    ):
        number = (
            BaseCRUDService
            .normalize_non_negative_int(
                value,
                field_name,
            )
        )

        if number <= 0:
            raise ValueError(
                f"{field_name} must be greater "
                "than zero."
            )

        return number

    @staticmethod
    def normalize_non_negative_float(
        value,
        field_name="Value",
    ):
        try:
            number = float(
                value or 0
            )

        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                f"{field_name} must be numeric: "
                f"{value}"
            ) from error

        if number < 0:
            raise ValueError(
                f"{field_name} cannot be negative."
            )

        return number

    @staticmethod
    def normalize_positive_float(
        value,
        field_name="Value",
    ):
        number = (
            BaseCRUDService
            .normalize_non_negative_float(
                value,
                field_name,
            )
        )

        if number <= 0:
            raise ValueError(
                f"{field_name} must be greater "
                "than zero."
            )

        return number

    # ==========================================================
    # Search helpers
    # ==========================================================

    @staticmethod
    def _normalize_search_keyword(
        keyword,
    ):
        return str(
            keyword or ""
        ).strip().lower()

    @staticmethod
    def _record_matches(
        record,
        fields,
        keyword,
    ):
        for field_name in fields:
            value = getattr(
                record,
                field_name,
                "",
            )

            if keyword in str(
                value or ""
            ).lower():
                return True

        return False

    # ==========================================================
    # Key helpers
    # ==========================================================

    @staticmethod
    def format_key(key):
        if isinstance(
            key,
            (tuple, list),
        ):
            return " / ".join(
                str(value)
                for value in key
            )

        return str(key)