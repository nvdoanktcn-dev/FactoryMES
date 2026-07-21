from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QMessageBox,
)

from src.models.production_assignment import (
    ProductionAssignment,
)
from src.models.production_execution import (
    ProductionExecution,
)
from src.models.production_order import (
    ProductionOrder,
)
from src.services.production_ng_service import (
    ProductionNGService,
)
from src.ui.dialogs.production_ng_dialog import (
    ProductionNGDialog,
)


class ProductionNGController:
    """
    Điều phối Production NG Page và Service.
    """

    def __init__(
        self,
        page,
        service=None,
    ):
        self.page = page
        self.service = (
            service
            or ProductionNGService()
        )

    # ==========================================================
    # Load
    # ==========================================================

    def load_records(self):
        try:
            records = (
                self.service
                .get_all_records()
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

            type_filter = (
                self.page.type_filter
                .currentData()
            )

            reason_filter = (
                self.page.reason_filter
                .currentData()
            )

            rows = []

            for record in records:
                execution = (
                    self.service.session
                    .query(ProductionExecution)
                    .filter(
                        ProductionExecution.id
                        == record.execution_id
                    )
                    .first()
                )

                assignment = None
                production_order = None

                if execution is not None:
                    assignment = (
                        self.service.session
                        .query(ProductionAssignment)
                        .filter(
                            ProductionAssignment.id
                            == execution.assignment_id
                        )
                        .first()
                    )

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
                        str(record.id or ""),
                        str(record.execution_id or ""),
                        str(record.ng_type or ""),
                        str(record.reason_code or ""),
                        str(record.reason_name or ""),
                        str(record.quantity or ""),
                        str(record.employee_code or ""),
                        str(record.status or ""),
                        str(record.remark or ""),
                        str(
                            assignment.machine_code
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
                        record.status or ""
                    ).strip().upper()
                    != status_filter
                ):
                    continue

                if (
                    type_filter
                    and str(
                        record.ng_type or ""
                    ).strip().upper()
                    != str(
                        type_filter
                    ).strip().upper()
                ):
                    continue

                if (
                    reason_filter
                    and str(
                        record.reason_code or ""
                    ).strip().upper()
                    != str(
                        reason_filter
                    ).strip().upper()
                ):
                    continue

                rows.append(
                    (
                        record,
                        execution,
                        assignment,
                        production_order,
                    )
                )

            rows.sort(
                key=lambda item: (
                    item[0].recorded_at,
                    item[0].id,
                ),
                reverse=True,
            )

            self.page.set_records(
                rows
            )

            self.page.update_summary(
                records
            )

            self.page.set_status_message(
                (
                    f"{len(rows)} displayed / "
                    f"{len(records)} total."
                )
            )

            return rows

        except Exception as error:
            self.page.show_error(
                error
            )
            return []

    # ==========================================================
    # Add
    # ==========================================================

    def add_record(self):
        dialog = ProductionNGDialog(
            parent=self.page,
            mode=ProductionNGDialog.MODE_ADD,
            session=self.service.session,
        )

        if dialog.exec() != QDialog.Accepted:
            return None

        data = dialog.get_data()

        try:
            record = self.service.record_ng(
                execution_id=data["execution_id"],
                ng_type=data["ng_type"],
                reason_code=data["reason_code"],
                quantity=data["quantity"],
                recorded_at=data["recorded_at"],
                employee_code=data["employee_code"],
                remark=data["remark"],
            )

            self.service.commit()
            self.load_records()

            QMessageBox.information(
                self.page,
                "Production NG",
                (
                    "NG record created successfully.\n\n"
                    f"NG ID: {record.id}\n"
                    f"Execution ID: {record.execution_id}\n"
                    f"Type: {record.ng_type}\n"
                    f"Reason: {record.reason_name}\n"
                    f"Quantity: {record.quantity}"
                ),
            )

            return record

        except Exception as error:
            self.service.rollback()
            self.page.show_error(
                error
            )
            return None

    # ==========================================================
    # Edit
    # ==========================================================

    def edit_selected(self):
        record = (
            self.page
            .selected_record()
        )

        if record is None:
            QMessageBox.warning(
                self.page,
                "Production NG",
                "Please select one NG record.",
            )
            return None

        if str(
            record.status or ""
        ).strip().upper() != "ACTIVE":
            QMessageBox.warning(
                self.page,
                "Production NG",
                (
                    "Only ACTIVE NG record "
                    "can be edited."
                ),
            )
            return None

        dialog = ProductionNGDialog(
            parent=self.page,
            mode=ProductionNGDialog.MODE_EDIT,
            ng_record=record,
            session=self.service.session,
        )

        if dialog.exec() != QDialog.Accepted:
            return None

        data = dialog.get_data()

        try:
            updated = self.service.update_ng(
                record.id,
                ng_type=data["ng_type"],
                reason_code=data["reason_code"],
                quantity=data["quantity"],
                recorded_at=data["recorded_at"],
                employee_code=data["employee_code"],
                remark=data["remark"],
            )

            self.service.commit()
            self.load_records()

            QMessageBox.information(
                self.page,
                "Production NG",
                (
                    "NG record updated successfully.\n\n"
                    f"NG ID: {updated.id}\n"
                    f"Quantity: {updated.quantity}"
                ),
            )

            return updated

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
        record = (
            self.page
            .selected_record()
        )

        if record is None:
            QMessageBox.warning(
                self.page,
                "Production NG",
                "Please select one NG record.",
            )
            return None

        if str(
            record.status or ""
        ).strip().upper() != "ACTIVE":
            QMessageBox.warning(
                self.page,
                "Production NG",
                (
                    "Only ACTIVE NG record "
                    "can be cancelled."
                ),
            )
            return None

        answer = QMessageBox.question(
            self.page,
            "Cancel Production NG",
            (
                "Cancel this NG record?\n\n"
                f"NG ID: {record.id}\n"
                f"Type: {record.ng_type}\n"
                f"Reason: {record.reason_name}\n"
                f"Quantity: {record.quantity}"
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
                .cancel_ng(
                    record.id
                )
            )

            self.service.commit()
            self.load_records()

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
        return self.load_records()

    def close(self):
        self.service.close()
