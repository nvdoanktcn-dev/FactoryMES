from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidgetItem

from src.services.robot_service import RobotService
from src.ui.dialogs.robot_dialog import RobotDialog
from src.ui.framework.master_crud_page import MasterCRUDPage


class RobotPage(MasterCRUDPage):
    """
    Danh mục Robot.
    """

    ENTITY_NAME = "Robot"

    HEADERS = [
        "Robot Code",
        "Robot Name",
        "Type",
        "Area",
        "Station",
        "Status",
    ]

    DEFAULT_EXPORT_NAME = "robot_master.xlsx"

    def __init__(self):
        super().__init__(
            title="🤖 Robot",
            headers=self.HEADERS,
            search_placeholder="Search robot...",
            service=RobotService(),
            importer=None,
            dialog_class=RobotDialog,
        )

        self.initialize_page()

    # ==========================================================
    # Data
    # ==========================================================

    def load_records(self, keyword):
        return self.service.search_robots(keyword)

    @staticmethod
    def record_to_row(robot):
        return [
            robot.robot_code or "",
            robot.robot_name or "",
            robot.robot_type or "",
            robot.area or "",
            robot.station or "",
            robot.status or "",
        ]

    @staticmethod
    def get_record_key(robot):
        return robot.robot_code

    # ==========================================================
    # Dialog
    # ==========================================================

    def create_dialog(self, parent=None, record=None):
        return self.dialog_class(parent=parent, robot=record)

    # ==========================================================
    # CRUD
    # ==========================================================

    def create_record(self, data):
        return self.service.create_robot(data)

    def update_record(self, record_key, data):
        return self.service.update_robot(record_key, data)

    def delete_record(self, record_key):
        return self.service.delete_robot(record_key)

    # ==========================================================
    # Table presentation
    # ==========================================================

    def create_table_item(self, record, column_index, value):
        item = QTableWidgetItem(self.display_value(value))
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)

        if column_index in {0, 2, 3, 4, 5}:
            item.setTextAlignment(Qt.AlignCenter)

        if column_index == 5:
            status = str(value or "").strip().upper()

            if status == "ACTIVE":
                item.setForeground(Qt.darkGreen)
            elif status == "MAINTENANCE":
                item.setForeground(Qt.darkYellow)
            elif status == "STOPPED":
                item.setForeground(Qt.red)

        return item

    # ==========================================================
    # Summary
    # ==========================================================

    def get_active_statuses(self):
        return {"ACTIVE"}

    # ==========================================================
    # Validation
    # ==========================================================

    def validate_dialog_data(self, data, is_edit=False):
        super().validate_dialog_data(data, is_edit=is_edit)

        if not str(data.get("robot_code", "")).strip():
            raise ValueError("Robot Code is required.")

        if not str(data.get("robot_name", "")).strip():
            raise ValueError("Robot Name is required.")

        return True

    # ==========================================================
    # Export
    # ==========================================================

    @staticmethod
    def record_to_export_row(robot):
        return {
            "Robot Code": robot.robot_code or "",
            "Robot Name": robot.robot_name or "",
            "Type": robot.robot_type or "",
            "Area": robot.area or "",
            "Station": robot.station or "",
            "Status": robot.status or "",
        }
