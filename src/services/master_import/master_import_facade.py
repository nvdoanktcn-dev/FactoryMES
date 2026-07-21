from __future__ import annotations

import time

import pandas as pd

from src.database.session import get_session
from src.services.master_import.excel_reader import ExcelReaderService
from src.services.master_import.import_engine import ImportContext
from src.services.master_import.import_log_service import ImportLogService
from src.services.master_import.master_import_response import MasterImportResponse
from src.services.master_import.rollback_service import RollbackService
from src.services.master_import.runtime import (
    build_employee_import_engine,
    build_machine_import_engine,
    build_product_import_engine,
    build_routing_import_engine,
    build_work_order_import_engine,
)
from src.services.master_import.schema import SchemaRegistry
from src.services.master_import.validation import ValidationService


class MasterImportFacade:
    """Facade điều phối Preview, Validation, Import, History và Rollback."""

    ENGINE_BUILDERS = {
        "PRODUCT": build_product_import_engine,
        "MACHINE": build_machine_import_engine,
        "EMPLOYEE": build_employee_import_engine,
        "ROUTING": build_routing_import_engine,
        "WORK_ORDER": build_work_order_import_engine,
    }

    def __init__(
        self,
        excel_reader=None,
        import_log_service=None,
        rollback_service=None,
    ):
        self.reader = excel_reader or ExcelReaderService()
        self.import_log_service = (
            import_log_service or ImportLogService()
        )
        self.rollback_service = (
            rollback_service or RollbackService()
        )

    def preview(self, request):
        start = time.perf_counter()

        result = self.reader.preview(
            file_path=request.file_path,
            sheet_name=request.sheet_name,
        )

        duration = time.perf_counter() - start

        return MasterImportResponse(
            success=True,
            message=(
                f"Preview loaded: {result.total_rows} row(s), "
                f"{len(result.headers)} column(s)."
            ),
            preview_rows=result.rows,
            sheet_names=result.sheet_names,
            headers=result.headers,
            total_rows=result.total_rows,
            header_row=result.header_row,
            duration=duration,
        )

    def validate(self, request):
        start = time.perf_counter()

        preview_result = self.reader.preview(
            file_path=request.file_path,
            sheet_name=request.sheet_name,
            limit=2_147_483_647,
        )

        dataframe = pd.DataFrame(
            preview_result.rows,
            columns=preview_result.headers,
        )

        schema = SchemaRegistry.get(
            request.module_name
        )

        validation_result = ValidationService(
            schema=schema
        ).validate(dataframe)

        errors = [
            self._validation_error_to_dict(error)
            for error in validation_result.errors
        ]
        warnings = [
            self._validation_error_to_dict(warning)
            for warning in validation_result.warnings
        ]

        duration = time.perf_counter() - start

        if errors:
            message = (
                f"Validation failed: {len(errors)} error(s), "
                f"{len(warnings)} warning(s)."
            )
        else:
            message = (
                f"Validation passed: {preview_result.total_rows} "
                "row(s) checked."
            )

        return MasterImportResponse(
            success=not errors,
            message=message,
            preview_rows=preview_result.rows,
            validation_errors=errors,
            validation_warnings=warnings,
            sheet_names=preview_result.sheet_names,
            headers=preview_result.headers,
            total_rows=preview_result.total_rows,
            header_row=preview_result.header_row,
            duration=duration,
        )

    def import_data(self, request):
        validation_response = self.validate(request)

        if validation_response is None:
            raise RuntimeError(
                "MasterImportFacade.validate() returned None."
            )

        if not validation_response.success:
            validation_response.message = (
                "Import blocked because validation failed."
            )
            return validation_response

        module_name = self._normalize_module_name(
            request.module_name
        )

        engine_builder = self.ENGINE_BUILDERS.get(
            module_name
        )

        if engine_builder is None:
            validation_response.success = False
            validation_response.message = (
                f"Unsupported import module: {module_name}"
            )
            return validation_response

        dataframe = pd.DataFrame(
            validation_response.preview_rows,
            columns=validation_response.headers,
        )

        if dataframe.empty:
            validation_response.success = False
            validation_response.message = (
                "Import blocked because the Excel sheet is empty."
            )
            return validation_response

        pending_log = self.import_log_service.create_log(
            module=module_name,
            file_path=request.file_path,
            sheet_name=request.sheet_name,
            user_name="FactoryMES User",
            total_rows=len(dataframe),
            inserted_rows=0,
            updated_rows=0,
            failed_rows=0,
            duration=0.0,
            status="PENDING",
            message="Import is running.",
        )

        import_log_id = pending_log.id
        session = get_session()

        try:
            engine = engine_builder(
                session=session
            )

            context = ImportContext(
                module_name=module_name,
                dataframe=dataframe,
                user="FactoryMES User",
                validate_only=False,
                dry_run=False,
                metadata={
                    "file_path": request.file_path,
                    "sheet_name": request.sheet_name,
                    "import_log_id": import_log_id,
                },
            )

            import_result = engine.execute(context)

            validation_response.success = import_result.success
            validation_response.imported_rows = (
                import_result.inserted_rows
                + import_result.updated_rows
            )
            validation_response.failed_rows = (
                import_result.failed_rows
            )
            validation_response.duration = (
                import_result.duration
            )
            validation_response.message = (
                f"{module_name} import completed: "
                f"{import_result.inserted_rows} inserted, "
                f"{import_result.updated_rows} updated, "
                f"{import_result.failed_rows} failed."
            )

            self.import_log_service.update_log(
                import_log_id,
                total_rows=import_result.total_rows,
                inserted_rows=import_result.inserted_rows,
                updated_rows=import_result.updated_rows,
                failed_rows=import_result.failed_rows,
                duration=import_result.duration,
                status=(
                    "SUCCESS"
                    if import_result.success
                    else "FAILED"
                ),
                message=validation_response.message,
            )

            return validation_response

        except Exception as error:
            validation_response.success = False
            validation_response.imported_rows = 0
            validation_response.failed_rows = len(dataframe)
            validation_response.message = (
                f"{module_name} import failed: {error}"
            )

            try:
                self.import_log_service.update_log(
                    import_log_id,
                    total_rows=len(dataframe),
                    inserted_rows=0,
                    updated_rows=0,
                    failed_rows=len(dataframe),
                    duration=validation_response.duration,
                    status="FAILED",
                    message=str(error),
                )
            except Exception:
                pass

            return validation_response

        finally:
            session.close()

    def rollback(self, log_id):
        try:
            result = self.rollback_service.rollback_import(
                log_id
            )

            return MasterImportResponse(
                success=True,
                message=result.get(
                    "message",
                    "Rollback completed.",
                ),
                imported_rows=0,
                failed_rows=0,
            )

        except Exception as error:
            return MasterImportResponse(
                success=False,
                message=f"Rollback failed: {error}",
                imported_rows=0,
                failed_rows=0,
            )

    def history(self):
        records = self.import_log_service.get_recent(
            limit=100
        )
        return self.import_log_service.to_history_rows(
            records
        )

    @staticmethod
    def _normalize_module_name(value):
        return str(value or "").strip().upper()

    @staticmethod
    def _validation_error_to_dict(error):
        return {
            "row": error.row,
            "field": error.column,
            "code": error.code,
            "message": error.message,
            "severity": error.severity,
            "value": error.value,
            "validator": error.validator,
        }
