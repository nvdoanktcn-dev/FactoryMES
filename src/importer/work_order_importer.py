from src.importer.generic_master_importer import (
    GenericMasterImporter,
)

from src.mapper.work_order_mapper import (
    WorkOrderMapper,
)

from src.schema.work_order_schema import (
    WorkOrderSchema,
)

from src.services.work_order_service import (
    WorkOrderService,
)

from src.validator.work_order_validator import (
    WorkOrderValidator,
)


class WorkOrderImporter(GenericMasterImporter):
    """
    Work Order Master Importer.
    """

    SCHEMA = WorkOrderSchema

    MAPPER = WorkOrderMapper

    SERVICE_CLASS = WorkOrderService

    SAVE_METHOD = "save_work_order"

    def __init__(self):
        super().__init__()

        self.validator = WorkOrderValidator(
            self.service.session
        )

    def preview(self, filename):

        preview = super().preview(
            filename
        )

        records, mapper_errors = (
            self.MAPPER.from_dataframe(
                preview["dataframe"]
            )
        )

        validator_errors = (
            self.validator
            .validate_dataframe_records(
                records
            )
        )

        preview["records"] = records

        preview["errors"] = (
            list(preview["result"].errors)
            + mapper_errors
            + validator_errors
        )

        return preview