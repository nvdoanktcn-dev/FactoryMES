from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Callable

from src.ui.controllers.oee_pareto_dashboard_controller import (
    OEEParetoDashboardController,
    OEEParetoDashboardData,
)


def assert_equal(
    actual: Any,
    expected: Any,
    message: str,
) -> None:
    if actual != expected:
        raise AssertionError(
            f"{message}\nExpected: {expected!r}\nActual:   {actual!r}"
        )


def assert_true(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def assert_is(
    actual: Any,
    expected: Any,
    message: str,
) -> None:
    if actual is not expected:
        raise AssertionError(
            f"{message}\nExpected identity: {expected!r}\n"
            f"Actual:            {actual!r}"
        )


def assert_raises(
    expected_exception: type[BaseException],
    action: Callable[[], object],
    message: str,
) -> None:
    try:
        action()
    except expected_exception:
        return
    except Exception as error:
        raise AssertionError(
            f"{message}\nExpected: {expected_exception.__name__}\n"
            f"Actual:   {type(error).__name__}: {error}"
        ) from error

    raise AssertionError(
        f"{message}\nExpected exception: "
        f"{expected_exception.__name__}"
    )


@dataclass(frozen=True)
class FakeDashboardFilters:
    start_date: date | None = None
    end_date: date | None = None
    machine_code: str | None = None
    employee_code: str | None = None
    work_order_no: str | None = None
    product_code: str | None = None

    def normalized(self) -> "FakeDashboardFilters":
        return FakeDashboardFilters(
            start_date=self.start_date,
            end_date=self.end_date,
            machine_code=self._clean(self.machine_code),
            employee_code=self._clean(self.employee_code),
            work_order_no=self._clean(self.work_order_no),
            product_code=self._clean(self.product_code),
        )

    @staticmethod
    def _clean(value: str | None) -> str | None:
        if value is None:
            return None

        text = str(value).strip()
        return text or None


class FakeSession:
    def __init__(
        self,
        *,
        rollback_error: Exception | None = None,
    ) -> None:
        self.rollback_count = 0
        self.close_count = 0
        self.rollback_error = rollback_error

    def rollback(self) -> None:
        self.rollback_count += 1

        if self.rollback_error is not None:
            raise self.rollback_error

    def close(self) -> None:
        self.close_count += 1


class FakeSessionFactory:
    def __init__(self) -> None:
        self.sessions: list[FakeSession] = []

    def __call__(self) -> FakeSession:
        session = FakeSession()
        self.sessions.append(session)
        return session


class FakeParetoService:
    def __init__(self) -> None:
        self.downtime_calls: list[dict[str, Any]] = []
        self.ng_calls: list[dict[str, Any]] = []
        self.downtime_result = object()
        self.ng_result = object()
        self.downtime_error: Exception | None = None
        self.ng_error: Exception | None = None

    def build_downtime_pareto(
        self,
        records: list[dict[str, Any]],
        **kwargs: Any,
    ) -> object:
        self.downtime_calls.append(
            {
                "records": records,
                **kwargs,
            }
        )

        if self.downtime_error is not None:
            raise self.downtime_error

        return self.downtime_result

    def build_ng_pareto(
        self,
        records: list[dict[str, Any]],
        **kwargs: Any,
    ) -> object:
        self.ng_calls.append(
            {
                "records": records,
                **kwargs,
            }
        )

        if self.ng_error is not None:
            raise self.ng_error

        return self.ng_result


@dataclass
class DowntimeObject:
    reason_name: str
    downtime_minutes: float
    start_time: datetime
    machine_code: str
    employee_code: str
    work_order_no: str
    product_code: str


@dataclass
class NGObject:
    defect_reason: str
    defect_quantity: int
    recorded_at: datetime
    machine_code: str
    operator_code: str
    work_order_no: str
    item_code: str


def make_controller(
    *,
    session_factory: FakeSessionFactory | None = None,
    service: FakeParetoService | None = None,
    downtime_records: list[object] | None = None,
    ng_records: list[object] | None = None,
    maximum_items: int = 10,
    focus_threshold: float = 80.0,
) -> tuple[
    OEEParetoDashboardController,
    FakeSessionFactory,
    FakeParetoService,
]:
    factory = (
        session_factory
        if session_factory is not None
        else FakeSessionFactory()
    )
    pareto_service = (
        service
        if service is not None
        else FakeParetoService()
    )
    downtime_data = (
        downtime_records
        if downtime_records is not None
        else []
    )
    ng_data = (
        ng_records
        if ng_records is not None
        else []
    )

    controller = OEEParetoDashboardController(
        session_factory=factory,
        pareto_service=pareto_service,
        downtime_loader=lambda _session: list(downtime_data),
        ng_loader=lambda _session: list(ng_data),
        maximum_items=maximum_items,
        focus_threshold=focus_threshold,
    )

    return controller, factory, pareto_service


def test_constructor_validates_configuration() -> None:
    assert_raises(
        ValueError,
        lambda: make_controller(maximum_items=0),
        "maximum_items=0 must be rejected.",
    )
    assert_raises(
        ValueError,
        lambda: make_controller(focus_threshold=0),
        "focus_threshold=0 must be rejected.",
    )
    assert_raises(
        ValueError,
        lambda: make_controller(focus_threshold=100.01),
        "focus_threshold greater than 100 must be rejected.",
    )


def test_load_downtime_normalizes_records_and_options() -> None:
    record = DowntimeObject(
        reason_name="Chờ liệu",
        downtime_minutes=45,
        start_time=datetime(2026, 7, 2, 9, 30),
        machine_code="BL02",
        employee_code="NV02",
        work_order_no="WO02",
        product_code="SP02",
    )
    controller, factory, service = make_controller(
        downtime_records=[record],
        maximum_items=7,
        focus_threshold=75.0,
    )
    filters = FakeDashboardFilters(
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 31),
        machine_code=" BL02 ",
        employee_code=" NV02 ",
        work_order_no=" WO02 ",
        product_code=" SP02 ",
    )

    result = controller.load_downtime_pareto(filters)

    assert_is(
        result,
        service.downtime_result,
        "Controller returned the wrong downtime result.",
    )
    assert_equal(
        len(service.downtime_calls),
        1,
        "Downtime Pareto service must be called once.",
    )

    call = service.downtime_calls[0]
    normalized_record = call["records"][0]

    assert_equal(
        normalized_record["reason"],
        "Chờ liệu",
        "Downtime reason alias was not normalized.",
    )
    assert_equal(
        normalized_record["duration_minutes"],
        45,
        "Downtime duration alias was not normalized.",
    )
    assert_equal(
        normalized_record["production_date"],
        datetime(2026, 7, 2, 9, 30),
        "Downtime date alias was not normalized.",
    )
    assert_equal(
        normalized_record["work_order_code"],
        "WO02",
        "Work-order alias was not normalized.",
    )
    assert_equal(
        call["maximum_items"],
        7,
        "maximum_items was not forwarded.",
    )
    assert_equal(
        call["focus_threshold"],
        75.0,
        "focus_threshold was not forwarded.",
    )

    pareto_filter = call["filters"]
    assert_equal(
        pareto_filter.start_date,
        date(2026, 7, 1),
        "Start date filter is incorrect.",
    )
    assert_equal(
        pareto_filter.end_date,
        date(2026, 7, 31),
        "End date filter is incorrect.",
    )
    assert_equal(
        pareto_filter.machine_codes,
        ("BL02",),
        "Machine filter is incorrect.",
    )
    assert_equal(
        pareto_filter.employee_codes,
        ("NV02",),
        "Employee filter is incorrect.",
    )
    assert_equal(
        pareto_filter.work_order_codes,
        ("WO02",),
        "Work-order filter is incorrect.",
    )
    assert_equal(
        pareto_filter.product_codes,
        ("SP02",),
        "Product filter is incorrect.",
    )

    session = factory.sessions[0]
    assert_equal(
        session.rollback_count,
        1,
        "Successful load must rollback the read-only session once.",
    )
    assert_equal(
        session.close_count,
        1,
        "Successful load must close the session once.",
    )


