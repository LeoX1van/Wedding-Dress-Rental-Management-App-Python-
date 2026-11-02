"""
ACCESSORY MODEL - Lớp dữ liệu Phụ kiện
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Accessory:
    """Đại diện cho một phụ kiện (vương miện, nhẫn, giày, hoa...)"""

    id: Optional[int] = None
    code: str = ""
    name: str = ""
    category: str = "phu_kien"
    type: str = ""                # Vương miện, Nhẫn, Giày, Cà vạt, Hoa...
    size: str = ""
    color: str = ""
    price_per_day: float = 0.0
    deposit: float = 0.0
    status: str = "available"     # available | rented | maintenance
    image_path: Optional[str] = None
    description: str = ""
    rental_count: int = 0
    created_at: Optional[str] = None

    @property
    def status_label(self) -> str:
        mapping = {
            "available": "✅ Còn trống",
            "rented": "🔴 Đang thuê",
            "maintenance": "🔧 Bảo trì",
        }
        return mapping.get(self.status, self.status)

    @property
    def is_available(self) -> bool:
        return self.status == "available"

    @classmethod
    def from_dict(cls, data: dict) -> "Accessory":
        return cls(
            id=data.get("id"),
            code=data.get("code", ""),
            name=data.get("name", ""),
            category=data.get("category", "phu_kien"),
            type=data.get("type", "") or "",
            size=data.get("size", "") or "",
            color=data.get("color", "") or "",
            price_per_day=float(data.get("price_per_day", 0)),
            deposit=float(data.get("deposit", 0)),
            status=data.get("status", "available"),
            image_path=data.get("image_path"),
            description=data.get("description", "") or "",
            rental_count=int(data.get("rental_count", 0)),
            created_at=data.get("created_at"),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "category": self.category,
            "type": self.type,
            "size": self.size,
            "color": self.color,
            "price_per_day": self.price_per_day,
            "deposit": self.deposit,
            "status": self.status,
            "image_path": self.image_path,
            "description": self.description,
            "rental_count": self.rental_count,
            "created_at": self.created_at,
        }

    def __str__(self) -> str:
        return f"{self.code} - {self.name} (💎 Phụ kiện)"
