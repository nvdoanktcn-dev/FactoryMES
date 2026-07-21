from __future__ import annotations

from src.database.session import get_session
from src.services.employee_service import EmployeeService
from src.services.machine_service import MachineService
from src.services.master_import.import_detail_service import ImportDetailService
from src.services.master_import.import_log_service import ImportLogService
from src.services.product_service import ProductService
from src.services.routing_service import RoutingService
from src.services.work_order_service import WorkOrderService
from datetime import date, datetime


class RollbackService:
    STATUS_SUCCESS = "SUCCESS"
    STATUS_ROLLED_BACK = "ROLLED_BACK"

    SUPPORTED_MODULES = {
        "PRODUCT",
        "MACHINE",
        "EMPLOYEE",
        "ROUTING",
        "WORK_ORDER",
    }

    def __init__(self, session=None):
        self._owns_session = session is None
        self.session = session or get_session()

        self.product_service = ProductService(session=self.session)
        self.machine_service = MachineService(session=self.session)
        self.employee_service = EmployeeService(session=self.session)
        self.routing_service = RoutingService(session=self.session)

        self.detail_service = ImportDetailService(
            session=self.session,
            auto_commit=False,
        )
        self.log_service = ImportLogService(
            session=self.session,
            auto_commit=False,
        )
        self.work_order_service = WorkOrderService(session=self.session)

    # ==========================================================
    # Public API
    # ==========================================================

    def rollback_import(self, log_id):
        log = self.log_service.get_by_id(log_id)

        if log is None:
            raise ValueError(f"Import Log not found: {log_id}")

        status = self._normalize_upper(log.status)

        if status == self.STATUS_ROLLED_BACK:
            raise ValueError("This import has already been rolled back.")

        if status != self.STATUS_SUCCESS:
            raise ValueError(
                f"Only SUCCESS imports can be rolled back. Current status: {status}"
            )

        module_name = self._normalize_upper(log.module)

        if module_name not in self.SUPPORTED_MODULES:
            raise NotImplementedError(
                f"Rollback for module '{module_name}' is not implemented."
            )

        details = self.detail_service.get_by_log_id(
            log_id,
            reverse=True,
        )

        if not details:
            raise ValueError(f"No ImportDetail records found for log {log_id}.")

        deleted_rows = 0
        restored_rows = 0

        try:
            for detail in details:
                result = self._rollback_detail(
                    module_name=module_name,
                    action=self._normalize_upper(detail.action),
                    entity_key=self._normalize_upper(detail.entity_key),
                    old_json=detail.old_json,
                )

                deleted_rows += result["deleted_rows"]
                restored_rows += result["restored_rows"]

            message = (
                "Rollback completed: "
                f"{deleted_rows} inserted row(s) deleted, "
                f"{restored_rows} updated row(s) restored."
            )

            self.log_service.update_log(
                log_id,
                status=self.STATUS_ROLLED_BACK,
                message=message,
            )

            self.session.commit()

            return {
                "success": True,
                "log_id": int(log_id),
                "module": module_name,
                "deleted_rows": deleted_rows,
                "restored_rows": restored_rows,
                "message": (
                    "Rollback completed: "
                    f"{deleted_rows} deleted, "
                    f"{restored_rows} restored."
                ),
            }

        except Exception:
            self.session.rollback()
            raise

        finally:
            if self._owns_session:
                self.session.close()

    # ==========================================================
    # Dispatcher
    # ==========================================================

    def _rollback_detail(
        self,
        *,
        module_name,
        action,
        entity_key,
        old_json,
    ):
        if module_name == "PRODUCT":
            return self._rollback_product_detail(
                action=action,
                entity_key=entity_key,
                old_json=old_json,
            )

        if module_name == "MACHINE":
            return self._rollback_machine_detail(
                action=action,
                entity_key=entity_key,
                old_json=old_json,
            )

        if module_name == "EMPLOYEE":
            return self._rollback_employee_detail(
                action=action,
                entity_key=entity_key,
                old_json=old_json,
            )

        if module_name == "ROUTING":
            return self._rollback_routing_detail(
                action=action,
                entity_key=entity_key,
                old_json=old_json,
            )

        if module_name == "WORK_ORDER":
            return self._rollback_work_order_detail(
                action=action,
                entity_key=entity_key,
                old_json=old_json,
            )

        raise NotImplementedError(
            f"Rollback dispatcher missing for module '{module_name}'."
        )

    # ==========================================================
    # Product rollback
    # ==========================================================

    def _rollback_product_detail(
        self,
        *,
        action,
        entity_key,
        old_json,
    ):
        if action == "INSERT":
            deleted = self._undo_product_insert(entity_key)
            return {
                "deleted_rows": 1 if deleted else 0,
                "restored_rows": 0,
            }

        if action == "UPDATE":
            self._undo_product_update(old_json)
            return {
                "deleted_rows": 0,
                "restored_rows": 1,
            }

        raise ValueError(
            f"Unsupported Product rollback action '{action}' for '{entity_key}'."
        )

    def _undo_product_insert(self, product_code):
        product = self.product_service.get_product(product_code)

        if product is None:
            return False

        self.session.delete(product)
        self.session.flush()
        return True

    def _undo_product_update(self, old_json):
        old_data = self.detail_service.from_json(old_json)

        if not old_data:
            raise ValueError("Missing old_json for Product UPDATE rollback.")

        product_code = self._normalize_upper(old_data.get("product_code"))

        if not product_code:
            raise ValueError("Missing product_code in Product old_json.")

        product = self.product_service.get_product(product_code)

        if product is None:
            raise ValueError(
                f"Cannot restore Product because it no longer exists: {product_code}"
            )

        product.product_name_vi = old_data.get("product_name_vi")
        product.product_name_cn = old_data.get("product_name_cn")
        product.customer = old_data.get("customer")
        product.material = old_data.get("material")
        product.unit = old_data.get("unit")
        product.status = old_data.get("status")

        self.session.flush()

    # ==========================================================
    # Machine rollback
    # ==========================================================

    def _rollback_machine_detail(
        self,
        *,
        action,
        entity_key,
        old_json,
    ):
        if action == "INSERT":
            deleted = self._undo_machine_insert(entity_key)
            return {
                "deleted_rows": 1 if deleted else 0,
                "restored_rows": 0,
            }

        if action == "UPDATE":
            self._undo_machine_update(old_json)
            return {
                "deleted_rows": 0,
                "restored_rows": 1,
            }

        raise ValueError(
            f"Unsupported Machine rollback action '{action}' for '{entity_key}'."
        )

    def _undo_machine_insert(self, machine_code):
        machine = self.machine_service.get_machine(machine_code)

        if machine is None:
            return False

        self.session.delete(machine)
        self.session.flush()
        return True

    def _undo_machine_update(self, old_json):
        old_data = self.detail_service.from_json(old_json)

        if not old_data:
            raise ValueError("Missing old_json for Machine UPDATE rollback.")

        machine_code = self._normalize_upper(old_data.get("machine_code"))

        if not machine_code:
            raise ValueError("Missing machine_code in Machine old_json.")

        machine = self.machine_service.get_machine(machine_code)

        if machine is None:
            raise ValueError(
                f"Cannot restore Machine because it no longer exists: {machine_code}"
            )

        machine.machine_name = old_data.get("machine_name")
        machine.machine_type = old_data.get("machine_type")
        machine.line = old_data.get("line")
        machine.location = old_data.get("location")
        machine.brand = old_data.get("brand")
        machine.model = old_data.get("model")
        machine.serial_number = old_data.get("serial_number")
        machine.status = old_data.get("status")

        self.session.flush()

    # ==========================================================
    # Employee rollback
    # ==========================================================

    def _rollback_employee_detail(
        self,
        *,
        action,
        entity_key,
        old_json,
    ):
        if action == "INSERT":
            deleted = self._undo_employee_insert(entity_key)
            return {
                "deleted_rows": 1 if deleted else 0,
                "restored_rows": 0,
            }

        if action == "UPDATE":
            self._undo_employee_update(old_json)
            return {
                "deleted_rows": 0,
                "restored_rows": 1,
            }

        raise ValueError(
            f"Unsupported Employee rollback action '{action}' for '{entity_key}'."
        )

    def _undo_employee_insert(self, employee_code):
        employee = self.employee_service.get_employee(employee_code)

        if employee is None:
            return False

        self.session.delete(employee)
        self.session.flush()
        return True

    def _undo_employee_update(self, old_json):
        old_data = self.detail_service.from_json(old_json)

        if not old_data:
            raise ValueError("Missing old_json for Employee UPDATE rollback.")

        employee_code = self._normalize_upper(old_data.get("employee_code"))

        if not employee_code:
            raise ValueError("Missing employee_code in Employee old_json.")

        employee = self.employee_service.get_employee(employee_code)

        if employee is None:
            raise ValueError(
                f"Cannot restore Employee because it no longer exists: {employee_code}"
            )

        employee.employee_name = old_data.get("employee_name")
        employee.department = old_data.get("department")
        employee.position = old_data.get("position")
        employee.shift = old_data.get("shift")
        employee.status = old_data.get("status")
        employee.remark = old_data.get("remark")

        self.session.flush()

    # ==========================================================
    # Routing rollback
    # ==========================================================

    def _rollback_routing_detail(
        self,
        *,
        action,
        entity_key,
        old_json,
    ):
        if action == "INSERT":
            deleted = self._undo_routing_insert(entity_key)
            return {
                "deleted_rows": 1 if deleted else 0,
                "restored_rows": 0,
            }

        if action == "UPDATE":
            self._undo_routing_update(old_json)
            return {
                "deleted_rows": 0,
                "restored_rows": 1,
            }

        raise ValueError(
            f"Unsupported Routing rollback action '{action}' for '{entity_key}'."
        )

    def _undo_routing_insert(self, entity_key):
        product_code, operation_no = self._parse_routing_key(entity_key)

        routing = self.routing_service.get_routing(
            product_code,
            operation_no,
        )

        if routing is None:
            return False

        self.session.delete(routing)
        self.session.flush()
        return True

    def _undo_routing_update(self, old_json):
        old_data = self.detail_service.from_json(old_json)

        if not old_data:
            raise ValueError("Missing old_json for Routing UPDATE rollback.")

        product_code = self._normalize_upper(old_data.get("product_code"))
        operation_no = old_data.get("operation_no")

        if not product_code:
            raise ValueError("Missing product_code in Routing old_json.")

        if operation_no is None:
            raise ValueError("Missing operation_no in Routing old_json.")

        try:
            operation_no = int(operation_no)
        except (TypeError, ValueError) as error:
            raise ValueError(
                "Invalid operation_no in Routing old_json."
            ) from error

        routing = self.routing_service.get_routing(
            product_code,
            operation_no,
        )

        if routing is None:
            raise ValueError(
                "Cannot restore Routing because it no longer exists: "
                f"{product_code}|{operation_no}"
            )

        routing.operation_name = old_data.get("operation_name")
        routing.process_type = old_data.get("process_type")
        routing.machine_type = old_data.get("machine_type")
        routing.standard_cycle_time_sec = old_data.get("standard_cycle_time_sec")
        routing.standard_output_pcs_hour = old_data.get("standard_output_pcs_hour")
        routing.standard_operator_count = old_data.get("standard_operator_count")
        routing.status = old_data.get("status")
        routing.remark = old_data.get("remark")

        self.session.flush()

    # ==========================================================
    # Work Order rollback
    # ==========================================================

    def _rollback_work_order_detail(
        self,
        *,
        action,
        entity_key,
        old_json,
    ):
        if action == "INSERT":
            deleted = self._undo_work_order_insert(entity_key)
            return {
                "deleted_rows": 1 if deleted else 0,
                "restored_rows": 0,
            }

        if action == "UPDATE":
            self._undo_work_order_update(old_json)
            return {
                "deleted_rows": 0,
                "restored_rows": 1,
            }

        raise ValueError(
            f"Unsupported Work Order rollback action '{action}' for '{entity_key}'."
        )

    def _undo_work_order_insert(self, work_order_no):
        work_order = self.work_order_service.get_work_order(work_order_no)

        if work_order is None:
            return False

        self.session.delete(work_order)
        self.session.flush()
        return True

    def _undo_work_order_update(self, old_json):
        old_data = self.detail_service.from_json(old_json)

        if not old_data:
            raise ValueError("Missing old_json for Work Order UPDATE rollback.")

        work_order_no = self._normalize_upper(old_data.get("work_order_no"))

        if not work_order_no:
            raise ValueError("Missing work_order_no in Work Order old_json.")

        work_order = self.work_order_service.get_work_order(work_order_no)

        if work_order is None:
            raise ValueError(
                f"Cannot restore Work Order because it no longer exists: {work_order_no}"
            )

        work_order.product_code = old_data.get("product_code")
        work_order.plan_qty = old_data.get("plan_qty")
        work_order.start_date = self._restore_date(old_data.get("start_date"))
        work_order.due_date = self._restore_date(old_data.get("due_date"))
        work_order.priority = old_data.get("priority")
        work_order.status = old_data.get("status")
        work_order.remark = old_data.get("remark")

        self.session.flush()

    # ==========================================================
    # Helpers
    # ==========================================================

    @staticmethod
    def _parse_routing_key(entity_key):
        text = str(entity_key or "").strip().upper()

        if "|" not in text:
            raise ValueError(f"Invalid Routing entity key: {entity_key}")

        product_code, operation_text = text.split("|", 1)
        product_code = product_code.strip()

        if not product_code:
            raise ValueError("Routing Product Code is empty.")

        try:
            operation_no = int(operation_text.strip())
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Invalid Routing Operation No in key: {entity_key}"
            ) from error

        if operation_no <= 0:
            raise ValueError("Routing Operation No must be greater than zero.")

        return product_code, operation_no

    @staticmethod
    def _restore_date(value):
        if value is None:
            return None

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        text = str(value).strip()

        if not text:
            return None

        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d",
        ]

        for date_format in formats:
            try:
                return datetime.strptime(text, date_format).date()
            except ValueError:
                continue

        try:
            return datetime.fromisoformat(text).date()
        except ValueError as error:
            raise ValueError(
                f"Invalid date value in Work Order rollback data: {value}"
            ) from error

    @staticmethod
    def _normalize_upper(value):
        return str(value or "").strip().upper()