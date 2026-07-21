from src.dto.chart_data import (
    BarChartData,
    ChartSeries,
    LineChartData,
    ParetoChartData,
)


class DashboardChartService:
    """
    Chuyển Manufacturing Analytics thành ChartData.

    Chart Widget không hiểu Product, Machine,
    Employee hoặc Production Log.

    Chart Widget chỉ nhận:
        labels
        values
        series
        title
        unit
    """

    def build(self, analytics):
        """
        Tạo toàn bộ dữ liệu biểu đồ Dashboard.
        """
        return {
            "daily_output":
                self.build_daily_output_chart(
                    analytics
                ),

            "daily_quality":
                self.build_daily_quality_chart(
                    analytics
                ),

            "oee_trend":
                self.build_oee_trend_chart(
                    analytics
                ),

            "machine_ranking":
                self.build_machine_ranking_chart(
                    analytics
                ),

            "employee_ranking":
                self.build_employee_ranking_chart(
                    analytics
                ),

            "ng_pareto":
                self.build_ng_pareto_chart(
                    analytics
                ),
        }

    # ==========================================================
    # Daily Output
    # ==========================================================

    def build_daily_output_chart(
        self,
        analytics,
    ):
        daily = self._section(
            analytics,
            "daily",
            [],
        )

        labels = [
            self._format_date_label(
                self._value(
                    item,
                    "production_date",
                    "",
                )
            )
            for item in daily
        ]

        ok_values = [
            self._number(
                self._value(
                    item,
                    "ok_qty",
                    0,
                )
            )
            for item in daily
        ]

        ng_values = [
            self._number(
                self._value(
                    item,
                    "ng_qty",
                    0,
                )
            )
            for item in daily
        ]

        total_values = [
            self._number(
                self._value(
                    item,
                    "total_qty",
                    (
                        ok_values[index]
                        + ng_values[index]
                    ),
                )
            )
            for index, item in enumerate(
                daily
            )
        ]

        return LineChartData(
            title="Daily Output Trend",
            labels=labels,
            series=[
                ChartSeries(
                    name="Total Qty",
                    values=total_values,
                    unit="PCS",
                ),
                ChartSeries(
                    name="OK Qty",
                    values=ok_values,
                    unit="PCS",
                ),
                ChartSeries(
                    name="NG Qty",
                    values=ng_values,
                    unit="PCS",
                ),
            ],
            x_label="Production Date",
            y_label="Quantity",
            unit="PCS",
            show_legend=True,
            show_markers=True,
        )

    # ==========================================================
    # Daily Quality
    # ==========================================================

    def build_daily_quality_chart(
        self,
        analytics,
    ):
        daily = self._section(
            analytics,
            "daily",
            [],
        )

        labels = [
            self._format_date_label(
                self._value(
                    item,
                    "production_date",
                    "",
                )
            )
            for item in daily
        ]

        yield_values = [
            self._number(
                self._value(
                    item,
                    "yield_percent",
                    0,
                )
            )
            for item in daily
        ]

        ng_percent_values = [
            self._number(
                self._value(
                    item,
                    "ng_percent",
                    0,
                )
            )
            for item in daily
        ]

        return LineChartData(
            title="Daily Quality Trend",
            labels=labels,
            series=[
                ChartSeries(
                    name="Yield",
                    values=yield_values,
                    unit="%",
                ),
                ChartSeries(
                    name="NG Rate",
                    values=ng_percent_values,
                    unit="%",
                ),
            ],
            x_label="Production Date",
            y_label="Percent",
            unit="%",
            show_legend=True,
            show_markers=True,
        )

    # ==========================================================
    # OEE Trend
    # ==========================================================

    def build_oee_trend_chart(
        self,
        analytics,
    ):
        daily = self._section(
            analytics,
            "daily",
            [],
        )

        labels = [
            self._format_date_label(
                self._value(
                    item,
                    "production_date",
                    "",
                )
            )
            for item in daily
        ]

        availability_values = [
            self._number(
                self._value(
                    item,
                    "availability_percent",
                    0,
                )
            )
            for item in daily
        ]

        quality_values = [
            self._number(
                self._value(
                    item,
                    "yield_percent",
                    0,
                )
            )
            for item in daily
        ]

        performance_values = [
            self._number(
                self._value(
                    item,
                    "performance_percent",
                    (
                        100.0
                        if self._number(
                            self._value(
                                item,
                                "total_qty",
                                0,
                            )
                        )
                        > 0
                        else 0.0
                    ),
                )
            )
            for item in daily
        ]

        oee_values = [
            (
                availability_values[index]
                * performance_values[index]
                * quality_values[index]
                / 10000
            )
            for index in range(
                len(labels)
            )
        ]

        return LineChartData(
            title="Daily OEE Trend",
            labels=labels,
            series=[
                ChartSeries(
                    name="Availability",
                    values=availability_values,
                    unit="%",
                ),
                ChartSeries(
                    name="Performance",
                    values=performance_values,
                    unit="%",
                ),
                ChartSeries(
                    name="Quality",
                    values=quality_values,
                    unit="%",
                ),
                ChartSeries(
                    name="OEE",
                    values=oee_values,
                    unit="%",
                ),
            ],
            x_label="Production Date",
            y_label="Percent",
            unit="%",
            show_legend=True,
            show_markers=True,
        )

    # ==========================================================
    # Machine Ranking
    # ==========================================================

    def build_machine_ranking_chart(
        self,
        analytics,
        limit=10,
    ):
        machine = list(
            self._section(
                analytics,
                "machine",
                [],
            )
            or []
        )

        ranked = sorted(
            machine,
            key=lambda item:
                self._number(
                    self._value(
                        item,
                        "ok_qty",
                        0,
                    )
                ),
            reverse=True,
        )[:limit]

        return BarChartData(
            title="Machine Output Ranking",
            labels=[
                str(
                    self._value(
                        item,
                        "machine_code",
                        "",
                    )
                )
                for item in ranked
            ],
            values=[
                self._number(
                    self._value(
                        item,
                        "ok_qty",
                        0,
                    )
                )
                for item in ranked
            ],
            x_label="OK Quantity",
            y_label="Machine",
            unit="PCS",
            horizontal=True,
            show_values=True,
        )

    # ==========================================================
    # Employee Ranking
    # ==========================================================

    def build_employee_ranking_chart(
        self,
        analytics,
        limit=10,
    ):
        employees = list(
            self._section(
                analytics,
                "employee",
                [],
            )
            or []
        )

        ranked = sorted(
            employees,
            key=lambda item:
                self._number(
                    self._value(
                        item,
                        "ok_qty",
                        0,
                    )
                ),
            reverse=True,
        )[:limit]

        return BarChartData(
            title="Employee Output Ranking",
            labels=[
                str(
                    self._value(
                        item,
                        "employee_code",
                        "",
                    )
                )
                for item in ranked
            ],
            values=[
                self._number(
                    self._value(
                        item,
                        "ok_qty",
                        0,
                    )
                )
                for item in ranked
            ],
            x_label="OK Quantity",
            y_label="Employee",
            unit="PCS",
            horizontal=True,
            show_values=True,
        )

    # ==========================================================
    # NG Pareto
    # ==========================================================

    def build_ng_pareto_chart(
        self,
        analytics,
        limit=10,
    ):
        ng_section = self._section(
            analytics,
            "ng",
            {},
        )

        by_product = list(
            self._section(
                ng_section,
                "by_product",
                [],
            )
            or []
        )

        ranked = sorted(
            by_product,
            key=lambda item:
                self._number(
                    self._value(
                        item,
                        "ng_qty",
                        0,
                    )
                ),
            reverse=True,
        )

        ranked = [
            item
            for item in ranked
            if self._number(
                self._value(
                    item,
                    "ng_qty",
                    0,
                )
            )
            > 0
        ][:limit]

        labels = [
            str(
                self._value(
                    item,
                    "product_code",
                    "",
                )
            )
            for item in ranked
        ]

        values = [
            self._number(
                self._value(
                    item,
                    "ng_qty",
                    0,
                )
            )
            for item in ranked
        ]

        cumulative_percent = (
            self.calculate_cumulative_percent(
                values
            )
        )

        return ParetoChartData(
            title="NG Pareto by Product",
            labels=labels,
            values=values,
            cumulative_percent=(
                cumulative_percent
            ),
            value_unit="PCS",
            percent_unit="%",
            threshold_percent=80.0,
        )

    # ==========================================================
    # Pareto helper
    # ==========================================================

    @staticmethod
    def calculate_cumulative_percent(
        values,
    ):
        normalized_values = [
            max(
                float(value or 0),
                0.0,
            )
            for value in values
        ]

        total = sum(
            normalized_values
        )

        if total <= 0:
            return [
                0.0
                for _ in normalized_values
            ]

        running_total = 0.0
        result = []

        for value in normalized_values:
            running_total += value

            result.append(
                running_total
                / total
                * 100
            )

        return result

    # ==========================================================
    # Helpers
    # ==========================================================

    @staticmethod
    def _section(
        source,
        field_name,
        default,
    ):
        if source is None:
            return default

        if isinstance(source, dict):
            return source.get(
                field_name,
                default,
            )

        return getattr(
            source,
            field_name,
            default,
        )

    @staticmethod
    def _value(
        source,
        field_name,
        default,
    ):
        if source is None:
            return default

        if isinstance(source, dict):
            value = source.get(
                field_name,
                default,
            )

        else:
            value = getattr(
                source,
                field_name,
                default,
            )

        if value is None:
            return default

        return value

    @staticmethod
    def _number(value):
        try:
            return float(
                value or 0
            )

        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    @staticmethod
    def _format_date_label(value):
        if value is None:
            return ""

        if hasattr(
            value,
            "strftime",
        ):
            return value.strftime(
                "%m-%d"
            )

        text = str(value)

        if len(text) >= 10:
            return text[5:10]

        return text