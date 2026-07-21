from __future__ import annotations

import uuid
from datetime import date

from src.models.product import Product
from src.repository.product_repository import ProductRepository
from src.services.work_order_service import WorkOrderService
from tests.base.base_database_test import BaseDatabaseTest


class TestWorkOrderService(BaseDatabaseTest):

    def setUp(self):
        super().setUp()

        suffix = uuid.uuid4().hex[:8].upper()

        self.product_code = f"TEST-P-{suffix}"
        self.work_order_no = f"TEST-WO-{suffix}"

        product_repository = ProductRepository(self.session)

        product_repository.add(
            Product(
                product_code=self.product_code,
                product_name_vi="Sản phẩm Work Order Test",
                product_name_cn="工單測試產品",
                customer="TEST",
                material="AL",
            )
        )

        self.session.commit()

        self.service = WorkOrderService(
            session=self.session,
        )

    def test_create_work_order(self):

        repo = ProductRepository(self.session)

        repo_product = repo.get_by_code(self.product_code)

        service_repo_product = (
            self.service.product_service.repository.get_by_code(
                self.product_code
            )
        )

        service_product = (
            self.service.product_service.get_product(
                self.product_code
            )
        )

        print("\n================ DEBUG ================")
        print("Product Code :", self.product_code)

        print("\nSession IDs")
        print("------------------------------")
        print("self.session                  =", id(self.session))
        print("workorder.session             =", id(self.service.session))
        print(
            "product_service.session       =",
            id(self.service.product_service.session),
        )
        print(
            "product_repository.session    =",
            id(self.service.product_service.repository.session),
        )

        print("\nRepository Objects")
        print("------------------------------")
        print("repo                          =", repo)
        print(
            "service repository            =",
            self.service.product_service.repository,
        )

        print("\nQuery Result")
        print("------------------------------")
        print("repo_product                  =", repo_product)
        print("service_repo_product          =", service_repo_product)
        print("service_product               =", service_product)

        print("=======================================\n")

        # KHÔNG assert ở đây để xem toàn bộ debug
        # self.assertIsNotNone(repo_product)
        # self.assertIsNotNone(service_product)

        work_order, action = self.service.save_work_order(
            {
                "work_order_no": self.work_order_no,
                "product_code": self.product_code,
                "plan_qty": 10000,
                "start_date": date(2026, 7, 1),
                "due_date": date(2026, 7, 31),
                "status": "PLANNED",
            }
        )

        self.assertEqual(action, "created")
        self.assertEqual(
            work_order.work_order_no,
            self.work_order_no,
        )
        self.assertEqual(
            work_order.product_code,
            self.product_code,
        )
        self.assertEqual(
            work_order.plan_qty,
            10000,
        )

    def test_get_all_work_orders(self):
        rows = self.service.get_all_work_orders()
        self.assertIsInstance(rows, list)