def test_load_ng_normalizes_records() -> None:
    record = NGObject(
        defect_reason="Gia công",
        defect_quantity=8,
        recorded_at=datetime(2026, 7, 3, 14, 0),
        machine_code="BL03",
        operator_code="NV03",
        work_order_no="WO03",
        item_code="SP03",
    )
    controller, factory, service = make_controller(
        ng_records=[record]
    )

    result = controller.load_ng_pareto(
        FakeDashboardFilters()
    )

    assert_is(
        result,
        service.ng_result,
        "Controller returned the wrong NG result.",
    )
    assert_equal(
        len(service.ng_calls),
        1,
        "NG Pareto service must be called once.",
    )

    normalized_record = service.ng_calls[0]["records"][0]

    assert_equal(
        normalized_record["reason"],
        "Gia công",
        "NG reason alias was not normalized.",
    )
    assert_equal(
        normalized_record["quantity"],
        8,
        "NG quantity alias was not normalized.",
    )
    assert_equal(
        normalized_record["production_date"],
        datetime(2026, 7, 3, 14, 0),
        "NG date alias was not normalized.",
    )
    assert_equal(
        normalized_record["employee_code"],
        "NV03",
        "Operator alias was not normalized.",
    )
    assert_equal(
        normalized_record["product_code"],
        "SP03",
        "Product alias was not normalized.",
    )

    session = factory.sessions[0]
    assert_equal(
        session.rollback_count,
        1,
        "NG load must rollback once.",
    )
    assert_equal(
        session.close_count,
        1,
        "NG load must close once.",
    )


