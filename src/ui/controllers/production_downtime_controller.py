from __future__ import annotations

from PySide6.QtWidgets import QDialog, QMessageBox

from src.models.production_assignment import ProductionAssignment
from src.models.production_execution import ProductionExecution
from src.models.production_order import ProductionOrder
from src.services.production_downtime_service import ProductionDowntimeService
from src.ui.dialogs.production_downtime_dialog import ProductionDowntimeDialog


class ProductionDowntimeController:
    def __init__(self, page, service=None):
        self.page = page
        self.service = service or ProductionDowntimeService()

    def load_events(self):
        try:
            events = self.service.get_all_events()
            keyword = self.page.search_box.text().strip().lower()
            status_filter = self.page.status_filter.currentText().strip().upper()
            reason_filter = self.page.reason_filter.currentData()

            rows = []

            for event in events:
                execution = (
                    self.service.session.query(ProductionExecution)
                    .filter(ProductionExecution.id == event.execution_id)
                    .first()
                )

                assignment = None
                production_order = None

                if execution is not None:
                    assignment = (
                        self.service.session.query(ProductionAssignment)
                        .filter(ProductionAssignment.id == execution.assignment_id)
                        .first()
                    )

                if assignment is not None:
                    production_order = (
                        self.service.session.query(ProductionOrder)
                        .filter(ProductionOrder.id == assignment.production_order_id)
                        .first()
                    )

                searchable = " ".join(
                    [
                        str(event.id or ""),
                        str(event.execution_id or ""),
                        str(event.reason_code or ""),
                        str(event.reason_name or ""),
                        str(event.status or ""),
                        str(event.remark or ""),
                        str(assignment.machine_code if assignment else ""),
                        str(assignment.employee_code if assignment else ""),
                        str(assignment.shift if assignment else ""),
                        str(production_order.work_order_no if production_order else ""),
                        str(production_order.product_code if production_order else ""),
                        str(production_order.operation_no if production_order else ""),
                    ]
                ).lower()

                if keyword and keyword not in searchable:
                    continue

                if (
                    status_filter != "ALL"
                    and str(event.status or "").strip().upper() != status_filter
                ):
                    continue

                if (
                    reason_filter
                    and str(event.reason_code or "").strip().upper()
                    != str(reason_filter).strip().upper()
                ):
                    continue

                rows.append((event, execution, assignment, production_order))

            rows.sort(
                key=lambda item: (item[0].start_time, item[0].id),
                reverse=True,
            )

            self.page.set_events(rows)
            self.page.update_summary(events)
            self.page.set_status_message(
                f"{len(rows)} displayed / {len(events)} total."
            )
            return rows

        except Exception as error:
            self.page.show_error(error)
            return []

    def start_downtime(self):
        dialog = ProductionDowntimeDialog(
            parent=self.page,
            mode=ProductionDowntimeDialog.MODE_START,
            session=self.service.session,
        )

        if dialog.exec() != QDialog.Accepted:
            return None

        data = dialog.get_data()

        try:
            event = self.service.start_downtime(
                execution_id=data["execution_id"],
                reason_code=data["reason_code"],
                start_time=data["start_time"],
                remark=data["remark"],
            )
            self.service.commit()
            self.load_events()

            QMessageBox.information(
                self.page,
                "Production Downtime",
                (
                    "Downtime started successfully.\n\n"
                    f"Downtime ID: {event.id}\n"
                    f"Execution ID: {event.execution_id}\n"
                    f"Reason: {event.reason_name}"
                ),
            )
            return event

        except Exception as error:
            self.service.rollback()
            self.page.show_error(error)
            return None

    def stop_selected(self):
        event = self.page.selected_event()

        if event is None:
            QMessageBox.warning(
                self.page,
                "Production Downtime",
                "Please select one Downtime Event.",
            )
            return None

        if str(event.status or "").strip().upper() != "OPEN":
            QMessageBox.warning(
                self.page,
                "Production Downtime",
                "Only OPEN downtime event can be stopped.",
            )
            return None

        dialog = ProductionDowntimeDialog(
            parent=self.page,
            mode=ProductionDowntimeDialog.MODE_STOP,
            downtime_event=event,
            session=self.service.session,
        )

        if dialog.exec() != QDialog.Accepted:
            return None

        data = dialog.get_data()

        try:
            result = self.service.stop_downtime(
                event.id,
                end_time=data["end_time"],
                remark=data["remark"],
            )
            self.service.commit()
            self.load_events()

            QMessageBox.information(
                self.page,
                "Production Downtime",
                (
                    "Downtime stopped successfully.\n\n"
                    f"Downtime ID: {result.id}\n"
                    f"Duration: {result.duration_minutes:.2f} min"
                ),
            )
            return result

        except Exception as error:
            self.service.rollback()
            self.page.show_error(error)
            return None

    def cancel_selected(self):
        event = self.page.selected_event()

        if event is None:
            QMessageBox.warning(
                self.page,
                "Production Downtime",
                "Please select one Downtime Event.",
            )
            return None

        if str(event.status or "").strip().upper() != "OPEN":
            QMessageBox.warning(
                self.page,
                "Production Downtime",
                "Only OPEN downtime event can be cancelled.",
            )
            return None

        answer = QMessageBox.question(
            self.page,
            "Cancel Production Downtime",
            (
                "Cancel this Downtime Event?\n\n"
                f"Downtime ID: {event.id}\n"
                f"Reason: {event.reason_name}"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return None

        try:
            result = self.service.cancel_downtime(event.id)
            self.service.commit()
            self.load_events()
            return result

        except Exception as error:
            self.service.rollback()
            self.page.show_error(error)
            return None

    def refresh(self):
        return self.load_events()

    def close(self):
        self.service.close()
