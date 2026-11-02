"""
DATABASE MODULE - Quản lý cơ sở dữ liệu SQLite
Hệ thống cho thuê áo cưới Văn An
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

DB_PATH = os.path.join(os.path.dirname(__file__), "wedding_rental.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    """Khởi tạo database và tạo bảng"""
    conn = get_connection()
    c = conn.cursor()

    # Bảng khách hàng
    c.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            email TEXT,
            address TEXT,
            id_card TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    # Bảng sản phẩm trang phục nữ
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            category TEXT NOT NULL,  -- 'nu', 'nam', 'phu_kien'
            type TEXT,               -- loại cụ thể
            size TEXT,
            color TEXT,
            price_per_day REAL NOT NULL,
            deposit REAL DEFAULT 0,
            status TEXT DEFAULT 'available',  -- available, rented, maintenance
            image_path TEXT,
            description TEXT,
            rental_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    # Bảng đơn thuê
    c.execute("""
        CREATE TABLE IF NOT EXISTS rental_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_code TEXT NOT NULL UNIQUE,
            customer_id INTEGER NOT NULL,
            rental_date TEXT NOT NULL,
            return_date TEXT NOT NULL,
            actual_return_date TEXT,
            total_days INTEGER,
            subtotal REAL DEFAULT 0,
            deposit_paid REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            total_amount REAL DEFAULT 0,
            paid_amount REAL DEFAULT 0,
            payment_method TEXT DEFAULT 'cash',
            status TEXT DEFAULT 'active',  -- active, returned, overdue, cancelled
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)

    # Bảng chi tiết đơn thuê
    c.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            price_per_day REAL NOT NULL,
            days INTEGER NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES rental_orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # Bảng thanh toán
    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_date TEXT DEFAULT (datetime('now','localtime')),
            payment_method TEXT DEFAULT 'cash',
            payment_type TEXT DEFAULT 'rental',  -- deposit, rental, penalty, refund
            notes TEXT,
            FOREIGN KEY (order_id) REFERENCES rental_orders(id)
        )
    """)


    # Bảng tài khoản người dùng
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

    # Tạo admin mặc định nếu chưa có
    import hashlib as _hl
    _salt = "wedding_rental_salt_2024"
    _hash = _hl.sha256(f"{_salt}admin123".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users (username, full_name, password_hash, role) VALUES (?,?,?,?)",
              ("admin", "Quản Trị Viên", _hash, "admin"))

    conn.commit()
    conn.close()
    print("✅ Database đã được khởi tạo thành công!")


def insert_sample_data():
    """Chèn dữ liệu mẫu vào database"""
    conn = get_connection()
    c = conn.cursor()

    # Kiểm tra nếu đã có dữ liệu
    c.execute("SELECT COUNT(*) FROM customers")
    if c.fetchone()[0] > 0:
        conn.close()
        return

    print("📦 Đang tải dữ liệu mẫu...")

    # ====== DỮ LIỆU KHÁCH HÀNG MẪU ======
    customers = [
        ("Nguyễn Thị Hoa", "0901234567", "hoa.nguyen@gmail.com", "123 Trần Hưng Đạo, Q1, TP.HCM", "012345678901", "Khách hàng thân thiết"),
        ("Trần Văn Minh", "0912345678", "minh.tran@gmail.com", "456 Lê Lợi, Q3, TP.HCM", "023456789012", ""),
        ("Lê Thị Mai", "0923456789", "mai.le@gmail.com", "789 Nguyễn Huệ, Q1, TP.HCM", "034567890123", "Đã thuê nhiều lần"),
        ("Phạm Văn Đức", "0934567890", "duc.pham@gmail.com", "321 Điện Biên Phủ, Q3, TP.HCM", "045678901234", ""),
        ("Hoàng Thị Lan", "0945678901", "lan.hoang@gmail.com", "654 Hai Bà Trưng, Q1, TP.HCM", "056789012345", "Khách VIP"),
        ("Vũ Minh Tuấn", "0956789012", "tuan.vu@gmail.com", "987 Pasteur, Q3, TP.HCM", "067890123456", ""),
        ("Đặng Thị Thu", "0967890123", "thu.dang@gmail.com", "147 Nam Kỳ Khởi Nghĩa, Q1, TP.HCM", "078901234567", ""),
        ("Bùi Quốc Hùng", "0978901234", "hung.bui@gmail.com", "258 Lý Tự Trọng, Q1, TP.HCM", "089012345678", "Khách mới"),
        ("Ngô Thị Bích", "0989012345", "bich.ngo@gmail.com", "369 Nguyễn Đình Chiểu, Q3, TP.HCM", "090123456789", ""),
        ("Trịnh Văn Nam", "0990123456", "nam.trinh@gmail.com", "741 Võ Văn Tần, Q3, TP.HCM", "001234567890", ""),
    ]

    for cust in customers:
        c.execute("""
            INSERT OR IGNORE INTO customers (name, phone, email, address, id_card, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, cust)

    # ====== DỮ LIỆU SẢN PHẨM MẪU ======
    products = [
        # Trang phục nữ
        ("VN001", "Váy Cưới Princess A-line", "nu", "Váy cưới", "S-M-L", "Trắng ngà", 500000, 2000000, "available", "Váy cưới kiểu A-line sang trọng, ren tay"),
        ("VN002", "Váy Cưới Ballgown Classic", "nu", "Váy cưới", "M-L-XL", "Trắng tinh", 600000, 2500000, "available", "Váy cưới dạng bồng xòe, phù hợp tiệc lớn"),
        ("VN003", "Áo Dài Cưới Truyền Thống", "nu", "Áo dài", "S-M-L-XL", "Đỏ thêu vàng", 350000, 1500000, "available", "Áo dài cưới truyền thống, thêu hoa văn tinh tế"),
        ("VN004", "Váy Dạ Hội Đỏ Quyến Rũ", "nu", "Váy dạ hội", "S-M-L", "Đỏ", 400000, 1800000, "available", "Váy dạ hội màu đỏ, phù hợp lễ tân hôn"),
        ("VN005", "Váy Cưới Mermaid Ôm Dáng", "nu", "Váy cưới", "S-M", "Kem", 550000, 2200000, "available", "Váy cưới đuôi cá ôm sát, tôn dáng"),
        ("VN006", "Áo Dài Hiện Đại Cách Tân", "nu", "Áo dài", "S-M-L", "Hồng pastel", 300000, 1200000, "available", "Áo dài cách tân hiện đại, trẻ trung"),
        # Trang phục nam
        ("TN001", "Vest Đen Classic 3 Mảnh", "nam", "Vest", "M-L-XL-XXL", "Đen", 300000, 1500000, "available", "Vest 3 mảnh màu đen classic, kèm cà vạt"),
        ("TN002", "Suit Trắng Royal Đẳng Cấp", "nam", "Suit", "M-L-XL", "Trắng", 350000, 1800000, "available", "Suit trắng cao cấp, phù hợp lễ cưới trang trọng"),
        ("TN003", "Vest Navy Xanh Đêm", "nam", "Vest", "M-L-XL", "Xanh navy", 280000, 1400000, "available", "Vest màu navy sang trọng, hiện đại"),
        ("TN004", "Áo Dài Nam Truyền Thống", "nam", "Áo dài", "M-L-XL", "Xanh cổ vịt", 250000, 1000000, "available", "Áo dài nam truyền thống, kèm quần"),
        ("TN005", "Bộ Tuxedo Đen Sang Trọng", "nam", "Tuxedo", "M-L-XL", "Đen", 400000, 2000000, "available", "Tuxedo đen cao cấp, kèm nơ bướm trắng"),
        ("TN006", "Vest Xám Bạc Hiện Đại", "nam", "Vest", "M-L-XL", "Xám bạc", 320000, 1600000, "available", "Vest xám bạc phong cách Âu châu"),
        # Phụ kiện
        ("PK001", "Vương Miện Cô Dâu Đính Đá", "phu_kien", "Vương miện", "Free", "Bạc", 100000, 500000, "available", "Vương miện đính đá pha lê, lấp lánh"),
        ("PK002", "Nhẫn Cưới Vàng 18K (Cặp)", "phu_kien", "Nhẫn", "Free", "Vàng", 200000, 2000000, "available", "Nhẫn cưới vàng 18K, thiết kế trơn thanh lịch"),
        ("PK003", "Khuyên Tai Ngọc Trai", "phu_kien", "Trang sức", "Free", "Trắng ngọc", 80000, 300000, "available", "Khuyên tai ngọc trai tự nhiên cao cấp"),
        ("PK004", "Giày Cô Dâu Cao Gót 7cm", "phu_kien", "Giày", "35-36-37-38-39", "Trắng", 150000, 500000, "available", "Giày cao gót đính ren, màu trắng tinh"),
        ("PK005", "Cà Vạt Lụa Cao Cấp", "phu_kien", "Cà vạt", "Free", "Đỏ/Đen/Navy", 50000, 200000, "available", "Cà vạt lụa cao cấp, nhiều màu"),
        ("PK006", "Hoa Cài Áo Chú Rể", "phu_kien", "Phụ kiện", "Free", "Trắng/Hồng", 30000, 100000, "available", "Hoa cài áo hoa tươi mẫu đơn"),
        ("PK007", "Khăn Voan Cô Dâu Dài", "phu_kien", "Khăn", "3m", "Trắng", 120000, 400000, "available", "Khăn voan dài 3m, viền ren"),
        ("PK008", "Bình Hoa Cầm Tay Cô Dâu", "phu_kien", "Hoa cầm tay", "Free", "Hồng trắng", 80000, 200000, "available", "Hoa cầm tay hoa hồng và baby breath"),
        ("PK009", "Cài Tóc Đính Đá Tiara", "phu_kien", "Cài tóc", "Free", "Vàng/Bạc", 70000, 250000, "available", "Cài tóc tiara đính đá pha lê"),
        ("PK010", "Thắt Lưng Nam Sang Trọng", "phu_kien", "Phụ kiện nam", "Free", "Đen", 40000, 150000, "available", "Thắt lưng nam da cao cấp, khóa vàng"),
    ]

    for prod in products:
        c.execute("""
            INSERT OR IGNORE INTO products 
            (code, name, category, type, size, color, price_per_day, deposit, status, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, prod)

    # ====== DỮ LIỆU ĐƠN THUÊ MẪU ======
    # Tạo đơn thuê với ngày trong quá khứ để có doanh thu
    base_date = datetime.now()

    orders_data = [
        # (customer_id, days_ago_start, duration_days, status, products)
        (1, 90, 3, "returned", [("VN001", 1), ("PK001", 1), ("PK003", 1)]),
        (2, 80, 2, "returned", [("TN001", 1), ("PK005", 1)]),
        (3, 70, 4, "returned", [("VN003", 1), ("PK007", 1)]),
        (4, 60, 3, "returned", [("TN002", 1), ("PK010", 1)]),
        (5, 55, 2, "returned", [("VN002", 1), ("PK002", 1), ("PK004", 1)]),
        (6, 45, 3, "returned", [("TN003", 1), ("PK005", 1)]),
        (7, 40, 2, "returned", [("VN004", 1), ("PK009", 1)]),
        (8, 30, 3, "returned", [("TN005", 1), ("PK006", 1)]),
        (1, 25, 2, "returned", [("VN005", 1), ("PK001", 1)]),
        (9, 20, 3, "returned", [("VN006", 1), ("PK007", 1), ("PK008", 1)]),
        (10, 15, 2, "returned", [("TN004", 1), ("PK010", 1)]),
        (3, 10, 3, "returned", [("VN001", 1), ("PK003", 1), ("PK009", 1)]),
        # Đơn đang thuê
        (2, 2, 5, "active", [("TN001", 1), ("TN002", 1)]),
        (5, 1, 3, "active", [("VN002", 1), ("PK001", 1)]),
        (7, 0, 4, "active", [("VN003", 1), ("PK007", 1)]),
        # Đơn quá hạn
        (4, 8, 3, "overdue", [("TN003", 1), ("PK005", 1)]),
    ]

    order_counter = 1
    for cust_id, days_ago, duration, status, items in orders_data:
        rental_date = (base_date - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        return_date = (base_date - timedelta(days=days_ago) + timedelta(days=duration)).strftime("%Y-%m-%d")
        order_code = f"DH{base_date.strftime('%Y%m')}{order_counter:03d}"

        # Tính tổng tiền
        subtotal = 0
        for prod_code, qty in items:
            c.execute("SELECT price_per_day FROM products WHERE code=?", (prod_code,))
            row = c.fetchone()
            if row:
                subtotal += row["price_per_day"] * duration * qty

        deposit = subtotal * 0.3
        total = subtotal

        actual_return = return_date if status in ("returned",) else None

        c.execute("""
            INSERT INTO rental_orders 
            (order_code, customer_id, rental_date, return_date, actual_return_date,
             total_days, subtotal, deposit_paid, total_amount, paid_amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (order_code, cust_id, rental_date, return_date, actual_return,
              duration, subtotal, deposit, total,
              total if status == "returned" else deposit, status))

        order_id = c.lastrowid

        # Thêm chi tiết đơn
        for prod_code, qty in items:
            c.execute("SELECT id, price_per_day FROM products WHERE code=?", (prod_code,))
            row = c.fetchone()
            if row:
                item_subtotal = row["price_per_day"] * duration * qty
                c.execute("""
                    INSERT INTO order_items (order_id, product_id, price_per_day, days, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                """, (order_id, row["id"], row["price_per_day"], duration, item_subtotal))

                # Cập nhật rental_count
                c.execute("UPDATE products SET rental_count = rental_count + 1 WHERE id=?", (row["id"],))

                # Cập nhật trạng thái sản phẩm nếu đang thuê
                if status == "active":
                    c.execute("UPDATE products SET status='rented' WHERE id=?", (row["id"],))

        # Thêm bản ghi thanh toán
        if status == "returned":
            c.execute("""
                INSERT INTO payments (order_id, amount, payment_date, payment_method, payment_type)
                VALUES (?, ?, ?, ?, ?)
            """, (order_id, total, return_date + " 10:00:00", "cash", "rental"))
        else:
            c.execute("""
                INSERT INTO payments (order_id, amount, payment_date, payment_method, payment_type)
                VALUES (?, ?, ?, ?, ?)
            """, (order_id, deposit, rental_date + " 10:00:00", "cash", "deposit"))

        order_counter += 1

    conn.commit()
    conn.close()
    print("✅ Dữ liệu mẫu đã được tải thành công!")
    print(f"   • {len(customers)} khách hàng")
    print(f"   • {len(products)} sản phẩm (trang phục nữ, nam, phụ kiện)")
    print(f"   • {len(orders_data)} đơn thuê mẫu")


# ========== CÁC HÀM TRUY VẤN ==========

def get_all_customers():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM customers ORDER BY name")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def search_customers(keyword):
    conn = get_connection()
    c = conn.cursor()
    kw = f"%{keyword}%"
    c.execute("SELECT * FROM customers WHERE name LIKE ? OR phone LIKE ? ORDER BY name", (kw, kw))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def add_customer(name, phone, email, address, id_card, notes):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO customers (name, phone, email, address, id_card, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, phone, email, address, id_card, notes))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return new_id

