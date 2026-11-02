"""
CONTEXT BUILDER - Tổng hợp dữ liệu từ DB để cung cấp cho Claude AI
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db


def build_system_prompt() -> str:
    """
    Tạo system prompt cho Claude AI, bao gồm thông tin sản phẩm thực từ database.
    Gọi hàm này mỗi khi mở cửa sổ chat để dữ liệu luôn cập nhật.
    """
    try:
        context_lines = []

        # --- Thông tin cửa hàng ---
        context_lines.append("""Bạn là trợ lý AI của cửa hàng **Áo Cưới Văn An** (tên gốc trong code là Thanh Hằng).
Nhiệm vụ của bạn là hỗ trợ nhân viên tư vấn khách hàng một cách thân thiện, chuyên nghiệp và chính xác.
Luôn trả lời bằng tiếng Việt. Sử dụng emoji phù hợp để tạo cảm giác thân thiện.
Không bịa đặt thông tin không có trong dữ liệu bên dưới.
""")

        # --- Sản phẩm từ DB ---
        conn = db.get_connection()
        c = conn.cursor()

        c.execute("""
            SELECT code, name, category, type, size, color, price_per_day, deposit, status, description
            FROM products ORDER BY category, code
        """)
        products = c.fetchall()

        if products:
            context_lines.append("## DANH MỤC SẢN PHẨM HIỆN CÓ:")

            categories = {
                "nu": "👗 TRANG PHỤC NỮ",
                "nam": "🤵 TRANG PHỤC NAM",
                "phu_kien": "💍 PHỤ KIỆN"
            }

            current_cat = None
            for p in products:
                cat = p["category"]
                if cat != current_cat:
                    current_cat = cat
                    context_lines.append(f"\n### {categories.get(cat, cat.upper())}")

                status_label = {"available": "✅ Có sẵn", "rented": "🔴 Đang thuê", "maintenance": "🔧 Bảo trì"}.get(p["status"], p["status"])
                price = f"{int(p['price_per_day']):,}đ/ngày"
                deposit = f"Đặt cọc: {int(p['deposit']):,}đ"
                context_lines.append(
                    f"- [{p['code']}] {p['name']} | Size: {p['size']} | Màu: {p['color']} | "
                    f"{price} | {deposit} | {status_label}"
                )
                if p["description"]:
                    context_lines.append(f"  → {p['description']}")

        # --- Thống kê nhanh ---
        c.execute("SELECT COUNT(*) FROM customers")
        total_customers = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM rental_orders WHERE status='active'")
        active_orders = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM products WHERE status='available'")
        available_products = c.fetchone()[0]

        conn.close()

        context_lines.append(f"""
## THÔNG TIN CỬA HÀNG:
- Tổng khách hàng trong hệ thống: {total_customers}
- Đơn đang thuê hiện tại: {active_orders}
- Sản phẩm đang có sẵn: {available_products}

## QUY ĐỊNH THUÊ:
- Giá tính theo ngày thuê thực tế
- Khách hàng phải đặt cọc khi nhận hàng
- Trả hàng trễ có thể phát sinh phí phạt
- Kiểm tra kỹ sản phẩm khi nhận và trả

## CÁCH TRẢ LỜI:
- Nếu khách hỏi sản phẩm nào đó: tra cứu danh sách ở trên và trả lời chính xác
- Nếu khách hỏi giá: cung cấp giá thuê/ngày và tiền đặt cọc
- Nếu sản phẩm đang được thuê: thông báo lịch lịch sự và gợi ý sản phẩm thay thế
- Nếu câu hỏi ngoài phạm vi cửa hàng: từ chối lịch sự và giữ focus vào tư vấn áo cưới
""")

        return "\n".join(context_lines)

    except Exception as e:
        return f"""Bạn là trợ lý AI của cửa hàng Áo Cưới Văn An.
Hỗ trợ tư vấn khách hàng về dịch vụ cho thuê áo cưới.
Trả lời bằng tiếng Việt, thân thiện và chuyên nghiệp.
(Lưu ý: Không thể tải dữ liệu sản phẩm - {e})"""