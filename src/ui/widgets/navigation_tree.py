from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem


class NavigationTree(QTreeWidget):
    def __init__(self):
        super().__init__()

        self.setHeaderHidden(True)
        self.setStyleSheet(
            """
            QTreeWidget {
                background-color: #263238;
                color: white;
                font-size: 14px;
                border: none;
            }

            QTreeWidget::item {
                padding: 8px;
            }

            QTreeWidget::item:selected {
                background-color: #1976D2;
            }
            """
        )

        self.build_menu()

    def build_menu(self):
        dashboard = QTreeWidgetItem(["📊 Dashboard"])

        master = QTreeWidgetItem(["📦 Master Data"])
        product = QTreeWidgetItem(["Product"])
        machine = QTreeWidgetItem(["Machine"])
        employee = QTreeWidgetItem(["Employee"])
        routing = QTreeWidgetItem(["Routing"])

        master.addChildren([product, machine, employee, routing])

        production = QTreeWidgetItem(["🏭 Production"])
        work_order = QTreeWidgetItem(["Work Order"])
        cnc = QTreeWidgetItem(["CNC"])
        robot = QTreeWidgetItem(["Robot"])

        production.addChildren([work_order, cnc, robot])

        inventory = QTreeWidgetItem(["📦 Inventory"])
        report = QTreeWidgetItem(["📈 Report"])
        system = QTreeWidgetItem(["⚙ System"])

        self.addTopLevelItem(dashboard)
        self.addTopLevelItem(master)
        self.addTopLevelItem(production)
        self.addTopLevelItem(inventory)
        self.addTopLevelItem(report)
        self.addTopLevelItem(system)

        self.expandAll()