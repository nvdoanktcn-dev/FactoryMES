"""
Smoke test cho các module mới: CNC (Machine + Production Log),
Robot (Robot + Operation Log), Inventory (StockIn/StockOut/
FinishedInventory), và cho fix commit-on-close của BaseService/
SessionOwnedService.

Không thay thế test suite đầy đủ, chỉ đảm bảo luồng CRUD cơ bản
hoạt động và dữ liệu thực sự được lưu (persist) sau khi service
đóng session, thay vì chỉ tồn tại tạm thời trong session đang mở.
"""
from __future__ import annotations

from datetime import date

from tests.base.database_test_case import DatabaseTestCase


class TestCommitOnClose(DatabaseTestCase):
    """
    Xác nhận fix: SessionOwnedService.close() phải commit trước khi
    đóng session, nếu không dữ liệu Add/Edit sẽ bị rollback âm thầm
    khi page/service bị đóng (đúng bug đã phát hiện trong session này).
    """

    def test_employee_persists_after_service_closed(self):
        """
        Dùng EmployeeService() không truyền session (giống hệt cách
        UI thực tế khởi tạo service) để xác nhận việc commit-on-close
        hoạt động xuyên suốt qua engine mặc định của ứng dụng, không
        chỉ trong self.session của DatabaseTestCase. Dọn dẹp bản ghi
        test ngay sau khi xác nhận để test có thể chạy lại nhiều lần.
        """
        import uuid

        from src.models.employee import Employee
        from src.services.employee_service import EmployeeService

        code = f"SMOKE_EMP_{uuid.uuid4().hex[:8].upper()}"

        service = EmployeeService()
        service.create_employee(
            {
                "employee_code": code,
                "employee_name": "Smoke Test",
            }
        )
        service.close()

        verify_service = EmployeeService()
        try:
            record = verify_service.get_employee(code)
            self.assertIsNotNone(record)
        finally:
            try:
                verify_service.repository.session.query(
                    Employee
                ).filter_by(
                    employee_code=code
                ).delete(
                    synchronize_session=False
                )
                verify_service.repository.session.commit()
            finally:
                verify_service.close()


class TestCNCMachineService(DatabaseTestCase):
    def test_create_update_delete(self):
        from src.services.cnc_machine_service import (
            CNCMachineService,
        )

        service = CNCMachineService(session=self.session)

        machine = service.create_cnc_machine(
            {
                "machine_code": "CNC-001",
                "machine_name": "CNC Machine 1",
                "axis_count": 5,
            }
        )
        self.assertEqual(machine.status, "ACTIVE")

        updated = service.update_cnc_machine(
            "CNC-001",
            {
                "machine_name": "CNC Machine 1 Updated",
                "status": "ACTIVE",
            },
        )
        self.assertEqual(
            updated.machine_name, "CNC Machine 1 Updated"
        )

        deleted = service.delete_cnc_machine("CNC-001")
        self.assertEqual(deleted.status, "INACTIVE")

        with self.assertRaises(Exception):
            service.create_cnc_machine(
                {
                    "machine_code": "",
                    "machine_name": "No code",
                }
            )


class TestCNCProductionLogService(DatabaseTestCase):
    def test_create_from_import_and_search(self):
        from src.services.cnc_production_log_service import (
            CNCProductionLogService,
        )

        service = CNCProductionLogService(session=self.session)

        log = service.create_log_from_import(
            {
                "log_date": date(2026, 7, 20),
                "machine_name": "CNC-01",
                "work_order_no": "WO001",
                "product_name": "Product A",
                "actual_pcs": 100,
                "total_ng": 2,
            },
            source_file="test.xlsx",
        )

        self.assertEqual(log.source_file, "test.xlsx")
        self.assertEqual(log.machine_name, "CNC-01")

        results = service.search_logs("wo001")
        self.assertEqual(len(results), 1)


