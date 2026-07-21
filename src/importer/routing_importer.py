from src.importer.generic_master_importer import (
    GenericMasterImporter,
)
from src.mapper.routing_mapper import RoutingMapper
from src.schema.routing_schema import RoutingSchema
from src.services.routing_service import RoutingService
from src.validator.routing_validator import RoutingValidator


class RoutingImporter(GenericMasterImporter):
    """
    Routing Master Importer.
    """

    SCHEMA = RoutingSchema
    MAPPER = RoutingMapper
    SERVICE_CLASS = RoutingService
    SAVE_METHOD = "save_routing"

    def __init__(self):
        super().__init__()

        self.routing_validator = RoutingValidator(
            self.service.session
        )

    def preview(self, filename):
        preview = super().preview(filename)

        records, mapping_errors = (
            self.MAPPER.from_dataframe(
                preview["dataframe"]
            )
        )

        file_errors = (
            self.routing_validator
            .validate_dataframe_records(records)
        )

        existing_errors = list(
            preview["result"].errors
        )

        combined_errors = (
            existing_errors
            + mapping_errors
            + file_errors
        )

        preview["records"] = records
        preview["errors"] = combined_errors

        return preview