from src.importer.generic_master_importer import (
    GenericMasterImporter,
)

from src.mapper.machine_mapper import (
    MachineMapper,
)

from src.schema.machine_schema import (
    MachineSchema,
)

from src.services.machine_service import (
    MachineService,
)


class MachineImporter(GenericMasterImporter):
    """
    Machine Master Importer
    """

    SCHEMA = MachineSchema

    MAPPER = MachineMapper

    SERVICE_CLASS = MachineService

    SAVE_METHOD = "save_machine"