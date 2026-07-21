from __future__ import annotations

from PySide6.QtWidgets import QDialog, QMessageBox

from src.services.routing_service import RoutingService
from src.ui.dialogs.routing_dialog import RoutingDialog


class RoutingController:
    def __init__(self, page, service=None):
        self.page = page
        self.service = service or RoutingService()

    def load_routings(self):
        try:
            routings = self.service.get_all_routings()
            keyword = self.page.search_box.text().strip().lower()
            process_type = self.page.process_filter.currentText().strip().upper()
            status = self.page.status_filter.currentText().strip().upper()

            filtered = []
            for routing in routings:
                searchable = " ".join([
                    str(routing.product_code or ""),
                    str(routing.operation_no or ""),
                    str(routing.operation_name or ""),
                    str(routing.process_type or ""),
                    str(routing.machine_type or ""),
                    str(routing.remark or ""),
                ]).lower()

                if keyword and keyword not in searchable:
                    continue
                if process_type != "ALL" and str(routing.process_type or "").upper() != process_type:
                    continue
                if status != "ALL" and str(routing.status or "").upper() != status:
                    continue
                filtered.append(routing)

            filtered.sort(key=lambda item: (str(item.product_code or ""), int(item.operation_no or 0)))
            self.page.set_routings(filtered)
            self.page.set_status_message(f"{len(filtered)} routing record(s).")
            return filtered
        except Exception as error:
            self.page.show_error(error)
            return []

    def add_routing(self):
        dialog = RoutingDialog(parent=self.page)
        if dialog.exec() != QDialog.Accepted:
            return None
        try:
            routing = self.service.create_routing(dialog.get_data())
            self.service.commit()
            self.load_routings()
            return routing
        except Exception as error:
            self.service.rollback()
            self.page.show_error(error)
            return None

    def edit_selected_routing(self):
        routing = self.page.selected_routing()
        if routing is None:
            QMessageBox.warning(self.page, "Routing", "Please select one routing record.")
            return None

        dialog = RoutingDialog(parent=self.page, routing=routing)
        if dialog.exec() != QDialog.Accepted:
            return None

        try:
            updated = self.service.update_routing(
                routing.product_code,
                routing.operation_no,
                dialog.get_data(),
            )
            self.service.commit()
            self.load_routings()
            return updated
        except Exception as error:
            self.service.rollback()
            self.page.show_error(error)
            return None

    def inactivate_selected_routing(self):
        routing = self.page.selected_routing()
        if routing is None:
            QMessageBox.warning(self.page, "Routing", "Please select one routing record.")
            return None

        answer = QMessageBox.question(
            self.page,
            "Confirm Inactive",
            f"Set {routing.product_code} / OP{routing.operation_no} to INACTIVE?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return None

        try:
            result = self.service.delete_routing(routing.product_code, routing.operation_no)
            self.service.commit()
            self.load_routings()
            return result
        except Exception as error:
            self.service.rollback()
            self.page.show_error(error)
            return None

    def close(self):
        self.service.close()
