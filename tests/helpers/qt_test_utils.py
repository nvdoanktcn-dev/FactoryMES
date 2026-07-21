class ImportAssertions:

    @staticmethod
    def assert_success(testcase, result):
        testcase.assertTrue(result.success)
        testcase.assertEqual(result.failed_rows, 0)

    @staticmethod
    def assert_failed(testcase, result):
        testcase.assertFalse(result.success)
        testcase.assertGreater(result.failed_rows, 0)