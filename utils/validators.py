"""
VALIDATORS - Kiểm tra và xác thực dữ liệu đầu vào
"""

import re
from datetime import datetime
from exceptions.rental_exceptions import ValidationError, InvalidDateError

DATE_FORMAT = "%Y-%m-%d"


def validate_required(value: str, field_name: str) -> str:
    """Kiểm tra trường bắt buộc không được để trống"""
    if not value or not value.strip():
        raise ValidationError(field=field_name,
                              message=f"Trường '{field_name}' không được để trống!")
    return value.strip()


def validate_phone(phone: str) -> str:
    """Kiểm tra số điện thoại hợp lệ (Việt Nam)"""
    phone = phone.strip()
    pattern = r"^(0|\+84)[0-9]{9,10}$"
    if not re.match(pattern, phone):
        raise ValidationError(field="phone",
                              message=f"Số điện thoại '{phone}' không hợp lệ! "
                                      "Vui lòng nhập đúng định dạng: 0xxxxxxxxx")
    return phone


def validate_date(date_str: str, field_name: str = "date") -> datetime:
    """
    Xác thực chuỗi ngày theo định dạng YYYY-MM-DD.
    Trả về đối tượng datetime nếu hợp lệ.
    """
    try:
        return datetime.strptime(date_str.strip(), DATE_FORMAT)
    except (ValueError, AttributeError):
        raise InvalidDateError(
            f"Ngày '{date_str}' không hợp lệ! Định dạng đúng: YYYY-MM-DD"
        )


def validate_date_range(rental_date_str: str, return_date_str: str) -> tuple:
    """
    Kiểm tra ngày thuê phải trước ngày trả.
    Trả về (rental_datetime, return_datetime).
    """
    rental_dt = validate_date(rental_date_str, "Ngày thuê")
    return_dt = validate_date(return_date_str, "Ngày trả")
    if return_dt <= rental_dt:
        raise InvalidDateError("Ngày trả phải sau ngày thuê!")
    return rental_dt, return_dt


def validate_positive_number(value_str: str, field_name: str = "Số tiền",
                             allow_zero: bool = True) -> float:
    """Kiểm tra giá trị số dương (hoặc không âm)"""
    try:
        val = float(str(value_str).strip() or "0")
    except ValueError:
        raise ValidationError(field=field_name,
                              message=f"'{field_name}' phải là số hợp lệ!")
    if not allow_zero and val <= 0:
        raise ValidationError(field=field_name,
                              message=f"'{field_name}' phải lớn hơn 0!")
    if val < 0:
        raise ValidationError(field=field_name,
                              message=f"'{field_name}' không được âm!")
    return val
