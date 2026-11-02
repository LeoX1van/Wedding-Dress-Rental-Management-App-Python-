"""
FLOATING CHAT - Nút chat nổi góc phải + popup cửa sổ chat
Gọi FloatingChat(root_window, app) để kích hoạt.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from .api_client import ClaudeAPIClient
from .context_builder import build_system_prompt
from .settings import load_api_key, save_api_key

_BG         = "#F0F2F5"
_CARD       = "#FFFFFF"
_BORDER     = "#E5E7EB"
_GRAY       = "#6B7280"
_DARK       = "#1A1D27"
_PRIMARY    = "#E8567A"
_PRIMARY_DK = "#C43D62"

_AI_BG      = "#FFF0F4"
_AI_BORDER  = "#F9C8D7"
_AI_FG      = "#1A1D27"
_USER_BG    = "#E8567A"
_USER_FG    = "#FFFFFF"
_TIME_FG    = "#9CA3AF"
_ERR_BG     = "#FEF2F2"
_ERR_FG     = "#DC2626"
_ERR_BDR    = "#FECACA"
_TYPING_BG  = "#F3F4F6"
_TYPING_FG  = "#6B7280"

_F_TITLE  = ("Segoe UI", 11, "bold")
_F_BODY   = ("Segoe UI", 10)
_F_SMALL  = ("Segoe UI", 8)
_F_BOLD   = ("Segoe UI", 10, "bold")
_F_ITALIC = ("Segoe UI", 9, "italic")
_F_NAME   = ("Segoe UI", 8, "bold")


class BubbleArea(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=_CARD, **kw)
        self._canvas = tk.Canvas(self, bg=_CARD, bd=0, highlightthickness=0)
        self._sb = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._sb.set)
        self._sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)
        self._inner = tk.Frame(self._canvas, bg=_CARD)
        self._win = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")
        self._inner.bind("<Configure>", lambda _e: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(
            self._win, width=e.width))
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self._canvas.bind(seq, self._scroll)
            self._inner.bind(seq, self._scroll)
        self._typing_frame = None
        self._typing_lbl   = None

    def _scroll(self, e):
        if e.num == 4:   self._canvas.yview_scroll(-1, "units")
        elif e.num == 5: self._canvas.yview_scroll(1,  "units")
        else:            self._canvas.yview_scroll(int(-1*(e.delta/120)), "units")

    def _to_bottom(self):
        self._canvas.update_idletasks()
        self._canvas.yview_moveto(1.0)

    def add_bubble(self, role, text, sender=""):
        now = datetime.now().strftime("%H:%M")
        is_user  = role == "user"
        is_error = role == "error"
        if is_user:
            bb, fg, bdr = _USER_BG, _USER_FG, _USER_BG
            name_color = _GRAY
            disp_name  = f"{sender or 'Bạn'}  👤"
        elif is_error:
            bb, fg, bdr = _ERR_BG, _ERR_FG, _ERR_BDR
            name_color = _ERR_FG
            disp_name  = "⚠️  Lỗi"
        else:
            bb, fg, bdr = _AI_BG, _AI_FG, _AI_BORDER
            name_color = _PRIMARY
            disp_name  = "🤖  Trợ lý AI"

        row = tk.Frame(self._inner, bg=_CARD)
        row.pack(fill="x", padx=8, pady=(6, 0))

        meta = tk.Frame(row, bg=_CARD)
        if is_user:
            meta.pack(anchor="e", padx=4)
            tk.Label(meta, text=now,       bg=_CARD, fg=_TIME_FG,   font=_F_SMALL).pack(side="right", padx=(4,0))
            tk.Label(meta, text=disp_name, bg=_CARD, fg=name_color, font=_F_NAME ).pack(side="right")
        else:
            meta.pack(anchor="w", padx=4)
            tk.Label(meta, text=disp_name, bg=_CARD, fg=name_color, font=_F_NAME ).pack(side="left")
            tk.Label(meta, text=now,       bg=_CARD, fg=_TIME_FG,   font=_F_SMALL).pack(side="left", padx=(4,0))

        brow = tk.Frame(row, bg=_CARD)
        brow.pack(anchor="e" if is_user else "w", pady=(2, 4))

        bubble = tk.Frame(brow, bg=bb, highlightbackground=bdr, highlightthickness=1)
        bubble.pack(padx=6)

        lbl = tk.Label(bubble, text=self._clean(text),
                       bg=bb, fg=fg, font=_F_BODY,
                       justify="left", wraplength=260, anchor="w")
        lbl.pack(padx=12, pady=8, anchor="w")

        for w in (bubble, lbl, row, brow, meta):
            for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                w.bind(seq, self._scroll)

        self._to_bottom()

    def _clean(self, text):
        return "\n".join(l.replace("**","") for l in text.split("\n")).strip()

    def show_typing(self):
        if self._typing_frame: return
        row = tk.Frame(self._inner, bg=_CARD)
        row.pack(fill="x", padx=8, pady=(6, 0))
        meta = tk.Frame(row, bg=_CARD)
        meta.pack(anchor="w", padx=4)
        tk.Label(meta, text="🤖  Trợ lý AI", bg=_CARD, fg=_PRIMARY, font=_F_NAME).pack(side="left")
        bubble = tk.Frame(row, bg=_TYPING_BG, highlightbackground=_BORDER, highlightthickness=1)
        bubble.pack(anchor="w", padx=6, pady=(2,4))
        self._typing_lbl = tk.Label(bubble, text="  ●      ",
                                     bg=_TYPING_BG, fg=_TYPING_FG, font=_F_ITALIC)
        self._typing_lbl.pack(ipadx=6, ipady=5)
        self._typing_frame = row
        self._anim(0)
        self._to_bottom()

    def _anim(self, n):
        if not self._typing_frame: return
        frames = ["  ●      ", "  ● ●   ", "  ● ● ●"]
        try: self._typing_lbl.config(text=frames[n % 3])
        except: return
        self._typing_frame.after(500, lambda: self._anim(n+1))

    def hide_typing(self):
        if self._typing_frame:
            self._typing_frame.destroy()
            self._typing_frame = None

    def clear(self):
        for w in self._inner.winfo_children(): w.destroy()
        self._typing_frame = None


class ChatPopup(tk.Toplevel):
    W, H = 360, 520

    def __init__(self, parent, app, client, on_close):
        super().__init__(parent)
        self.app      = app
        self.client   = client
        self.on_close = on_close
        self._waiting = False
        self._has_ph  = False

        self.overrideredirect(True)
        self.configure(bg=_PRIMARY)
        self.attributes("-topmost", True)
        self._build()
        self._greet()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=_PRIMARY)
        hdr.pack(fill="x")

        tk.Label(hdr, text="🤖  AI Tư Vấn Áo Cưới Văn An",
                 bg=_PRIMARY, fg="white", font=_F_TITLE,
                 padx=12, pady=10).pack(side="left")

        tk.Button(hdr, text="✕", bg=_PRIMARY, fg="white",
                  font=("Segoe UI", 13, "bold"), relief="flat",
                  padx=10, pady=8, cursor="hand2",
                  activebackground=_PRIMARY_DK,
                  command=self._close).pack(side="right")

        tk.Button(hdr, text="⚙", bg=_PRIMARY, fg="white",
                  font=("Segoe UI", 12), relief="flat",
                  padx=8, pady=8, cursor="hand2",
                  activebackground=_PRIMARY_DK,
                  command=self._api_key_dlg).pack(side="right")

        # Bubble area
        self.bubble_area = BubbleArea(self)
        self.bubble_area.pack(fill="both", expand=True)

        # Divider
        tk.Frame(self, bg=_BORDER, height=1).pack(fill="x")

        # Input
        bar = tk.Frame(self, bg=_CARD, pady=8)
        bar.pack(fill="x", padx=8)

        wrap = tk.Frame(bar, bg=_CARD, highlightbackground=_BORDER, highlightthickness=1)
        wrap.pack(side="left", fill="x", expand=True, padx=(0,6))

        self.ivar = tk.StringVar()
        self.entry = tk.Entry(wrap, textvariable=self.ivar,
                              font=_F_BODY, relief="flat", bd=0,
                              bg=_CARD, fg=_DARK)
        self.entry.pack(fill="x", ipady=7, padx=8)
        self.entry.bind("<Return>",   lambda _: self._send())
        self.entry.bind("<FocusIn>",  self._fi)
        self.entry.bind("<FocusOut>", self._fo)
        self._ph()

        self.send_btn = tk.Button(bar, text="▶",
                                   bg=_PRIMARY, fg="white",
                                   font=_F_BOLD, relief="flat",
                                   padx=12, pady=6, cursor="hand2",
                                   activebackground=_PRIMARY_DK,
                                   command=self._send, state="disabled")
        self.send_btn.pack(side="right")

    def _ph(self):
        self.entry.insert(0, "Nhập câu hỏi...")
        self.entry.config(fg=_GRAY)
        self._has_ph = True

    def _fi(self, _e):
        if self._has_ph:
            self.entry.delete(0, "end")
            self.entry.config(fg=_DARK)
            self._has_ph = False

    def _fo(self, _e):
        if not self.ivar.get().strip(): self._ph()

    def _greet(self):
        self.bubble_area.add_bubble(
            "assistant",
            "Xin chào! 👋\nTôi có thể tư vấn về:\n"
            "• 👗 Váy cưới & áo dài\n"
            "• 🤵 Vest & suit chú rể\n"
            "• 💍 Phụ kiện cưới\n"
            "• 💰 Giá thuê & đặt cọc\n\nHãy hỏi tôi nhé!"
        )
        self._set_state("normal")

    def _set_state(self, s):
        self.entry.config(state=s)
        self.send_btn.config(state=s)

    def _send(self):
        if self._waiting or self._has_ph: return
        text = self.ivar.get().strip()
        if not text: return
        self.ivar.set("")
        self._ph()
        sender = getattr(self.app, "current_user", {}).get("full_name", "Bạn")
        self.bubble_area.add_bubble("user", text, sender=sender)
        self._waiting = True
        self._set_state("disabled")
        self.bubble_area.show_typing()
        self.client.send_message(
            text,
            on_success=lambda r: self.after(0, lambda: self._ok(r)),
            on_error=lambda e:   self.after(0, lambda: self._err(e)),
        )

    def _ok(self, reply):
        self.bubble_area.hide_typing()
        self.bubble_area.add_bubble("assistant", reply)
        self._waiting = False
        self._set_state("normal")
        self.entry.focus()

    def _err(self, err):
        self.bubble_area.hide_typing()
        self.bubble_area.add_bubble("error", err)
        self._waiting = False
        self._set_state("normal")

    def _close(self):
        self.on_close()
        self.destroy()

    def _api_key_dlg(self):
        ApiKeyDialog(self, self._on_new_key)

    def _on_new_key(self, key):
        save_api_key(key)
        sp = build_system_prompt()
        self.client.__init__(key, sp)
        self.client.reset_history()
        self.bubble_area.clear()
        self._greet()


class FloatingChat:
    BTN_SIZE = 56

    def __init__(self, root, app):
        self.root   = root
        self.app    = app
        self.popup  = None
        self.client = None
        self._open  = False
        self._init_client()
        self._build_btn()
        root.bind("<Configure>", self._reposition, add="+")

    def _init_client(self):
        key = load_api_key()
        if key:
            sp = build_system_prompt()
            self.client = ClaudeAPIClient(key, sp)

    def _build_btn(self):
        s = self.BTN_SIZE
        self._btn_win = tk.Toplevel(self.root)
        self._btn_win.overrideredirect(True)
        self._btn_win.attributes("-topmost", True)
        self._btn_win.geometry(f"{s}x{s}")
        self._btn_win.configure(bg=_PRIMARY)

        self._cv = tk.Canvas(self._btn_win, width=s, height=s,
                              bg=_PRIMARY, highlightthickness=0, bd=0)
        self._cv.pack()

        r = s // 2 - 2
        cx = cy = s // 2
        self._circle = self._cv.create_oval(cx-r, cy-r, cx+r, cy+r,
                                             fill=_PRIMARY, outline=_PRIMARY_DK, width=2)
        self._icon   = self._cv.create_text(cx, cy, text="💬",
                                             font=("Segoe UI", 22), fill="white")
        self._cv.bind("<Button-1>", self._toggle)
        self._cv.bind("<Enter>",    lambda _: self._cv.itemconfig(self._circle, fill=_PRIMARY_DK))
        self._cv.bind("<Leave>",    lambda _: self._cv.itemconfig(self._circle, fill=_PRIMARY))
        self._cv.config(cursor="hand2")
        self._reposition()

    def _reposition(self, _e=None):
        self.root.update_idletasks()
        rx = self.root.winfo_x()
        ry = self.root.winfo_y()
        rw = self.root.winfo_width()
        rh = self.root.winfo_height()
        s  = self.BTN_SIZE
        x  = rx + rw - s - 20
        y  = ry + rh - s - 20
        self._btn_win.geometry(f"{s}x{s}+{x}+{y}")
        if self.popup and self.popup.winfo_exists():
            px = rx + rw - ChatPopup.W - 20
            py = ry + rh - ChatPopup.H - s - 28
            self.popup.geometry(f"{ChatPopup.W}x{ChatPopup.H}+{px}+{py}")

    def _toggle(self, _e=None):
        if self._open: self._close_popup()
        else:          self._open_popup()

    def _open_popup(self):
        if not self.client:
            ApiKeyDialog(self.root, self._on_key_set)
            return
        self._open = True
        self._cv.itemconfig(self._icon, text="✕")
        self.root.update_idletasks()
        rx = self.root.winfo_x(); ry = self.root.winfo_y()
        rw = self.root.winfo_width(); rh = self.root.winfo_height()
        s  = self.BTN_SIZE
        px = rx + rw - ChatPopup.W - 20
        py = ry + rh - ChatPopup.H - s - 28
        self.popup = ChatPopup(self.root, self.app, self.client, self._on_closed)
        self.popup.geometry(f"{ChatPopup.W}x{ChatPopup.H}+{px}+{py}")

    def _close_popup(self):
        self._open = False
        self._cv.itemconfig(self._icon, text="💬")
        if self.popup and self.popup.winfo_exists():
            self.popup.destroy()
        self.popup = None

    def _on_closed(self):
        self._open = False
        self._cv.itemconfig(self._icon, text="💬")

    def _on_key_set(self, key):
        save_api_key(key)
        sp = build_system_prompt()
        self.client = ClaudeAPIClient(key, sp)
        self._open_popup()


class ApiKeyDialog(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.title("Cài đặt Anthropic API Key")
        self.geometry("460x270")
        self.resizable(False, False)
        self.grab_set()
        self.configure(bg=_BG)
        self._build()

    def _build(self):
        tk.Label(self, text="🔑 Nhập Anthropic API Key",
                 bg=_BG, fg=_DARK, font=("Segoe UI", 14, "bold")).pack(pady=(18,2))
        tk.Label(self, text="Lấy tại: console.anthropic.com → API Keys",
                 bg=_BG, fg=_GRAY, font=_F_SMALL).pack()
        card = tk.Frame(self, bg=_CARD, highlightbackground=_BORDER, highlightthickness=1)
        card.pack(fill="x", padx=24, pady=12)
        tk.Label(card, text="API Key:", bg=_CARD, fg=_DARK,
                 font=_F_BODY, anchor="w").pack(fill="x", padx=14, pady=(10,0))
        self.kv = tk.StringVar(value=load_api_key())
        entry = tk.Entry(card, textvariable=self.kv, show="●",
                         font=_F_BODY, relief="solid", bd=1)
        entry.pack(fill="x", padx=14, ipady=6, pady=(3,3))
        sv = tk.BooleanVar()
        tk.Checkbutton(card, text="Hiện key", variable=sv,
                       bg=_CARD, fg=_GRAY, font=_F_SMALL, cursor="hand2",
                       command=lambda: entry.config(show="" if sv.get() else "●")
                       ).pack(anchor="w", padx=14, pady=(0,10))
        self.mv = tk.StringVar()
        tk.Label(self, textvariable=self.mv, bg=_BG, fg="#EF4444", font=_F_SMALL).pack()
        bf = tk.Frame(self, bg=_BG); bf.pack(pady=6)
        tk.Button(bf, text="💾 Lưu", bg=_PRIMARY, fg="white",
                  font=_F_BOLD, relief="flat", padx=18, pady=6,
                  cursor="hand2", command=self._save).pack(side="left", padx=6)
        tk.Button(bf, text="Huỷ", relief="flat", padx=14, pady=6,
                  cursor="hand2", command=self.destroy).pack(side="left")

    def _save(self):
        k = self.kv.get().strip()
        if not k:
            self.mv.set("⚠️ Vui lòng nhập API key!"); return
        if not k.startswith("sk-ant-"):
            self.mv.set("⚠️ Key không hợp lệ (phải bắt đầu sk-ant-)"); return
        self.callback(k)
        self.destroy()


# Giữ lại để không lỗi import cũ
class AIChatFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=_BG)
        tk.Label(self, text="🤖 Chat AI đang chạy ở góc phải màn hình ↘",
                 bg=_BG, fg=_GRAY, font=("Segoe UI", 13)).pack(expand=True)