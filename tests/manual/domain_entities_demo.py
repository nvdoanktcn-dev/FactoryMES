from src.domain.entities import (
    Employee,
    Machine,
    Product,
    Routing,
    WorkOrder,
)

product = Product(
    product_code="P001",
    product_name="Housing",
)

machine = Machine(
    machine_code="BL01",
    machine_name="Brother",
    machine_type="CNC",
)

employee = Employee(
    employee_code="E001",
    employee_name="Nguyen Van A",
    department="CNC",
)

routing = Routing(
    routing_code="R001",
    product_code="P001",
    operation_no=10,
    machine_code="BL01",
    cycle_time=45,
)

work_order = WorkOrder(
    work_order="WO240001",
    product_code="P001",
    quantity=5000,
    plan_date="2026-07-13",
)

print(product.to_dict())
print(machine.to_dict())
print(employee.to_dict())
print(routing.to_dict())
print(work_order.to_dict())

print("Domain Entity OK")