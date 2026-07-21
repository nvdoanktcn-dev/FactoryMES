import uuid

from tests.base.base_database_test import BaseDatabaseTest
from src.models.product import Product
from src.repository.product_repository import ProductRepository


class TestProductRepository(BaseDatabaseTest):

    def setUp(self):
        super().setUp()

        self.repo = ProductRepository(self.session)

    def test_add_product(self):

        code = f"TEST-{uuid.uuid4().hex[:8]}"

        product = Product(
            product_code=code,
            product_name_vi="Repository Test",
            product_name_cn="Repository Test",
            customer="TEST",
            material="AL",
        )

        self.repo.add(product)

        saved = self.repo.get_by_code(code)

        self.assertIsNotNone(saved)
        self.assertEqual(saved.product_code, code)

    def test_get_all(self):

        rows = self.repo.get_all()

        self.assertIsInstance(rows, list)