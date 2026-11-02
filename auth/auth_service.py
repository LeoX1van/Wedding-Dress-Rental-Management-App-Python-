"""
AUTH SERVICE - Xác thực người dùng & phân quyền
Hệ thống cho thuê áo cưới Thanh Hằng

Vai trò:
  admin     - Toàn quyền: xem/sửa/xóa tất cả, quản lý tài khoản
  manager   - Quản lý: xem doanh số, in hóa đơn, quản lý kho & đơn thuê
  staff     - Nhân viên: tạo đơn, tra cứu khách hàng, kho (chỉ xem)

Cách dùng:
  from auth import AuthService, ROLE_LABELS
"""

import hashlib
import sys
import os

# Cho phép import database từ thư mục cha
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import database as db


# ======= PHÂN QUYỀN THEO VAI TRÒ =======
PERMISSIONS = {
    "dashboard":       ["admin", "manager", "staff"],
    "orders":          ["admin", "manager", "staff"],
    "new_order":       ["admin", "manager", "staff"],
    "wardrobe_female": ["admin", "manager", "staff"],
    "wardrobe_male":   ["admin", "manager", "staff"],
    "accessories":     ["admin", "manager", "staff"],
    "customers":       ["admin", "manager", "staff"],
    "return_schedule": ["admin", "manager", "staff"],
    "revenue":         ["admin", "manager"],       # Nhân viên KHÔNG xem doanh số
    "invoice":         ["admin", "manager"],       # Nhân viên KHÔNG in hóa đơn
    "manage_users":    ["admin"],                  # Chỉ admin quản lý tài khoản
    "change_password": ["admin", "manager", "staff"],
}

ROLE_LABELS = {
    "admin":   "👑 Quản trị viên",
    "manager": "🏷️ Quản lý",
    "staff":   "👤 Nhân viên",
}


def _hash_password(password: str) -> str:
    """Hash mật khẩu SHA-256 + salt"""
    salt = "wedding_rental_salt_2024"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


class AuthService:

    # ---------- Đăng nhập ----------

    @staticmethod
    def login(username: str, password: str) -> dict | None:
        """
        Xác thực đăng nhập.
        Trả về dict thông tin user nếu thành công, None nếu sai/bị khóa.
        """
        if not username or not password:
            return None
        user = db.get_user_by_username(username.strip())
        if user and user["password_hash"] == _hash_password(password) and user["is_active"]:
            return user
        return None

    # ---------- Đăng ký / Tạo tài khoản ----------

    @staticmethod
    def register(username: str, full_name: str, password: str,
                 role: str = "staff", created_by: int = None) -> int:
        """
        Tạo tài khoản mới. Trả về ID user vừa tạo.
        Raises ValueError nếu dữ liệu không hợp lệ hoặc username trùng.
        """
        username = username.strip()
        full_name = full_name.strip()

        if not username or not full_name or not password:
            raise ValueError("Tên đăng nhập, họ tên và mật khẩu không được để trống!")
        if len(username) < 3:
            raise ValueError("Tên đăng nhập phải có ít nhất 3 ký tự!")
        if len(password) < 6:
            raise ValueError("Mật khẩu phải có ít nhất 6 ký tự!")
        if role not in ("admin", "manager", "staff"):
            raise ValueError("Vai trò không hợp lệ!")
        if db.get_user_by_username(username):
            raise ValueError(f"Tên đăng nhập '{username}' đã tồn tại!")

        return db.create_user(username, full_name, _hash_password(password), role, created_by)

    # ---------- Đổi mật khẩu ----------

    @staticmethod
    def change_password(user_id: int, old_password: str, new_password: str) -> None:
        """Đổi mật khẩu. Raises ValueError nếu mật khẩu cũ sai hoặc mới quá ngắn."""
        user = db.get_user_by_id(user_id)
        if not user:
            raise ValueError("Không tìm thấy tài khoản!")
        if user["password_hash"] != _hash_password(old_password):
            raise ValueError("Mật khẩu cũ không đúng!")
        if len(new_password) < 6:
            raise ValueError("Mật khẩu mới phải có ít nhất 6 ký tự!")
        db.update_user_password(user_id, _hash_password(new_password))

    @staticmethod
    def reset_password(user_id: int, new_password: str) -> None:
        """Admin reset mật khẩu cho user khác (không cần mật khẩu cũ)."""
        if len(new_password) < 6:
            raise ValueError("Mật khẩu mới phải có ít nhất 6 ký tự!")
        db.update_user_password(user_id, _hash_password(new_password))

    # ---------- Phân quyền ----------

    @staticmethod
    def can_access(role: str, menu_key: str) -> bool:
        """Kiểm tra role có quyền truy cập menu_key không."""
        return role in PERMISSIONS.get(menu_key, [])

    @staticmethod
    def get_accessible_menus(role: str) -> list[str]:
        """Trả về danh sách menu_key mà role được phép vào."""
        return [key for key, roles in PERMISSIONS.items() if role in roles]

    # ---------- Quản lý user (admin) ----------

    @staticmethod
    def get_all_users() -> list:
        return db.get_all_users()

    @staticmethod
    def update_user(user_id: int, full_name: str, role: str) -> None:
        if not full_name.strip():
            raise ValueError("Họ tên không được để trống!")
        if role not in ("admin", "manager", "staff"):
            raise ValueError("Vai trò không hợp lệ!")
        db.update_user_info(user_id, full_name.strip(), role)

    @staticmethod
    def toggle_user_active(user_id: int, is_active: bool) -> None:
        db.set_user_active(user_id, is_active)
