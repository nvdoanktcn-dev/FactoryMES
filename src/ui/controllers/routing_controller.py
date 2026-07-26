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
            capacity_method = getattr(
                self.service,
                "build_capacity_profile",
                None,
            )
            capacity_profile = (
                capacity_method(routings)
                if callable(capacity_method)
                else {}
            )
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
            self.page.set_routings(
                filtered,
                capacity_profile=capacity_profile,
            )
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

        current_status = str(
            routing.status or ""
        ).strip().upper()
        activate = current_status == "INACTIVE"
        target_status = (
            "ACTIVE"
            if activate
            else "INACTIVE"
        )
        action_text = (
            "Activate"
            if activate
            else "Set Inactive"
        )

        answer = QMessageBox.question(
            self.page,
            f"Confirm {action_text}",
            (
                f"Set {routing.product_code} / "
                f"OP{routing.operation_no} "
                f"to {target_status}?"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return None

        try:
            result = self.service.set_routing_status(
                routing.product_code,
                routing.operation_no,
                target_status,
            )
            self.service.commit()
            self.load_routings()
            return result
        except Exception as error:
            self.service.rollback()
            self.page.show_error(error)
            return None

    def update_status_action(self):
        routing = self.page.selected_routing()
        text = "Set Inactive"

        if (
            routing is not None
            and str(
                routing.status or ""
            ).strip().upper() == "INACTIVE"
        ):
            text = "Activate"

        self.page.btn_inactive.setText(text)

    def close(self):
        self.service.close()
