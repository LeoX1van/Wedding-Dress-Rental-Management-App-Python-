"""
MAIN APPLICATION - Phần mềm Quản lý Cho Thuê Áo Cưới
Áo Cưới Văn An - Hệ thống quản lý
Ngôn ngữ: Python (tkinter + matplotlib)
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sys
import os
import hashlib

sys.path.insert(0, os.path.dirname(__file__))

import database as db
from services.rental_service import RentalService
from services.inventory_service import InventoryService
from services.report_service import ReportService
from utils.helpers import format_currency, current_date_str, date_after_days, days_until
from utils.validators import validate_required, validate_date_range, validate_positive_number
from exceptions.rental_exceptions import WeddingRentalError
from ai_chat.chat_window import FloatingChat


# ======= AUTH - PHÂN QUYỀN =======
_SALT = "wedding_rental_salt_2024"

def _hash_pw(pw: str) -> str:
    return hashlib.sha256(f"{_SALT}{pw}".encode()).hexdigest()

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
    return role in PERMISSIONS.get(key, [])

def get_accessible_menus(role: str) -> list:
    return [k for k, roles in PERMISSIONS.items() if role in roles]



# ======= MÀN HÌNH ĐĂNG NHẬP =======
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Đăng nhập - Áo Cưới Văn An")
        self.geometry("440x560")
        self.resizable(False, False)
        self.configure(bg="#F0F2F5")
        self.logged_user = None
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"440x560+{(sw-440)//2}+{(sh-560)//2}")
        self._build()

    def _build(self):
        banner = tk.Frame(self, bg="#E8567A", height=160)
        banner.pack(fill="x"); banner.pack_propagate(False)
        tk.Label(banner, text="💍", bg="#E8567A", fg="white",
                 font=("Segoe UI", 36)).pack(pady=(28, 0))
        tk.Label(banner, text="Áo Cưới Văn An", bg="#E8567A", fg="white",
                 font=("Segoe UI", 16, "bold")).pack()
        tk.Label(banner, text="Hệ thống quản lý cho thuê",
                 bg="#E8567A", fg="#FFD6E4", font=("Segoe UI", 9)).pack()

        card = tk.Frame(self, bg="white",
                        highlightbackground="#E5E7EB", highlightthickness=1)
        card.pack(fill="both", expand=True, padx=32, pady=24)

        tk.Label(card, text="ĐĂNG NHẬP HỆ THỐNG", bg="white",
                 fg="#1A1D27", font=("Segoe UI", 13, "bold")).pack(pady=(24, 2))
        tk.Label(card, text="Nhập thông tin tài khoản của bạn",
                 bg="white", fg="#6B7280", font=("Segoe UI", 9)).pack(pady=(0, 18))

        tk.Label(card, text="Tên đăng nhập", bg="white", fg="#374151",
                 font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x", padx=28)
        self.uv = tk.StringVar()
        ue = tk.Entry(card, textvariable=self.uv, font=("Segoe UI", 11),
                      relief="solid", bd=1)
        ue.pack(fill="x", padx=28, ipady=7, pady=(3, 12))
        ue.focus()

        tk.Label(card, text="Mật khẩu", bg="white", fg="#374151",
                 font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x", padx=28)
        self.pv = tk.StringVar()
        self.pe = tk.Entry(card, textvariable=self.pv, show="●",
                           font=("Segoe UI", 11), relief="solid", bd=1)
        self.pe.pack(fill="x", padx=28, ipady=7, pady=(3, 4))
        self.pe.bind("<Return>", lambda e: self._login())

        self.showpw = tk.BooleanVar()
        tk.Checkbutton(card, text="Hiện mật khẩu", variable=self.showpw,
                       bg="white", fg="#6B7280", font=("Segoe UI", 8),
                       command=lambda: self.pe.config(show="" if self.showpw.get() else "●"),
                       cursor="hand2").pack(anchor="w", padx=28, pady=(0, 12))

        self.msg = tk.StringVar()
        tk.Label(card, textvariable=self.msg, bg="white", fg="#EF4444",
                 font=("Segoe UI", 9), wraplength=340).pack(pady=(0, 6))

        tk.Button(card, text="🔐  ĐĂNG NHẬP", bg="#E8567A", fg="white",
                  font=("Segoe UI", 11, "bold"), relief="flat", pady=9,
                  cursor="hand2", activebackground="#C43D62",
                  command=self._login).pack(fill="x", padx=28, pady=(0, 10))

        hint = tk.Frame(card, bg="#FFF7ED",
                        highlightbackground="#FED7AA", highlightthickness=1)
        hint.pack(fill="x", padx=28, pady=(2, 0))
        tk.Label(hint, text="💡  Tài khoản mặc định: admin / admin123",
                 bg="#FFF7ED", fg="#92400E", font=("Segoe UI", 8),
                 padx=10, pady=6).pack()

        ue.bind("<Return>", lambda e: self.pe.focus())

    def _login(self):
        u = self.uv.get().strip()
        p = self.pv.get()
        if not u or not p:
            self.msg.set("⚠️ Vui lòng nhập đầy đủ thông tin!"); return
        user = db.get_user_by_username(u)
        if user and user["password_hash"] == _hash_pw(p) and user["is_active"]:
            db.update_last_login(user["id"])
            self.logged_user = user
            self.destroy()
        else:
            self.msg.set("❌ Sai tên đăng nhập / mật khẩu hoặc tài khoản bị khóa!")
            self.pv.set("")

# ======= CỬA SỔ CHÍNH =======
class WeddingRentalApp(tk.Tk):
    def __init__(self, current_user: dict):
        super().__init__()
        self.current_user = current_user
        self.title("Áo Cưới Văn An - Hệ Thống Quản Lý")
        self.geometry("1280x780")
        self.minsize(1100, 700)
        self.configure(bg="#F0F2F5")

        self.colors = {
            "primary": "#E8567A",
            "primary_dark": "#C43D62",
            "secondary": "#5B9BD5",
            "sidebar_bg": "#2C2F3A",
            "sidebar_text": "#C8CDD8",
            "sidebar_active": "#E8567A",
            "content_bg": "#F0F2F5",
            "card_bg": "#FFFFFF",
            "text_dark": "#1A1D27",
            "text_gray": "#6B7280",
            "success": "#22C55E",
            "warning": "#F59E0B",
            "danger": "#EF4444",
            "border": "#E5E7EB",
        }

        self.font_title = ("Segoe UI", 20, "bold")
        self.font_h2 = ("Segoe UI", 14, "bold")
        self.font_h3 = ("Segoe UI", 11, "bold")
        self.font_body = ("Segoe UI", 10)
        self.font_small = ("Segoe UI", 9)

        self.current_frame = None
        self._build_layout()
        self._show_dashboard()
        self.after(300, lambda: FloatingChat(self, self))

    def _build_layout(self):
        self.sidebar = tk.Frame(self, bg=self.colors["sidebar_bg"], width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        logo_frame = tk.Frame(self.sidebar, bg="#1E2130", height=70)
        logo_frame.pack(fill="x")
        logo_frame.pack_propagate(False)
        tk.Label(logo_frame, text="💍 Văn An", bg="#1E2130",
                 fg="#FFFFFF", font=("Segoe UI", 13, "bold")).pack(pady=22)
        tk.Label(logo_frame, text="Hệ thống quản lý", bg="#1E2130",
                 fg="#9CA3AF", font=("Segoe UI", 8)).place(x=42, y=42)

        # --- Thông tin người đăng nhập ---
        uf = tk.Frame(self.sidebar, bg="#252837", pady=6)
        uf.pack(fill="x")
        role_lbl = ROLE_LABELS.get(self.current_user["role"], self.current_user["role"])
        tk.Label(uf, text=f"👤 {self.current_user['full_name']}",
                 bg="#252837", fg="#FFFFFF", font=("Segoe UI", 9, "bold"),
                 padx=14).pack(anchor="w")
        tk.Label(uf, text=role_lbl, bg="#252837", fg="#F9A8C9",
                 font=("Segoe UI", 8), padx=14).pack(anchor="w")
        tk.Button(uf, text="🚪 Đăng xuất", bg="#252837", fg="#9CA3AF",
                  font=("Segoe UI", 8), relief="flat", padx=14, cursor="hand2",
                  activebackground="#3D4155", activeforeground="white",
                  command=self._logout).pack(anchor="w", pady=(4, 0))

        self.menu_buttons = {}
        accessible = get_accessible_menus(self.current_user["role"])
        all_menus = [
            ("TỔNG QUAN", [("🏠  Tổng quan", "dashboard")]),
            ("NGHIỆP VỤ", [
                ("📋  Đơn thuê", "orders"),
                ("➕  Tạo đơn mới", "new_order"),
                ("👗  Kho trang phục nữ", "wardrobe_female"),
                ("🤵  Kho trang phục nam", "wardrobe_male"),
                ("💎  Phụ kiện", "accessories"),
            ]),
            ("QUẢN LÝ", [
                ("👥  Khách hàng", "customers"),
                ("📅  Lịch trả đồ", "return_schedule"),
                ("📊  Doanh số", "revenue"),
                ("🧾  In hóa đơn", "invoice"),
            ]),
            ("HỆ THỐNG", [
                ("🔑  Quản lý tài khoản", "manage_users"),
                ("🔒  Đổi mật khẩu", "change_password"),
            ]),
        ]

        for group_name, items in all_menus:
            visible = [(lbl, k) for lbl, k in items
                       if k in accessible or k == "change_password"]
            if not visible:
                continue
            tk.Label(self.sidebar, text=group_name, bg=self.colors["sidebar_bg"],
                     fg="#6B7280", font=("Segoe UI", 8, "bold"),
                     padx=20, pady=4).pack(fill="x", pady=(12, 0))
            for label, key in visible:
                btn = tk.Button(
                    self.sidebar, text=label, bg=self.colors["sidebar_bg"],
                    fg=self.colors["sidebar_text"], font=("Segoe UI", 10),
                    relief="flat", cursor="hand2", anchor="w", padx=20, pady=7,
                    activebackground="#3D4155", activeforeground="#FFFFFF",
                    command=lambda k=key: self._navigate(k)
                )
                btn.pack(fill="x")
                self.menu_buttons[key] = btn

        self.content_area = tk.Frame(self, bg=self.colors["content_bg"])
        self.content_area.pack(side="right", fill="both", expand=True)

    def _navigate(self, key):
        for k, btn in self.menu_buttons.items():
            btn.configure(bg=self.colors["sidebar_bg"], fg=self.colors["sidebar_text"])
        if key in self.menu_buttons:
            self.menu_buttons[key].configure(bg="#3D4155", fg="#FFFFFF")
        for w in self.content_area.winfo_children():
            w.destroy()

        frames = {
            "dashboard": DashboardFrame,
            "orders": OrdersFrame,
            "new_order": NewOrderFrame,
            "wardrobe_female": WardrobeFrame,
            "wardrobe_male": WardrobeMaleFrame,
            "accessories": AccessoriesFrame,
            "customers": CustomersFrame,
            "return_schedule": ReturnScheduleFrame,
            "revenue": RevenueFrame,
            "invoice": InvoiceFrame,
            "manage_users": ManageUsersFrame,
            "change_password": ChangePasswordFrame,
        }

        if key in frames:
            frame = frames[key](self.content_area, self)
            frame.pack(fill="both", expand=True)

    def _logout(self):
        if messagebox.askyesno("Đăng xuất", "Bạn có chắc muốn đăng xuất?"):
            self.destroy()
            login = LoginWindow()
            login.mainloop()
            if login.logged_user:
                WeddingRentalApp(login.logged_user).mainloop()

    def _show_dashboard(self):
        self._navigate("dashboard")


# ======= DASHBOARD =======
class DashboardFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=app.colors["content_bg"])
        self.app = app
        self._build()

    def _build(self):
        from datetime import datetime
        header = tk.Frame(self, bg=self.app.colors["content_bg"])
        header.pack(fill="x", padx=24, pady=(20, 10))
        tk.Label(header, text="Tổng quan", bg=self.app.colors["content_bg"],
                 fg=self.app.colors["text_dark"], font=self.app.font_title).pack(side="left")
        tk.Label(header, text=f"Hôm nay: {datetime.now().strftime('%d/%m/%Y')}",
                 bg=self.app.colors["content_bg"], fg=self.app.colors["text_gray"],
                 font=self.app.font_body).pack(side="right", pady=8)
        tk.Button(header, text="+ Tạo đơn mới", bg=self.app.colors["primary"],
                  fg="white", font=("Segoe UI", 10, "bold"), relief="flat",
                  padx=16, pady=6, cursor="hand2",
                  command=lambda: self.app._navigate("new_order")).pack(side="right", padx=10)

        stats = ReportService.get_dashboard_stats()
        cards_frame = tk.Frame(self, bg=self.app.colors["content_bg"])
        cards_frame.pack(fill="x", padx=24, pady=(0, 16))

        rev_change = 0
        if stats["last_month_revenue"] > 0:
            rev_change = (stats["current_month_revenue"] - stats["last_month_revenue"]) / stats["last_month_revenue"] * 100

        cards = [
            ("Đơn đang thuê", str(stats["active_orders"]),
             "+2 so với tuần trước", self.app.colors["text_dark"], "#EBF3FF", "📋"),
            ("Doanh thu tháng này",
             format_currency(stats['current_month_revenue']),
             f"{'+' if rev_change >= 0 else ''}{rev_change:.0f}% so với tháng trước",
             "#22C55E", "#F0FDF4", "💰"),
            ("Quá hạn trả", str(stats["overdue_orders"]),
             "Cần liên hệ ngay", "#EF4444", "#FEF2F2", "⚠️"),
            ("Tổng sản phẩm", str(stats["total_products"]),
             f"{stats['female_products']} trang phục · {stats['accessories']} phụ kiện",
             self.app.colors["text_dark"], "#FFF7ED", "👗"),
        ]

        for i, (title, value, sub, val_color, bg_color, icon) in enumerate(cards):
            card = tk.Frame(cards_frame, bg=bg_color, relief="flat",
                            highlightbackground=self.app.colors["border"],
                            highlightthickness=1)
            card.grid(row=0, column=i, padx=6, pady=4, sticky="nsew", ipadx=12, ipady=12)
            cards_frame.columnconfigure(i, weight=1)
            tk.Label(card, text=icon + "  " + title, bg=bg_color,
                     fg=self.app.colors["text_gray"], font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(12, 2))
            tk.Label(card, text=value, bg=bg_color,
                     fg=val_color, font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=14)
            tk.Label(card, text=sub, bg=bg_color,
                     fg=self.app.colors["text_gray"], font=("Segoe UI", 8)).pack(anchor="w", padx=14, pady=(2, 10))

        bottom = tk.Frame(self, bg=self.app.colors["content_bg"])
        bottom.pack(fill="both", expand=True, padx=24, pady=4)
        bottom.columnconfigure(0, weight=3)
        bottom.columnconfigure(1, weight=2)

        left_card = self._make_card(bottom, "Đơn gần đây")
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        cols = ("Khách hàng", "Trạng thái", "Ngày thuê", "Tổng tiền")
        tree = ttk.Treeview(left_card, columns=cols, show="headings", height=6)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=130 if col != "Khách hàng" else 160)
        tree.pack(fill="both", expand=True, padx=8, pady=4)

        status_labels = {"active": "Đang thuê", "returned": "Đã trả", "overdue": "Quá hạn"}
        for row in stats["recent_orders"]:
            status = status_labels.get(row["status"], row["status"])
            tree.insert("", "end", values=(
                row["name"], status, row["rental_date"],
                format_currency(row['total_amount'])
            ))

        right_card = self._make_card(bottom, "Sản phẩm thuê nhiều nhất")
        right_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        for i, prod in enumerate(stats["top_products"], 1):
            cat_map = {"nu": "👗 Nữ", "nam": "🤵 Nam", "phu_kien": "💎 Phụ kiện"}
            row_frame = tk.Frame(right_card, bg=self.app.colors["card_bg"])
            row_frame.pack(fill="x", padx=10, pady=3)
            rank_colors = ["#E8567A", "#5B9BD5", "#22C55E", "#F59E0B", "#8B5CF6"]
            tk.Label(row_frame, text=str(i), bg=rank_colors[i-1], fg="white",
                     font=("Segoe UI", 9, "bold"), width=2, height=1).pack(side="left", padx=(0, 8))
            tk.Label(row_frame, text=prod["name"][:28], bg=self.app.colors["card_bg"],
                     fg=self.app.colors["text_dark"], font=("Segoe UI", 9)).pack(side="left")
            tk.Label(row_frame, text=f"{prod['rental_count']} lần",
                     bg=self.app.colors["card_bg"], fg=self.app.colors["text_gray"],
                     font=("Segoe UI", 9)).pack(side="right")

    def _make_card(self, parent, title):
        frame = tk.Frame(parent, bg=self.app.colors["card_bg"],
                         highlightbackground=self.app.colors["border"], highlightthickness=1)
        tk.Label(frame, text=title, bg=self.app.colors["card_bg"],
                 fg=self.app.colors["text_dark"], font=self.app.font_h3,
                 padx=16, pady=10).pack(anchor="w")
        tk.Frame(frame, bg=self.app.colors["border"], height=1).pack(fill="x")
        return frame


# ======= KHÁCH HÀNG =======
class CustomersFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=app.colors["content_bg"])
        self.app = app
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=self.app.colors["content_bg"])
        hdr.pack(fill="x", padx=24, pady=(20, 12))
        tk.Label(hdr, text="👥 Khách hàng", bg=self.app.colors["content_bg"],
                 fg=self.app.colors["text_dark"], font=self.app.font_title).pack(side="left")
        tk.Button(hdr, text="+ Thêm khách hàng", bg=self.app.colors["primary"],
                  fg="white", font=("Segoe UI", 10, "bold"), relief="flat",
                  padx=14, pady=6, cursor="hand2",
                  command=self._add_customer).pack(side="right")

        search_frame = tk.Frame(self, bg=self.app.colors["content_bg"])
        search_frame.pack(fill="x", padx=24, pady=(0, 10))
        tk.Label(search_frame, text="🔍 Tìm kiếm:", bg=self.app.colors["content_bg"],
                 fg=self.app.colors["text_gray"], font=self.app.font_body).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self._load_data())
        tk.Entry(search_frame, textvariable=self.search_var, font=self.app.font_body,
                 width=30, relief="solid", bd=1).pack(side="left", padx=8, ipady=4)

        card = tk.Frame(self, bg=self.app.colors["card_bg"],
                        highlightbackground=self.app.colors["border"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        cols = ("ID", "Họ và tên", "Điện thoại", "Email", "Địa chỉ", "CMND/CCCD", "Ghi chú")
        self.tree = ttk.Treeview(card, columns=cols, show="headings", height=18)
        widths = [40, 160, 110, 160, 200, 120, 120]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, minwidth=40)
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        self.tree.bind("<Double-1>", self._edit_customer)

        btn_frame = tk.Frame(card, bg=self.app.colors["card_bg"])
        btn_frame.pack(fill="x", padx=8, pady=6)
        tk.Button(btn_frame, text="✏️ Sửa", bg=self.app.colors["secondary"], fg="white",
                  relief="flat", padx=12, pady=4, cursor="hand2",
                  command=self._edit_customer_btn).pack(side="left", padx=4)
        tk.Button(btn_frame, text="🗑️ Xóa", bg=self.app.colors["danger"], fg="white",
                  relief="flat", padx=12, pady=4, cursor="hand2",
                  command=self._delete_customer).pack(side="left", padx=4)

        self._load_data()

    def _load_data(self):
        kw = self.search_var.get() if hasattr(self, "search_var") else ""
        customers = RentalService.get_all_customers(kw)
        self.tree.delete(*self.tree.get_children())
        for c in customers:
            self.tree.insert("", "end", iid=c.id, values=(
                c.id, c.name, c.phone, c.email, c.address, c.id_card, c.notes
            ))

    def _add_customer(self):
        CustomerDialog(self, self.app, None, self._load_data)

    def _edit_customer_btn(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Thông báo", "Vui lòng chọn khách hàng!")
            return
        CustomerDialog(self, self.app, int(sel[0]), self._load_data)

    def _edit_customer(self, event):
        sel = self.tree.selection()
        if sel:
            CustomerDialog(self, self.app, int(sel[0]), self._load_data)

    def _delete_customer(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Thông báo", "Vui lòng chọn khách hàng!")
            return
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa khách hàng này?"):
            RentalService.delete_customer(int(sel[0]))
            self._load_data()


class CustomerDialog(tk.Toplevel):
    def __init__(self, parent, app, cid, callback):
        super().__init__(parent)
        self.app = app
        self.cid = cid
        self.callback = callback
        self.title("Thêm khách hàng" if not cid else "Sửa thông tin khách hàng")
        self.geometry("480x420")
        self.resizable(False, False)
        self.grab_set()
        self._build()
        if cid:
            self._load_data()

    def _build(self):
        tk.Label(self, text="Thông tin khách hàng", font=("Segoe UI", 13, "bold"), pady=12).pack()
        form = tk.Frame(self)
        form.pack(padx=24, pady=8, fill="x")
        fields = [("Họ và tên *", "name"), ("Điện thoại *", "phone"),
                  ("Email", "email"), ("Địa chỉ", "address"),
                  ("CMND/CCCD", "id_card"), ("Ghi chú", "notes")]
        self.vars = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(form, text=label, font=("Segoe UI", 9), anchor="w",
                     width=14).grid(row=i, column=0, sticky="w", pady=5)
            var = tk.StringVar()
            self.vars[key] = var
            tk.Entry(form, textvariable=var, font=("Segoe UI", 10),
                     width=30, relief="solid", bd=1).grid(row=i, column=1, sticky="ew", pady=5, padx=(8, 0))
            form.columnconfigure(1, weight=1)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=16)
        tk.Button(btn_frame, text="💾 Lưu", bg=self.app.colors["primary"], fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat", padx=20, pady=6,
                  cursor="hand2", command=self._save).pack(side="left", padx=8)
        tk.Button(btn_frame, text="Hủy", relief="flat", padx=16, pady=6,
                  cursor="hand2", command=self.destroy).pack(side="left", padx=8)

    def _load_data(self):
        customers = RentalService.get_all_customers()
        for c in customers:
            if c.id == self.cid:
                for key, var in self.vars.items():
                    var.set(getattr(c, key, "") or "")
                break

    def _save(self):
        name = self.vars["name"].get().strip()
        phone = self.vars["phone"].get().strip()
        if not name or not phone:
            messagebox.showerror("Lỗi", "Vui lòng nhập họ tên và điện thoại!")
            return
        try:
            if self.cid:
                RentalService.update_customer(
                    self.cid, name, phone,
                    self.vars["email"].get(), self.vars["address"].get(),
                    self.vars["id_card"].get(), self.vars["notes"].get())
            else:
                RentalService.add_customer(
                    name, phone,
                    self.vars["email"].get(), self.vars["address"].get(),
                    self.vars["id_card"].get(), self.vars["notes"].get())
            self.callback()
            self.destroy()
        except WeddingRentalError as e:
            messagebox.showerror("Lỗi", str(e))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu: {e}")


# ======= KHO TRANG PHỤC =======
class WardrobeFrame(tk.Frame):
    def __init__(self, parent, app, category="nu", title="👗 Kho Trang Phục Nữ"):
        super().__init__(parent, bg=app.colors["content_bg"])
        self.app = app
        self.category = category
        self.page_title = title
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=self.app.colors["content_bg"])
        hdr.pack(fill="x", padx=24, pady=(20, 12))
        tk.Label(hdr, text=self.page_title, bg=self.app.colors["content_bg"],
                 fg=self.app.colors["text_dark"], font=self.app.font_title).pack(side="left")
        tk.Button(hdr, text="+ Thêm sản phẩm", bg=self.app.colors["primary"], fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat", padx=14, pady=6, cursor="hand2",
                  command=self._add_product).pack(side="right")

        flt = tk.Frame(self, bg=self.app.colors["content_bg"])
        flt.pack(fill="x", padx=24, pady=(0, 10))
        self.filter_var = tk.StringVar(value="Tất cả")
        tk.Label(flt, text="Trạng thái:", bg=self.app.colors["content_bg"],
                 fg=self.app.colors["text_gray"], font=self.app.font_body).pack(side="left")
        status_cb = ttk.Combobox(flt, textvariable=self.filter_var,
                                  values=["Tất cả", "Còn trống", "Đang thuê", "Bảo trì"],
                                  width=12, state="readonly")
        status_cb.pack(side="left", padx=8)
        status_cb.bind("<<ComboboxSelected>>", lambda e: self._load_data())

        card = tk.Frame(self, bg=self.app.colors["card_bg"],
                        highlightbackground=self.app.colors["border"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        cols = ("Mã", "Tên sản phẩm", "Loại", "Kích cỡ", "Màu sắc", "Giá/ngày", "Tiền cọc", "Trạng thái", "Số lần thuê")
        self.tree = ttk.Treeview(card, columns=cols, show="headings", height=18)
        widths = [70, 220, 100, 90, 90, 100, 100, 90, 80]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w)
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        self.tree.tag_configure("rented", background="#FEF9C3")
        self.tree.tag_configure("maintenance", background="#FEE2E2")

        btn_frame = tk.Frame(card, bg=self.app.colors["card_bg"])
        btn_frame.pack(fill="x", padx=8, pady=6)
        tk.Button(btn_frame, text="✏️ Sửa", bg=self.app.colors["secondary"], fg="white",
                  relief="flat", padx=12, pady=4, cursor="hand2",
                  command=self._edit_product).pack(side="left", padx=4)
        tk.Button(btn_frame, text="🗑️ Xóa", bg=self.app.colors["danger"], fg="white",
                  relief="flat", padx=12, pady=4, cursor="hand2",
                  command=self._delete_product).pack(side="left", padx=4)

        self._load_data()

    def _load_data(self):
        status_map = {"Còn trống": "available", "Đang thuê": "rented", "Bảo trì": "maintenance"}
        products = InventoryService.get_all_products(self.category)
        flt = self.filter_var.get()
        if flt != "Tất cả":
            products = [p for p in products if p.status == status_map.get(flt)]

        self.tree.delete(*self.tree.get_children())
        for p in products:
            tag = "rented" if p.status == "rented" else ("maintenance" if p.status == "maintenance" else "")
            self.tree.insert("", "end", iid=p.id, tags=(tag,), values=(
                p.code, p.name, p.type, p.size, p.color,
                format_currency(p.price_per_day),
                format_currency(p.deposit),
                p.status_label,
                p.rental_count
            ))

    def _add_product(self):
        ProductDialog(self, self.app, None, self.category, self._load_data)

    def _edit_product(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Thông báo", "Vui lòng chọn sản phẩm!")
            return
        ProductDialog(self, self.app, int(sel[0]), self.category, self._load_data)

    def _delete_product(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Thông báo", "Vui lòng chọn sản phẩm!")
            return
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa sản phẩm này?"):
            InventoryService.delete_product(int(sel[0]))
            self._load_data()


class WardrobeMaleFrame(WardrobeFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app, category="nam", title="🤵 Kho Trang Phục Nam")


class AccessoriesFrame(WardrobeFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app, category="phu_kien", title="💎 Phụ Kiện")


class ProductDialog(tk.Toplevel):
    def __init__(self, parent, app, pid, category, callback):
        super().__init__(parent)
        self.app = app
        self.pid = pid
        self.category = category
        self.callback = callback
        self.title("Thêm sản phẩm" if not pid else "Sửa sản phẩm")
        self.geometry("500x500")
        self.resizable(False, False)
        self.grab_set()
        self._build()
        if pid:
            self._load_data()

    def _build(self):
        tk.Label(self, text="Thông tin sản phẩm", font=("Segoe UI", 13, "bold"), pady=10).pack()
        form = tk.Frame(self)
        form.pack(padx=24, pady=8, fill="x")

        cat_options = {"nu": "Trang phục nữ", "nam": "Trang phục nam", "phu_kien": "Phụ kiện"}
        fields = [
            ("Mã sản phẩm *", "code", "entry"),
            ("Tên sản phẩm *", "name", "entry"),
            ("Danh mục", "category", "combo"),
            ("Loại", "type", "entry"),
            ("Kích cỡ", "size", "entry"),
            ("Màu sắc", "color", "entry"),
            ("Giá thuê/ngày *", "price_per_day", "entry"),
            ("Tiền cọc", "deposit", "entry"),
            ("Trạng thái", "status", "status_combo"),
            ("Mô tả", "description", "entry"),
        ]
        self.vars = {}
        for i, (label, key, ftype) in enumerate(fields):
            tk.Label(form, text=label, font=("Segoe UI", 9), anchor="w",
                     width=16).grid(row=i, column=0, sticky="w", pady=4)
            if ftype == "combo":
                var = tk.StringVar(value=cat_options.get(self.category, "Trang phục nữ"))
                cb = ttk.Combobox(form, textvariable=var, state="readonly",
                                   values=list(cat_options.values()), width=28)
                cb.grid(row=i, column=1, sticky="ew", pady=4, padx=(8, 0))
            elif ftype == "status_combo":
                var = tk.StringVar(value="available")
                cb = ttk.Combobox(form, textvariable=var, state="readonly",
                                   values=["available", "rented", "maintenance"], width=28)
                cb.grid(row=i, column=1, sticky="ew", pady=4, padx=(8, 0))
            else:
                var = tk.StringVar()
                tk.Entry(form, textvariable=var, font=("Segoe UI", 10),
                         width=30, relief="solid", bd=1).grid(row=i, column=1, sticky="ew", pady=4, padx=(8, 0))
            self.vars[key] = var
            form.columnconfigure(1, weight=1)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=16)
        tk.Button(btn_frame, text="💾 Lưu", bg=self.app.colors["primary"], fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat", padx=20, pady=6,
                  cursor="hand2", command=self._save).pack(side="left", padx=8)
        tk.Button(btn_frame, text="Hủy", relief="flat", padx=16, pady=6,
                  cursor="hand2", command=self.destroy).pack(side="left", padx=8)

    def _load_data(self):
        products = InventoryService.get_all_products()
        cat_map = {"nu": "Trang phục nữ", "nam": "Trang phục nam", "phu_kien": "Phụ kiện"}
        for p in products:
            if p.id == self.pid:
                self.vars["code"].set(p.code)
                self.vars["name"].set(p.name)
                self.vars["category"].set(cat_map.get(p.category, "Trang phục nữ"))
                self.vars["type"].set(p.type or "")
                self.vars["size"].set(p.size or "")
                self.vars["color"].set(p.color or "")
                self.vars["price_per_day"].set(str(p.price_per_day))
                self.vars["deposit"].set(str(p.deposit))
                self.vars["status"].set(p.status)
                self.vars["description"].set(p.description or "")
                break

    def _save(self):
        try:
            code = self.vars["code"].get().strip()
            name = self.vars["name"].get().strip()
            price = float(self.vars["price_per_day"].get() or 0)
            if not code or not name or price <= 0:
                messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ mã, tên, giá thuê!")
                return
            cat_rev = {"Trang phục nữ": "nu", "Trang phục nam": "nam", "Phụ kiện": "phu_kien"}
            category = cat_rev.get(self.vars["category"].get(), self.category)
            if self.pid:
                InventoryService.update_product(
                    self.pid, code, name, category,
                    self.vars["type"].get(), self.vars["size"].get(), self.vars["color"].get(),
                    price, float(self.vars["deposit"].get() or 0),
                    self.vars["description"].get(), self.vars["status"].get())
            else:
                InventoryService.add_product(
                    code, name, category,
                    self.vars["type"].get(), self.vars["size"].get(), self.vars["color"].get(),
                    price, float(self.vars["deposit"].get() or 0),
                    self.vars["description"].get())
            self.callback()
            self.destroy()
        except WeddingRentalError as e:
            messagebox.showerror("Lỗi", str(e))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu: {e}")


# ======= ĐƠN THUÊ =======
class OrdersFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=app.colors["content_bg"])
        self.app = app
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=self.app.colors["content_bg"])
        hdr.pack(fill="x", padx=24, pady=(20, 12))
        tk.Label(hdr, text="📋 Đơn Thuê", bg=self.app.colors["content_bg"],
                 fg=self.app.colors["text_dark"], font=self.app.font_title).pack(side="left")
        tk.Button(hdr, text="+ Tạo đơn mới", bg=self.app.colors["primary"], fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat", padx=14, pady=6, cursor="hand2",
                  command=lambda: self.app._navigate("new_order")).pack(side="right")

        flt = tk.Frame(self, bg=self.app.colors["content_bg"])
        flt.pack(fill="x", padx=24, pady=(0, 10))
        self.status_var = tk.StringVar(value="Tất cả")
        tk.Label(flt, text="Trạng thái:", bg=self.app.colors["content_bg"],
                 fg=self.app.colors["text_gray"], font=self.app.font_body).pack(side="left")
        status_cb = ttk.Combobox(flt, textvariable=self.status_var,
                                  values=["Tất cả", "Đang thuê", "Đã trả", "Quá hạn", "Đã hủy"],
                                  width=14, state="readonly")
        status_cb.pack(side="left", padx=8)
        status_cb.bind("<<ComboboxSelected>>", lambda e: self._load_data())

        card = tk.Frame(self, bg=self.app.colors["card_bg"],
                        highlightbackground=self.app.colors["border"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        cols = ("Mã đơn", "Khách hàng", "SĐT", "Ngày thuê", "Ngày trả", "Tổng tiền", "Đã trả", "Trạng thái")
        self.tree = ttk.Treeview(card, columns=cols, show="headings", height=18)
        widths = [100, 150, 110, 100, 100, 120, 120, 100]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w)
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        self.tree.bind("<Double-1>", self._view_order)
        self.tree.tag_configure("overdue", background="#FEE2E2")
        self.tree.tag_configure("returned", background="#F0FDF4")

        btn_frame = tk.Frame(card, bg=self.app.colors["card_bg"])
        btn_frame.pack(fill="x", padx=8, pady=6)
        tk.Button(btn_frame, text="👁️ Xem chi tiết", bg=self.app.colors["secondary"], fg="white",
                  relief="flat", padx=12, pady=4, cursor="hand2",
                  command=self._view_order_btn).pack(side="left", padx=4)
        tk.Button(btn_frame, text="✅ Xác nhận trả đồ", bg=self.app.colors["success"], fg="white",
                  relief="flat", padx=12, pady=4, cursor="hand2",
                  command=self._return_order).pack(side="left", padx=4)

        self._load_data()

    def _load_data(self):
        status_map = {"Đang thuê": "active", "Đã trả": "returned", "Quá hạn": "overdue", "Đã hủy": "cancelled"}
        flt = self.status_var.get()
        sf = status_map.get(flt) if flt != "Tất cả" else None
        orders = RentalService.get_all_orders(sf)

        self.tree.delete(*self.tree.get_children())
        for o in orders:
            tag = "overdue" if o.status == "overdue" else ("returned" if o.status == "returned" else "")
            self.tree.insert("", "end", iid=o.id, tags=(tag,), values=(
                o.order_code, o.customer_name, o.customer_phone,
                o.rental_date, o.return_date,
                format_currency(o.total_amount),
                format_currency(o.paid_amount),
                o.status_label
            ))

    def _view_order_btn(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Thông báo", "Vui lòng chọn đơn thuê!")
            return
        OrderDetailDialog(self, self.app, int(sel[0]))

    def _view_order(self, event):
        sel = self.tree.selection()
        if sel:
            OrderDetailDialog(self, self.app, int(sel[0]))

    def _return_order(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Thông báo", "Vui lòng chọn đơn thuê!")
            return
        ReturnOrderDialog(self, self.app, int(sel[0]), self._load_data)


# ======= TẠO ĐƠN MỚI =======
class NewOrderFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=app.colors["content_bg"])
        self.app = app
        self.selected_products = []
        self._build()

    def _build(self):
        canvas = tk.Canvas(self, bg=self.app.colors["content_bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self.app.colors["content_bg"])
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        hdr = tk.Frame(scroll_frame, bg=self.app.colors["content_bg"])
        hdr.pack(fill="x", padx=24, pady=(20, 12))
        tk.Label(hdr, text="➕ Tạo Đơn Thuê Mới", bg=self.app.colors["content_bg"],
                 fg=self.app.colors["text_dark"], font=self.app.font_title).pack(side="left")

        body = tk.Frame(scroll_frame, bg=self.app.colors["content_bg"])
        body.pack(fill="x", padx=24)

        left = tk.Frame(body, bg=self.app.colors["card_bg"],
                        highlightbackground=self.app.colors["border"], highlightthickness=1)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=4)
        tk.Label(left, text="Thông tin đơn thuê", bg=self.app.colors["card_bg"],
                 font=self.app.font_h3, padx=16, pady=10).pack(anchor="w")
        tk.Frame(left, bg=self.app.colors["border"], height=1).pack(fill="x")

        form = tk.Frame(left, bg=self.app.colors["card_bg"])
        form.pack(fill="x", padx=16, pady=12)

        tk.Label(form, text="Khách hàng *", bg=self.app.colors["card_bg"],
                 font=("Segoe UI", 9), anchor="w").grid(row=0, column=0, sticky="w", pady=6)
        self.customer_var = tk.StringVar()
        customers = RentalService.get_all_customers()
        cust_options = [f"{c.name} - {c.phone}" for c in customers]
        self.customer_combo = ttk.Combobox(form, textvariable=self.customer_var,
                                            values=cust_options, width=30, state="readonly")
        self.customer_combo.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=6)
        self.customers_data = customers

        tk.Label(form, text="Ngày thuê *", bg=self.app.colors["card_bg"],
                 font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=6)
        self.rental_date_var = tk.StringVar(value=current_date_str())
        tk.Entry(form, textvariable=self.rental_date_var, font=("Segoe UI", 10),
                 relief="solid", bd=1, width=32).grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=6)

        tk.Label(form, text="Ngày trả *", bg=self.app.colors["card_bg"],
                 font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=6)
        self.return_date_var = tk.StringVar(value=date_after_days(3))
        tk.Entry(form, textvariable=self.return_date_var, font=("Segoe UI", 10),
                 relief="solid", bd=1, width=32).grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=6)

        tk.Label(form, text="Tiền cọc (đ)", bg=self.app.colors["card_bg"],
                 font=("Segoe UI", 9)).grid(row=3, column=0, sticky="w", pady=6)
        self.deposit_var = tk.StringVar(value="0")
        tk.Entry(form, textvariable=self.deposit_var, font=("Segoe UI", 10),
                 relief="solid", bd=1, width=32).grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=6)

        tk.Label(form, text="Giảm giá (đ)", bg=self.app.colors["card_bg"],
                 font=("Segoe UI", 9)).grid(row=4, column=0, sticky="w", pady=6)
        self.discount_var = tk.StringVar(value="0")
        tk.Entry(form, textvariable=self.discount_var, font=("Segoe UI", 10),
                 relief="solid", bd=1, width=32).grid(row=4, column=1, sticky="ew", padx=(8, 0), pady=6)

        tk.Label(form, text="Thanh toán", bg=self.app.colors["card_bg"],
                 font=("Segoe UI", 9)).grid(row=5, column=0, sticky="w", pady=6)
        self.payment_var = tk.StringVar(value="cash")
        ttk.Combobox(form, textvariable=self.payment_var,
                     values=["cash", "transfer", "card"], width=30, state="readonly").grid(
            row=5, column=1, sticky="ew", padx=(8, 0), pady=6)

        tk.Label(form, text="Ghi chú", bg=self.app.colors["card_bg"],
                 font=("Segoe UI", 9)).grid(row=6, column=0, sticky="nw", pady=6)
        self.notes_var = tk.StringVar()
        tk.Entry(form, textvariable=self.notes_var, font=("Segoe UI", 10),
                 relief="solid", bd=1, width=32).grid(row=6, column=1, sticky="ew", padx=(8, 0), pady=6)
        form.columnconfigure(1, weight=1)

        right = tk.Frame(body, bg=self.app.colors["card_bg"],
                         highlightbackground=self.app.colors["border"], highlightthickness=1)
        right.pack(side="right", fill="both", expand=True, padx=(8, 0), pady=4)
        tk.Label(right, text="Chọn sản phẩm", bg=self.app.colors["card_bg"],
                 font=self.app.font_h3, padx=16, pady=10).pack(anchor="w")
        tk.Frame(right, bg=self.app.colors["border"], height=1).pack(fill="x")

        cat_f = tk.Frame(right, bg=self.app.colors["card_bg"])
        cat_f.pack(fill="x", padx=8, pady=6)
        self.prod_cat_var = tk.StringVar(value="Tất cả")
        ttk.Combobox(cat_f, textvariable=self.prod_cat_var,
                     values=["Tất cả", "Trang phục nữ", "Trang phục nam", "Phụ kiện"],
                     width=18, state="readonly").pack(side="left")
        tk.Button(cat_f, text="Lọc", bg=self.app.colors["secondary"], fg="white",
                  relief="flat", padx=8, pady=2, cursor="hand2",
                  command=self._filter_products).pack(side="left", padx=6)

        self.prod_listbox = tk.Listbox(right, height=8, font=("Segoe UI", 9), selectmode="multiple")
        self.prod_listbox.pack(fill="x", padx=8, pady=4)
        self._load_available_products()

        tk.Button(right, text="➕ Thêm vào đơn", bg=self.app.colors["primary"], fg="white",
                  relief="flat", padx=12, pady=4, cursor="hand2",
                  command=self._add_to_order).pack(padx=8, pady=4, anchor="w")

        tk.Label(right, text="Sản phẩm trong đơn:", bg=self.app.colors["card_bg"],
                 font=("Segoe UI", 9, "bold"), padx=8).pack(anchor="w")
        self.order_prod_listbox = tk.Listbox(right, height=5, font=("Segoe UI", 9))
        self.order_prod_listbox.pack(fill="x", padx=8, pady=2)
        tk.Button(right, text="❌ Xóa khỏi đơn", bg=self.app.colors["danger"], fg="white",
                  relief="flat", padx=10, pady=3, cursor="hand2",
                  command=self._remove_from_order).pack(padx=8, pady=4, anchor="w")

        bottom = tk.Frame(scroll_frame, bg=self.app.colors["card_bg"],
                          highlightbackground=self.app.colors["border"], highlightthickness=1)
        bottom.pack(fill="x", padx=24, pady=8)
        self.total_label = tk.Label(bottom, text="Tổng tiền: 0đ",
                                     bg=self.app.colors["card_bg"],
                                     fg=self.app.colors["primary"],
                                     font=("Segoe UI", 14, "bold"), pady=12, padx=20)
        self.total_label.pack(side="left")
        tk.Button(bottom, text="💾 Tạo đơn thuê", bg=self.app.colors["primary"], fg="white",
                  font=("Segoe UI", 11, "bold"), relief="flat", padx=24, pady=8,
                  cursor="hand2", command=self._save_order).pack(side="right", padx=16, pady=8)

    def _load_available_products(self, category=None):
        self.available_products = InventoryService.get_available_products(category)
        self.prod_listbox.delete(0, "end")
        cat_map = {"nu": "👗", "nam": "🤵", "phu_kien": "💎"}
        for p in self.available_products:
            icon = cat_map.get(p.category, "")
            self.prod_listbox.insert("end",
                f"{icon} {p.code} - {p.name} ({format_currency(p.price_per_day)}/ngày)")

    def _filter_products(self):
        cat_map = {"Trang phục nữ": "nu", "Trang phục nam": "nam", "Phụ kiện": "phu_kien"}
        cat = cat_map.get(self.prod_cat_var.get())
        self._load_available_products(cat)

    def _add_to_order(self):
        indices = self.prod_listbox.curselection()
        if not indices:
            messagebox.showwarning("Thông báo", "Vui lòng chọn sản phẩm!")
            return
        for i in indices:
            prod = self.available_products[i]
            if prod.id not in [p.id for p in self.selected_products]:
                self.selected_products.append(prod)
        self._update_order_list()

    def _remove_from_order(self):
        sel = self.order_prod_listbox.curselection()
        if sel:
            self.selected_products.pop(sel[0])
            self._update_order_list()

    def _update_order_list(self):
        self.order_prod_listbox.delete(0, "end")
        for p in self.selected_products:
            self.order_prod_listbox.insert("end", f"{p.name} - {format_currency(p.price_per_day)}/ngày")
        self._calc_total()

    def _calc_total(self):
        from utils.helpers import days_between
        days = days_between(self.rental_date_var.get(), self.return_date_var.get())
        total = sum(p.price_per_day * days for p in self.selected_products)
        discount = float(self.discount_var.get() or 0)
        total -= discount
        self.total_label.configure(text=f"Tổng tiền: {format_currency(total)}  ({days} ngày)")

    def _save_order(self):
        if not self.customer_var.get():
            messagebox.showerror("Lỗi", "Vui lòng chọn khách hàng!")
            return
        if not self.selected_products:
            messagebox.showerror("Lỗi", "Vui lòng chọn ít nhất 1 sản phẩm!")
            return
        cust_idx = self.customer_combo.current()
        customer = self.customers_data[cust_idx]
        try:
            order = RentalService.create_order(
                customer.id,
                self.rental_date_var.get(),
                self.return_date_var.get(),
                [p.id for p in self.selected_products],
                float(self.deposit_var.get() or 0),
                float(self.discount_var.get() or 0),
                self.notes_var.get(),
                self.payment_var.get()
            )
            messagebox.showinfo("Thành công",
                f"✅ Tạo đơn thuê thành công!\nMã đơn: {order.order_code}\nKhách: {customer.name}")
            self.app._navigate("orders")
        except WeddingRentalError as e:
            messagebox.showerror("Lỗi", str(e))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tạo đơn: {e}")


# ======= CHI TIẾT ĐƠN THUÊ =======
class OrderDetailDialog(tk.Toplevel):
    def __init__(self, parent, app, order_id):
        super().__init__(parent)
        self.app = app
        self.order_id = order_id
        self.title("Chi tiết đơn thuê")
        self.geometry("600x500")
        self.grab_set()
        self._build()

    def _build(self):
        try:
            order = RentalService.get_order_by_id(self.order_id)
        except WeddingRentalError:
            return

        tk.Label(self, text=f"Chi tiết đơn: {order.order_code}",
                 font=("Segoe UI", 14, "bold"), pady=12).pack()

        info = tk.Frame(self, relief="solid", bd=1)
        info.pack(fill="x", padx=16, pady=8)
        fields = [
            ("Khách hàng", order.customer_name),
            ("Điện thoại", order.customer_phone),
            ("Ngày thuê", order.rental_date),
            ("Ngày trả dự kiến", order.return_date),
            ("Ngày trả thực tế", order.actual_return_date or "Chưa trả"),
            ("Trạng thái", order.status_label),
            ("Tổng tiền", format_currency(order.total_amount)),
            ("Đã thanh toán", format_currency(order.paid_amount)),
        ]
        for i, (label, value) in enumerate(fields):
            row = tk.Frame(info, bg="#F9FAFB" if i % 2 == 0 else "white")
            row.pack(fill="x")
            tk.Label(row, text=label + ":", font=("Segoe UI", 9, "bold"),
                     width=22, anchor="w", padx=12, pady=5, bg=row["bg"]).pack(side="left")
            tk.Label(row, text=str(value), font=("Segoe UI", 9),
                     anchor="w", bg=row["bg"]).pack(side="left")

        tk.Label(self, text="Sản phẩm trong đơn:", font=("Segoe UI", 10, "bold"),
                 pady=8).pack(anchor="w", padx=16)
        for item in order.items:
            row = tk.Frame(self, bg="#EBF3FF")
            row.pack(fill="x", padx=16, pady=2)
            tk.Label(row, text=f"• {item.product_name} ({item.product_code})",
                     bg="#EBF3FF", font=("Segoe UI", 9), padx=12, pady=4).pack(side="left")
            tk.Label(row, text=f"{format_currency(item.price_per_day)} × {item.days} ngày = {format_currency(item.subtotal)}",
                     bg="#EBF3FF", font=("Segoe UI", 9)).pack(side="right", padx=12)

        tk.Button(self, text="Đóng", relief="flat", bg=self.app.colors["primary"],
                  fg="white", padx=20, pady=6, cursor="hand2",
                  command=self.destroy).pack(pady=12)


# ======= XÁC NHẬN TRẢ ĐỒ =======
class ReturnOrderDialog(tk.Toplevel):
    def __init__(self, parent, app, order_id, callback):
        super().__init__(parent)
        self.app = app
        self.order_id = order_id
        self.callback = callback
        self.title("Xác nhận trả đồ")
        self.geometry("420x300")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        try:
            self.order = RentalService.get_order_by_id(self.order_id)
        except WeddingRentalError:
            self.destroy()
            return

        tk.Label(self, text="Xác nhận trả đồ", font=("Segoe UI", 13, "bold"), pady=10).pack()
        tk.Label(self, text=f"Đơn: {self.order.order_code} | Khách: {self.order.customer_name}",
                 font=("Segoe UI", 10), fg=self.app.colors["text_gray"]).pack()
        tk.Label(self, text=f"Còn lại cần thu: {format_currency(self.order.remaining_amount)}",
                 font=("Segoe UI", 11, "bold"), fg=self.app.colors["danger"], pady=8).pack()

        form = tk.Frame(self)
        form.pack(padx=24, pady=8)
        tk.Label(form, text="Ngày trả thực tế:", font=("Segoe UI", 9), anchor="w").grid(
            row=0, column=0, sticky="w", pady=6)
        self.return_date_var = tk.StringVar(value=current_date_str())
        tk.Entry(form, textvariable=self.return_date_var, font=("Segoe UI", 10),
                 relief="solid", bd=1, width=20).grid(row=0, column=1, padx=8)

        tk.Label(form, text="Số tiền thu thêm:", font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=6)
        self.extra_var = tk.StringVar(value=str(max(0, int(self.order.remaining_amount))))
        tk.Entry(form, textvariable=self.extra_var, font=("Segoe UI", 10),
                 relief="solid", bd=1, width=20).grid(row=1, column=1, padx=8)

        tk.Label(form, text="Phương thức TT:", font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=6)
        self.payment_var = tk.StringVar(value="cash")
        ttk.Combobox(form, textvariable=self.payment_var, values=["cash", "transfer", "card"],
                     width=18, state="readonly").grid(row=2, column=1, padx=8)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=12)
        tk.Button(btn_frame, text="✅ Xác nhận trả", bg=self.app.colors["success"], fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat", padx=16, pady=6,
                  cursor="hand2", command=self._confirm).pack(side="left", padx=8)
        tk.Button(btn_frame, text="Hủy", relief="flat", padx=14, pady=6,
                  cursor="hand2", command=self.destroy).pack(side="left", padx=8)

    def _confirm(self):
        try:
            RentalService.return_order(self.order_id, self.return_date_var.get(),
                                       float(self.extra_var.get() or 0), self.payment_var.get())
            messagebox.showinfo("Thành công", "✅ Đã xác nhận trả đồ thành công!")
            self.callback()
            self.destroy()
        except WeddingRentalError as e:
            messagebox.showerror("Lỗi", str(e))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xác nhận: {e}")


# ======= LỊCH TRẢ ĐỒ =======
class ReturnScheduleFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=app.colors["content_bg"])
        self.app = app
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=self.app.colors["content_bg"])
        hdr.pack(fill="x", padx=24, pady=(20, 12))
        tk.Label(hdr, text="📅 Lịch Trả Đồ", bg=self.app.colors["content_bg"],
                 fg=self.app.colors["text_dark"], font=self.app.font_title).pack(side="left")

        overdue_frame = tk.Frame(self, bg="#FEF2F2",
                                  highlightbackground="#EF4444", highlightthickness=1)
        overdue_frame.pack(fill="x", padx=24, pady=(0, 12))
        tk.Label(overdue_frame, text="⚠️ Đơn quá hạn - Cần liên hệ ngay!",
                 bg="#FEF2F2", fg="#DC2626", font=("Segoe UI", 11, "bold"),
                 padx=16, pady=8).pack(anchor="w")

        overdue_orders = ReportService.get_overdue_orders()
        if overdue_orders:
            for o in overdue_orders:
                row = tk.Frame(overdue_frame, bg="#FEF2F2")
                row.pack(fill="x", padx=16, pady=2)
                tk.Label(row,
                         text=f"🔴 {o['order_code']} | {o['customer_name']} | {o['customer_phone']} | Hạn: {o['return_date']}",
                         bg="#FEF2F2", font=("Segoe UI", 9)).pack(side="left")
                tk.Button(row, text="📞 Liên hệ", bg="#EF4444", fg="white", relief="flat",
                          padx=8, pady=2, cursor="hand2").pack(side="right", padx=8)
        else:
            tk.Label(overdue_frame, text="✅ Không có đơn quá hạn",
                     bg="#FEF2F2", fg="#16A34A", font=("Segoe UI", 10), padx=16, pady=4).pack(anchor="w")

        card = tk.Frame(self, bg=self.app.colors["card_bg"],
                        highlightbackground=self.app.colors["border"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        tk.Label(card, text="Tất cả đơn đang thuê", bg=self.app.colors["card_bg"],
                 font=self.app.font_h3, padx=16, pady=10).pack(anchor="w")
        tk.Frame(card, bg=self.app.colors["border"], height=1).pack(fill="x")

        cols = ("Mã đơn", "Khách hàng", "SĐT", "Ngày thuê", "Ngày trả dự kiến", "Số ngày còn lại")
        tree = ttk.Treeview(card, columns=cols, show="headings", height=15)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=140)
        tree.pack(fill="both", expand=True, padx=8, pady=8)
        tree.tag_configure("overdue", background="#FEE2E2")
        tree.tag_configure("warning", background="#FEF9C3")

        orders = RentalService.get_all_orders("active")
        for o in orders:
            d_left = days_until(o.return_date)
            tag = "overdue" if d_left < 0 else ("warning" if d_left <= 2 else "")
            label = f"QUÁ HẠN {abs(d_left)} ngày" if d_left < 0 else f"{d_left} ngày"
            tree.insert("", "end", tags=(tag,), values=(
                o.order_code, o.customer_name, o.customer_phone,
                o.rental_date, o.return_date, label
            ))


# ======= DOANH SỐ =======
class RevenueFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=app.colors["content_bg"])
        self.app = app
        self._build()

    def _build(self):
        from datetime import datetime
        try:
            current_year = datetime.now().year

            # Header
            hdr = tk.Frame(self, bg=self.app.colors["content_bg"])
            hdr.pack(fill="x", padx=24, pady=(20, 8))
            tk.Label(hdr, text="📊 Doanh Số", bg=self.app.colors["content_bg"],
                     fg=self.app.colors["text_dark"], font=self.app.font_title).pack(side="left")
            tk.Button(hdr, text="📥 Xuất Excel", bg="#22C55E", fg="white",
                      font=("Segoe UI", 10, "bold"), relief="flat", padx=14, pady=6,
                      cursor="hand2", command=self._export_excel).pack(side="right", padx=4)
            tk.Button(hdr, text="🔄 Làm mới", bg=self.app.colors["secondary"], fg="white",
                      font=("Segoe UI", 10, "bold"), relief="flat", padx=14, pady=6,
                      cursor="hand2", command=self._do_refresh).pack(side="right", padx=4)

            # Bộ lọc năm
            filter_bar = tk.Frame(self, bg=self.app.colors["content_bg"])
            filter_bar.pack(fill="x", padx=24, pady=(0, 8))
            tk.Label(filter_bar, text="Năm:", bg=self.app.colors["content_bg"],
                     fg=self.app.colors["text_gray"], font=self.app.font_body).pack(side="left")
            years = [str(y) for y in range(current_year - 3, current_year + 1)]
            self.year_var = tk.StringVar(value=str(current_year))
            year_cb = ttk.Combobox(filter_bar, textvariable=self.year_var,
                                    values=years, width=8, state="readonly")
            year_cb.pack(side="left", padx=8)
            year_cb.bind("<<ComboboxSelected>>", lambda e: self._do_refresh())

            # Cards tóm tắt
            self.cards_frame = tk.Frame(self, bg=self.app.colors["content_bg"])
            self.cards_frame.pack(fill="x", padx=24, pady=(0, 10))

            # Notebook
            self.nb = ttk.Notebook(self)
            self.nb.pack(fill="both", expand=True, padx=24, pady=(0, 16))
            self.chart_tab = tk.Frame(self.nb, bg=self.app.colors["card_bg"])
            self.table_tab = tk.Frame(self.nb, bg=self.app.colors["card_bg"])
            self.nb.add(self.chart_tab, text="  📈 Biểu đồ  ")
            self.nb.add(self.table_tab, text="  📋 Bảng chi tiết  ")

            self._do_refresh()

        except Exception as e:
            tk.Label(self, text=f"❌ Lỗi khởi tạo màn hình Doanh Số:\n{e}",
                     bg=self.app.colors["content_bg"], fg="red",
                     font=("Segoe UI", 11), wraplength=600).pack(pady=40)

    def _do_refresh(self):
        try:
            for w in self.cards_frame.winfo_children():
                w.destroy()
            for w in self.chart_tab.winfo_children():
                w.destroy()
            for w in self.table_tab.winfo_children():
                w.destroy()

            year = int(self.year_var.get())
            all_months = [f"{year}-{m:02d}" for m in range(1, 13)]

            # Lấy dữ liệu 6 tháng gần nhất
            rev_data, months = self._get_6months_data()
            # Lấy dữ liệu cả năm
            year_rev, year_orders, year_dep = self._query_db(
                "SELECT COALESCE(SUM(total_amount),0), COUNT(*), COALESCE(SUM(deposit_paid),0) "
                "FROM rental_orders WHERE strftime('%Y',rental_date)=? AND status!='cancelled'",
                (str(year),)
            )
            # Tháng này / tháng trước
            from datetime import datetime
            now = datetime.now()
            this_m = now.strftime("%Y-%m")
            if now.month == 1:
                last_m = f"{now.year-1}-12"
            else:
                last_m = f"{now.year}-{now.month-1:02d}"

            this_rev, _, _ = self._query_db(
                "SELECT COALESCE(SUM(total_amount),0),0,0 FROM rental_orders "
                "WHERE strftime('%Y-%m',rental_date)=? AND status!='cancelled'", (this_m,))
            last_rev, _, _ = self._query_db(
                "SELECT COALESCE(SUM(total_amount),0),0,0 FROM rental_orders "
                "WHERE strftime('%Y-%m',rental_date)=? AND status!='cancelled'", (last_m,))

            avg = year_rev / 12 if year_rev else 0

            # Vẽ cards
            cards = [
                ("💰 Tháng này", format_currency(this_rev), "#22C55E", "#F0FDF4"),
                ("📅 Tháng trước", format_currency(last_rev), "#5B9BD5", "#EBF3FF"),
                (f"📆 Tổng năm {year}", format_currency(year_rev), "#E8567A", "#FFF1F4"),
                ("📊 TB/tháng", format_currency(avg), "#F59E0B", "#FFFBEB"),
                (f"🧾 Số đơn {year}", str(int(year_orders)), "#8B5CF6", "#F5F3FF"),
            ]
            for i, (title, value, val_color, bg) in enumerate(cards):
                c = tk.Frame(self.cards_frame, bg=bg,
                             highlightbackground=self.app.colors["border"], highlightthickness=1)
                c.grid(row=0, column=i, padx=5, sticky="nsew", ipadx=8, ipady=6)
                self.cards_frame.columnconfigure(i, weight=1)
                tk.Label(c, text=title, bg=bg, fg=self.app.colors["text_gray"],
                         font=("Segoe UI", 8), padx=10).pack(anchor="w", pady=(8, 2))
                tk.Label(c, text=value, bg=bg, fg=val_color,
                         font=("Segoe UI", 12, "bold"), padx=10).pack(anchor="w", pady=(0, 8))

            self._draw_chart(self.chart_tab, rev_data, months)
            self._draw_table(self.table_tab, all_months, year)

        except Exception as e:
            tk.Label(self.chart_tab, text=f"❌ Lỗi tải dữ liệu: {e}",
                     bg=self.app.colors["card_bg"], fg="red",
                     font=("Segoe UI", 10)).pack(pady=20)

    def _query_db(self, sql, params=()):
        """Chạy câu query, trả về tuple (val1, val2, val3), mặc định (0,0,0) nếu lỗi"""
        try:
            conn = db.get_connection()
            row = conn.execute(sql, params).fetchone()
            conn.close()
            if row:
                return (row[0] or 0, row[1] or 0, row[2] or 0)
            return (0, 0, 0)
        except Exception:
            return (0, 0, 0)

    def _get_6months_data(self):
        """Lấy dữ liệu doanh thu và tiền cọc 6 tháng gần nhất"""
        from datetime import datetime, date
        import calendar
        months = []
        now = date.today()
        for i in range(5, -1, -1):
            month = now.month - i
            year = now.year
            while month <= 0:
                month += 12
                year -= 1
            months.append(f"{year}-{month:02d}")

        rev_data = {}
        for m in months:
            rev, _, dep = self._query_db(
                "SELECT COALESCE(SUM(total_amount),0),0,COALESCE(SUM(deposit_paid),0) "
                "FROM rental_orders WHERE strftime('%Y-%m',rental_date)=? AND status!='cancelled'",
                (m,))
            rev_data[m] = rev
            rev_data[m + "_dep"] = dep
        return rev_data, months

    def _get_month_detail(self, month_str):
        rev, orders, dep = self._query_db(
            "SELECT COALESCE(SUM(total_amount),0),COUNT(*),COALESCE(SUM(deposit_paid),0) "
            "FROM rental_orders WHERE strftime('%Y-%m',rental_date)=? AND status!='cancelled'",
            (month_str,))
        return (rev, int(orders), dep)

    def _draw_chart(self, parent, rev_data, months):
        tk.Label(parent, text="Biểu đồ Doanh thu & Tiền cọc (6 tháng gần nhất)",
                 bg=self.app.colors["card_bg"], font=self.app.font_h3,
                 padx=16, pady=10).pack(anchor="w")
        tk.Frame(parent, bg=self.app.colors["border"], height=1).pack(fill="x")

        # Legend
        lgd = tk.Frame(parent, bg=self.app.colors["card_bg"])
        lgd.pack(anchor="e", padx=20, pady=(6, 0))
        tk.Frame(lgd, bg="#E8567A", width=12, height=12).pack(side="left")
        tk.Label(lgd, text="  Doanh thu    ", bg=self.app.colors["card_bg"],
                 font=("Segoe UI", 8)).pack(side="left")
        tk.Frame(lgd, bg="#5B9BD5", width=12, height=12).pack(side="left")
        tk.Label(lgd, text="  Tiền cọc", bg=self.app.colors["card_bg"],
                 font=("Segoe UI", 8)).pack(side="left")

        canvas = tk.Canvas(parent, bg="#FAFAFA", highlightthickness=0, height=260)
        canvas.pack(fill="x", padx=12, pady=8)

        revenues = [rev_data.get(m, 0) for m in months]
        deposits = [rev_data.get(m + "_dep", 0) for m in months]
        all_vals = revenues + deposits
        max_val = max(all_vals) if any(v > 0 for v in all_vals) else 1

        def _render(event=None):
            canvas.delete("all")
            W = canvas.winfo_width()
            H = int(canvas["height"])
            if W < 80:
                return
            ML, MR, MT, MB = 70, 20, 16, 44
            cw = W - ML - MR
            ch = H - MT - MB

            # Grid + Y labels (bỏ dash để tránh lỗi Windows)
            for s in range(6):
                frac = s / 5
                yp = MT + ch - int(ch * frac)
                canvas.create_line(ML, yp, W - MR, yp, fill="#E5E7EB")
                lbl = f"{max_val * frac / 1e6:.1f}M"
                canvas.create_text(ML - 5, yp, text=lbl, anchor="e",
                                   font=("Segoe UI", 7), fill="#6B7280")

            # Axes
            canvas.create_line(ML, MT, ML, MT + ch, fill="#9CA3AF", width=1)
            canvas.create_line(ML, MT + ch, W - MR, MT + ch, fill="#9CA3AF", width=1)

            n = len(months)
            if n == 0:
                canvas.create_text(W // 2, H // 2, text="Chưa có dữ liệu doanh thu",
                                   font=("Segoe UI", 11), fill="#9CA3AF")
                return
            grp = cw / n
            bw = max(10, int(grp * 0.26))

            for i, m in enumerate(months):
                cx = int(ML + grp * i + grp / 2)
                lbl = m[5:] + "/" + m[:4]
                canvas.create_text(cx, MT + ch + 16, text=lbl,
                                   font=("Segoe UI", 7), fill="#374151")

                # Doanh thu bar
                rev = revenues[i]
                x0 = cx - bw - 2
                bh = int(ch * rev / max_val) if max_val > 0 else 0
                if bh > 0:
                    canvas.create_rectangle(int(x0), MT + ch - bh,
                                            int(x0 + bw), MT + ch,
                                            fill="#E8567A", outline="#C43D62")
                    canvas.create_text(int(x0 + bw / 2), MT + ch - bh - 9,
                                       text=f"{rev/1e6:.1f}M",
                                       font=("Segoe UI", 7, "bold"), fill="#C43D62")

                # Tiền cọc bar
                dep = deposits[i]
                x1 = cx + 2
                bh2 = int(ch * dep / max_val) if max_val > 0 else 0
                if bh2 > 0:
                    canvas.create_rectangle(int(x1), MT + ch - bh2,
                                            int(x1 + bw), MT + ch,
                                            fill="#5B9BD5", outline="#3A7FC1")
                    canvas.create_text(int(x1 + bw / 2), MT + ch - bh2 - 9,
                                       text=f"{dep/1e6:.1f}M",
                                       font=("Segoe UI", 7, "bold"), fill="#3A7FC1")

        canvas.bind("<Configure>", _render)
        canvas.after(200, _render)

    def _draw_table(self, parent, all_months, year):
        tk.Label(parent, text=f"Chi tiết doanh thu 12 tháng năm {year}",
                 bg=self.app.colors["card_bg"], font=self.app.font_h3, padx=16, pady=10).pack(anchor="w")
        tk.Frame(parent, bg=self.app.colors["border"], height=1).pack(fill="x")

        cols = ("Tháng", "Số đơn", "Tiền cọc thu", "Doanh thu", "Tích lũy")
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=13)
        widths = [100, 80, 160, 180, 180]
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")
        tree.pack(fill="both", expand=True, padx=12, pady=8)

        month_names = ["Tháng 1","Tháng 2","Tháng 3","Tháng 4","Tháng 5","Tháng 6",
                       "Tháng 7","Tháng 8","Tháng 9","Tháng 10","Tháng 11","Tháng 12"]
        cumulative = 0
        total_rev = 0; total_orders = 0; total_dep = 0
        for i, m in enumerate(all_months):
            rev, orders, dep = self._get_month_detail(m)
            cumulative += rev
            total_rev += rev; total_orders += orders; total_dep += dep
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", tags=(tag,), values=(
                month_names[i],
                str(orders),
                format_currency(dep),
                format_currency(rev),
                format_currency(cumulative),
            ))

        tree.tag_configure("even", background="#FAFAFA")
        tree.tag_configure("odd", background="#FFFFFF")

        # Dòng tổng
        total_frame = tk.Frame(parent, bg="#FFF1F4",
                               highlightbackground=self.app.colors["border"], highlightthickness=1)
        total_frame.pack(fill="x", padx=12, pady=(0, 8))
        summary = [
            ("Tổng cả năm", f"{total_orders} đơn",
             format_currency(total_dep), format_currency(total_rev))
        ]
        for lbl, orders_s, dep_s, rev_s in summary:
            row = tk.Frame(total_frame, bg="#FFF1F4")
            row.pack(fill="x", padx=16, pady=6)
            tk.Label(row, text=f"📌 {lbl}:", bg="#FFF1F4",
                     font=("Segoe UI", 10, "bold"), fg="#E8567A").pack(side="left")
            tk.Label(row, text=f"  {orders_s}  |  Cọc: {dep_s}  |  Doanh thu: {rev_s}",
                     bg="#FFF1F4", font=("Segoe UI", 10), fg=self.app.colors["text_dark"]).pack(side="left")

    def _get_year_data(self, year):
        """Lấy tổng doanh thu, số đơn, tiền cọc cả năm"""
        rev, orders, dep = self._query_db(
            "SELECT COALESCE(SUM(total_amount),0), COUNT(*), COALESCE(SUM(deposit_paid),0) "
            "FROM rental_orders WHERE strftime('%Y',rental_date)=? AND status!='cancelled'",
            (str(year),)
        )
        return rev, int(orders), dep

    def _export_excel(self):
        from tkinter import filedialog
        import datetime as dt
        year = int(self.year_var.get())
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=f"doanh_so_ao_cuoi_van_an_{year}.xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Lưu báo cáo Excel"
        )
        if not filepath:
            return
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter

            wb = openpyxl.Workbook()

            # ===== Sheet 1: Doanh thu theo tháng =====
            ws1 = wb.active
            ws1.title = f"Doanh thu {year}"

            # Style helpers
            pink_fill = PatternFill("solid", fgColor="E8567A")
            light_pink = PatternFill("solid", fgColor="FFF1F4")
            gray_fill = PatternFill("solid", fgColor="F3F4F6")
            white_fill = PatternFill("solid", fgColor="FFFFFF")
            thin = Side(style="thin", color="D1D5DB")
            border = Border(left=thin, right=thin, top=thin, bottom=thin)
            center = Alignment(horizontal="center", vertical="center")

            # Title
            ws1.merge_cells("A1:F1")
            ws1["A1"] = f"ÁO CƯỚI VĂN AN - BÁO CÁO DOANH SỐ NĂM {year}"
            ws1["A1"].font = Font(name="Arial", bold=True, size=14, color="FFFFFF")
            ws1["A1"].fill = pink_fill
            ws1["A1"].alignment = Alignment(horizontal="center", vertical="center")
            ws1.row_dimensions[1].height = 30

            ws1.merge_cells("A2:F2")
            ws1["A2"] = f"Ngày xuất: {dt.datetime.now().strftime('%d/%m/%Y %H:%M')}"
            ws1["A2"].font = Font(name="Arial", size=9, italic=True, color="6B7280")
            ws1["A2"].alignment = center
            ws1.row_dimensions[2].height = 18

            # Header row
            headers = ["Tháng", "Số đơn thuê", "Tiền cọc thu (VNĐ)", "Doanh thu (VNĐ)", "Tích lũy (VNĐ)", "% trên tổng năm"]
            for col_idx, h in enumerate(headers, 1):
                cell = ws1.cell(row=4, column=col_idx, value=h)
                cell.font = Font(name="Arial", bold=True, size=10, color="FFFFFF")
                cell.fill = pink_fill
                cell.alignment = center
                cell.border = border
            ws1.row_dimensions[4].height = 22

            month_names = ["Tháng 1","Tháng 2","Tháng 3","Tháng 4","Tháng 5","Tháng 6",
                           "Tháng 7","Tháng 8","Tháng 9","Tháng 10","Tháng 11","Tháng 12"]
            all_months = [f"{year}-{m:02d}" for m in range(1, 13)]
            month_data = []
            for m in all_months:
                rev, orders, dep = self._get_month_detail(m)
                month_data.append((rev, orders, dep))

            total_year_rev = sum(d[0] for d in month_data)
            cumulative = 0

            for i, (m_name, (rev, orders, dep)) in enumerate(zip(month_names, month_data)):
                cumulative += rev
                row_num = 5 + i
                pct = (rev / total_year_rev * 100) if total_year_rev > 0 else 0
                fill = gray_fill if i % 2 == 0 else white_fill
                row_vals = [m_name, orders, dep, rev, cumulative, pct / 100]
                for col_idx, val in enumerate(row_vals, 1):
                    cell = ws1.cell(row=row_num, column=col_idx, value=val)
                    cell.font = Font(name="Arial", size=10)
                    cell.fill = fill
                    cell.alignment = center
                    cell.border = border
                    if col_idx in (3, 4, 5):
                        cell.number_format = '#,##0'
                    elif col_idx == 6:
                        cell.number_format = '0.0%'
                ws1.row_dimensions[row_num].height = 18

            # Total row
            total_row = 5 + 12
            totals = ["TỔNG NĂM", f"=SUM(B5:B16)", f"=SUM(C5:C16)", f"=SUM(D5:D16)", "", "100%"]
            for col_idx, val in enumerate(totals, 1):
                cell = ws1.cell(row=total_row, column=col_idx, value=val)
                cell.font = Font(name="Arial", bold=True, size=10, color="E8567A")
                cell.fill = light_pink
                cell.alignment = center
                cell.border = border
                if col_idx in (3, 4) and isinstance(val, str) and val.startswith("="):
                    cell.number_format = '#,##0'
            ws1.row_dimensions[total_row].height = 22

            # Column widths
            col_widths = [14, 14, 22, 22, 22, 16]
            for i, w in enumerate(col_widths, 1):
                ws1.column_dimensions[get_column_letter(i)].width = w

            # ===== Sheet 2: Danh sách đơn thuê =====
            ws2 = wb.create_sheet(f"Đơn thuê {year}")
            try:
                conn = db.get_connection()
                c2 = conn.cursor()
                c2.execute("""
                    SELECT ro.order_code, cu.name, cu.phone,
                           ro.rental_date, ro.return_date, ro.total_days,
                           ro.total_amount, ro.deposit_paid, ro.discount,
                           ro.payment_method, ro.status, ro.notes
                    FROM rental_orders ro
                    JOIN customers cu ON cu.id = ro.customer_id
                    WHERE strftime('%Y', ro.rental_date) = ? AND ro.status != 'cancelled'
                    ORDER BY ro.rental_date
                """, (str(year),))
                orders_list = c2.fetchall()
                conn.close()
            except Exception:
                orders_list = []

            ws2.merge_cells("A1:L1")
            ws2["A1"] = f"DANH SÁCH ĐƠN THUÊ NĂM {year}"
            ws2["A1"].font = Font(name="Arial", bold=True, size=13, color="FFFFFF")
            ws2["A1"].fill = pink_fill
            ws2["A1"].alignment = center
            ws2.row_dimensions[1].height = 28

            hdrs2 = ["Mã đơn", "Khách hàng", "SĐT", "Ngày thuê", "Ngày trả",
                     "Số ngày", "Tổng tiền (VNĐ)", "Tiền cọc (VNĐ)", "Giảm giá (VNĐ)",
                     "Thanh toán", "Trạng thái", "Ghi chú"]
            for col_idx, h in enumerate(hdrs2, 1):
                cell = ws2.cell(row=3, column=col_idx, value=h)
                cell.font = Font(name="Arial", bold=True, size=10, color="FFFFFF")
                cell.fill = pink_fill
                cell.alignment = center
                cell.border = border

            status_map = {"active": "Đang thuê", "returned": "Đã trả", "overdue": "Quá hạn", "cancelled": "Hủy"}
            for i, row_data in enumerate(orders_list):
                r = 4 + i
                fill = gray_fill if i % 2 == 0 else white_fill
                vals = list(row_data)
                vals[10] = status_map.get(vals[10], vals[10])
                for col_idx, val in enumerate(vals, 1):
                    cell = ws2.cell(row=r, column=col_idx, value=val)
                    cell.font = Font(name="Arial", size=9)
                    cell.fill = fill
                    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                    cell.border = border
                    if col_idx in (7, 8, 9):
                        cell.number_format = '#,##0'
                ws2.row_dimensions[r].height = 16

            ws2_widths = [14, 20, 14, 12, 12, 8, 18, 16, 16, 12, 12, 20]
            for i, w in enumerate(ws2_widths, 1):
                ws2.column_dimensions[get_column_letter(i)].width = w

            # ===== Sheet 3: Thống kê tóm tắt =====
            ws3 = wb.create_sheet("Tóm tắt")
            ws3.merge_cells("A1:C1")
            ws3["A1"] = "THỐNG KÊ TÓNG QUAN"
            ws3["A1"].font = Font(name="Arial", bold=True, size=13, color="FFFFFF")
            ws3["A1"].fill = pink_fill
            ws3["A1"].alignment = center
            ws3.row_dimensions[1].height = 28

            year_rev, year_orders_count, year_dep = self._get_year_data(year)
            stats_data = [
                ("Năm báo cáo", str(year)),
                ("Tổng số đơn thuê", year_orders_count),
                ("Tổng doanh thu", year_rev),
                ("Tổng tiền cọc thu", year_dep),
                ("Doanh thu trung bình/tháng", year_rev / 12 if year_rev else 0),
                ("Doanh thu trung bình/đơn", year_rev / year_orders_count if year_orders_count else 0),
            ]
            for i, (lbl, val) in enumerate(stats_data):
                r = 3 + i
                ws3.cell(row=r, column=1, value=lbl).font = Font(name="Arial", bold=True, size=10)
                cell = ws3.cell(row=r, column=2, value=val)
                cell.font = Font(name="Arial", size=10)
                cell.alignment = Alignment(horizontal="right")
                if isinstance(val, (int, float)) and lbl != "Năm báo cáo":
                    cell.number_format = '#,##0'
                for col in range(1, 3):
                    ws3.cell(row=r, column=col).border = border
                    ws3.cell(row=r, column=col).fill = gray_fill if i % 2 == 0 else white_fill
                ws3.row_dimensions[r].height = 18

            ws3.column_dimensions["A"].width = 35
            ws3.column_dimensions["B"].width = 22

            wb.save(filepath)
            messagebox.showinfo("Thành công",
                                f"✅ Đã xuất báo cáo Excel thành công!\n\n📁 {filepath}")
        except ImportError:
            messagebox.showerror("Lỗi",
                                 "❌ Cần cài openpyxl để xuất Excel!\n\nChạy lệnh:\npip install openpyxl")
        except Exception as e:
            messagebox.showerror("Lỗi", f"❌ Không thể xuất file:\n{e}")


# ======= IN HÓA ĐƠN =======
class InvoiceFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=app.colors["content_bg"])
        self.app = app
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=self.app.colors["content_bg"])
        hdr.pack(fill="x", padx=24, pady=(20, 12))
        tk.Label(hdr, text="🧾 In Hóa Đơn", bg=self.app.colors["content_bg"],
                 fg=self.app.colors["text_dark"], font=self.app.font_title).pack(side="left")

        sel_frame = tk.Frame(self, bg=self.app.colors["card_bg"],
                              highlightbackground=self.app.colors["border"], highlightthickness=1)
        sel_frame.pack(fill="x", padx=24, pady=(0, 12))
        tk.Label(sel_frame, text="Chọn đơn thuê:", bg=self.app.colors["card_bg"],
                 font=self.app.font_h3, padx=16, pady=10).pack(side="left")

        self.order_var = tk.StringVar()
        self.orders_data = RentalService.get_all_orders()
        order_options = [f"{o.order_code} - {o.customer_name} ({o.rental_date})" for o in self.orders_data]
        order_cb = ttk.Combobox(sel_frame, textvariable=self.order_var,
                                 values=order_options, width=45, state="readonly")
        order_cb.pack(side="left", padx=8, pady=10)
        order_cb.bind("<<ComboboxSelected>>", self._preview_invoice)

        tk.Button(sel_frame, text="🖨️ In / Lưu hóa đơn", bg=self.app.colors["primary"],
                  fg="white", font=("Segoe UI", 10, "bold"), relief="flat",
                  padx=14, pady=6, cursor="hand2", command=self._print_invoice).pack(side="right", padx=12)

        self.preview = tk.Text(self, font=("Courier New", 10), bg="#FFFBEB", relief="solid", bd=1)
        self.preview.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        self.preview.configure(state="disabled")

    def _get_selected_order(self):
        sel = self.order_var.get()
        for o in self.orders_data:
            if sel.startswith(o.order_code):
                return o
        return self.orders_data[0] if self.orders_data else None

    def _preview_invoice(self, event=None):
        order = self._get_selected_order()
        if not order:
            return
        full_order = RentalService.get_order_by_id(order.id)
        text = self._generate_invoice_text(full_order)
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", text)
        self.preview.configure(state="disabled")

    def _generate_invoice_text(self, order):
        line = "=" * 55
        text = f"""
{line}
          ÁO CƯỚI VĂN AN
       Hệ thống quản lý cho thuê áo cưới
{line}
                HÓA ĐƠN THUÊ
{line}
M� đơn   : {order.order_code}
Ngày lập  : {order.created_at[:10] if order.created_at else ''}
{line}
THÔNG TIN KHÁCH HÀNG:
  Họ tên  : {order.customer_name}
  SĐT     : {order.customer_phone}
{line}
THÔNG TIN THUÊ:
  Ngày thuê : {order.rental_date}
  Ngày trả  : {order.return_date}
  Số ngày   : {order.total_days} ngày
{line}
CHI TIẾT SẢN PHẨM:
"""
        for item in order.items:
            text += f"  • {item.product_name}\n"
            text += f"    {format_currency(item.price_per_day)} × {item.days} ngày = {format_currency(item.subtotal)}\n"
        text += f"""
{line}
  Tạm tính : {format_currency(order.subtotal)}
  Giảm giá : {format_currency(order.discount)}
  TỔNG TIỀN: {format_currency(order.total_amount)}
  Đã trả   : {format_currency(order.paid_amount)}
  Còn lại  : {format_currency(order.remaining_amount)}
{line}
Trạng thái: {order.status.upper()}
{line}
  Cảm ơn quý khách đã tin dùng dịch vụ!
       Áo Cưới Văn An hân hạnh phục vụ!
{line}
"""
        return text

    def _print_invoice(self):
        if not self.order_var.get():
            messagebox.showwarning("Thông báo", "Vui lòng chọn đơn thuê!")
            return
        order = self._get_selected_order()
        if not order:
            return
        full_order = RentalService.get_order_by_id(order.id)
        text = self._generate_invoice_text(full_order)
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt"), ("All files", "*.*")],
            initialfile=f"HoaDon_{order.order_code}.txt"
        )
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(text)
            messagebox.showinfo("Thành công", f"✅ Đã lưu hóa đơn:\n{filename}")




# ======= QUẢN LÝ TÀI KHOẢN (chỉ admin) =======
class ManageUsersFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=app.colors["content_bg"])
        self.app = app
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=self.app.colors["content_bg"])
        hdr.pack(fill="x", padx=24, pady=(20, 12))
        tk.Label(hdr, text="🔑 Quản lý tài khoản", bg=self.app.colors["content_bg"],
                 fg=self.app.colors["text_dark"], font=self.app.font_title).pack(side="left")
        tk.Button(hdr, text="+ Thêm tài khoản", bg=self.app.colors["primary"],
                  fg="white", font=("Segoe UI", 10, "bold"), relief="flat",
                  padx=14, pady=6, cursor="hand2",
                  command=self._add_user).pack(side="right")

        card = tk.Frame(self, bg=self.app.colors["card_bg"],
                        highlightbackground=self.app.colors["border"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        cols = ("ID", "Tên đăng nhập", "Họ và tên", "Vai trò", "Trạng thái", "Đăng nhập cuối")
        self.tree = ttk.Treeview(card, columns=cols, show="headings", height=16)
        widths = [40, 130, 180, 140, 100, 160]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, minwidth=40)
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        self.tree.tag_configure("inactive", foreground="#9CA3AF")

        btn_f = tk.Frame(card, bg=self.app.colors["card_bg"])
        btn_f.pack(fill="x", padx=8, pady=6)
        tk.Button(btn_f, text="✏️ Sửa", bg=self.app.colors["secondary"], fg="white",
                  relief="flat", padx=12, pady=4, cursor="hand2",
                  command=self._edit_user).pack(side="left", padx=4)
        tk.Button(btn_f, text="🔑 Reset mật khẩu", bg=self.app.colors["warning"], fg="white",
                  relief="flat", padx=12, pady=4, cursor="hand2",
                  command=self._reset_pw).pack(side="left", padx=4)
        tk.Button(btn_f, text="⛔ Khóa / Mở khóa", bg=self.app.colors["danger"], fg="white",
                  relief="flat", padx=12, pady=4, cursor="hand2",
                  command=self._toggle_active).pack(side="left", padx=4)

        self._load()

    def _load(self):
        users = db.get_all_users()
        self.tree.delete(*self.tree.get_children())
        for u in users:
            status = "✅ Hoạt động" if u["is_active"] else "🔴 Bị khóa"
            last = (u["last_login"] or "Chưa đăng nhập")[:16]
            tag = "" if u["is_active"] else "inactive"
            self.tree.insert("", "end", iid=u["id"],
                values=(u["id"], u["username"], u["full_name"],
                        ROLE_LABELS.get(u["role"], u["role"]), status, last),
                tags=(tag,))

    def _sel(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Thông báo", "Vui lòng chọn tài khoản!")
            return None
        return int(sel[0])

    def _add_user(self):
        UserDialog(self, self.app, None, self.app.current_user["id"], self._load)

    def _edit_user(self):
        uid = self._sel()
        if uid:
            UserDialog(self, self.app, uid, self.app.current_user["id"], self._load)

    def _reset_pw(self):
        uid = self._sel()
        if not uid: return
        new_pw = simpledialog.askstring(
            "Reset mật khẩu", "Nhập mật khẩu mới (≥ 6 ký tự):", show="*", parent=self)
        if not new_pw: return
        if len(new_pw) < 6:
            messagebox.showerror("Lỗi", "Mật khẩu phải có ít nhất 6 ký tự!"); return
        db.update_user_password(uid, _hash_pw(new_pw))
        messagebox.showinfo("Thành công", "✅ Đã reset mật khẩu!")

    def _toggle_active(self):
        uid = self._sel()
        if not uid: return
        if uid == self.app.current_user["id"]:
            messagebox.showwarning("Cảnh báo", "Không thể khóa tài khoản đang đăng nhập!"); return
        users = db.get_all_users()
        user = next((u for u in users if u["id"] == uid), None)
        if not user: return
        new_state = not bool(user["is_active"])
        action = "mở khóa" if new_state else "khóa"
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn {action} tài khoản này?"):
            db.set_user_active(uid, new_state)
            self._load()


class UserDialog(tk.Toplevel):
    def __init__(self, parent, app, uid, created_by, callback):
        super().__init__(parent)
        self.app = app; self.uid = uid
        self.created_by = created_by; self.callback = callback
        self.title("Thêm tài khoản" if not uid else "Sửa tài khoản")
        self.geometry("420x380"); self.resizable(False, False); self.grab_set()
        self._build()
        if uid: self._load()

    def _build(self):
        tk.Label(self, text="Thông tin tài khoản",
                 font=("Segoe UI", 13, "bold"), pady=12).pack()
        form = tk.Frame(self); form.pack(padx=24, pady=8, fill="x")
        self.vars = {}
        rows = [("Tên đăng nhập *", "username"), ("Họ và tên *", "full_name")]
        for i, (lbl, key) in enumerate(rows):
            tk.Label(form, text=lbl, font=("Segoe UI", 9),
                     anchor="w", width=18).grid(row=i, column=0, sticky="w", pady=6)
            v = tk.StringVar(); self.vars[key] = v
            e = tk.Entry(form, textvariable=v, font=("Segoe UI", 10),
                         width=24, relief="solid", bd=1)
            e.grid(row=i, column=1, sticky="ew", pady=6, padx=(8, 0))
            if self.uid and key == "username": e.config(state="disabled")
            form.columnconfigure(1, weight=1)

        tk.Label(form, text="Vai trò *", font=("Segoe UI", 9),
                 anchor="w", width=18).grid(row=2, column=0, sticky="w", pady=6)
        self.role_var = tk.StringVar(value="staff")
        ttk.Combobox(form, textvariable=self.role_var,
                     values=["admin", "manager", "staff"],
                     state="readonly", width=22).grid(row=2, column=1, sticky="ew", pady=6, padx=(8, 0))

        if not self.uid:
            tk.Label(form, text="Mật khẩu *", font=("Segoe UI", 9),
                     anchor="w", width=18).grid(row=3, column=0, sticky="w", pady=6)
            self.pw_var = tk.StringVar()
            tk.Entry(form, textvariable=self.pw_var, show="●",
                     font=("Segoe UI", 10), width=24, relief="solid", bd=1).grid(
                row=3, column=1, sticky="ew", pady=6, padx=(8, 0))

        bf = tk.Frame(self); bf.pack(pady=16)
        tk.Button(bf, text="💾 Lưu", bg=self.app.colors["primary"], fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat", padx=20, pady=6,
                  cursor="hand2", command=self._save).pack(side="left", padx=8)
        tk.Button(bf, text="Hủy", relief="flat", padx=16, pady=6,
                  cursor="hand2", command=self.destroy).pack(side="left", padx=8)

    def _load(self):
        users = db.get_all_users()
        u = next((x for x in users if x["id"] == self.uid), None)
        if u:
            self.vars["username"].set(u["username"])
            self.vars["full_name"].set(u["full_name"])
            self.role_var.set(u["role"])

    def _save(self):
        fn = self.vars["full_name"].get().strip()
        role = self.role_var.get()
        if not fn:
            messagebox.showerror("Lỗi", "Họ tên không được để trống!"); return
        try:
            if self.uid:
                db.update_user_info(self.uid, fn, role)
                messagebox.showinfo("Thành công", "✅ Đã cập nhật tài khoản!")
            else:
                un = self.vars["username"].get().strip()
                pw = self.pw_var.get()
                if not un or not pw:
                    messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin!"); return
                if len(un) < 3:
                    messagebox.showerror("Lỗi", "Tên đăng nhập phải có ít nhất 3 ký tự!"); return
                if len(pw) < 6:
                    messagebox.showerror("Lỗi", "Mật khẩu phải có ít nhất 6 ký tự!"); return
                if db.get_user_by_username(un):
                    messagebox.showerror("Lỗi", f"Tên đăng nhập '{un}' đã tồn tại!"); return
                db.create_user(un, fn, _hash_pw(pw), role, self.created_by)
                messagebox.showinfo("Thành công", "✅ Đã tạo tài khoản mới!")
            self.callback(); self.destroy()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))


# ======= ĐỔI MẬT KHẨU =======
class ChangePasswordFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=app.colors["content_bg"])
        self.app = app
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=self.app.colors["content_bg"])
        hdr.pack(fill="x", padx=24, pady=(20, 12))
        tk.Label(hdr, text="🔒 Đổi mật khẩu", bg=self.app.colors["content_bg"],
                 fg=self.app.colors["text_dark"], font=self.app.font_title).pack(side="left")

        card = tk.Frame(self, bg=self.app.colors["card_bg"],
                        highlightbackground=self.app.colors["border"], highlightthickness=1)
        card.pack(padx=24, pady=8, ipadx=20, ipady=16)

        tk.Label(card, text=f"Tài khoản: {self.app.current_user['username']}",
                 bg=self.app.colors["card_bg"], fg=self.app.colors["text_gray"],
                 font=("Segoe UI", 10), pady=8).pack()

        form = tk.Frame(card, bg=self.app.colors["card_bg"]); form.pack(padx=20, pady=8)
        labels = ["Mật khẩu hiện tại", "Mật khẩu mới", "Xác nhận mật khẩu mới"]
        self.pvars = [tk.StringVar() for _ in labels]
        for i, (lbl, v) in enumerate(zip(labels, self.pvars)):
            tk.Label(form, text=lbl, font=("Segoe UI", 9), anchor="w",
                     width=22, bg=self.app.colors["card_bg"]).grid(row=i, column=0, pady=8, sticky="w")
            tk.Entry(form, textvariable=v, show="●", font=("Segoe UI", 10),
                     width=24, relief="solid", bd=1).grid(row=i, column=1, pady=8, padx=(8, 0))

        self.msg = tk.StringVar()
        tk.Label(card, textvariable=self.msg, bg=self.app.colors["card_bg"],
                 fg=self.app.colors["danger"], font=("Segoe UI", 9)).pack(pady=4)

        tk.Button(card, text="🔒 Đổi mật khẩu", bg=self.app.colors["primary"], fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat", padx=20, pady=8,
                  cursor="hand2", command=self._save).pack(pady=8)

    def _save(self):
        old_pw, new_pw, confirm = [v.get() for v in self.pvars]
        if not old_pw or not new_pw or not confirm:
            self.msg.set("⚠️ Vui lòng điền đầy đủ!"); return
        if new_pw != confirm:
            self.msg.set("❌ Mật khẩu mới và xác nhận không khớp!"); return
        if len(new_pw) < 6:
            self.msg.set("❌ Mật khẩu mới phải có ít nhất 6 ký tự!"); return
        user = db.get_user_by_id(self.app.current_user["id"])
        if not user or user["password_hash"] != _hash_pw(old_pw):
            self.msg.set("❌ Mật khẩu cũ không đúng!"); return
        db.update_user_password(self.app.current_user["id"], _hash_pw(new_pw))
        self.msg.set("")
        messagebox.showinfo("Thành công", "✅ Đổi mật khẩu thành công!")
        for v in self.pvars: v.set("")

# ======= ENTRY POINT =======
def main():
    print("=" * 55)
    print("   ÁO CƯỚI VĂN AN - HỆ THỐNG QUẢN LÝ")
    print("=" * 55)
    db.init_database()
    db.insert_sample_data()
    print("\n🚀 Đang khởi động giao diện...")

    login = LoginWindow()
    login.mainloop()
    if not login.logged_user:
        return  # Người dùng tắt cửa sổ đăng nhập

    app = WeddingRentalApp(login.logged_user)
    app.mainloop()


if __name__ == "__main__":
    main()