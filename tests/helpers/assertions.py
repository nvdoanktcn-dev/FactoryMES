from datetime import datetime


def assert_assignment_created(testcase, assignment):

    testcase.assertIsNotNone(
        assignment
    )

    testcase.assertIsNotNone(
        assignment.id
    )

    testcase.assertEqual(
        assignment.status,
        "DRAFT"
    )

    testcase.assertIsNotNone(
        assignment.production_order_id
    )


def assert_assignment_released(
    testcase,
    assignment,
):

    testcase.assertEqual(
        assignment.status,
        "RELEASED"
    )


def assert_assignment_started(
    testcase,
    assignment,
):

    testcase.assertEqual(
        assignment.status,
        "IN_PROGRESS"
    )


def assert_execution_running(
    testcase,
    execution,
):

    testcase.assertIsNotNone(
        execution.id
    )

    testcase.assertEqual(
        execution.status,
        "RUNNING"
    )

    testcase.assertIsNotNone(
        execution.assignment_id
    )


def assert_execution_completed(
    testcase,
    execution,
):

    testcase.assertEqual(
        execution.status,
        "COMPLETED"
    )

    testcase.assertGreaterEqual(
        execution.ok_qty,
        0
    )

    testcase.assertGreaterEqual(
        execution.ng_qty,
        0
    )

    testcase.assertGreaterEqual(
        execution.runtime_minutes,
        0
    )


def assert_downtime_open(
    testcase,
    event,
):

    testcase.assertEqual(
        event.status,
        "OPEN"
    )

    testcase.assertIsNotNone(
        event.execution_id
    )


def assert_downtime_closed(
    testcase,
    event,
):

    testcase.assertEqual(
        event.status,
        "CLOSED"
    )

    testcase.assertGreaterEqual(
        event.duration_minutes,
        0
    )