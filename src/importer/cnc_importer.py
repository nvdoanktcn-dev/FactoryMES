from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from src.importer.base_importer import BaseImporter
from src.importer.data_cleaner import DataCleaner
from src.importer.data_validator import DataValidator


@dataclass
class CNCImportResult:
    """
    Kết quả import CNC theo interface mà MasterCRUDPage.handle_import()
    cần: total/valid dùng cho preview, total/created/updated/skipped/
    invalid/errors dùng cho thông báo kết quả sau khi import.
    """

    total: int = 0
    valid: int = 0
    invalid: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list = field(default_factory=list)


class CNCImporter(BaseImporter):
    """
    CNC Excel/CSV Importer.

    Pipeline

        Read File
            │
            ▼
        Data Cleaner
            │
            ▼
        Data Validator
            │
            ▼
        CNCProductionLogService (lưu vào tb_cnc_production_log)
    """

    SUPPORTED_EXTENSIONS = {
        ".xlsx",
        ".xlsm",
        ".xls",
        ".csv",
    }

    def __init__(self):
        self.cleaner = DataCleaner()
        self.validator = DataValidator()

    # ==========================================================
    # Load File
    # ==========================================================

    def load_file(self, filename):
        path = Path(filename)

        if not path.exists():
            raise FileNotFoundError(
                f"File not found:\n{filename}"
            )

        suffix = path.suffix.lower()

        if suffix not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                "Unsupported file format.\n\n"
                "Supported:\n"
                ".xlsx\n"
                ".xlsm\n"
                ".xls\n"
                ".csv"
            )

        try:

            if suffix in [".xlsx", ".xlsm"]:

                return pd.read_excel(
                    filename,
                    engine="openpyxl"
                )

            if suffix == ".xls":

                return pd.read_excel(
                    filename,
                    engine="xlrd"
                )

            if suffix == ".csv":

                return self.read_csv(filename)

        except ImportError as error:

            if suffix == ".xls":

                raise ImportError(
                    "Import xlrd failed.\n\n"
                    "Install:\n\n"
                    "python -m pip install xlrd==2.0.1"
                ) from error

            if suffix in [".xlsx", ".xlsm"]:

                raise ImportError(
                    "Import openpyxl failed.\n\n"
                    "Install:\n\n"
                    "python -m pip install openpyxl"
                ) from error

            raise

        except Exception as error:

            raise ValueError(
                f"Unable to read file.\n\n{error}"
            ) from error

    # ==========================================================
    # CSV
    # ==========================================================

    @staticmethod
    def read_csv(filename):

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
                    filename,
                    encoding=encoding
                )

            except UnicodeDecodeError as error:

                last_error = error

            except pd.errors.ParserError as error:

                raise ValueError(
                    f"CSV structure error:\n{error}"
                ) from error

            except pd.errors.EmptyDataError as error:

                raise ValueError(
                    "CSV file is empty."
                ) from error

        raise ValueError(
            f"CSV encoding error:\n{last_error}"
        )

    # ==========================================================
    # Cleaner
    # ==========================================================

    def clean_data(self, dataframe):

        return self.cleaner.clean(dataframe)

    # ==========================================================
    # Load + Clean (shared by preview and import_file)
    # ==========================================================

    def _load_and_clean(self, filename):

        dataframe = self.load_file(filename)

        dataframe = self.clean_data(dataframe)

        return dataframe

    # ==========================================================
    # Validator
    # ==========================================================

    def validate_data(self, dataframe):
        """
        Trả về danh sách lỗi dạng [{"row": ..., "message": ...}].

        Nếu file thiếu cột bắt buộc, lỗi cột được coi như áp dụng
        cho toàn bộ các dòng (không thể xác định dòng cụ thể).
        """
        try:
            return self.validator.validate_dataframe(dataframe)

        except ValueError as error:
            return [
                {"row": index + 2, "message": str(error)}
                for index in range(len(dataframe))
            ]

    # ==========================================================
    # Preview
    # ==========================================================

    def preview(self, filename):
        dataframe = self._load_and_clean(filename)

        errors = self.validate_data(dataframe)

        result = CNCImportResult(
            total=len(dataframe),
            valid=len(dataframe) - len(errors),
            invalid=len(errors),
            errors=errors,
        )

        return {
            "result": result,
            "errors": errors,
            "dataframe": dataframe,
        }

    # ==========================================================
    # Save
    # ==========================================================

    def save(self, dataframe, source_file=None):
        """
        Lưu các dòng vào CNCProductionLog qua CNCProductionLogService.

        Import cục bộ để tránh phụ thuộc vòng (importer <-> service)
        khi module này được nạp trước khi DB sẵn sàng.
        """
        from src.services.cnc_production_log_service import (
            CNCProductionLogService,
        )

        if dataframe is None or dataframe.empty:
            return 0

        service = CNCProductionLogService()

        created = 0

        try:
            for _, row in dataframe.iterrows():
                data = self._row_to_log_data(row)

                service.create_log_from_import(
                    data,
                    source_file=source_file,
                )

                created += 1

        finally:
            service.close()

        return created

    @staticmethod
    def _row_to_log_data(row):
        def value(column):
            result = row.get(column)

            try:
                if pd.isna(result):
                    return None
            except (TypeError, ValueError):
                pass

            return result

        log_date = value("Ngày")

        if hasattr(log_date, "date"):
            log_date = log_date.date()

        return {
            "log_date": log_date,
            "machine_name": value("Tên thiết bị"),
            "work_order_no": value("Mã công lệnh"),
            "product_name": value("Tên sản phẩm"),
            "operator_name": value("Nhân viên thao tác"),
            "operation": value("OP"),
            "shift": value("Ca"),
            "actual_time_hours": value("Thời gian thực tế (H)"),
            "qty_ok": value("Số lượng OK"),
            "qty_ok_plus_ng": value(
                "Số lượng OK+Số lượng gia công NG"
            ),
            "total_ng": value("Tổng NG"),
            "raw_ng": value("Phôi NG"),
            "process_ng": value("Gia công NG"),
            "actual_pcs": value("Thực tế PCS"),
            "standard_pcs": value("Tiêu chuẩn sản lượng PCS"),
            "diff_pcs": value("Chênh lệch PCS"),
        }

    # ==========================================================
    # Import
    # ==========================================================

    def import_file(self, filename):
        dataframe = self._load_and_clean(filename)

        errors = self.validate_data(dataframe)

        invalid_rows = {
            error["row"] - 2
            for error in errors
            if isinstance(error.get("row"), int)
        }

        valid_dataframe = dataframe.drop(
            index=[
                index
                for index in dataframe.index
                if index in invalid_rows
            ]
        )

        created = self.save(
            valid_dataframe,
            source_file=Path(filename).name,
        )

        return CNCImportResult(
            total=len(dataframe),
            valid=len(dataframe) - len(errors),
            invalid=len(errors),
            created=created,
            updated=0,
            skipped=0,
            errors=errors,
        )

    # ==========================================================
    # Information
    # ==========================================================

    @staticmethod
    def get_preview_info(dataframe):

        return {

            "rows": len(dataframe),

            "columns": len(dataframe.columns),

            "column_names": list(dataframe.columns),

            "memory_mb": round(
                dataframe.memory_usage(deep=True).sum()
                / 1024
                / 1024,
                2
            ),

        }

    # ==========================================================
    # Statistics
    # ==========================================================

    @staticmethod
    def get_statistics(dataframe):

        statistics = {

            "rows": len(dataframe),

            "columns": len(dataframe.columns),

            "empty_rows": int(
                dataframe.isna().all(axis=1).sum()
            ),

            "empty_columns": int(
                dataframe.isna().all().sum()
            ),

        }

        return statistics
