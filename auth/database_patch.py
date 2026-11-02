"""
DATABASE PATCH - Thêm bảng users vào database hiện có
Hệ thống cho thuê áo cưới Văn An

Chạy file này MỘT LẦN để nâng cấp database:
    python auth/database_patch.py

Hoặc gọi trong code:
    from auth.database_patch import apply_patch
    apply_patch()

File này an toàn để chạy nhiều lần (idempotent):
  - Nếu bảng users đã tồn tại → bỏ qua
  - Nếu tài khoản admin đã tồn tại → bỏ qua
"""

import sqlite3
import hashlib
import os
import sys

# Tìm đường dẫn database.db từ thư mục cha
BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DB_PATH  = os.path.join(BASE_DIR, "wedding_rental.db")


def _hash(password: str) -> str:
    salt = "wedding_rental_salt_2024"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def apply_patch(db_path: str = DB_PATH) -> None:
    """
    Thêm bảng users và tài khoản admin mặc định vào database.
    Hoàn toàn an toàn khi chạy nhiều lần.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # ── 1. Tạo bảng users nếu chưa có ──────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    NOT NULL UNIQUE,
            full_name     TEXT    NOT NULL,
            password_hash TEXT    NOT NULL,
            role          TEXT    NOT NULL DEFAULT 'staff',
            is_active     INTEGER NOT NULL DEFAULT 1,
            created_by    INTEGER,
            created_at    TEXT    DEFAULT (datetime('now','localtime')),
            last_login    TEXT
        )
    """)
    print("✅ Bảng 'users' đã sẵn sàng.")

    # ── 2. Thêm các hàm hỗ trợ vào database ────────────────────────────────
    # Thêm cột last_login nếu thiếu (phòng trường hợp bảng cũ hơn)
    try:
        c.execute("ALTER TABLE users ADD COLUMN last_login TEXT")
        print("   + Đã thêm cột last_login.")
    except sqlite3.OperationalError:
        pass  # Cột đã tồn tại → bỏ qua

    # ── 3. Tạo tài khoản admin mặc định nếu chưa có ─────────────────────────
    c.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
    if c.fetchone()[0] == 0:
        c.execute("""
            INSERT INTO users (username, full_name, password_hash, role)
            VALUES (?, ?, ?, ?)
        """, ("admin", "Quản Trị Viên", _hash("admin123"), "admin"))
        print("✅ Đã tạo tài khoản admin mặc định  (admin / admin123).")
    else:
        print("ℹ️  Tài khoản admin đã tồn tại, bỏ qua.")

    conn.commit()
    conn.close()
    print("\n🎉 Patch hoàn tất! Database đã sẵn sàng dùng hệ thống phân quyền.")


# ── Các hàm CRUD cho database.py gọi ────────────────────────────────────────
# Bạn hãy dán các hàm này vào cuối file database.py gốc của mình.

USER_DB_FUNCTIONS = '''
# ========== HÀM QUẢN LÝ NGƯỜI DÙNG (thêm vào database.py) ==========

def get_user_by_username(username: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users ORDER BY role, username")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def create_user(username, full_name, password_hash, role, created_by=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO users (username, full_name, password_hash, role, created_by)
        VALUES (?, ?, ?, ?, ?)
    """, (username, full_name, password_hash, role, created_by))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return new_id

def update_user_password(user_id, password_hash):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET password_hash=? WHERE id=?", (password_hash, user_id))
    conn.commit()
    conn.close()

def update_user_info(user_id, full_name, role):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET full_name=?, role=? WHERE id=?", (full_name, role, user_id))
    conn.commit()
    conn.close()

def set_user_active(user_id, is_active):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET is_active=? WHERE id=?", (1 if is_active else 0, user_id))
    conn.commit()
    conn.close()

def update_last_login(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET last_login=datetime(\'now\',\'localtime\') WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
'''


if __name__ == "__main__":
    print("=" * 55)
    print("  AUTH DATABASE PATCH - Áo Cưới Thanh Hằng")
    print("=" * 55)

    # Cho phép truyền đường dẫn DB tùy chỉnh qua argument
    path = sys.argv[1] if len(sys.argv) > 1 else DB_PATH
    if not os.path.exists(path):
        print(f"⚠️  Không tìm thấy database tại: {path}")
        print("   Hãy chạy main.py một lần trước để tạo DB, rồi chạy lại patch này.")
        sys.exit(1)

    apply_patch(path)

    print("\n" + "─" * 55)
    print("📋 BƯỚC TIẾP THEO:")
    print("   1. Dán các hàm trong USER_DB_FUNCTIONS vào cuối database.py")
    print("      (hoặc xem file auth/database_patch.py phần USER_DB_FUNCTIONS)")
    print("   2. Thêm vào main.py:")
    print("      from auth import AuthService, ROLE_LABELS")
    print("   3. Chạy lại main.py bình thường")
    print("─" * 55)
