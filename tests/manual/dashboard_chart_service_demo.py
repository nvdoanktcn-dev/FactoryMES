from datetime import date

from src.dto.chart_data import (
    BarChartData,
    LineChartData,
    ParetoChartData,
)
from src.services.dashboard_chart_service import (
    DashboardChartService,
)


analytics = {
    "daily": [
        {
            "production_date":
                date(2026, 7, 1),

            "ok_qty":
                900,

            "ng_qty":
                100,

            "total_qty":
                1000,

            "yield_percent":
                90.0,

            "ng_percent":
                10.0,

            "availability_percent":
                80.0,

            "performance_percent":
                95.0,
        },
        {
            "production_date":
                date(2026, 7, 2),

            "ok_qty":
                970,

            "ng_qty":
                30,

            "total_qty":
                1000,

            "yield_percent":
                97.0,

            "ng_percent":
                3.0,

            "availability_percent":
                90.0,

            "performance_percent":
                98.0,
        },
    ],

    "machine": [
        {
            "machine_code":
                "BL01",

            "ok_qty":
                1000,
        },
        {
            "machine_code":
                "BL02",

            "ok_qty":
                800,
        },
    ],

    "employee": [
        {
            "employee_code":
                "E001",

            "ok_qty":
                700,
        },
        {
            "employee_code":
                "E002",

            "ok_qty":
                900,
        },
    ],

    "ng": {
        "by_product": [
            {
                "product_code":
                    "P001",

                "ng_qty":
                    60,
            },
            {
                "product_code":
                    "P002",

                "ng_qty":
                    30,
            },
            {
                "product_code":
                    "P003",

                "ng_qty":
                    10,
            },
        ]
    },
}


service = DashboardChartService()

charts = service.build(
    analytics
)


print("=" * 90)
print("DASHBOARD CHART SERVICE")
print("=" * 90)


daily_output = charts[
    "daily_output"
]

print()
print("DAILY OUTPUT")
print(
    daily_output.labels
)

for series in daily_output.series:
    print(
        series.name,
        series.values,
    )


machine_ranking = charts[
    "machine_ranking"
]

print()
print("MACHINE RANKING")
print(
    machine_ranking.labels
)
print(
    machine_ranking.values
)


employee_ranking = charts[
    "employee_ranking"
]

print()
print("EMPLOYEE RANKING")
print(
    employee_ranking.labels
)
print(
    employee_ranking.values
)


pareto = charts[
    "ng_pareto"
]

print()
print("NG PARETO")
print(
    pareto.labels
)
print(
    pareto.values
)
print(
    pareto.cumulative_percent
)


assert isinstance(
    daily_output,
    LineChartData,
)

assert isinstance(
    machine_ranking,
    BarChartData,
)

assert isinstance(
    employee_ranking,
    BarChartData,
)

assert isinstance(
    pareto,
    ParetoChartData,
)


assert daily_output.labels == [
    "07-01",
    "07-02",
]

assert machine_ranking.labels == [
    "BL01",
    "BL02",
]

assert employee_ranking.labels == [
    "E002",
    "E001",
]

assert pareto.labels == [
    "P001",
    "P002",
    "P003",
]

assert [
    round(value, 2)
    for value
    in pareto.cumulative_percent
] == [
    60.0,
    90.0,
    100.0,
]


print()
print(
    "DashboardChartService test passed."
)