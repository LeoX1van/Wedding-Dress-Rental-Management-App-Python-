"""
BUSINESS LAYER - Lớp logic nghiệp vụ
Áo Cưới Văn An - Hệ thống quản lý
Chứa: xác thực, phân quyền, hằng số vai trò
"""

import hashlib

# ======= XÁC THỰC & MÃ HÓA =======
_SALT = "wedding_rental_salt_2024"


class AuthLogic:
    """Xử lý logic xác thực người dùng"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Mã hóa mật khẩu với salt cố định"""
        return hashlib.sha256(f"{_SALT}{password}".encode()).hexdigest()

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Kiểm tra mật khẩu có khớp với hash không"""
        return AuthLogic.hash_password(password) == hashed


# ======= VAI TRÒ & PHÂN QUYỀN =======
ROLE_LABELS = {
    "admin":   "👑 Quản trị viên",
    "manager": "🏷️ Quản lý",
    "staff":   "👤 Nhân viên",
}

# menu_key → danh sách role được phép
PERMISSIONS = {
    "dashboard":       ["admin", "manager", "staff"],
    "orders":          ["admin", "manager", "staff"],
    "new_order":       ["admin", "manager", "staff"],
    "wardrobe_female": ["admin", "manager", "staff"],
    "wardrobe_male":   ["admin", "manager", "staff"],
    "accessories":     ["admin", "manager", "staff"],
    "customers":       ["admin", "manager", "staff"],
    "return_schedule": ["admin", "manager", "staff"],
    "revenue":         ["admin", "manager"],
    "invoice":         ["admin", "manager"],
    "manage_users":    ["admin"],
    "change_password": ["admin", "manager", "staff"],
}


def can_access(role: str, key: str) -> bool:
    """Kiểm tra role có quyền truy cập menu_key không"""
    return role in PERMISSIONS.get(key, [])


def get_accessible_menus(role: str) -> list:
    """Trả về danh sách các menu mà role được phép truy cập"""
    return [k for k, roles in PERMISSIONS.items() if role in roles]