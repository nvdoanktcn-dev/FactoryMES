from src.importer.generic_master_importer import GenericMasterImporter
from src.mapper.employee_mapper import EmployeeMapper
from src.schema.employee_schema import EmployeeSchema
from src.services.employee_service import EmployeeService


class EmployeeImporter(GenericMasterImporter):
    SCHEMA = EmployeeSchema
    MAPPER = EmployeeMapper
    SERVICE_CLASS = EmployeeService
    SAVE_METHOD = "save_employee"