def update_customer(cid, name, phone, email, address, id_card, notes):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE customers SET name=?, phone=?, email=?, address=?, id_card=?, notes=?
        WHERE id=?
    """, (name, phone, email, address, id_card, notes, cid))
    conn.commit()
    conn.close()

def delete_customer(cid):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM customers WHERE id=?", (cid,))
    conn.commit()
    conn.close()

def get_all_products(category=None):
    conn = get_connection()
    c = conn.cursor()
    if category:
        c.execute("SELECT * FROM products WHERE category=? ORDER BY name", (category,))
    else:
        c.execute("SELECT * FROM products ORDER BY category, name")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def get_available_products(category=None):
    conn = get_connection()
    c = conn.cursor()
    if category:
        c.execute("SELECT * FROM products WHERE status='available' AND category=? ORDER BY name", (category,))
    else:
        c.execute("SELECT * FROM products WHERE status='available' ORDER BY category, name")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def add_product(code, name, category, ptype, size, color, price_per_day, deposit, description):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO products (code, name, category, type, size, color, price_per_day, deposit, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (code, name, category, ptype, size, color, price_per_day, deposit, description))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return new_id

def update_product(pid, code, name, category, ptype, size, color, price_per_day, deposit, description, status):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE products SET code=?, name=?, category=?, type=?, size=?, color=?,
        price_per_day=?, deposit=?, description=?, status=? WHERE id=?
    """, (code, name, category, ptype, size, color, price_per_day, deposit, description, status, pid))
    conn.commit()
    conn.close()

