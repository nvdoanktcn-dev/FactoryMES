from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QMessageBox,
)

from src.models.production_assignment import (
    ProductionAssignment,
)
from src.models.production_order import (
    ProductionOrder,
)
from src.services.production_execution_service import (
    ProductionExecutionService,
)
from src.ui.dialogs.production_execution_dialog import (
    ProductionExecutionDialog,
)


class ProductionExecutionController:
    """
    Điều phối Production Execution Page và Service.
    """

    def __init__(
        self,
        page,
        service=None,
    ):
        self.page = page
        self.service = (
            service
            or ProductionExecutionService()
        )

    # ==========================================================
    # Load
    # ==========================================================

    def load_executions(self):
        try:
            executions = (
                self.service
                .get_all_executions()
            )

            keyword = (
                self.page.search_box
                .text()
                .strip()
                .lower()
            )

            status_filter = (
                self.page.status_filter
                .currentText()
                .strip()
                .upper()
            )

            rows = []

            for execution in executions:
                assignment = (
                    self.service.session
                    .query(ProductionAssignment)
                    .filter(
                        ProductionAssignment.id
                        == execution.assignment_id
                    )
                    .first()
                )

                production_order = None

                if assignment is not None:
                    production_order = (
                        self.service.session
                        .query(ProductionOrder)
                        .filter(
                            ProductionOrder.id
                            == assignment.production_order_id
                        )
                        .first()
                    )

                searchable = " ".join(
                    [
                        str(
                            execution.id
                            or ""
                        ),
                        str(
                            execution.assignment_id
                            or ""
                        ),
                        str(
                            execution.status
                            or ""
                        ),
                        str(
                            assignment.machine_code
                            if assignment
                            else ""
                        ),
                        str(
                            assignment.employee_code
                            if assignment
                            else ""
                        ),
                        str(
                            assignment.shift
                            if assignment
                            else ""
                        ),
                        str(
                            production_order.work_order_no
                            if production_order
                            else ""
                        ),
                        str(
                            production_order.product_code
                            if production_order
                            else ""
                        ),
                        str(
                            production_order.operation_no
                            if production_order
                            else ""
                        ),
                        str(
                            production_order.operation_name
                            if production_order
                            else ""
                        ),
                    ]
                ).lower()

                if (
                    keyword
                    and keyword not in searchable
                ):
                    continue

                if (
                    status_filter != "ALL"
                    and str(
                        execution.status
                        or ""
                    ).upper()
                    != status_filter
                ):
                    continue

                rows.append(
                    (
                        execution,
                        assignment,
                        production_order,
                    )
                )

            rows.sort(
                key=lambda item: (
                    item[0].start_time,
                    item[0].id,
                ),
                reverse=True,
            )

            self.page.set_executions(
                rows
            )

            self.page.update_summary(
                executions
            )

            self.page.set_status_message(
                (
                    f"{len(rows)} displayed / "
                    f"{len(executions)} total."
                )
            )

            return rows

        except Exception as error:
            self.page.show_error(
                error
            )
            return []

    # ==========================================================
    # Start
    # ==========================================================

    def start_execution(self):
        dialog = ProductionExecutionDialog(
            parent=self.page,
            mode=(
                ProductionExecutionDialog
                .MODE_START
            ),
            session=self.service.session,
        )

        if dialog.exec() != QDialog.Accepted:
            return None

        data = dialog.get_data()

        try:
            execution = (
                self.service
                .start_execution(
                    assignment_id=data[
                        "assignment_id"
                    ],
                    start_time=data[
                        "start_time"
                    ],
                    remark=data[
                        "remark"
                    ],
                )
            )

            self.service.commit()
            self.load_executions()

            QMessageBox.information(
                self.page,
                "Production Execution",
                (
                    "Execution started successfully.\n\n"
                    f"Execution ID: {execution.id}\n"
                    f"Assignment ID: "
                    f"{execution.assignment_id}"
                ),
            )

            return execution

        except Exception as error:
            self.service.rollback()
            self.page.show_error(
                error
            )
            return None

    # ==========================================================
    # Stop / Complete
    # ==========================================================

    def stop_selected(self):
        return self._finish_selected(
            mode=(
                ProductionExecutionDialog
                .MODE_STOP
            )
        )

    def complete_selected(self):
        return self._finish_selected(
            mode=(
                ProductionExecutionDialog
                .MODE_COMPLETE
            )
        )

    def _finish_selected(
        self,
        *,
        mode,
    ):
        execution = (
            self.page
            .selected_execution()
        )

        if execution is None:
            QMessageBox.warning(
                self.page,
                "Production Execution",
                "Please select one Execution.",
            )
            return None

        if str(
            execution.status
            or ""
        ).strip().upper() != "RUNNING":
            QMessageBox.warning(
                self.page,
                "Production Execution",
                (
                    "Only RUNNING execution "
                    "can be stopped or completed."
                ),
            )
            return None

        dialog = ProductionExecutionDialog(
            parent=self.page,
            mode=mode,
            execution=execution,
            session=self.service.session,
        )

        if dialog.exec() != QDialog.Accepted:
            return None

        data = dialog.get_data()

        try:
            result = (
                self.service
                .stop_execution(
                    execution.id,
                    ok_qty=data[
                        "ok_qty"
                    ],
                    ng_qty=data[
                        "ng_qty"
                    ],
                    processing_ng_qty=data[
                        "processing_ng_qty"
                    ],
                    blank_ng_qty=data[
                        "blank_ng_qty"
                    ],
                    downtime_minutes=data[
                        "downtime_minutes"
                    ],
                    end_time=data[
                        "end_time"
                    ],
                    complete=data[
                        "complete"
                    ],
                    remark=data[
                        "remark"
                    ],
                )
            )

            self.service.commit()
            self.load_executions()

            action_text = (
                "completed"
                if data["complete"]
                else "stopped"
            )

            QMessageBox.information(
                self.page,
                "Production Execution",
                (
                    f"Execution {action_text} successfully.\n\n"
                    f"Execution ID: {result.id}\n"
                    f"Runtime: "
                    f"{result.runtime_minutes:.2f} min\n"
                    f"Downtime: "
                    f"{result.downtime_minutes:.2f} min\n"
                    f"OK: {result.ok_qty}\n"
                    f"NG: {result.ng_qty}"
                ),
            )

            return result

        except Exception as error:
            self.service.rollback()
            self.page.show_error(
                error
            )
            return None

    # ==========================================================
    # Cancel
    # ==========================================================

    def cancel_selected(self):
        execution = (
            self.page
            .selected_execution()
        )

        if execution is None:
            QMessageBox.warning(
                self.page,
                "Production Execution",
                "Please select one Execution.",
            )
            return None

        answer = QMessageBox.question(
            self.page,
            "Cancel Production Execution",
            (
                "Cancel this Production Execution?\n\n"
                f"Execution ID: {execution.id}"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return None

        try:
            result = (
                self.service
                .cancel_execution(
                    execution.id
                )
            )

            self.service.commit()
            self.load_executions()

            return result

        except Exception as error:
            self.service.rollback()
            self.page.show_error(
                error
            )
            return None

    # ==========================================================
    # Refresh / Close
    # ==========================================================

    def refresh(self):
        return self.load_executions()

    def close(self):
        self.service.close()
