import unittest
import pandas as pd

from src.validator.product_validator import ProductValidator


class TestProductValidator(unittest.TestCase):

    def setUp(self):
        self.validator = ProductValidator()

    def tearDown(self):
        close = getattr(self.validator, "close", None)
        if callable(close):
            close()   

    def test_valid_dataframe(self):
        df = pd.DataFrame({
            "product_code": ["P001", "P002"],
            "product_name_vi": ["SP1", "SP2"],
        })

        errors = self.validator.validate_dataframe(df)

        self.assertEqual(errors, [])

    def test_duplicate_product(self):
        df = pd.DataFrame({
            "product_code": ["P001", "P001"],
            "product_name_vi": ["SP1", "SP2"],
        })

        errors = self.validator.validate_dataframe(df)

        self.assertTrue(any("Duplicate product_code" in e for e in errors))

    def test_blank_product_code(self):
        df = pd.DataFrame({
            "product_code": [""],
            "product_name_vi": ["SP1"],
        })

        errors = self.validator.validate_dataframe(df)

        self.assertTrue(any("product_code is empty" in e for e in errors))

    def test_blank_product_name(self):
        df = pd.DataFrame({
            "product_code": ["P001"],
            "product_name_vi": [""],
        })

        errors = self.validator.validate_dataframe(df)

        self.assertTrue(any("product_name_vi is empty" in e for e in errors))


if __name__ == "__main__":
    unittest.main()