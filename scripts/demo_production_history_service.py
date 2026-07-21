from datetime import date

from src.services.production_history_service import (
    ProductionHistoryService,
)


service = ProductionHistoryService()

records = service.search(
    start_date=date(
        2026,
        7,
        1,
    ),
    end_date=date(
        2026,
        7,
        31,
    ),
)


print("=" * 90)
print("PRODUCTION HISTORY")
print("=" * 90)

print("Records:", len(records))


summary = service.build_summary(
    records
)

print()
print("SUMMARY")
print("-" * 90)

for key, value in summary.items():
    print(
        f"{key}: {value}"
    )


print()
print("BY MACHINE")
print("-" * 90)

for item in service.group_by_machine(
    records
):
    print(
        item["machine_code"],
        "OK:",
        item["ok_qty"],
        "NG:",
        item["ng_qty"],
        "Yield:",
        round(
            item["yield_percent"],
            2,
        ),
        "Runtime H:",
        round(
            item["runtime_hour"],
            2,
        ),
    )


print()
print("BY EMPLOYEE")
print("-" * 90)

for item in service.group_by_employee(
    records
):
    print(
        item["employee_code"],
        "OK:",
        item["ok_qty"],
        "NG:",
        item["ng_qty"],
        "Yield:",
        round(
            item["yield_percent"],
            2,
        ),
    )


print()
print("TOP NG PRODUCTS")
print("-" * 90)

for item in service.get_top_ng_products(
    records
):
    print(
        item["product_code"],
        "NG:",
        item["ng_qty"],
        "NG Rate:",
        round(
            item["ng_percent"],
            2,
        ),
    )


assert summary["record_count"] == len(
    records
)

assert summary["ok_qty"] >= 0
assert summary["ng_qty"] >= 0
assert summary["total_qty"] == (
    summary["ok_qty"]
    + summary["ng_qty"]
)

print()
print(
    "ProductionHistoryService test passed."
)