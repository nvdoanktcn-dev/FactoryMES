class ProductValidator:

    REQUIRED_COLUMNS = [
        "product_code",
        "product_name_vi"
    ]

    def validate_dataframe(self, df):
        errors = []

        for column in self.REQUIRED_COLUMNS:
            if column not in df.columns:
                errors.append(f"Missing column: {column}")

        if errors:
            return errors

        for index, row in df.iterrows():
            row_number = index + 2

            product_code = row.get("product_code")
            product_name_vi = row.get("product_name_vi")

            if not product_code or str(product_code).strip() == "":
                errors.append(f"Row {row_number}: product_code is empty")

            if not product_name_vi or str(product_name_vi).strip() == "":
                errors.append(f"Row {row_number}: product_name_vi is empty")

        duplicated = df[df["product_code"].duplicated()]["product_code"].tolist()

        for code in duplicated:
            errors.append(f"Duplicate product_code in Excel: {code}")

        return errors