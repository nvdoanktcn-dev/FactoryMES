from src.importer.master_base_importer import MasterBaseImporter


class GenericMasterImporter(MasterBaseImporter):
    """
    Importer dùng chung cho dữ liệu Master.

    Importer con chỉ cần khai báo:

        SCHEMA
        MAPPER
        SERVICE_CLASS
        SAVE_METHOD

    Ví dụ:

        class ProductImporter(GenericMasterImporter):
            SCHEMA = ProductSchema
            MAPPER = ProductMapper
            SERVICE_CLASS = ProductService
            SAVE_METHOD = "save_product"
    """

    SCHEMA = None
    MAPPER = None
    SERVICE_CLASS = None
    SAVE_METHOD = None

    def __init__(self):
        self._validate_configuration()

        self.service = self.SERVICE_CLASS()

        self.REQUIRED_COLUMNS = list(
            getattr(
                self.SCHEMA,
                "REQUIRED_COLUMNS",
                [],
            )
        )

        self.COLUMN_MAPPING = dict(
            getattr(
                self.SCHEMA,
                "COLUMN_MAPPING",
                {},
            )
        )

    # ==========================================================
    # Configuration
    # ==========================================================

    def _validate_configuration(self):
        if self.SCHEMA is None:
            raise ValueError(
                f"{self.__class__.__name__}.SCHEMA is required."
            )

        if self.MAPPER is None:
            raise ValueError(
                f"{self.__class__.__name__}.MAPPER is required."
            )

        if self.SERVICE_CLASS is None:
            raise ValueError(
                f"{self.__class__.__name__}.SERVICE_CLASS is required."
            )

        if not self.SAVE_METHOD:
            raise ValueError(
                f"{self.__class__.__name__}.SAVE_METHOD is required."
            )

        if not hasattr(self.MAPPER, "from_row"):
            raise ValueError(
                f"{self.MAPPER.__name__} must provide from_row()."
            )

        if not hasattr(
            self.SERVICE_CLASS,
            self.SAVE_METHOD,
        ):
            raise ValueError(
                f"{self.SERVICE_CLASS.__name__} does not provide "
                f"{self.SAVE_METHOD}()."
            )

    # ==========================================================
    # Data preparation
    # ==========================================================

    def clean_dataframe(self, dataframe):
        """
        Làm sạch chung cho các cột dạng text.

        Importer con có thể override nếu cần xử lý riêng.
        """
        df = dataframe.copy()

        columns = set(
            getattr(
                self.SCHEMA,
                "REQUIRED_COLUMNS",
                [],
            )
        )

        columns.update(
            getattr(
                self.SCHEMA,
                "OPTIONAL_COLUMNS",
                [],
            )
        )

        for column in columns:
            if column not in df.columns:
                continue

            df[column] = df[column].map(
                self.clean_text
            )

        return df

    # ==========================================================
    # Validation
    # ==========================================================

    def validate_row(self, row, row_number):
        """
        Mapping dòng trước để Schema kiểm tra dữ liệu chuẩn.

        row_number được giữ trong chữ ký để tương thích
        MasterBaseImporter và phục vụ thông báo lỗi.
        """
        data = self.map_row(row)

        validator = getattr(
            self.SCHEMA,
            "validate_data",
            None,
        )

        if validator is not None:
            validator(data)

        return True

    # ==========================================================
    # Mapping
    # ==========================================================

    def map_row(self, row):
        return self.MAPPER.from_row(row)

    # ==========================================================
    # Save / Upsert
    # ==========================================================

    def save_record(self, data):
        save_method = getattr(
            self.service,
            self.SAVE_METHOD,
        )

        result = save_method(data)

        return self._resolve_action(result)

    @staticmethod
    def _resolve_action(result):
        """
        Hỗ trợ các dạng kết quả từ Service:

        1. (object, "created")
        2. "created"
        3. object có thuộc tính import_action
        4. None -> skipped
        """
        if isinstance(result, tuple):
            if len(result) >= 2:
                action = result[1]
                return GenericMasterImporter._normalize_action(
                    action
                )

        if isinstance(result, str):
            return GenericMasterImporter._normalize_action(
                result
            )

        if result is None:
            return "skipped"

        action = getattr(
            result,
            "import_action",
            None,
        )

        if action:
            return GenericMasterImporter._normalize_action(
                action
            )

        # Service đã lưu thành công nhưng không trả action.
        return "updated"

    @staticmethod
    def _normalize_action(action):
        value = str(action or "").strip().lower()

        if value in {
            "created",
            "updated",
            "skipped",
        }:
            return value

        return "skipped"