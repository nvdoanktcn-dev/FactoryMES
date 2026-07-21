from src.framework.exception import ValidationError


class BaseValidator:
    @staticmethod
    def required(value, field_name):
        if value is None or str(value).strip() == "":
            raise ValidationError(f"{field_name} is required.")

    @staticmethod
    def max_length(value, field_name, max_len):
        if value and len(str(value)) > max_len:
            raise ValidationError(
                f"{field_name} must be less than {max_len} characters."
            )