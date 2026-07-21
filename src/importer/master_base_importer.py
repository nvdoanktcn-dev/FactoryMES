from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd


class MasterImportResult:
    """
    Kết quả preview hoặc import dữ liệu Master.
    """

    def __init__(self):
        self.total = 0
        self.valid = 0
        self.invalid = 0
        self.created = 0
        self.updated = 0
        self.skipped = 0
        self.errors = []

    def add_valid(self):
        self.valid += 1

    def add_error(self, row_number, message):
        self.invalid += 1
        self.errors.append({
            "row": row_number,
            "message": str(message),
        })

    def add_created(self):
        self.created += 1

    def add_updated(self):
        self.updated += 1

    def add_skipped(self):
        self.skipped += 1

    def finish(self, total):
        self.total = int(total or 0)

    @property
    def success(self):
        return self.invalid == 0

    def to_dict(self):
        return {
            "total": self.total,
            "valid": self.valid,
            "invalid": self.invalid,
            "created": self.created,
            "updated": self.updated,
            "skipped": self.skipped,
            "errors": list(self.errors),
            "success": self.success,
        }


class MasterBaseImporter(ABC):
    """
    Lớp nền dùng chung cho Product, Machine, Employee,
    Routing và Work Order Importer.

    Pipeline:

        File
        -> đọc dữ liệu
        -> chuẩn hóa tiêu đề
        -> mapping tên cột
        -> làm sạch dữ liệu
        -> kiểm tra cột bắt buộc
        -> kiểm tra từng dòng
        -> preview
        -> ghi dữ liệu qua Service
    """

    SUPPORTED_EXTENSIONS = {
        ".xlsx",
        ".xlsm",
        ".xls",
        ".csv",
    }

    REQUIRED_COLUMNS = []
    COLUMN_MAPPING = {}

    def load_file(self, filename):
        """
        Đọc Excel hoặc CSV và trả về DataFrame.
        """
        path = Path(filename)

        if not path.exists():
            raise FileNotFoundError(
                f"File not found:\n{filename}"
            )

        if not path.is_file():
            raise ValueError(
                f"Path is not a file:\n{filename}"
            )

        suffix = path.suffix.lower()

        if suffix not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                "Unsupported file format.\n"
                "Supported formats: .xlsx, .xlsm, .xls, .csv"
            )

        try:
            if suffix in {".xlsx", ".xlsm"}:
                return pd.read_excel(
                    path,
                    engine="openpyxl",
                )

            if suffix == ".xls":
                return pd.read_excel(
                    path,
                    engine="xlrd",
                )

            return self._read_csv(path)

        except ImportError as error:
            if suffix == ".xls":
                raise ImportError(
                    "Reading .xls requires xlrd.\n"
                    "Run: python -m pip install xlrd==2.0.1"
                ) from error

            if suffix in {".xlsx", ".xlsm"}:
                raise ImportError(
                    "Reading .xlsx/.xlsm requires openpyxl.\n"
                    "Run: python -m pip install openpyxl"
                ) from error

            raise

        except Exception as error:
            raise ValueError(
                f"Unable to read master file:\n"
                f"{filename}\n\n{error}"
            ) from error

    @staticmethod
    def _read_csv(path):
        """
        Thử các encoding thường gặp tại Việt Nam.
        """
        encodings = [
            "utf-8-sig",
            "utf-8",
            "cp1258",
            "latin1",
        ]

        last_error = None

        for encoding in encodings:
            try:
                return pd.read_csv(
                    path,
                    encoding=encoding,
                )

            except UnicodeDecodeError as error:
                last_error = error

        raise ValueError(
            f"Unable to determine CSV encoding: {last_error}"
        )

    def prepare_dataframe(self, dataframe):
        """
        Thực hiện toàn bộ bước chuẩn hóa chung.
        """
        if dataframe is None:
            raise ValueError("DataFrame is required.")

        df = dataframe.copy()

        df.columns = [
            self.normalize_column_name(column)
            for column in df.columns
        ]

        df = self.rename_columns(df)
        df = df.dropna(how="all")
        df = self.clean_dataframe(df)

        return df.reset_index(drop=True)

    @staticmethod
    def normalize_column_name(column):
        """
        Chuẩn hóa xuống dòng, khoảng trắng và ký tự toàn chiều.
        """
        value = str(column)

        value = value.replace("\r\n", "\n")
        value = value.replace("\r", "\n")
        value = value.replace("\u3000", " ")
        value = value.strip()

        lines = [
            " ".join(line.split())
            for line in value.split("\n")
            if line.strip()
        ]

        return " ".join(lines)

    def rename_columns(self, dataframe):
        """
        Mapping nhiều tên Excel khác nhau về tên cột chuẩn.
        """
        normalized_mapping = {
            self.normalize_column_name(source): target
            for source, target in self.COLUMN_MAPPING.items()
        }

        rename_map = {}

        for column in dataframe.columns:
            normalized = self.normalize_column_name(column)

            if normalized in normalized_mapping:
                rename_map[column] = normalized_mapping[normalized]

        return dataframe.rename(columns=rename_map)

    def validate_columns(self, dataframe):
        """
        Kiểm tra các cột bắt buộc.
        """
        missing_columns = [
            column
            for column in self.REQUIRED_COLUMNS
            if column not in dataframe.columns
        ]

        if missing_columns:
            formatted = "\n".join(
                f"- {column}"
                for column in missing_columns
            )

            raise ValueError(
                "Missing required columns:\n"
                f"{formatted}"
            )

    def preview(self, filename):
        """
        Đọc, chuẩn hóa và kiểm tra dữ liệu nhưng chưa ghi database.
        """
        dataframe = self.load_file(filename)
        dataframe = self.prepare_dataframe(dataframe)

        self.validate_columns(dataframe)

        result = MasterImportResult()

        for index, row in dataframe.iterrows():
            excel_row = index + 2

            try:
                self.validate_row(row, excel_row)
                result.add_valid()

            except Exception as error:
                result.add_error(
                    excel_row,
                    str(error),
                )

        result.finish(len(dataframe))

        return {
            "filename": str(filename),
            "dataframe": dataframe,
            "result": result,
            "rows": len(dataframe),
            "columns": len(dataframe.columns),
            "column_names": list(dataframe.columns),
        }

    def import_file(self, filename):
        """
        Import các dòng hợp lệ.

        Một dòng lỗi không làm dừng toàn bộ file.
        """
        preview = self.preview(filename)
        dataframe = preview["dataframe"]

        result = MasterImportResult()

        for index, row in dataframe.iterrows():
            excel_row = index + 2

            try:
                self.validate_row(row, excel_row)

                data = self.map_row(row)

                action = self.save_record(data)

                if action == "created":
                    result.add_created()

                elif action == "updated":
                    result.add_updated()

                else:
                    result.add_skipped()

                result.add_valid()

            except Exception as error:
                result.add_error(
                    excel_row,
                    str(error),
                )

        result.finish(len(dataframe))
        return result

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
    def to_int(value, default=0):
        if value is None or pd.isna(value) or value == "":
            return default

        try:
            return int(float(value))

        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Invalid integer value: {value}"
            ) from error

    @staticmethod
    def to_float(value, default=0.0):
        if value is None or pd.isna(value) or value == "":
            return default

        try:
            return float(value)

        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Invalid numeric value: {value}"
            ) from error

    @staticmethod
    def require_value(value, field_name):
        text = MasterBaseImporter.clean_text(value)

        if not text:
            raise ValueError(
                f"{field_name} is required."
            )

        return text

    def clean_dataframe(self, dataframe):
        """
        Importer con có thể override khi cần xử lý riêng.
        """
        return dataframe

    @abstractmethod
    def validate_row(self, row, row_number):
        """
        Kiểm tra nghiệp vụ của một dòng.
        """

    @abstractmethod
    def map_row(self, row):
        """
        Chuyển một dòng DataFrame thành dictionary chuẩn.
        """

    @abstractmethod
    def save_record(self, data):
        """
        Lưu dữ liệu qua Service.

        Trả về một trong các giá trị:
        - created
        - updated
        - skipped
        """