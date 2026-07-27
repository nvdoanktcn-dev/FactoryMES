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
    def _filter_tree(
        cls,
        tree,
        allowed_pages,
    ):
        if allowed_pages is None:
            return
        allowed = set(allowed_pages)

        def filter_children(parent):
            for index in range(
                parent.childCount() - 1,
                -1,
                -1,
            ):
                item = parent.child(index)
                filter_children(item)
                page_key = item.data(
                    0,
                    Qt.UserRole,
                )
                denied_leaf = (
                    page_key is not None
                    and str(page_key) not in allowed
                )
                empty_group = (
                    page_key is None
                    and item.childCount() == 0
                )
                if denied_leaf or empty_group:
                    parent.takeChild(index)

        filter_children(
            tree.invisibleRootItem()
        )
    @classmethod
    def build_menu(
        cls,
        tree,
        allowed_pages=None,
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

        equipment = cls._create_item(
            "🦾 Equipment"
        )

        equipment.addChildren([
            cls._create_item(
                "CNC",
                "CNC",
            ),
            cls._create_item(
                "Robot",
                "Robot",
            ),
        ])

        inventory = cls._create_item(
            "📦 Inventory",
            "Inventory",
        )

        reports = cls._create_item(
            "📈 Reports"
        )

        reports.addChildren([
            cls._create_item(
                "Machine Utilization",
                "Machine Utilization Report",
            ),
            cls._create_item(
                "Production / Inventory",
                "Production Inventory Reconciliation",
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
            equipment
        )
        tree.addTopLevelItem(
            inventory
        )
        tree.addTopLevelItem(
            reports
        )
        tree.addTopLevelItem(
            system
        )

        cls._filter_tree(
            tree,
            allowed_pages,
        )

        tree.expandAll()
