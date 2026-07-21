from datetime import date

from src.services.manufacturing_analytics_service import (
    ManufacturingAnalyticsService,
)


START_DATE = date(
    2026,
    7,
    1,
)

END_DATE = date(
    2026,
    7,
    31,
)


service = ManufacturingAnalyticsService()

analytics = service.build(
    start_date=START_DATE,
    end_date=END_DATE,
)


print("=" * 100)
print("MANUFACTURING ANALYTICS")
print("=" * 100)

print(
    "Period:",
    analytics["period"],
)

print(
    "Records:",
    analytics["record_count"],
)


print()
print("SUMMARY")
print("-" * 100)

for key, value in (
    analytics["summary"].items()
):
    print(
        f"{key}: {value}"
    )


print()
print("OEE")
print("-" * 100)

for key, value in (
    analytics["oee"].items()
):
    if key != "errors":
        print(
            f"{key}: {value}"
        )


print()
print("MACHINES")
print("-" * 100)

for item in analytics["machine"]:
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
        "OEE:",
        round(
            item["oee_percent"],
            2,
        ),
    )


print()
print("EMPLOYEES")
print("-" * 100)

for item in analytics["employee"]:
    print(
        item["employee_code"],
        "OK:",
        item["ok_qty"],
        "Efficiency:",
        round(
            item["efficiency_percent"],
            2,
        ),
    )


print()
print("PRODUCTS")
print("-" * 100)

for item in analytics["product"]:
    print(
        item["product_code"],
        "Total:",
        item["total_qty"],
        "Yield:",
        round(
            item["yield_percent"],
            2,
        ),
        "Cycle:",
        round(
            item[
                "actual_cycle_time_sec"
            ],
            3,
        ),
    )


print()
print("WORK ORDERS")
print("-" * 100)

for item in analytics[
    "work_order"
]:
    print(
        item["work_order_no"],
        "Plan:",
        item["plan_qty"],
        "Completed:",
        item["completed_qty"],
        "Progress:",
        round(
            item[
                "progress_percent"
            ],
            2,
        ),
    )


print()
print("TOP NG PRODUCTS")
print("-" * 100)

for item in analytics[
    "ng"
][
    "by_product"
][:10]:
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


summary = analytics["summary"]

assert summary["record_count"] == (
    analytics["record_count"]
)

assert summary["total_qty"] == (
    summary["ok_qty"]
    + summary["ng_qty"]
)

assert isinstance(
    analytics["machine"],
    list,
)

assert isinstance(
    analytics["employee"],
    list,
)

assert isinstance(
    analytics["product"],
    list,
)

assert isinstance(
    analytics["work_order"],
    list,
)

assert isinstance(
    analytics["daily"],
    list,
)

assert "by_product" in analytics["ng"]
assert "overall" in analytics["oee"]


print()
print(
    "ManufacturingAnalyticsService "
    "test passed."
)