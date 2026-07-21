from src.services.production_entry_lookup_service import (
    ProductionEntryLookupService,
)


WORK_ORDER_NO = "WO202607001"


service = ProductionEntryLookupService()

context = service.build_entry_context(
    WORK_ORDER_NO
)

work_order = context["work_order"]
routings = context["routings"]
employees = context["employees"]

print("=" * 80)
print("PRODUCTION ENTRY LOOKUP")
print("=" * 80)

print("Work Order :", work_order.work_order_no)
print("Product    :", context["product_code"])
print("Status     :", work_order.status)
print("Routing OP :", len(routings))
print("Employees  :", len(employees))

print()
print("ROUTING")

for routing in routings:
    print(
        routing.sequence,
        routing.op_no,
        routing.machine_code,
        routing.machine_type,
        routing.cycle_time_sec,
    )

assert work_order.work_order_no == WORK_ORDER_NO
assert len(routings) > 0
assert len(employees) > 0


first_op = routings[0].op_no

machines = service.get_machines_for_operation(
    WORK_ORDER_NO,
    first_op,
)

print()
print("SELECTED OP :", first_op)
print("MACHINES")

for machine in machines:
    print(
        machine.machine_code,
        machine.machine_name,
        machine.machine_type,
        machine.status,
    )

assert len(machines) > 0

print()
print(
    "ProductionEntryLookupService test passed."
)