class TestCNCImporter(DatabaseTestCase):
    def test_clean_and_validate(self):
        import pandas as pd

        from src.importer.cnc_importer import CNCImporter

        dataframe = pd.DataFrame(
            [
                {
                    "Ngày": "2026-07-20",
                    "Tên thiết bị": "cnc-02",
                    "Mã công lệnh": "wo002",
                    "Tên sản phẩm": "Product B",
                    "Nhân viên thao tác": "NV01",
                    "Thực tế PCS": 50,
                    "Tổng NG": 1,
                }
            ]
        )

        importer = CNCImporter()

        cleaned = importer.clean_data(dataframe)
        errors = importer.validate_data(cleaned)
        self.assertEqual(errors, [])

        self.assertEqual(cleaned["Tên thiết bị"][0], "CNC-02")
        self.assertEqual(cleaned["Mã công lệnh"][0], "WO002")

    def test_row_to_log_data_and_save_via_service(self):
        """
        importer.save() luôn tự tạo CNCProductionLogService() riêng
        (giống mọi GenericMasterImporter khác trong ứng dụng), nên
        test này gọi thẳng _row_to_log_data() + service với session
        test thay vì gọi save() (vốn dùng session sản xuất thật, chỉ
        có sẵn khi app đã chạy Base.metadata.create_all()).
        """
        import pandas as pd

        from src.importer.cnc_importer import CNCImporter
        from src.services.cnc_production_log_service import (
            CNCProductionLogService,
        )

        dataframe = pd.DataFrame(
            [
                {
                    "Ngày": "2026-07-20",
                    "Tên thiết bị": "cnc-02",
                    "Mã công lệnh": "wo002",
                    "Tên sản phẩm": "Product B",
                    "Nhân viên thao tác": "NV01",
                    "Thực tế PCS": 50,
                    "Tổng NG": 1,
                }
            ]
        )

        importer = CNCImporter()
        cleaned = importer.clean_data(dataframe)

        service = CNCProductionLogService(session=self.session)

        for _, row in cleaned.iterrows():
            data = importer._row_to_log_data(row)
            service.create_log_from_import(
                data, source_file="unit_test.csv"
            )

        results = service.search_logs("WO002")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].machine_name, "CNC-02")
        self.assertEqual(results[0].source_file, "unit_test.csv")


class TestRobotService(DatabaseTestCase):
    def test_create_update_delete(self):
        from src.services.robot_service import RobotService

        service = RobotService(session=self.session)

        robot = service.create_robot(
            {
                "robot_code": "ROBOT-001",
                "robot_name": "Welding Robot 1",
                "area": "Line 1",
            }
        )
        self.assertEqual(robot.status, "ACTIVE")

        updated = service.update_robot(
            "ROBOT-001",
            {
                "robot_name": "Welding Robot 1 Updated",
                "status": "MAINTENANCE",
            },
        )
        self.assertEqual(updated.status, "MAINTENANCE")

        stopped = service.delete_robot("ROBOT-001")
        self.assertEqual(stopped.status, "STOPPED")


class TestRobotOperationLogService(DatabaseTestCase):
    def test_create_requires_existing_robot(self):
        from src.framework.exception import ValidationError
        from src.services.robot_operation_log_service import (
            RobotOperationLogService,
        )
        from src.services.robot_service import RobotService

        robot_service = RobotService(session=self.session)
        robot_service.create_robot(
            {
                "robot_code": "ROBOT-002",
                "robot_name": "Assembly Robot",
            }
        )

        log_service = RobotOperationLogService(
            session=self.session
        )

        log = log_service.create_log(
            {
                "robot_code": "robot-002",
                "log_date": date(2026, 7, 20),
                "output_qty": 120,
                "ng_qty": 3,
                "status": "COMPLETED",
            }
        )
        self.assertEqual(log.robot_code, "ROBOT-002")

        with self.assertRaises(ValidationError):
            log_service.create_log(
                {
                    "robot_code": "ROBOT-DOES-NOT-EXIST",
                    "output_qty": 10,
                }
            )


class TestInventoryServices(DatabaseTestCase):
    def test_stock_in_stock_out_finished_inventory(self):
        from src.services.finished_inventory_service import (
            FinishedInventoryService,
        )
        from src.services.stock_in_service import StockInService
        from src.services.stock_out_service import StockOutService

        stock_in_service = StockInService(session=self.session)
        stock_out_service = StockOutService(session=self.session)
        inventory_service = FinishedInventoryService(
            session=self.session
        )

        stock_in = stock_in_service.create_stock_in(
            {
                "stock_in_date": date(2026, 7, 20),
                "item_code": "RM001",
                "qty": 100,
                "supplier": "Supplier A",
            }
        )
        self.assertEqual(stock_in.item_code, "RM001")

        stock_out = stock_out_service.create_stock_out(
            {
                "stock_out_date": date(2026, 7, 21),
                "item_code": "RM001",
                "qty": 30,
            }
        )
        self.assertEqual(stock_out.qty, 30)

        inventory = inventory_service.create_inventory(
            {
                "inventory_date": date(2026, 7, 22),
                "work_order": "WO003",
                "product_code": "P001",
                "qty": 70,
            }
        )
        self.assertEqual(inventory.qty, 70)

        with self.assertRaises(Exception):
            stock_in_service.create_stock_in(
                {
                    "stock_in_date": date(2026, 7, 20),
                    "item_code": "",
                    "qty": 10,
                }
            )
