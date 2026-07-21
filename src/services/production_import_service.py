from pathlib import Path

from src.engine.production_engine import ProductionEngine
from src.importer.cnc_importer import CNCImporter
from src.importer.import_result import ImportResult
from src.mapper.production_mapper import ProductionMapper
from src.services.import_log_service import ImportLogService
from src.utils.file_hash import sha256_file


class ProductionImportService:
    """
    Pipeline nhập dữ liệu sản xuất CNC:

    File
        -> kiểm tra hash
        -> CNCImporter
        -> DataCleaner
        -> DataValidator
        -> ProductionMapper
        -> ProductionEngine
        -> ProductionLog
        -> ImportLog
    """

    def __init__(self):
        self.cnc_importer = CNCImporter()
        self.mapper = ProductionMapper()
        self.production_engine = ProductionEngine()
        self.import_log_service = ImportLogService()

    def preview_cnc(self, filename):
        """
        Đọc, làm sạch, validate và mapping dữ liệu.

        Hàm này chưa ghi dữ liệu sản xuất vào database.
        """
        self._validate_file(filename)

        file_hash = sha256_file(filename)
        existing_log = self.import_log_service.get_by_hash(file_hash)

        dataframe = self.cnc_importer.preview(filename)
        records, mapping_errors = self.mapper.map_dataframe(dataframe)

        return {
            "filename": filename,
            "file_hash": file_hash,
            "already_imported": existing_log is not None,
            "existing_import_log": existing_log,
            "dataframe": dataframe,
            "records": records,
            "errors": mapping_errors,
            "rows": len(dataframe),
            "mapped": len(records),
            "failed": len(mapping_errors),
        }

    def import_cnc(self, filename):
        """
        Nhập dữ liệu CNC thật vào ProductionLog.

        Quy tắc:
        - File đã import thì dừng ngay.
        - Một dòng lỗi không làm dừng toàn bộ file.
        - Chỉ tạo ImportLog khi toàn bộ file không có lỗi.
        """
        self._validate_file(filename)

        file_hash = sha256_file(filename)
        existing_log = self.import_log_service.get_by_hash(file_hash)

        if existing_log is not None:
            imported_at = getattr(existing_log, "imported_at", None)
            imported_at_text = (
                imported_at.strftime("%Y-%m-%d %H:%M:%S")
                if imported_at
                else "Unknown"
            )

            raise ValueError(
                "This file has already been imported.\n\n"
                f"File: {existing_log.file_name}\n"
                f"Imported at: {imported_at_text}\n"
                f"Total rows: {existing_log.total_rows}\n"
                f"Success rows: {existing_log.success_rows}\n"
                f"Failed rows: {existing_log.failed_rows}"
            )

        result = ImportResult()

        try:
            dataframe = self.cnc_importer.preview(filename)

        except Exception as error:
            result.add_error(0, str(error))
            result.finish(0)
            return result

        records, mapping_errors = self.mapper.map_dataframe(dataframe)

        for error in mapping_errors:
            result.add_error(
                error["row"],
                error["message"],
            )

        # map_dataframe chỉ trả các record mapping thành công.
        # Vì vậy cần giữ đúng số dòng Excel gốc tương ứng.
        record_index = 0

        for dataframe_index, row in dataframe.iterrows():
            excel_row = dataframe_index + 2

            row_has_mapping_error = any(
                error["row"] == excel_row
                for error in mapping_errors
            )

            if row_has_mapping_error:
                continue

            if record_index >= len(records):
                result.add_error(
                    excel_row,
                    "Mapped production record was not found.",
                )
                continue

            record = records[record_index]
            record_index += 1

            try:
                self.production_engine.process_log(record)
                result.add_success()

            except Exception as error:
                result.add_error(
                    excel_row,
                    str(error),
                )

        result.finish(len(dataframe))

        # Chỉ đánh dấu file đã import khi không có bất kỳ lỗi nào.
        if result.failed == 0:
            self.import_log_service.create(
                file_name=Path(filename).name,
                file_hash=file_hash,
                import_type="CNC",
                total=result.total,
                success=result.success,
                failed=result.failed,
                imported_by="System",
                remark="Imported by ProductionImportService",
            )

        return result

    def check_duplicate(self, filename):
        """
        Kiểm tra file đã được import hay chưa mà không đọc Excel.
        """
        self._validate_file(filename)

        file_hash = sha256_file(filename)
        existing_log = self.import_log_service.get_by_hash(file_hash)

        return {
            "is_duplicate": existing_log is not None,
            "file_hash": file_hash,
            "import_log": existing_log,
        }

    @staticmethod
    def _validate_file(filename):
        if not filename:
            raise ValueError("File path is required.")

        path = Path(filename)

        if not path.exists():
            raise FileNotFoundError(
                f"File not found:\n{filename}"
            )

        if not path.is_file():
            raise ValueError(
                f"Path is not a file:\n{filename}"
            )