from datetime import date

from src.services.oee_service import OEEService


MACHINE_CODE = "BL01"
PRODUCTION_DATE = date(2026, 7, 1)


service = OEEService()

result = service.calculate_machine_day(
    machine_code=MACHINE_CODE,
    production_date=PRODUCTION_DATE,
)

print("=" * 70)
print("OEE SERVICE")
print("=" * 70)

for item in result["items"]:
    print(
        item.machine_code,
        item.production_date,
        item.shift,
        "Availability:",
        round(item.availability_percent, 2),
        "Performance:",
        round(item.performance_percent, 2),
        "Quality:",
        round(item.quality_percent, 2),
        "OEE:",
        round(item.oee_percent, 2),
    )

print("Errors:", result["errors"])

assert not result["errors"], result["errors"]

print("OEEService test passed.")