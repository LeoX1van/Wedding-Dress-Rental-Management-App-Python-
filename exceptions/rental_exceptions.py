"""
EXCEPTIONS MODULE - Xử lý lỗi tùy chỉnh
Hệ thống cho thuê áo cưới Thanh Hằng
"""


class WeddingRentalError(Exception):
    """Lỗi cơ sở của hệ thống cho thuê áo cưới"""
    pass


class CustomerNotFoundError(WeddingRentalError):
    """Không tìm thấy khách hàng"""
    def __init__(self, customer_id=None, message=None):
        self.customer_id = customer_id
        msg = message or f"Không tìm thấy khách hàng (ID={customer_id})"
        super().__init__(msg)


class ProductNotFoundError(WeddingRentalError):
    """Không tìm thấy sản phẩm"""
    def __init__(self, product_id=None, message=None):
        self.product_id = product_id
        msg = message or f"Không tìm thấy sản phẩm (ID={product_id})"
        super().__init__(msg)


class OrderNotFoundError(WeddingRentalError):
    """Không tìm thấy đơn thuê"""
    def __init__(self, order_id=None, message=None):
        self.order_id = order_id
        msg = message or f"Không tìm thấy đơn thuê (ID={order_id})"
        super().__init__(msg)


class ProductUnavailableError(WeddingRentalError):
    """Sản phẩm không khả dụng (đang được thuê hoặc bảo trì)"""
    def __init__(self, product_name=None, message=None):
        self.product_name = product_name
        msg = message or f"Sản phẩm '{product_name}' hiện không khả dụng"
        super().__init__(msg)


class InvalidDateError(WeddingRentalError):
    """Ngày không hợp lệ"""
    def __init__(self, message="Ngày không hợp lệ hoặc sai định dạng"):
        super().__init__(message)


class DuplicateCodeError(WeddingRentalError):
    """Mã bị trùng lặp (mã khách hàng, mã sản phẩm, ...)"""
    def __init__(self, code=None, message=None):
        self.code = code
        msg = message or f"Mã '{code}' đã tồn tại trong hệ thống"
        super().__init__(msg)


class ValidationError(WeddingRentalError):
    """Lỗi xác thực dữ liệu đầu vào"""
    def __init__(self, field=None, message=None):
        self.field = field
        msg = message or f"Dữ liệu không hợp lệ (trường: {field})"
        super().__init__(msg)
