from pathlib import Path

import pandas as pd

from src.importer.base_importer import BaseImporter
from src.importer.data_cleaner import DataCleaner
from src.importer.data_validator import DataValidator
from src.importer.import_result import ImportResult


class CNCImporter(BaseImporter):
    """
    CNC Excel Importer

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
        Production Engine (Next Sprint)
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

        result = ImportResult()

        dataframe_errors = self.validator.validate_dataframe(
            dataframe
        )

        if dataframe_errors:

            for error in dataframe_errors:

                result.add_error(
                    error["row"],
                    error["message"]
                )

            result.finish(len(dataframe))

            return result

        for index, row in dataframe.iterrows():

            try:

                if self.validator.validate(row):

                    result.add_success()

                else:

                    result.add_error(
                        index + 2,
                        "Validation failed."
                    )

            except Exception as error:

                result.add_error(
                    index + 2,
                    str(error)
                )

        result.finish(len(dataframe))

        return result

    # ==========================================================
    # Preview
    # ==========================================================

    def preview(self, filename):

        dataframe = self._load_and_clean(filename)

        errors = self.validator.validate_dataframe(
            dataframe
        )

        if errors:

            details = "\n".join(
                f"Row {error['row']}: {error['message']}"
                for error in errors
            )

            raise ValueError(
                f"Found {len(errors)} error(s):\n\n{details}"
            )

        return dataframe

    # ==========================================================
    # Save
    # ==========================================================

    def save(self, dataframe):
        """
        Sprint hiện tại chưa ghi Database.

        Sprint tiếp theo:

            dataframe
                │
                ▼
        ProductionEngine.process_log()
        """

        return True

    # ==========================================================
    # Import
    # ==========================================================

    def import_file(self, filename):

        dataframe = self._load_and_clean(filename)

        result = self.validate_data(
            dataframe
        )

        if result.failed == 0:

            self.save(dataframe)

        return result

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