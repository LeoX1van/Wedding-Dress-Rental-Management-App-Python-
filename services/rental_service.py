"""
RENTAL SERVICE - Xử lý nghiệp vụ Thuê / Trả đồ & Quản lý đơn thuê
"""

import database as db
from models.order import Order, OrderItem
from models.customer import Customer
from exceptions.rental_exceptions import (
    OrderNotFoundError, CustomerNotFoundError, ProductUnavailableError, ValidationError
)
from utils.validators import validate_required, validate_date_range, validate_positive_number
from utils.helpers import days_between


class RentalService:
    """Cung cấp toàn bộ nghiệp vụ liên quan đến đơn thuê"""

    # ---------- Đọc đơn thuê ----------

    @staticmethod
    def get_all_orders(status_filter: str = None) -> list[Order]:
        """
        Lấy tất cả đơn thuê, tuỳ chọn lọc theo trạng thái.

        Args:
            status_filter: 'active' | 'returned' | 'overdue' | 'cancelled' | None
        Returns:
            Danh sách Order
        """
        rows = db.get_all_orders()
        orders = [Order.from_dict(r) for r in rows]
        if status_filter:
            orders = [o for o in orders if o.status == status_filter]
        return orders

    @staticmethod
    def get_order_by_id(order_id: int) -> Order:
        """
        Lấy đơn thuê theo ID, kèm danh sách sản phẩm.

        Raises:
            OrderNotFoundError: Nếu không tìm thấy đơn.
        """
        rows = db.get_all_orders()
        data = next((r for r in rows if r["id"] == order_id), None)
        if not data:
            raise OrderNotFoundError(order_id)

        order = Order.from_dict(data)
        item_rows = db.get_order_details(order_id)
        order.items = [OrderItem.from_dict(i) for i in item_rows]
        return order

    @staticmethod
    def get_overdue_orders() -> list[Order]:
        """Lấy danh sách đơn quá hạn"""
        rows = db.get_overdue_orders()
        return [Order.from_dict(r) for r in rows]

    # ---------- Tạo đơn thuê ----------

    @staticmethod
    def create_order(
        customer_id: int,
        rental_date: str,
        return_date: str,
        product_ids: list[int],
        deposit_paid: float = 0.0,
        discount: float = 0.0,
        notes: str = "",
        payment_method: str = "cash",
    ) -> Order:
        """
        Tạo đơn thuê mới.

        Args:
            customer_id: ID khách hàng
            rental_date: Ngày thuê (YYYY-MM-DD)
            return_date: Ngày trả dự kiến (YYYY-MM-DD)
            product_ids: Danh sách ID sản phẩm
            deposit_paid: Tiền cọc đã trả
            discount: Giảm giá
            notes: Ghi chú
            payment_method: Phương thức thanh toán

        Returns:
            Order vừa tạo.

        Raises:
            ValidationError, InvalidDateError, ProductUnavailableError
        """
        # Xác thực ngày
        validate_date_range(rental_date, return_date)

        if not product_ids:
            raise ValidationError(message="Vui lòng chọn ít nhất 1 sản phẩm!")

        # Lấy thông tin sản phẩm
        all_products = db.get_all_products()
        prod_map = {p["id"]: p for p in all_products}

        items = []
        for pid in product_ids:
            p = prod_map.get(pid)
            if not p:
                raise ValidationError(message=f"Không tìm thấy sản phẩm ID={pid}")
            if p["status"] != "available":
                raise ProductUnavailableError(product_name=p["name"])
            items.append((pid, p["price_per_day"], 1))

        deposit_paid = validate_positive_number(str(deposit_paid), "Tiền cọc")
        discount = validate_positive_number(str(discount), "Giảm giá")

        order_id, order_code = db.create_order(
            customer_id, rental_date, return_date,
            items, deposit_paid, discount, notes, payment_method
        )
        return RentalService.get_order_by_id(order_id)

    # ---------- Trả đồ ----------

    @staticmethod
    def return_order(order_id: int, actual_return_date: str,
                     extra_payment: float = 0.0, payment_method: str = "cash") -> None:
        """
        Xác nhận trả đồ và thu tiền còn lại.

        Args:
            order_id: ID đơn thuê
            actual_return_date: Ngày trả thực tế (YYYY-MM-DD)
            extra_payment: Số tiền thu thêm
            payment_method: Phương thức thanh toán

        Raises:
            OrderNotFoundError, InvalidDateError, ValidationError
        """
        # Kiểm tra đơn tồn tại
        RentalService.get_order_by_id(order_id)

        from utils.validators import validate_date
        validate_date(actual_return_date, "Ngày trả thực tế")
        extra_payment = validate_positive_number(str(extra_payment), "Số tiền thu thêm")

        db.return_order(order_id, actual_return_date, extra_payment, payment_method)

    # ---------- Khách hàng ----------

    @staticmethod
    def get_all_customers(search: str = "") -> list[Customer]:
        """Lấy danh sách khách hàng, hỗ trợ tìm kiếm theo tên/SĐT"""
        if search:
            rows = db.search_customers(search)
        else:
            rows = db.get_all_customers()
        return [Customer.from_dict(r) for r in rows]

    @staticmethod
    def add_customer(name: str, phone: str, email: str = "",
                     address: str = "", id_card: str = "", notes: str = "") -> Customer:
        """
        Thêm khách hàng mới.

        Raises:
            ValidationError: Nếu thiếu họ tên hoặc SĐT.
        """
        validate_required(name, "Họ tên")
        validate_required(phone, "Số điện thoại")
        cid = db.add_customer(name.strip(), phone.strip(), email, address, id_card, notes)
        rows = db.get_all_customers()
        data = next((r for r in rows if r["id"] == cid), None)
        return Customer.from_dict(data) if data else Customer(id=cid, name=name, phone=phone)

    @staticmethod
    def update_customer(cid: int, name: str, phone: str, email: str = "",
                        address: str = "", id_card: str = "", notes: str = "") -> None:
        """Cập nhật thông tin khách hàng"""
        validate_required(name, "Họ tên")
        validate_required(phone, "Số điện thoại")
        db.update_customer(cid, name.strip(), phone.strip(), email, address, id_card, notes)

    @staticmethod
    def delete_customer(cid: int) -> None:
        """Xóa khách hàng"""
        db.delete_customer(cid)
