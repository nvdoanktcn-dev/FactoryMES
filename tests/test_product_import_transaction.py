from __future__ import annotations

import pandas as pd

from src.models.product import Product
from src.services.master_import.import_engine import (
    ImportContext,
    ImportEngine,
    ImporterRegistry,
)
from src.services.master_import.importers import ProductImporter
from src.services.master_import.transaction import (
    SQLAlchemyTransactionManager,
)
from src.services.product_service import ProductService
from tests.base.base_database_test import BaseDatabaseTest


class TestProductImportTransaction(BaseDatabaseTest):
    PRODUCT_CODES = (
        "TX-P001",
        "TX-P002",
    )

    def setUp(self):
        super().setUp()

        self.product_service = ProductService(
            session=self.session,
        )

        self._delete_test_products()
        self.session.commit()

        self.engine = self._build_engine()

    def tearDown(self):
        try:
            self.session.rollback()
            self._delete_test_products()
            self.session.commit()
        finally:
            super().tearDown()

    def _delete_test_products(self):
        (
            self.session.query(Product)
            .filter(
                Product.product_code.in_(
                    self.PRODUCT_CODES
                )
            )
            .delete(
                synchronize_session=False
            )
        )

    def _build_engine(self):
        registry = ImporterRegistry()

        registry.register(
            ProductImporter(
                product_service=self.product_service,
            )
        )

        transaction_manager = SQLAlchemyTransactionManager(
            session=self.session,
        )

        return ImportEngine(
            registry=registry,
            transaction_manager=transaction_manager,
        )

    @staticmethod
    def _create_valid_dataframe():
        return pd.DataFrame(
            [
                {
                    "Product Code": "TX-P001",
                    "Product Name": "Transaction Product 1",
                    "Customer": "TOYOTA",
                    "Material": "ADC12",
                    "Unit": "PCS",
                    "Cycle Time (Sec)": 45,
                    "Standard Output (PCS/H)": 80,
                    "Status": "ACTIVE",
                },
                {
                    "Product Code": "TX-P002",
                    "Product Name": "Transaction Product 2",
                    "Customer": "HONDA",
                    "Material": "AL6061",
                    "Unit": "PCS",
                    "Cycle Time (Sec)": 40,
                    "Standard Output (PCS/H)": 90,
                    "Status": "ACTIVE",
                },
            ]
        )

    def test_valid_import_is_committed(self):
        result = self.engine.execute(
            ImportContext(
                module_name="PRODUCT",
                dataframe=self._create_valid_dataframe(),
                user="transaction-test",
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(
            result.inserted_rows,
            2,
        )

        self.session.expire_all()

        product_1 = self.product_service.get_product(
            "TX-P001"
        )
        product_2 = self.product_service.get_product(
            "TX-P002"
        )

        self.assertIsNotNone(product_1)
        self.assertIsNotNone(product_2)

        self.assertEqual(
            product_1.product_name_vi,
            "Transaction Product 1",
        )
        self.assertEqual(
            product_2.product_name_vi,
            "Transaction Product 2",
        )