def test_load_all_uses_one_session_and_returns_both_results() -> None:
    controller, factory, service = make_controller(
        downtime_records=[
            {
                "downtime_reason": "Sửa máy",
                "minutes": 60,
                "record_date": "2026-07-04",
            }
        ],
        ng_records=[
            {
                "ng_type": "Phôi",
                "count": 5,
                "record_date": "2026-07-04",
            }
        ],
    )

    result = controller.load_all(
        FakeDashboardFilters()
    )

    assert_true(
        isinstance(result, OEEParetoDashboardData),
        "load_all() must return OEEParetoDashboardData.",
    )
    assert_is(
        result.downtime,
        service.downtime_result,
        "load_all() returned the wrong downtime result.",
    )
    assert_is(
        result.ng,
        service.ng_result,
        "load_all() returned the wrong NG result.",
    )
    assert_equal(
        len(factory.sessions),
        1,
        "load_all() must use exactly one session.",
    )
    assert_equal(
        len(service.downtime_calls),
        1,
        "load_all() must calculate downtime once.",
    )
    assert_equal(
        len(service.ng_calls),
        1,
        "load_all() must calculate NG once.",
    )

    session = factory.sessions[0]
    assert_equal(
        session.rollback_count,
        1,
        "load_all() must rollback once after successful reads.",
    )
    assert_equal(
        session.close_count,
        1,
        "load_all() must close its session.",
    )


def test_empty_filter_values_become_empty_tuples() -> None:
    controller, _factory, service = make_controller()

    controller.load_downtime_pareto(
        FakeDashboardFilters(
            machine_code="   ",
            employee_code="",
            work_order_no=None,
            product_code="  ",
        )
    )

    pareto_filter = service.downtime_calls[0]["filters"]

    assert_equal(
        pareto_filter.machine_codes,
        (),
        "Blank machine filter must become an empty tuple.",
    )
    assert_equal(
        pareto_filter.employee_codes,
        (),
        "Blank employee filter must become an empty tuple.",
    )
    assert_equal(
        pareto_filter.work_order_codes,
        (),
        "Missing work-order filter must become an empty tuple.",
    )
    assert_equal(
        pareto_filter.product_codes,
        (),
        "Blank product filter must become an empty tuple.",
    )


def test_mapping_records_preserve_original_fields() -> None:
    controller, _factory, service = make_controller(
        downtime_records=[
            {
                "reason_code": "DT01",
                "duration": 25,
                "created_at": "2026-07-05T10:00:00",
                "custom_note": "Bảo trì định kỳ",
            }
        ]
    )

    controller.load_downtime_pareto(
        FakeDashboardFilters()
    )

    normalized_record = service.downtime_calls[0]["records"][0]

    assert_equal(
        normalized_record["reason"],
        "DT01",
        "reason_code alias was not normalized.",
    )
    assert_equal(
        normalized_record["duration_minutes"],
        25,
        "duration alias was not normalized.",
    )
    assert_equal(
        normalized_record["production_date"],
        "2026-07-05T10:00:00",
        "String datetime was not preserved.",
    )
    assert_equal(
        normalized_record["custom_note"],
        "Bảo trì định kỳ",
        "Original mapping fields must be preserved.",
    )


def test_load_downtime_rolls_back_and_closes_on_service_error() -> None:
    service = FakeParetoService()
    service.downtime_error = RuntimeError(
        "downtime calculation failed"
    )
    controller, factory, _service = make_controller(
        service=service,
        downtime_records=[
            {
                "reason": "Chờ người",
                "duration_minutes": 10,
            }
        ],
    )

    assert_raises(
        RuntimeError,
        lambda: controller.load_downtime_pareto(
            FakeDashboardFilters()
        ),
        "Downtime service error must be propagated.",
    )

    session = factory.sessions[0]
    assert_equal(
        session.rollback_count,
        1,
        "Error path must rollback once.",
    )
    assert_equal(
        session.close_count,
        1,
        "Error path must still close the session.",
    )


