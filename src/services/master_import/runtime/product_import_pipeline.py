from __future__ import annotations

from src.services.master_import.import_engine import (
    ImportEngine,
    ImporterRegistry,
)
from src.services.master_import.importers import (
    ProductImporter,
)
from src.services.master_import.transaction import (
    SQLAlchemyTransactionManager,
)
from src.services.product_service import (
    ProductService,
)
from src.services.master_import.import_detail_service import (
    ImportDetailService,
)


def build_product_import_engine(
    session,
) -> ImportEngine:
    """
    Tạo ImportEngine cho Product sử dụng chung
    một SQLAlchemy session.

    Session này được dùng đồng thời bởi:
    - ProductService
    - ProductRepository
    - SQLAlchemyTransactionManager
    """

    if session is None:
        raise ValueError(
            "SQLAlchemy session is required."
        )

    product_service = ProductService(
        session=session
    )

    import_detail_service = (
        ImportDetailService(
            session=session,
            auto_commit=False,
        )
    )

    product_importer = ProductImporter(
        product_service=product_service,
        import_detail_service=(
            import_detail_service 
        ),
    )

    registry = ImporterRegistry()

    registry.register(
        product_importer
    )

    transaction_manager = (
        SQLAlchemyTransactionManager(
            session=session,
            close_on_finish=False,
        )
    )

    return ImportEngine(
        registry=registry,
        transaction_manager=(
            transaction_manager
        ),
    )