from __future__ import annotations

from PySide6.QtWidgets import (
    QInputDialog,
    QMessageBox,
)

from src.services.production_order_generator import (
    ProductionOrderGenerator,
)
from src.services.production_order_service import (
    ProductionOrderService,
)


class ProductionOrderController:
    def __init__(
        self,
        page,
        service=None,
        generator=None,
    ):
        self.page = page

        self.service = (
            service
            or ProductionOrderService()
        )

        self.generator = (
            generator
            or ProductionOrderGenerator(
                session=self.service.session
            )
        )

    # ==========================================================
    # Load
    # ==========================================================

    def load_orders(self):
        try:
            orders = (
                self.service
                .get_all_production_orders()
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

            process_filter = (
                self.page.process_filter
                .currentText()
                .strip()
                .upper()
            )

            filtered = []

            for order in orders:
                searchable = " ".join(
                    [
                        str(
                            order.work_order_no
                            or ""
                        ),
                        str(
                            order.product_code
                            or ""
                        ),
                        str(
                            order.operation_no
                            or ""
                        ),
                        str(
                            order.operation_name
                            or ""
                        ),
                        str(
                            order.process_type
                            or ""
                        ),
                        str(
                            order.machine_code
                            or ""
                        ),
                        str(
                            order.employee_code
                            or ""
                        ),
                        str(
                            order.shift
                            or ""
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
                        order.status or ""
                    ).upper()
                    != status_filter
                ):
                    continue

                if (
                    process_filter != "ALL"
                    and str(
                        order.process_type or ""
                    ).upper()
                    != process_filter
                ):
                    continue

                filtered.append(
                    order
                )

            filtered.sort(
                key=lambda item: (
                    str(
                        item.work_order_no
                        or ""
                    ),
                    int(
                        item.operation_no
                        or 0
                    ),
                )
            )

            self.page.set_orders(
                filtered
            )

            self.page.update_summary(
                orders
            )

            self.page.set_status_message(
                (
                    f"{len(filtered)} displayed / "
                    f"{len(orders)} total."
                )
            )

            return filtered

        except Exception as error:
            self.page.show_error(
                error
            )
            return []

    # ==========================================================
    # Generate
    # ==========================================================

    def generate_orders(self):
        work_order_no, accepted = (
            QInputDialog.getText(
                self.page,
                "Generate Production Orders",
                "Work Order No:",
            )
        )

        if not accepted:
            return None

        work_order_no = str(
            work_order_no or ""
        ).strip().upper()

        if not work_order_no:
            return None

        try:
            result = self.generator.generate(
                work_order_no,
                auto_commit=True,
            )

            self.load_orders()

            QMessageBox.information(
                self.page,
                "Generate Production Orders",
                (
                    f"Work Order: {work_order_no}\n\n"
                    f"Created: "
                    f"{result['created_count']}\n"
                    f"Skipped: "
                    f"{result['skipped_count']}\n"
                    f"Routing OP: "
                    f"{result['routing_count']}"
                ),
            )

            return result

        except Exception as error:
            self.page.show_error(
                error
            )
            return None

    def regenerate_selected_work_order(
        self,
    ):
        selected = self.page.selected_order()

        if selected is None:
            QMessageBox.warning(
                self.page,
                "Production Order",
                "Please select one Production Order.",
            )
            return None

        work_order_no = (
            selected.work_order_no
        )

        answer = QMessageBox.question(
            self.page,
            "Regenerate Production Orders",
            (
                "Delete replaceable Production Orders "
                "and generate them again?\n\n"
                f"Work Order: {work_order_no}"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return None

        try:
            result = self.generator.regenerate(
                work_order_no,
                auto_commit=True,
            )

            self.load_orders()

            QMessageBox.information(
                self.page,
                "Regenerate",
                (
                    f"Created: "
                    f"{result['created_count']}\n"
                    f"Skipped: "
                    f"{result['skipped_count']}"
                ),
            )

            return result

        except Exception as error:
            self.page.show_error(
                error
            )
            return None

    # ==========================================================
    # Workflow
    # ==========================================================

    def release_selected(self):
        return self._run_selected_action(
            action_name="Release",
            method=self.service.release,
        )

    def start_selected(self):
        return self._run_selected_action(
            action_name="Start",
            method=self.service.start,
        )

    def hold_selected(self):
        return self._run_selected_action(
            action_name="Hold",
            method=self.service.hold,
        )

    def complete_selected(self):
        order = self.page.selected_order()

        if order is None:
            QMessageBox.warning(
                self.page,
                "Production Order",
                "Please select one Production Order.",
            )
            return None

        completed_qty, accepted = (
            QInputDialog.getInt(
                self.page,
                "Complete Production Order",
                "Completed Qty:",
                int(
                    order.completed_qty
                    or order.plan_qty
                    or 0
                ),
                0,
                int(
                    order.plan_qty
                    or 2_000_000_000
                ),
            )
        )

        if not accepted:
            return None

        ng_qty, accepted = (
            QInputDialog.getInt(
                self.page,
                "Complete Production Order",
                "NG Qty:",
                int(
                    order.ng_qty
                    or 0
                ),
                0,
                int(
                    order.plan_qty
                    or 2_000_000_000
                ),
            )
        )

        if not accepted:
            return None

        try:
            result = self.service.complete(
                order.work_order_no,
                order.operation_no,
                completed_qty=completed_qty,
                ng_qty=ng_qty,
            )

            self.service.commit()
            self.load_orders()

            return result

        except Exception as error:
            self.service.rollback()
            self.page.show_error(
                error
            )
            return None

    def _run_selected_action(
        self,
        *,
        action_name,
        method,
    ):
        order = self.page.selected_order()

        if order is None:
            QMessageBox.warning(
                self.page,
                "Production Order",
                "Please select one Production Order.",
            )
            return None

        try:
            result = method(
                order.work_order_no,
                order.operation_no,
            )

            self.service.commit()
            self.load_orders()

            self.page.set_status_message(
                (
                    f"{action_name}: "
                    f"{order.work_order_no} / "
                    f"OP{order.operation_no}"
                )
            )

            return result

        except Exception as error:
            self.service.rollback()
            self.page.show_error(
                error
            )
            return None

    def close(self):
        self.service.close()