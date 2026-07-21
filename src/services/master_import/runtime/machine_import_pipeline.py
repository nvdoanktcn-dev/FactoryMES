from __future__ import annotations

from src.services.machine_service import (
    MachineService,
)
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
    MachineMapper,
)
from src.services.master_import.runtime.machine_import_config import (
    database_machine_to_dict,
    machine_entity_key,
    machine_entity_to_service_data,
)
from src.services.master_import.transaction import (
    SQLAlchemyTransactionManager,
)


def build_machine_import_engine(
    session,
) -> ImportEngine:
    if session is None:
        raise ValueError(
            "SQLAlchemy session is required."
        )

    machine_service = MachineService(
        session=session
    )

    detail_service = ImportDetailService(
        session=session,
        auto_commit=False,
    )

    importer = GenericMasterImporter(
        module_name="MACHINE",
        mapper=MachineMapper(),
        service=machine_service,
        save_method=(
            machine_service.save_machine
        ),
        get_method=(
            machine_service.get_machine
        ),
        entity_key_getter=(
            machine_entity_key
        ),
        entity_to_service_data=(
            machine_entity_to_service_data
        ),
        database_entity_to_dict=(
            database_machine_to_dict
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
        transaction_manager=(
            transaction_manager
        ),
    )