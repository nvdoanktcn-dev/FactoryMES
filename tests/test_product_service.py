from __future__ import annotations

import uuid

from src.framework.exception import DuplicateError
from src.services.product_service import ProductService
from tests.base.base_database_test import BaseDatabaseTest


class TestProductService(BaseDatabaseTest):

    def setUp(self):
        super().setUp()

        self.service = ProductService(
            session=self.session,
        )

        self.product_code = f"TEST-P-{uuid.uuid4().hex[:8].upper()}"

    def test_create_product(self):
        product = self.service.create_product(
            product_code=self.product_code,
            product_name_vi="Sản phẩm kiểm thử",
            product_name_cn="測試產品",
            customer="TEST",
            material="AL",
        )

        self.assertIsNotNone(product)
        self.assertEqual(product.product_code, self.product_code)
        self.assertEqual(product.product_name_vi, "Sản phẩm kiểm thử")

    def test_get_all_products(self):
        products = self.service.get_all_products()

        self.assertIsInstance(products, list)

    def test_duplicate_product_raises_error(self):
        self.service.create_product(
            product_code=self.product_code,
            product_name_vi="Sản phẩm kiểm thử",
            product_name_cn="測試產品",
            customer="TEST",
            material="AL",
        )

        with self.assertRaises(DuplicateError):
            self.service.create_product(
                product_code=self.product_code,
                product_name_vi="Sản phẩm trùng",
                product_name_cn="重複產品",
                customer="TEST",
                material="AL",
            )