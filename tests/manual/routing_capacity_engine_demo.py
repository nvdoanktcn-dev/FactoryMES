from types import SimpleNamespace

from src.engine.routing_capacity_engine import (
    RoutingCapacityEngine,
)


routing = [
    SimpleNamespace(
        product_code="P001",
        op_no="OP10",
        sequence=10,
        machine_code="BL01",
        machine_type="CNC",
        cycle_time_sec=20,
    ),
    SimpleNamespace(
        product_code="P001",
        op_no="OP20",
        sequence=20,
        machine_code="BL02",
        machine_type="CNC",
        cycle_time_sec=80,
    ),
    SimpleNamespace(
        product_code="P001",
        op_no="OP30",
        sequence=30,
        machine_code="BR01",
        machine_type="ROBOT",
        cycle_time_sec=40,
    ),
]


available_machine_counts = {
    # Có thể khai báo theo mã máy.
    "BL01": 1,
    "BL02": 2,

    # Hoặc theo loại máy.
    "ROBOT": 2,
}


engine = RoutingCapacityEngine()

items = engine.calculate(
    routing_list=routing,
    available_machine_counts=(
        available_machine_counts
    ),
)


print("=" * 100)
print("ROUTING CAPACITY")
print("=" * 100)

for item in items:
    print(
        f"{item.op_no:<8}",
        f"Capacity={item.capacity_per_hour:>8.2f}",
        f"Need={item.required_machine_count:>6.2f}",
        f"NeedInt={item.required_machine_count_int:>3}",
        f"Available={item.available_machine_count:>3}",
        f"Shortage={item.machine_shortage:>3}",
        f"Ratio={item.capacity_ratio:>7.2f}%",
        f"Rank={item.bottleneck_rank:>2}",
        f"Bottleneck={item.is_bottleneck}",
        f"Status={item.capacity_status}",
    )


assert round(
    items[0].capacity_per_hour,
    2,
) == 180.0

assert items[0].required_machine_count_int == 1
assert items[0].machine_shortage == 0

assert round(
    items[1].capacity_per_hour,
    2,
) == 45.0

assert round(
    items[1].required_machine_count,
    2,
) == 4.0

assert items[1].required_machine_count_int == 4
assert items[1].available_machine_count == 2
assert items[1].machine_shortage == 2
assert items[1].is_bottleneck is True
assert items[1].bottleneck_rank == 1

assert round(
    items[2].capacity_per_hour,
    2,
) == 90.0

assert items[2].required_machine_count_int == 2
assert items[2].available_machine_count == 2
assert items[2].machine_shortage == 0


summary = engine.calculate_summary(
    routing_list=routing,
    available_machine_counts=(
        available_machine_counts
    ),
)

print()
print("=" * 100)
print("ROUTING SUMMARY")
print("=" * 100)

for key, value in summary.items():
    if key != "items":
        print(
            f"{key}: {value}"
        )


assert summary["product_code"] == "P001"
assert summary["operation_count"] == 3
assert summary["bottleneck_op"] == "OP20"
assert summary["total_required_machine_count"] == 7
assert summary["total_available_machine_count"] == 5
assert summary["total_machine_shortage"] == 2
assert summary["has_machine_shortage"] is True


print()
print(
    "RoutingCapacityEngine test passed."
)