def test_load_ng_rolls_back_and_closes_on_loader_error() -> None:
    factory = FakeSessionFactory()
    service = FakeParetoService()

    def failing_loader(
        _session: FakeSession,
    ) -> list[object]:
        raise LookupError("NG loader failed")

    controller = OEEParetoDashboardController(
        session_factory=factory,
        pareto_service=service,
        downtime_loader=lambda _session: [],
        ng_loader=failing_loader,
    )

    assert_raises(
        LookupError,
        lambda: controller.load_ng_pareto(
            FakeDashboardFilters()
        ),
        "Loader error must be propagated.",
    )

    session = factory.sessions[0]
    assert_equal(
        session.rollback_count,
        1,
        "Loader error must trigger rollback.",
    )
    assert_equal(
        session.close_count,
        1,
        "Loader error must still close the session.",
    )


def test_load_all_stops_when_downtime_calculation_fails() -> None:
    service = FakeParetoService()
    service.downtime_error = RuntimeError(
        "downtime failed"
    )
    controller, factory, _service = make_controller(
        service=service,
        downtime_records=[
            {
                "reason": "Máy hỏng",
                "duration_minutes": 30,
            }
        ],
        ng_records=[
            {
                "reason": "Gia công",
                "quantity": 2,
            }
        ],
    )

    assert_raises(
        RuntimeError,
        lambda: controller.load_all(
            FakeDashboardFilters()
        ),
        "load_all() must propagate downtime errors.",
    )

    assert_equal(
        len(service.downtime_calls),
        1,
        "Downtime calculation should have been attempted once.",
    )
    assert_equal(
        len(service.ng_calls),
        0,
        "NG calculation must not run after downtime failure.",
    )

    session = factory.sessions[0]
    assert_equal(
        session.rollback_count,
        1,
        "load_all() error must rollback once.",
    )
    assert_equal(
        session.close_count,
        1,
        "load_all() error must close the session.",
    )


def test_unsupported_record_type_raises_type_error() -> None:
    class UnsupportedRecord:
        __slots__ = ()

    controller, factory, _service = make_controller(
        downtime_records=[UnsupportedRecord()]
    )

    assert_raises(
        TypeError,
        lambda: controller.load_downtime_pareto(
            FakeDashboardFilters()
        ),
        "Unsupported record types must raise TypeError.",
    )

    session = factory.sessions[0]
    assert_equal(
        session.rollback_count,
        1,
        "Normalization error must trigger rollback.",
    )
    assert_equal(
        session.close_count,
        1,
        "Normalization error must close the session.",
    )


def test_record_with_dict_support_is_normalized() -> None:
    class PlainObject:
        def __init__(self) -> None:
            self.reason = "Lập trình sản phẩm"
            self.duration_minutes = 35
            self.production_date = date(2026, 7, 6)
            self.machine_code = "BL06"

    controller, _factory, service = make_controller(
        downtime_records=[PlainObject()]
    )

    controller.load_downtime_pareto(
        FakeDashboardFilters()
    )

    normalized_record = service.downtime_calls[0]["records"][0]

    assert_equal(
        normalized_record["reason"],
        "Lập trình sản phẩm",
        "Plain-object reason was not normalized.",
    )
    assert_equal(
        normalized_record["duration_minutes"],
        35,
        "Plain-object duration was not normalized.",
    )
    assert_equal(
        normalized_record["production_date"],
        date(2026, 7, 6),
        "Plain-object date was not normalized.",
    )
    assert_equal(
        normalized_record["machine_code"],
        "BL06",
        "Plain-object machine code was not preserved.",
    )


TESTS: tuple[Callable[[], None], ...] = (
    test_constructor_validates_configuration,
    test_load_downtime_normalizes_records_and_options,
    test_load_ng_normalizes_records,
    test_load_all_uses_one_session_and_returns_both_results,
    test_empty_filter_values_become_empty_tuples,
    test_mapping_records_preserve_original_fields,
    test_load_downtime_rolls_back_and_closes_on_service_error,
    test_load_ng_rolls_back_and_closes_on_loader_error,
    test_load_all_stops_when_downtime_calculation_fails,
    test_unsupported_record_type_raises_type_error,
    test_record_with_dict_support_is_normalized,
)


def run_all_tests() -> None:
    failures: list[str] = []

    for test in TESTS:
        try:
            test()
            print(f"[PASS] {test.__name__}")
        except Exception as error:
            failures.append(
                f"{test.__name__}: "
                f"{type(error).__name__}: {error}"
            )
            print(
                f"[FAIL] {test.__name__}: "
                f"{type(error).__name__}: {error}"
            )

    if failures:
        details = "\n".join(
            f"- {failure}"
            for failure in failures
        )
        raise AssertionError(
            f"{len(failures)} test(s) failed:\n{details}"
        )

    print(
        f"All {len(TESTS)} OEE Pareto dashboard "
        "controller tests passed."
    )


if __name__ == "__main__":
    run_all_tests()


