from __future__ import annotations

import pandas as pd

from src.database.session import get_session
from src.services.product_service import ProductService

from src.services.master_import.import_engine import (
    ImportContext,
    ImportEngine,
    ImporterRegistry,
)

from src.services.master_import.importers import (
    ProductImporter,
)

from src.services.master_import.transaction import (
    SQLAlchemyTransactionManager,
)


# ==========================================================
# Service giả để tạo lỗi ở dòng thứ 2
# ==========================================================

class FailingProductService:

    def __init__(self, real_service):

        self.real_service = real_service

        self.counter = 0

    def save_product(self, data):

        self.counter += 1

        # Dòng thứ hai sẽ lỗi
        if self.counter == 2:
            raise RuntimeError(
                "Fake rollback error."
            )

        return self.real_service.save_product(data)

    def get_product(self, code):

        return self.real_service.get_product(code)


# ==========================================================
# Main Test
# ==========================================================

session = get_session()

try:

    # ------------------------------------------------------
    # Product Service thật
    # ------------------------------------------------------

    real_service = ProductService(
        session=session
    )

    # ------------------------------------------------------
    # Xóa dữ liệu cũ nếu tồn tại
    # ------------------------------------------------------

    for code in [
        "RB-P001",
        "RB-P002",
    ]:

        product = real_service.get_product(code)

        if product is not None:

            session.delete(product)

    session.commit()

    # ------------------------------------------------------
    # Service giả
    # ------------------------------------------------------

    failing_service = FailingProductService(
        real_service
    )

    # ------------------------------------------------------
    # Registry
    # ------------------------------------------------------

    registry = ImporterRegistry()

    registry.register(

        ProductImporter(

            product_service=failing_service

        )

    )

    # ------------------------------------------------------
    # Engine
    # ------------------------------------------------------

    engine = ImportEngine(

        registry=registry,

        transaction_manager=

            SQLAlchemyTransactionManager(

                session=session

            ),

    )

    # ------------------------------------------------------
    # DataFrame
    # ------------------------------------------------------

    dataframe = pd.DataFrame(

        [

            {

                "Product Code": "RB-P001",

                "Product Name": "Rollback Product 1",

                "Customer": "TOYOTA",

                "Material": "ADC12",

                "Unit": "PCS",

                "Cycle Time (Sec)": 45,

                "Standard Output (PCS/H)": 80,

                "Status": "ACTIVE",

            },

            {

                "Product Code": "RB-P002",

                "Product Name": "Rollback Product 2",

                "Customer": "HONDA",

                "Material": "ADC12",

                "Unit": "PCS",

                "Cycle Time (Sec)": 45,

                "Standard Output (PCS/H)": 80,

                "Status": "ACTIVE",

            },

        ]

    )

    context = ImportContext(

        module_name="PRODUCT",

        dataframe=dataframe,

        user="rollback-test",

    )

    # ------------------------------------------------------
    # Execute
    # ------------------------------------------------------

    try:

        engine.execute(context)

    except Exception as ex:

        print()

        print("Rollback executed.")

        print(ex)

    # ------------------------------------------------------
    # Làm mới Session
    # ------------------------------------------------------

    session.expire_all()

    # ------------------------------------------------------
    # Kiểm tra dữ liệu
    # ------------------------------------------------------

    product1 = real_service.get_product(
        "RB-P001"
    )

    product2 = real_service.get_product(
        "RB-P002"
    )

    print()

    print("RB-P001 :", product1)

    print("RB-P002 :", product2)

    assert product1 is None

    assert product2 is None

    print()

    print("=" * 60)

    print("Rollback test passed.")

    print("=" * 60)

finally:

    session.close()