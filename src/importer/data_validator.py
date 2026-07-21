import pandas as pd


class DataValidator:

    REQUIRED_COLUMNS = [
        "Ngày",
        "Tên thiết bị",
        "Mã công lệnh",
        "Tên sản phẩm",
        "Nhân viên thao tác",
        "Thực tế PCS",
    ]

    def validate(self, row):
        """
        Validate một dòng dữ liệu.
        """
        self.validate_required_fields(row)
        self.validate_numeric_fields(row)

        return True

    def validate_dataframe(self, dataframe):
        """
        Validate toàn bộ DataFrame.
        """
        self.validate_columns(dataframe)

        errors = []

        for index, row in dataframe.iterrows():
            try:
                self.validate(row)

            except Exception as error:
                errors.append(
                    {
                        "row": index + 2,
                        "message": str(error)
                    }
                )

        return errors

    def validate_columns(self, dataframe):

        missing = []

        for column in self.REQUIRED_COLUMNS:
            if column not in dataframe.columns:
                missing.append(column)

        if missing:
            raise ValueError(
                "Missing columns:\n"
                + "\n".join(missing)
            )

    @staticmethod
    def validate_required_fields(row):

        required = [
            "Ngày",
            "Tên thiết bị",
            "Mã công lệnh",
            "Tên sản phẩm",
        ]

        for field in required:

            value = row.get(field)

            if pd.isna(value):
                raise ValueError(
                    f"{field} is empty."
                )

            if str(value).strip() == "":
                raise ValueError(
                    f"{field} is empty."
                )

    @staticmethod
    def validate_numeric_fields(row):

        numeric_fields = [
            "Thực tế PCS",
            "Tổng NG",
            "Gia công NG",
        ]

        for field in numeric_fields:

            if field not in row:
                continue

            value = row[field]

            if pd.isna(value):
                continue

            try:
                float(value)

            except Exception:
                raise ValueError(
                    f"{field} is not numeric."
                )