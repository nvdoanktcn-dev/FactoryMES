from __future__ import annotations

from PySide6.QtWidgets import QDialog, QMessageBox

from src.services.work_order_service import WorkOrderService
from src.ui.dialogs.work_order_dialog import WorkOrderDialog


class WorkOrderController:
    def __init__(self, page, service=None):
        self.page = page
        self.service = service or WorkOrderService()

    def load_work_orders(self):
        try:
            work_orders = self.service.get_all_work_orders()
            keyword = self.page.search_box.text().strip().lower()
            status = self.page.status_filter.currentText().strip().upper()
            priority = self.page.priority_filter.currentText().strip().upper()

            filtered = []
            for work_order in work_orders:
                searchable = " ".join(
                    [
                        str(work_order.work_order_no or ""),
                        str(work_order.product_code or ""),
                        str(work_order.status or ""),
                        str(work_order.priority or ""),
                        str(work_order.remark or ""),
                    ]
                ).lower()

                if keyword and keyword not in searchable:
                    continue
                if status != "ALL" and str(work_order.status or "").upper() != status:
                    continue
                if priority != "ALL" and str(work_order.priority or "").upper() != priority:
                    continue
                filtered.append(work_order)

            filtered.sort(
                key=lambda item: (
                    item.due_date,
                    str(item.work_order_no or ""),
                )
            )
            self.page.set_work_orders(filtered)
            self.page.set_status_message(f"{len(filtered)} work order(s).")
            return filtered
        except Exception as error:
            self.page.show_error(error)
            return []

    def add_work_order(self):
        dialog = WorkOrderDialog(parent=self.page)
        if dialog.exec() != QDialog.Accepted:
            return None

        try:
            work_order = self.service.create_work_order(dialog.get_data())
            self.service.commit()
            self.load_work_orders()
            QMessageBox.information(
                self.page,
                "Work Order",
                f"Work Order created: {work_order.work_order_no}",
            )
            return work_order
        except Exception as error:
            self.service.rollback()
            self.page.show_error(error)
            return None

    def edit_selected_work_order(self):
        work_order = self.page.selected_work_order()
        if work_order is None:
            QMessageBox.warning(self.page, "Work Order", "Please select one Work Order.")
            return None

        dialog = WorkOrderDialog(parent=self.page, work_order=work_order)
        if dialog.exec() != QDialog.Accepted:
            return None

        try:
            updated = self.service.update_work_order(
                work_order.work_order_no,
                dialog.get_data(),
            )
            self.service.commit()
            self.load_work_orders()
            QMessageBox.information(
                self.page,
                "Work Order",
                f"Work Order updated: {updated.work_order_no}",
            )
            return updated
        except Exception as error:
            self.service.rollback()
            self.page.show_error(error)
            return None

    def cancel_selected_work_order(self):
        work_order = self.page.selected_work_order()
        if work_order is None:
            QMessageBox.warning(self.page, "Work Order", "Please select one Work Order.")
            return None

        answer = QMessageBox.question(
            self.page,
            "Confirm Cancel",
            f"Cancel this Work Order?\n\n{work_order.work_order_no}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return None

        try:
            result = self.service.delete_work_order(work_order.work_order_no)
            self.service.commit()
            self.load_work_orders()
            return result
        except Exception as error:
            self.service.rollback()
            self.page.show_error(error)
            return None

    def release_selected_work_order(self):
        return self._change_selected_status(self.service.release_work_order)

    def start_selected_work_order(self):
        return self._change_selected_status(self.service.start_work_order)

    def complete_selected_work_order(self):
        return self._change_selected_status(self.service.complete_work_order)

    def _change_selected_status(self, service_method):
        work_order = self.page.selected_work_order()
        if work_order is None:
            QMessageBox.warning(self.page, "Work Order", "Please select one Work Order.")
            return None

        try:
            result = service_method(work_order.work_order_no)
            self.service.commit()
            self.load_work_orders()
            return result
        except Exception as error:
            self.service.rollback()
            self.page.show_error(error)
            return None

    def close(self):
        self.service.close()
