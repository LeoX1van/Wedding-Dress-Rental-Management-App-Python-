"""
ORDER MODEL - Lớp dữ liệu Đơn thuê & Chi tiết đơn thuê
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class OrderItem:
    """Chi tiết một sản phẩm trong đơn thuê"""

    id: Optional[int] = None
    order_id: Optional[int] = None
    product_id: Optional[int] = None
    product_name: str = ""
    product_code: str = ""
    category: str = ""
    price_per_day: float = 0.0
    days: int = 1
    subtotal: float = 0.0

    @classmethod
    def from_dict(cls, data: dict) -> "OrderItem":
        return cls(
            id=data.get("id"),
            order_id=data.get("order_id"),
            product_id=data.get("product_id"),
            product_name=data.get("product_name", ""),
            product_code=data.get("product_code", ""),
            category=data.get("category", ""),
            price_per_day=float(data.get("price_per_day", 0)),
            days=int(data.get("days", 1)),
            subtotal=float(data.get("subtotal", 0)),
        )


@dataclass
class Order:
    """Đại diện cho một đơn thuê"""

    id: Optional[int] = None
    order_code: str = ""
    customer_id: Optional[int] = None
    customer_name: str = ""
    customer_phone: str = ""
    rental_date: str = ""
    return_date: str = ""
    actual_return_date: Optional[str] = None
    total_days: int = 1
    subtotal: float = 0.0
    deposit_paid: float = 0.0
    discount: float = 0.0
    total_amount: float = 0.0
    paid_amount: float = 0.0
    payment_method: str = "cash"
    status: str = "active"        # active | returned | overdue | cancelled
    notes: str = ""
    created_at: Optional[str] = None
    items: List[OrderItem] = field(default_factory=list)

    # -------- computed properties --------

    @property
    def status_label(self) -> str:
        mapping = {
            "active": "🔵 Đang thuê",
            "returned": "✅ Đã trả",
            "overdue": "🔴 Quá hạn",
            "cancelled": "⛔ Đã hủy",
        }
        return mapping.get(self.status, self.status)

    @property
    def remaining_amount(self) -> float:
        return max(0.0, self.total_amount - self.paid_amount)

    # -------- factory --------

    @classmethod
    def from_dict(cls, data: dict) -> "Order":
        return cls(
            id=data.get("id"),
            order_code=data.get("order_code", ""),
            customer_id=data.get("customer_id"),
            customer_name=data.get("customer_name", ""),
            customer_phone=data.get("customer_phone", ""),
            rental_date=data.get("rental_date", ""),
            return_date=data.get("return_date", ""),
            actual_return_date=data.get("actual_return_date"),
            total_days=int(data.get("total_days", 1) or 1),
            subtotal=float(data.get("subtotal", 0) or 0),
            deposit_paid=float(data.get("deposit_paid", 0) or 0),
            discount=float(data.get("discount", 0) or 0),
            total_amount=float(data.get("total_amount", 0) or 0),
            paid_amount=float(data.get("paid_amount", 0) or 0),
            payment_method=data.get("payment_method", "cash"),
            status=data.get("status", "active"),
            notes=data.get("notes", "") or "",
            created_at=data.get("created_at"),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "order_code": self.order_code,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "rental_date": self.rental_date,
            "return_date": self.return_date,
            "actual_return_date": self.actual_return_date,
            "total_days": self.total_days,
            "subtotal": self.subtotal,
            "deposit_paid": self.deposit_paid,
            "discount": self.discount,
            "total_amount": self.total_amount,
            "paid_amount": self.paid_amount,
            "payment_method": self.payment_method,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at,
        }

    def __str__(self) -> str:
        return f"{self.order_code} - {self.customer_name} ({self.status_label})"
