from datetime import datetime, time, timedelta

import pandas as pd


class ProductionMapper:
    """
    Chuyển một dòng dữ liệu sản xuất đã được DataCleaner chuẩn hóa
    thành dictionary chuẩn dùng bởi ProductionEngine.

    Mapper không truy cập database.
    Mapper không tạo batch_no.
    ProductionImportService sẽ gán batch_no cho từng bản ghi
    trước khi gọi ProductionEngine.
    """

    def map_row(self, row):
        if row is None:
            raise ValueError("Production row is required.")

        production_date = self._to_date(
            row.get("Ngày")
        )

        work_order_no = self._text(
            row.get("Mã công lệnh")
        ).upper()

        machine_code = self._text(
            row.get("Tên thiết bị")
        ).upper()

        product_code = self._resolve_product_code(
            row
        )

        employee_code = self._text(
            row.get("Nhân viên thao tác")
        ).upper()

        op_no = self._normalize_op(
            row.get("OP")
        )

        shift = self._normalize_shift(
            row.get("Ca")
        )

        ok_qty = self._resolve_ok_qty(row)
        ng_qty = self._resolve_ng_qty(row)

        start_time, finish_time = self._resolve_times(
            row=row,
            production_date=production_date,
        )

        run_time_sec = self._resolve_runtime_seconds(
            row
        )

        downtime_min = self._to_float(
            row.get("Thời gian dừng (phút)", 0)
        )

        downtime_reason = self._text(
            row.get("Lý do dừng")
        )

        status = self._text(
            row.get("Trạng thái")
        ).upper() or "COMPLETED"

        remark = self._text(
            row.get("Ghi chú")
        )

        data = {
            "work_order_no": work_order_no,
            "product_code": product_code,
            "op_no": op_no,
            "machine_code": machine_code,
            "employee_code": employee_code,
            "shift": shift,
            "start_time": start_time,
            "finish_time": finish_time,
            "run_time_sec": run_time_sec,
            "ok_qty": ok_qty,
            "ng_qty": ng_qty,
            "downtime_min": downtime_min,
            "downtime_reason": downtime_reason,
            "status": status,
            "remark": remark,
        }

        self._validate_mapped_data(data)

        return data

    def map_dataframe(self, dataframe):
        """
        Chuyển toàn bộ DataFrame thành danh sách Production DTO.

        Returns:
            tuple:
                records: danh sách dictionary hợp lệ
                errors: danh sách lỗi theo dòng Excel
        """
        if dataframe is None:
            raise ValueError("DataFrame is required.")

        records = []
        errors = []

        for index, row in dataframe.iterrows():
            excel_row = index + 2

            try:
                records.append(
                    self.map_row(row)
                )

            except Exception as error:
                errors.append({
                    "row": excel_row,
                    "message": str(error),
                })

        return records, errors

    @staticmethod
    def _validate_mapped_data(data):
        required_fields = {
            "work_order_no": "Work Order No",
            "product_code": "Product Code",
            "machine_code": "Machine Code",
            "employee_code": "Employee Code",
            "op_no": "Operation No",
        }

        for field, display_name in required_fields.items():
            if not data.get(field):
                raise ValueError(
                    f"{display_name} is required."
                )

        ok_qty = data.get("ok_qty", 0)
        ng_qty = data.get("ng_qty", 0)

        if ok_qty < 0:
            raise ValueError(
                "OK quantity cannot be negative."
            )

        if ng_qty < 0:
            raise ValueError(
                "NG quantity cannot be negative."
            )

        if ok_qty == 0 and ng_qty == 0:
            raise ValueError(
                "OK quantity and NG quantity "
                "cannot both be zero."
            )

        if (
            not data.get("start_time")
            or not data.get("finish_time")
        ) and data.get("run_time_sec", 0) <= 0:
            raise ValueError(
                "Runtime is required. Provide actual hours "
                "or start/finish time."
            )

    def _resolve_product_code(self, row):
        """
        Ưu tiên:
        1. Mã sản phẩm
        2. Product Code
        3. Tên sản phẩm

        Tên sản phẩm chỉ là phương án tương thích tạm thời.
        """
        product_code = self._text(
            row.get("Mã sản phẩm")
        ).upper()

        if product_code:
            return product_code

        product_code = self._text(
            row.get("Product Code")
        ).upper()

        if product_code:
            return product_code

        return self._text(
            row.get("Tên sản phẩm")
        ).upper()

    def _resolve_ok_qty(self, row):
        """
        Thứ tự ưu tiên:

        1. Số lượng OK
        2. Thực tế PCS - Tổng NG
        3. OK + Gia công NG - Gia công NG
        """
        if self._has_value(
            row.get("Số lượng OK")
        ):
            return max(
                0,
                self._to_int(
                    row.get("Số lượng OK")
                ),
            )

        actual_qty = self._to_int(
            row.get("Thực tế PCS")
        )

        total_ng = self._resolve_ng_qty(row)

        if actual_qty > 0:
            return max(
                0,
                actual_qty - total_ng,
            )

        total_processed = self._to_int(
            row.get(
                "Số lượng OK+Số lượng gia công NG"
            )
        )

        machining_ng = self._to_int(
            row.get("Gia công NG")
        )

        return max(
            0,
            total_processed - machining_ng,
        )

    def _resolve_ng_qty(self, row):
        """
        Ưu tiên Tổng NG.

        Nếu Tổng NG không có giá trị thì:
            NG = Phôi NG + Gia công NG
        """
        if self._has_value(
            row.get("Tổng NG")
        ):
            return max(
                0,
                self._to_int(
                    row.get("Tổng NG")
                ),
            )

        blank_ng = self._to_int(
            row.get("Phôi NG")
        )

        machining_ng = self._to_int(
            row.get("Gia công NG")
        )

        return max(
            0,
            blank_ng + machining_ng,
        )

    def _resolve_runtime_seconds(self, row):
        """
        Ưu tiên cột Thời gian thực tế (H).

        Giá trị giờ được chuyển sang giây.
        """
        actual_hours = self._to_float(
            row.get("Thời gian thực tế (H)")
        )

        if actual_hours > 0:
            return round(
                actual_hours * 3600,
                2,
            )

        runtime_sec = self._to_float(
            row.get("Thời gian chạy (giây)")
        )

        if runtime_sec > 0:
            return runtime_sec

        return 0.0

    def _resolve_times(
        self,
        row,
        production_date,
    ):
        """
        Ghép Ngày với Giờ bắt đầu và Giờ kết thúc.

        Nếu ca đêm có giờ kết thúc nhỏ hơn giờ bắt đầu,
        finish_time được cộng thêm một ngày.
        """
        start_value = row.get("Giờ bắt đầu")
        finish_value = row.get("Giờ kết thúc")

        start_time = self._combine_date_time(
            production_date,
            start_value,
        )

        finish_time = self._combine_date_time(
            production_date,
            finish_value,
        )

        if (
            start_time is not None
            and finish_time is not None
            and finish_time < start_time
        ):
            finish_time += timedelta(days=1)

        return start_time, finish_time

    @staticmethod
    def _combine_date_time(
        date_value,
        time_value,
    ):
        if date_value is None:
            return None

        if time_value is None or pd.isna(time_value):
            return None

        if isinstance(time_value, pd.Timestamp):
            return datetime.combine(
                date_value,
                time_value.time(),
            )

        if isinstance(time_value, datetime):
            return datetime.combine(
                date_value,
                time_value.time(),
            )

        if isinstance(time_value, time):
            return datetime.combine(
                date_value,
                time_value,
            )

        # Excel đôi khi trả thời gian dưới dạng phần của một ngày.
        if isinstance(time_value, (int, float)):
            if 0 <= float(time_value) < 1:
                total_seconds = int(
                    round(float(time_value) * 86400)
                )

                hours = total_seconds // 3600
                minutes = (
                    total_seconds % 3600
                ) // 60
                seconds = total_seconds % 60

                if hours >= 24:
                    hours = 23
                    minutes = 59
                    seconds = 59

                return datetime.combine(
                    date_value,
                    time(
                        hour=hours,
                        minute=minutes,
                        second=seconds,
                    ),
                )

        text = str(time_value).strip()

        if not text or text.lower() in {
            "nan",
            "none",
            "nat",
        }:
            return None

        formats = [
            "%H:%M:%S",
            "%H:%M",
            "%I:%M:%S %p",
            "%I:%M %p",
        ]

        for date_format in formats:
            try:
                parsed_time = datetime.strptime(
                    text,
                    date_format,
                ).time()

                return datetime.combine(
                    date_value,
                    parsed_time,
                )

            except ValueError:
                continue

        raise ValueError(
            f"Invalid time value: {time_value}"
        )

    @staticmethod
    def _to_date(value):
        if value is None or pd.isna(value):
            return None

        if isinstance(value, pd.Timestamp):
            return value.date()

        if isinstance(value, datetime):
            return value.date()

        parsed = pd.to_datetime(
            value,
            errors="coerce",
            dayfirst=True,
        )

        if pd.isna(parsed):
            return None

        return parsed.date()

    @staticmethod
    def _normalize_op(value):
        text = ProductionMapper._text(
            value
        ).upper()

        if not text:
            return ""

        digits = "".join(
            character
            for character in text
            if character.isdigit()
        )

        if digits:
            return f"OP{int(digits)}"

        return text

    @staticmethod
    def _normalize_shift(value):
        text = ProductionMapper._text(
            value
        ).upper()

        mapping = {
            "DAY": "DAY",
            "D": "DAY",
            "NGÀY": "DAY",
            "CA NGÀY": "DAY",
            "白班": "DAY",

            "NIGHT": "NIGHT",
            "N": "NIGHT",
            "ĐÊM": "NIGHT",
            "CA ĐÊM": "NIGHT",
            "夜班": "NIGHT",

            "ADMIN": "ADMIN",
            "HÀNH CHÍNH": "ADMIN",
        }

        return mapping.get(text, text)

    @staticmethod
    def _text(value):
        if value is None or pd.isna(value):
            return ""

        text = str(value).strip()

        if text.lower() in {
            "nan",
            "none",
            "nat",
        }:
            return ""

        return " ".join(text.split())

    @staticmethod
    def _has_value(value):
        if value is None or pd.isna(value):
            return False

        text = str(value).strip().lower()

        return text not in {
            "",
            "nan",
            "none",
            "nat",
        }

    @staticmethod
    def _to_int(value):
        if value is None or pd.isna(value):
            return 0

        if isinstance(value, str):
            value = value.strip()

            if not value:
                return 0

            value = value.replace(",", "")
            value = value.replace(" ", "")

        try:
            return int(float(value))

        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _to_float(value):
        if value is None or pd.isna(value):
            return 0.0

        if isinstance(value, str):
            value = value.strip()

            if not value:
                return 0.0

            value = value.replace(",", ".")
            value = value.replace(" ", "")

        try:
            return float(value)

        except (TypeError, ValueError):
            return 0.0