def delete_product(pid):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id=?", (pid,))
    conn.commit()
    conn.close()

def get_all_orders():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT ro.*, cu.name as customer_name, cu.phone as customer_phone
        FROM rental_orders ro
        JOIN customers cu ON ro.customer_id = cu.id
        ORDER BY ro.created_at DESC
    """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def get_order_details(order_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT oi.*, p.name as product_name, p.code as product_code, p.category
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
    """, (order_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def create_order(customer_id, rental_date, return_date, items, deposit_paid, discount, notes, payment_method):
    """items: list of (product_id, price_per_day, days)"""
    conn = get_connection()
    c = conn.cursor()

    # Tạo mã đơn
    c.execute("SELECT COUNT(*) FROM rental_orders")
    count = c.fetchone()[0]
    order_code = f"DH{datetime.now().strftime('%Y%m')}{count+1:03d}"

    # Tính số ngày và tổng tiền
    d1 = datetime.strptime(rental_date, "%Y-%m-%d")
    d2 = datetime.strptime(return_date, "%Y-%m-%d")
    total_days = max(1, (d2 - d1).days)

    subtotal = sum(ppd * total_days for _, ppd, _ in items)
    total_amount = subtotal - discount

    c.execute("""
        INSERT INTO rental_orders 
        (order_code, customer_id, rental_date, return_date, total_days,
         subtotal, deposit_paid, discount, total_amount, paid_amount, 
         payment_method, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
    """, (order_code, customer_id, rental_date, return_date, total_days,
          subtotal, deposit_paid, discount, total_amount, deposit_paid,
          payment_method, notes))

    order_id = c.lastrowid

    for prod_id, ppd, days in items:
        item_sub = ppd * total_days
        c.execute("""
            INSERT INTO order_items (order_id, product_id, price_per_day, days, subtotal)
            VALUES (?, ?, ?, ?, ?)
        """, (order_id, prod_id, ppd, total_days, item_sub))
        c.execute("UPDATE products SET status='rented', rental_count=rental_count+1 WHERE id=?", (prod_id,))

    if deposit_paid > 0:
        c.execute("""
            INSERT INTO payments (order_id, amount, payment_method, payment_type)
            VALUES (?, ?, ?, 'deposit')
        """, (order_id, deposit_paid, payment_method))

    conn.commit()
    conn.close()
    return order_id, order_code

def return_order(order_id, actual_return_date, extra_payment, payment_method):
    conn = get_connection()
    c = conn.cursor()

    c.execute("UPDATE rental_orders SET status='returned', actual_return_date=? WHERE id=?",
              (actual_return_date, order_id))

    items = get_order_details(order_id)
    for item in items:
        c.execute("UPDATE products SET status='available' WHERE id=?", (item["product_id"],))

    if extra_payment > 0:
        c.execute("""
            INSERT INTO payments (order_id, amount, payment_method, payment_type)
            VALUES (?, ?, ?, 'rental')
        """, (order_id, extra_payment, payment_method))
        c.execute("UPDATE rental_orders SET paid_amount = paid_amount + ? WHERE id=?",
                  (extra_payment, order_id))

    conn.commit()
    conn.close()

def get_revenue_stats():
    """Thống kê doanh thu theo tháng"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT strftime('%Y-%m', payment_date) as month,
               SUM(amount) as revenue,
               COUNT(DISTINCT order_id) as orders
        FROM payments
        WHERE payment_type IN ('rental', 'deposit')
        GROUP BY month
        ORDER BY month DESC
        LIMIT 12
    """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def get_dashboard_stats():
    """Lấy thống kê tổng quan cho dashboard"""
    conn = get_connection()
    c = conn.cursor()

    stats = {}

    c.execute("SELECT COUNT(*) FROM rental_orders WHERE status='active'")
    stats["active_orders"] = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM rental_orders WHERE status='overdue'")
    stats["overdue_orders"] = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM products")
    stats["total_products"] = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM products WHERE category='nu'")
    stats["female_products"] = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM products WHERE category='phu_kien'")
    stats["accessories"] = c.fetchone()[0]

    # Doanh thu tháng hiện tại
    current_month = datetime.now().strftime("%Y-%m")
    c.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM payments
        WHERE strftime('%Y-%m', payment_date) = ?
        AND payment_type IN ('rental')
    """, (current_month,))
    stats["current_month_revenue"] = c.fetchone()[0]

    # Doanh thu tháng trước
    last_month = (datetime.now().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    c.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM payments
        WHERE strftime('%Y-%m', payment_date) = ?
        AND payment_type IN ('rental')
    """, (last_month,))
    stats["last_month_revenue"] = c.fetchone()[0]

    # Top sản phẩm được thuê nhiều nhất
    c.execute("""
        SELECT p.name, p.category, p.rental_count
        FROM products p ORDER BY rental_count DESC LIMIT 5
    """)
    stats["top_products"] = [dict(r) for r in c.fetchall()]

    # Đơn gần đây
    c.execute("""
        SELECT ro.order_code, cu.name, ro.status, ro.total_amount, ro.rental_date
        FROM rental_orders ro
        JOIN customers cu ON ro.customer_id = cu.id
        ORDER BY ro.created_at DESC LIMIT 5
    """)
    stats["recent_orders"] = [dict(r) for r in c.fetchall()]

    conn.close()
    return stats

