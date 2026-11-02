"""
HELPERS - Các hàm tiện ích dùng chung trong toàn bộ ứng dụng
"""

from datetime import datetime, timedelta

DATE_FORMAT = "%Y-%m-%d"
DATE_DISPLAY_FORMAT = "%d/%m/%Y"


def format_currency(amount: float) -> str:
    """
    Định dạng số tiền theo kiểu Việt Nam.
    Ví dụ: 1500000 → '1.500.000đ'
    """
    return f"{amount:,.0f}đ".replace(",", ".")


def format_date_display(date_str: str) -> str:
    """
    Chuyển đổi YYYY-MM-DD sang DD/MM/YYYY để hiển thị.
    Trả về chuỗi gốc nếu không parse được.
    """
    try:
        dt = datetime.strptime(date_str, DATE_FORMAT)
        return dt.strftime(DATE_DISPLAY_FORMAT)
    except (ValueError, TypeError):
        return date_str or ""


def days_between(start_str: str, end_str: str) -> int:
    """
    Tính số ngày giữa hai ngày (YYYY-MM-DD).
    Trả về ít nhất 1 nếu cùng ngày hoặc có lỗi.
    """
    try:
        d1 = datetime.strptime(start_str, DATE_FORMAT)
        d2 = datetime.strptime(end_str, DATE_FORMAT)
        return max(1, (d2 - d1).days)
    except (ValueError, TypeError):
        return 1


def current_date_str() -> str:
    """Trả về ngày hôm nay theo định dạng YYYY-MM-DD"""
    return datetime.now().strftime(DATE_FORMAT)


def date_after_days(days: int = 3) -> str:
    """Trả về ngày sau n ngày kể từ hôm nay (YYYY-MM-DD)"""
    return (datetime.now() + timedelta(days=days)).strftime(DATE_FORMAT)


def days_until(date_str: str) -> int:
    """
    Số ngày còn lại đến ngày date_str.
    Âm nếu đã quá hạn.
    """
    try:
        target = datetime.strptime(date_str, DATE_FORMAT)
        return (target - datetime.now()).days
    except (ValueError, TypeError):
        return 0


def truncate_text(text: str, max_len: int = 30) -> str:
    """Cắt ngắn văn bản nếu vượt quá độ dài tối đa"""
    if not text:
        return ""
    return text if len(text) <= max_len else text[:max_len - 1] + "…"
