from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTreeWidgetItem


class MenuManager:
    """
    Xây dựng cây menu điều hướng.

    Text hiển thị có thể chứa icon/emoji.
    Khóa điều hướng được lưu riêng trong Qt.UserRole.
    """

    @staticmethod
    def _create_item(
        text,
        page_key=None,
    ):
        item = QTreeWidgetItem(
            [text]
        )

        item.setData(
            0,
            Qt.UserRole,
            page_key,
        )

        return item

    @classmethod
    def build_menu(
        cls,
        tree,
    ):
        tree.clear()
        tree.setHeaderHidden(True)

        dashboard = cls._create_item(
            "📊 Dashboard",
            "Dashboard",
        )

        master = cls._create_item(
            "📦 Master Data"
        )

        master.addChildren([
            cls._create_item(
                "Product",
                "Product",
            ),
            cls._create_item(
                "Machine",
                "Machine",
            ),
            cls._create_item(
                "Employee",
                "Employee",
            ),
            cls._create_item(
                "Routing",
                "Routing",
            ),
        ])

        production = cls._create_item(
            "🏭 Production"
        )

        production.addChildren([
            cls._create_item(
                "Work Order",
                "Work Order",
            ),
            cls._create_item(
                "Production",
                "Production",
            ),
            cls._create_item(
                "Production Assignment",
                "Production Assignment",
            ),
            cls._create_item(
                "Production Execution",
                "Production Execution",
            ),
            cls._create_item(
                "Production Downtime",
                "Production Downtime",
            ),
            cls._create_item(
                "Production NG",
                "Production NG",
            ),
            cls._create_item(
                "OEE Dashboard",
                "OEE Dashboard",
            ),
        ])

        system = cls._create_item(
            "⚙ System"
        )

        system.addChildren([
            cls._create_item(
                "Master Import",
                "Master Import",
            ),
        ])

        tree.addTopLevelItem(
            dashboard
        )
        tree.addTopLevelItem(
            master
        )
        tree.addTopLevelItem(
            production
        )
        tree.addTopLevelItem(
            system
        )

        tree.expandAll()