def get_overdue_orders():
    conn = get_connection()
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("""
        SELECT ro.*, cu.name as customer_name, cu.phone as customer_phone
        FROM rental_orders ro
        JOIN customers cu ON ro.customer_id = cu.id
        WHERE ro.status = 'active' AND ro.return_date < ?
        ORDER BY ro.return_date
    """, (today,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def get_revenue_by_6months():
    """Doanh thu 6 tháng gần nhất"""
    conn = get_connection()
    c = conn.cursor()
    months = []
    for i in range(5, -1, -1):
        d = datetime.now().replace(day=1) - timedelta(days=i*30)
        months.append(d.strftime("%Y-%m"))

    result = {}
    for m in months:
        c.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM payments
            WHERE strftime('%Y-%m', payment_date) = ?
            AND payment_type = 'rental'
        """, (m,))
        result[m] = c.fetchone()[0]

        c.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM payments
            WHERE strftime('%Y-%m', payment_date) = ?
            AND payment_type = 'deposit'
        """, (m,))
        result[m + "_dep"] = c.fetchone()[0]

    conn.close()
    return result, months


# ========== HÀM QUẢN LÝ NGƯỜI DÙNG ==========

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
    c.execute("UPDATE users SET last_login=datetime('now','localtime') WHERE id=?", (user_id,))
    conn.commit()
    conn.close()