import re

import pandas as pd


class DataCleaner:
    """
    Chuẩn hóa dữ liệu Excel CNC/Robot trước khi Validation.

    Bước này chỉ làm sạch dữ liệu, chưa kiểm tra dữ liệu
    có tồn tại trong Database hay chưa.
    """

    COLUMN_MAPPING = {
        "Số TT": "TT",
        "TT": "TT",

        "Ngày": "Ngày",

        "Tên thiết bị": "Tên thiết bị",

        "Mã lệnh sản xuất": "Mã công lệnh",
        "Mã công lệnh": "Mã công lệnh",

        "Tên sản phẩm": "Tên sản phẩm",

        "Thời gian thực tế\n(H)": "Thời gian thực tế (H)",
        "Thời gian thực tế (H)": "Thời gian thực tế (H)",

        "Số lượng OK+Số lượng gia công NG":
            "Số lượng OK+Số lượng gia công NG",

        "（OK+NG）\nSố lượng OK+Số lượng gia công NG":
            "Số lượng OK+Số lượng gia công NG",

        "Số lượng\nOK": "Số lượng OK",
        "Số lượng OK": "Số lượng OK",

        "Tổng NG": "Tổng NG",
        "Phôi NG": "Phôi NG",
        "Gia công NG": "Gia công NG",

        "Thực tế\nPCS": "Thực tế PCS",
        "Thực tế PCS": "Thực tế PCS",

        "Tiêu chuẩn sản lượng\nPCS": "Tiêu chuẩn sản lượng PCS",
        "Tiêu chuẩn sản lượng PCS": "Tiêu chuẩn sản lượng PCS",

        "Chênh lệch\nPCS": "Chênh lệch PCS",
        "Chênh lệch PCS": "Chênh lệch PCS",

        "Tỷ lệ hoàn thành": "Tỷ lệ hoàn thành",
        "Tỷ lệ lỗi": "Tỷ lệ lỗi",
        "Tỷ lệ sử dụng": "Tỷ lệ sử dụng",
        "Tỷ lệ sử dụng thiết bị": "Tỷ lệ sử dụng thiết bị",

        "Nhân viên thao tác": "Nhân viên thao tác",

        "OP": "OP",
        "Công đoạn": "OP",

        "Ca": "Ca",
        "Shift": "Ca",
    }

    TEXT_COLUMNS = [
        "Tên thiết bị",
        "Mã công lệnh",
        "Tên sản phẩm",
        "Nhân viên thao tác",
        "OP",
        "Ca",
    ]

    NUMERIC_COLUMNS = [
        "Thời gian thực tế (H)",
        "Số lượng OK+Số lượng gia công NG",
        "Số lượng OK",
        "Tổng NG",
        "Phôi NG",
        "Gia công NG",
        "Thực tế PCS",
        "Tiêu chuẩn sản lượng PCS",
        "Chênh lệch PCS",
    ]

    PERCENT_COLUMNS = [
        "Tỷ lệ hoàn thành",
        "Tỷ lệ lỗi",
        "Tỷ lệ sử dụng",
        "Tỷ lệ sử dụng thiết bị",
    ]

    def clean(self, dataframe):
        if dataframe is None:
            raise ValueError("DataFrame is required.")

        df = dataframe.copy()

        df = self.clean_column_names(df)
        df = self.rename_columns(df)
        df = self.remove_empty_rows(df)
        df = self.clean_text_columns(df)
        df = self.clean_date_column(df)
        df = self.clean_numeric_columns(df)
        df = self.clean_percentage_columns(df)
        df = self.normalize_machine_code(df)
        df = self.normalize_work_order(df)
        df = self.normalize_operation(df)
        df = self.normalize_shift(df)

        return df.reset_index(drop=True)

    def clean_column_names(self, df):
        df.columns = [
            self.normalize_column_name(column)
            for column in df.columns
        ]

        return df

    @staticmethod
    def normalize_column_name(column):
        value = str(column)

        value = value.replace("\r\n", "\n")
        value = value.replace("\r", "\n")
        value = value.replace("\u3000", " ")
        value = value.strip()

        value = re.sub(r"[ \t]+", " ", value)
        value = re.sub(r"\n+", "\n", value)

        return value

    def rename_columns(self, df):
        rename_map = {}

        for column in df.columns:
            normalized_column = self.normalize_column_name(column)

            if normalized_column in self.COLUMN_MAPPING:
                rename_map[column] = self.COLUMN_MAPPING[normalized_column]

        return df.rename(columns=rename_map)

    @staticmethod
    def remove_empty_rows(df):
        df = df.dropna(how="all")

        important_columns = [
            column
            for column in [
                "Tên thiết bị",
                "Mã công lệnh",
                "Tên sản phẩm",
            ]
            if column in df.columns
        ]

        if important_columns:
            df = df.dropna(
                how="all",
                subset=important_columns
            )

        return df

    def clean_text_columns(self, df):
        for column in self.TEXT_COLUMNS:
            if column not in df.columns:
                continue

            df[column] = (
                df[column]
                .fillna("")
                .astype(str)
                .map(self.clean_text_value)
            )

        return df

    @staticmethod
    def clean_text_value(value):
        value = str(value)

        if value.lower() in {"nan", "none", "nat"}:
            return ""

        value = value.replace("\u3000", " ")
        value = value.replace("\r", " ")
        value = value.replace("\n", " ")
        value = re.sub(r"\s+", " ", value)

        return value.strip()

    @staticmethod
    def clean_date_column(df):
        if "Ngày" not in df.columns:
            return df

        df["Ngày"] = pd.to_datetime(
            df["Ngày"],
            errors="coerce",
            dayfirst=True
        )

        return df

    def clean_numeric_columns(self, df):
        for column in self.NUMERIC_COLUMNS:
            if column not in df.columns:
                continue

            df[column] = (
                df[column]
                .map(self.normalize_number)
                .pipe(pd.to_numeric, errors="coerce")
                .fillna(0)
            )

        return df

    def clean_percentage_columns(self, df):
        for column in self.PERCENT_COLUMNS:
            if column not in df.columns:
                continue

            df[column] = df[column].map(
                self.normalize_percentage
            )

        return df

    @staticmethod
    def normalize_number(value):
        if pd.isna(value):
            return 0

        if isinstance(value, (int, float)):
            return value

        value = str(value).strip()

        if not value:
            return 0

        value = value.replace(",", "")
        value = value.replace(" ", "")

        return value

    @staticmethod
    def normalize_percentage(value):
        if pd.isna(value):
            return 0.0

        if isinstance(value, (int, float)):
            number = float(value)

            if number > 1:
                return number / 100

            return number

        value = str(value).strip()

        if not value:
            return 0.0

        has_percent_sign = "%" in value

        value = value.replace("%", "")
        value = value.replace(",", ".")
        value = value.strip()

        try:
            number = float(value)

            if has_percent_sign or number > 1:
                return number / 100

            return number

        except ValueError:
            return 0.0

    @staticmethod
    def normalize_machine_code(df):
        if "Tên thiết bị" not in df.columns:
            return df

        df["Tên thiết bị"] = (
            df["Tên thiết bị"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        return df

    @staticmethod
    def normalize_work_order(df):
        if "Mã công lệnh" not in df.columns:
            return df

        df["Mã công lệnh"] = (
            df["Mã công lệnh"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        return df

    @staticmethod
    def normalize_operation(df):
        if "OP" not in df.columns:
            return df

        def normalize_op(value):
            value = str(value).strip().upper()

            if not value or value in {"NAN", "NONE"}:
                return ""

            number_match = re.search(r"\d+", value)

            if number_match:
                return f"OP{int(number_match.group())}"

            return value

        df["OP"] = df["OP"].map(normalize_op)

        return df

    @staticmethod
    def normalize_shift(df):
        if "Ca" not in df.columns:
            return df

        shift_mapping = {
            "DAY": "DAY",
            "NGÀY": "DAY",
            "CA NGÀY": "DAY",
            "D": "DAY",

            "NIGHT": "NIGHT",
            "ĐÊM": "NIGHT",
            "CA ĐÊM": "NIGHT",
            "N": "NIGHT",
        }

        def normalize_shift_value(value):
            value = str(value).strip().upper()

            if not value or value in {"NAN", "NONE"}:
                return ""

            return shift_mapping.get(value, value)

        df["Ca"] = df["Ca"].map(normalize_shift_value)

        return df