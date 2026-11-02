"""
CUSTOMER MODEL - Lớp dữ liệu Khách hàng
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Customer:
    """Đại diện cho một khách hàng"""

    id: Optional[int] = None
    name: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    id_card: str = ""
    notes: str = ""
    created_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Customer":
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            phone=data.get("phone", ""),
            email=data.get("email", "") or "",
            address=data.get("address", "") or "",
            id_card=data.get("id_card", "") or "",
            notes=data.get("notes", "") or "",
            created_at=data.get("created_at"),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "id_card": self.id_card,
            "notes": self.notes,
            "created_at": self.created_at,
        }

    def __str__(self) -> str:
        return f"{self.name} ({self.phone})"
