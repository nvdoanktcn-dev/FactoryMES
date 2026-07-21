from __future__ import annotations

from PySide6.QtWidgets import QDialog, QMessageBox

from src.models.production_order import ProductionOrder
from src.services.production_assignment_service import (
    ProductionAssignmentService,
)
from src.ui.dialogs.production_assignment_dialog import (
    ProductionAssignmentDialog,
)
from src.ui.dialogs.production_assignment_history_dialog import (
    ProductionAssignmentHistoryDialog,
)


class ProductionAssignmentController:
    def __init__(self, page, service=None):
        self.page = page
        self.service = service or ProductionAssignmentService()

    def load_assignments(self):
        try:
            assignments = self.service.get_all_assignments()
            keyword = self.page.search_box.text().strip().lower()
            status = self.page.status_filter.currentText().strip().upper()
            rows = []

            for assignment in assignments:
                production_order = (
                    self.service.session.query(ProductionOrder)
                    .filter(
                        ProductionOrder.id == assignment.production_order_id
                    )
                    .first()
                )

                searchable = " ".join(
                    [
                        str(assignment.id or ""),
                        str(assignment.machine_code or ""),
                        str(assignment.employee_code or ""),
                        str(assignment.shift or ""),
                        str(assignment.status or ""),
                        str(
                            production_order.work_order_no
                            if production_order
                            else ""
                        ),
                        str(
                            production_order.operation_no
                            if production_order
                            else ""
                        ),
                    ]
                ).lower()

                if keyword and keyword not in searchable:
                    continue

                if (
                    status != "ALL"
                    and str(assignment.status or "").upper() != status
                ):
                    continue

                rows.append((assignment, production_order))

            rows.sort(
                key=lambda item: (
                    item[0].planned_start or item[0].created_at,
                    item[0].id,
                )
            )

            self.page.set_assignments(rows)
            self.page.set_status_message(f"{len(rows)} assignment(s).")
            return rows

        except Exception as error:
            self.page.show_error(error)
            return []

    def add_assignment(self):
        dialog = ProductionAssignmentDialog(
            parent=self.page,
            session=self.service.session,
        )

        if dialog.exec() != QDialog.Accepted:
            return None

        try:
            assignment = self.service.create_assignment(dialog.get_data())
            self.service.commit()
            self.load_assignments()
            return assignment
        except Exception as error:
            self.service.rollback()
            self.page.show_error(error)
            return None

    def edit_selected(self):
        assignment = self.page.selected_assignment()

        if assignment is None:
            QMessageBox.warning(
                self.page,
                "Production Assignment",
                "Please select one assignment.",
            )
            return None

        dialog = ProductionAssignmentDialog(
            parent=self.page,
            assignment=assignment,
            session=self.service.session,
        )

        if dialog.exec() != QDialog.Accepted:
            return None

        try:
            updated = self.service.update_assignment(
                assignment.id,
                dialog.get_data(),
            )
            self.service.commit()
            self.load_assignments()
            return updated
        except Exception as error:
            self.service.rollback()
            self.page.show_error(error)
            return None

    def release_selected(self):
        return self._run_action("Release", self.service.release)

    def start_selected(self):
        return self._run_action("Start", self.service.start)

    def hold_selected(self):
        return self._run_action("Hold", self.service.hold)

    def complete_selected(self):
        return self._run_action("Complete", self.service.complete)

    def cancel_selected(self):
        return self._run_action(
            "Cancel",
            self.service.cancel,
            confirm=True,
        )

    def _run_action(self, action_name, method, confirm=False):
        assignment = self.page.selected_assignment()

        if assignment is None:
            QMessageBox.warning(
                self.page,
                "Production Assignment",
                "Please select one assignment.",
            )
            return None

        if confirm:
            answer = QMessageBox.question(
                self.page,
                action_name,
                f"{action_name} Assignment #{assignment.id}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if answer != QMessageBox.Yes:
                return None

        try:
            result = method(assignment.id)
            self.service.commit()
            self.load_assignments()
            return result
        except Exception as error:
            self.service.rollback()
            self.page.show_error(error)
            return None

    def close(self):
        self.service.close()

    def show_selected_history(self):
        assignment = (
            self.page
            .selected_assignment()
        )

        if assignment is None:
            QMessageBox.warning(
                self.page,
                "Production Assignment",
                "Please select one assignment.",
            )
            return None

        dialog = ProductionAssignmentHistoryDialog(
            parent=self.page,
            assignment=assignment,
            session=self.service.session,
        )

        dialog.exec()

        return dialog


