from __future__ import annotations

from src.services.master_import.import_detail_service import (
    ImportDetailService,
)
from src.services.master_import.import_engine import (
    ImportEngine,
    ImporterRegistry,
)
from src.services.master_import.importers import (
    GenericMasterImporter,
)
from src.services.master_import.mappers import (
    WorkOrderMapper,
)
from src.services.master_import.runtime.work_order_import_config import (
    database_work_order_to_dict,
    work_order_entity_key,
    work_order_entity_to_service_data,
)
from src.services.master_import.transaction import (
    SQLAlchemyTransactionManager,
)
from src.services.work_order_service import (
    WorkOrderService,
)


def build_work_order_import_engine(
    session,
) -> ImportEngine:
    if session is None:
        raise ValueError(
            "SQLAlchemy session is required."
        )

    work_order_service = WorkOrderService(
        session=session
    )

    detail_service = ImportDetailService(
        session=session,
        auto_commit=False,
    )

    importer = GenericMasterImporter(
        module_name="WORK_ORDER",
        mapper=WorkOrderMapper(),
        service=work_order_service,
        save_method=(
            work_order_service.save_work_order
        ),
        get_method=(
            work_order_service.get_work_order
        ),
        entity_key_getter=(
            work_order_entity_key
        ),
        entity_to_service_data=(
            work_order_entity_to_service_data
        ),
        database_entity_to_dict=(
            database_work_order_to_dict
        ),
        import_detail_service=(
            detail_service
        ),
    )

    registry = ImporterRegistry()

    registry.register(
        importer
    )

    transaction_manager = (
        SQLAlchemyTransactionManager(
            session=session,
            close_on_finish=False,
        )
    )

    return ImportEngine(
        registry=registry,
        transaction_manager=transaction_manager,
    )