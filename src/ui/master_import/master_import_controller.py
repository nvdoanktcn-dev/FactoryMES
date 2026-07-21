from PySide6.QtWidgets import QMessageBox

from src.services.master_import import (
    MasterImportFacade,
    MasterImportRequest,
)


class MasterImportController:
    def __init__(self, page, facade=None):
        self.page = page
        self.facade = facade or MasterImportFacade()
        self.current_file = ""
        self.last_response = None
        self._connect_history_events()

    def create_request(
        self,
        validate_only=False,
        ignore_current_sheet=False,
    ):
        sheet_name = None

        if not ignore_current_sheet:
            sheet_name = (
                self.page.toolbar.sheet_name()
                or None
            )

        return MasterImportRequest(
            module_name=self.page.toolbar.module_name(),
            file_path=self.page.toolbar.file_path(),
            sheet_name=sheet_name,
            validate_only=validate_only,
        )

    def preview(self):
        request = self.create_request(
            ignore_current_sheet=True
        )

        response = self.facade.preview(request)
        self.last_response = response

        selected_sheet = (
            getattr(
                response,
                "selected_sheet",
                None,
            )
            or (
                response.sheet_names[0]
                if response.sheet_names
                else None
            )
        )

        self.page.toolbar.set_sheet_names(
            sheet_names=response.sheet_names,
            selected_sheet=selected_sheet,
        )

        self.page.preview_table.set_preview_rows(
            response.preview_rows
        )

        self.page.toolbar.update_preview_info(
            total_rows=response.total_rows,
            total_columns=len(response.headers),
            header_row=response.header_row,
            duration=response.duration,
        )

        self.page.progress_panel.set_status(
            response.message
        )

        return response

    def validate(self):
        request = self.create_request(
            validate_only=True
        )

        response = self.facade.validate(request)
        self.last_response = response

        self.page.preview_table.set_preview_rows(
            response.preview_rows
        )
        self.page.validation_panel.set_errors(
            response.validation_errors
        )
        self.page.toolbar.set_validation_state(
            response.success
            and not response.validation_errors
        )

        selected_sheet = (
            request.sheet_name
            if request.sheet_name
            in (response.sheet_names or [])
            else (
                response.sheet_names[0]
                if response.sheet_names
                else None
            )
        )

        self.page.toolbar.set_sheet_names(
            sheet_names=response.sheet_names,
            selected_sheet=selected_sheet,
        )

        self.page.toolbar.update_preview_info(
            total_rows=response.total_rows,
            total_columns=len(response.headers),
            header_row=response.header_row,
            duration=response.duration,
        )

        self.page.progress_panel.set_status(
            response.message
        )
        self.page.progress_panel.set_progress(
            100 if response.success else 0
        )

        return response

    def import_data(self):
        request = self.create_request()

        self.page.toolbar.set_loading(True)
        self.page.progress_panel.set_status(
            "Importing data..."
        )
        self.page.progress_panel.set_progress(10)

        try:
            response = self.facade.import_data(request)

            if response is None:
                raise RuntimeError(
                    "MasterImportFacade.import_data() returned None."
                )

            self.last_response = response
            self.page.validation_panel.set_errors(
                response.validation_errors
            )

            if response.success:
                self.page.progress_panel.set_progress(
                    100
                )
                self.page.toolbar.set_rollback_enabled(
                    True
                )
                self.page.toolbar.set_validation_state(
                    False
                )
            else:
                self.page.progress_panel.set_progress(
                    0
                )
                self.page.toolbar.set_rollback_enabled(
                    False
                )

            self.page.progress_panel.set_status(
                response.message
            )
            self.load_history()

            return response

        finally:
            self.page.toolbar.set_loading(False)

    def rollback(self):
        log_id = (
            self.page.history_panel.selected_log_id()
        )

        if log_id is None:
            QMessageBox.warning(
                self.page,
                "Rollback",
                (
                    "Please select one import history "
                    "record before rollback."
                ),
            )
            return None

        selected_record = (
            self.page.history_panel.selected_history()
        )

        status = ""

        if isinstance(selected_record, dict):
            status = str(
                selected_record.get("status", "")
            ).strip().upper()

        if status == "ROLLED_BACK":
            QMessageBox.information(
                self.page,
                "Rollback",
                "This import has already been rolled back.",
            )
            self.page.toolbar.set_rollback_enabled(
                False
            )
            return None

        if status and status != "SUCCESS":
            QMessageBox.warning(
                self.page,
                "Rollback",
                (
                    "Only a SUCCESS import can be "
                    "rolled back.\n\n"
                    f"Current status: {status}"
                ),
            )
            return None

        answer = QMessageBox.question(
            self.page,
            "Confirm Rollback",
            (
                "Rollback the selected import?\n\n"
                f"Import Log ID: {log_id}\n\n"
                "Inserted records will be deleted.\n"
                "Updated records will be restored."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return None

        self.page.toolbar.set_loading(True)
        self.page.progress_panel.set_status(
            f"Rolling back Import Log #{log_id}..."
        )
        self.page.progress_panel.set_progress(20)

        try:
            response = self.facade.rollback(log_id)
            self.last_response = response

            if response.success:
                self.page.progress_panel.set_progress(
                    100
                )
                QMessageBox.information(
                    self.page,
                    "Rollback",
                    response.message,
                )
            else:
                self.page.progress_panel.set_progress(
                    0
                )
                QMessageBox.critical(
                    self.page,
                    "Rollback Failed",
                    response.message,
                )

            self.page.progress_panel.set_status(
                response.message
            )
            self.page.toolbar.set_rollback_enabled(
                False
            )
            self.load_history()

            return response

        finally:
            self.page.toolbar.set_loading(False)

    def load_history(self):
        records = self.facade.history()
        self.page.history_panel.set_history(records)
        self.page.toolbar.set_rollback_enabled(False)
        return records

    def _connect_history_events(self):
        table = self.page.history_panel.table
        table.itemSelectionChanged.connect(
            self._update_rollback_state
        )

    def _update_rollback_state(self):
        record = (
            self.page.history_panel.selected_history()
        )
        enabled = False

        if isinstance(record, dict):
            status = str(
                record.get("status", "")
            ).strip().upper()
            log_id = record.get("id")
            enabled = (
                log_id is not None
                and status == "SUCCESS"
            )

        self.page.toolbar.set_rollback_enabled(
            enabled
        )
