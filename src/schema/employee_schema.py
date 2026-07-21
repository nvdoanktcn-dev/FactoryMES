class EmployeeSchema:

    REQUIRED_COLUMNS = [
        "Employee Code",
        "Employee Name",
    ]

    OPTIONAL_COLUMNS = [
        "Department",
        "Position",
        "Status",
    ]

    COLUMN_MAPPING = {

        "Mã nhân viên": "Employee Code",
        "员工编号": "Employee Code",
        "Employee Code": "Employee Code",

        "Tên nhân viên": "Employee Name",
        "员工姓名": "Employee Name",
        "Employee Name": "Employee Name",

        "Bộ phận": "Department",
        "Department": "Department",

        "Chức vụ": "Position",
        "Position": "Position",

        "Trạng thái": "Status",
        "Status": "Status",
    }

    DEFAULT_STATUS = "ACTIVE"

    @classmethod
    def normalize_status(cls, value):

        text = str(value or "").strip().upper()

        if not text:
            return cls.DEFAULT_STATUS

        mapping = {

            "ACTIVE": "ACTIVE",
            "HOẠT ĐỘNG": "ACTIVE",
            "启用": "ACTIVE",

            "INACTIVE": "INACTIVE",
            "停用": "INACTIVE",
        }

        return mapping.get(
            text,
            cls.DEFAULT_STATUS,
        )

    @classmethod
    def validate_data(cls, data):

        if not data.get("employee_code"):
            raise ValueError(
                "Employee Code is required."
            )

        if not data.get("employee_name"):
            raise ValueError(
                "Employee Name is required."
            )

        return True