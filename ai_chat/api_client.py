"""
API CLIENT - Gọi Anthropic Claude API
"""

import urllib.request
import urllib.error
import json
import threading
from typing import Callable, Optional


CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 1024
MAX_HISTORY = 20  # Số lượt hội thoại tối đa giữ trong context


class ClaudeAPIClient:
    """Client gọi Anthropic API, quản lý lịch sử hội thoại."""

    def __init__(self, api_key: str, system_prompt: str):
        self.api_key = api_key.strip()
        self.system_prompt = system_prompt
        self.history: list[dict] = []  # [{role, content}]

    def reset_history(self):
        self.history = []

    def _trim_history(self):
        """Giữ tối đa MAX_HISTORY lượt (user+assistant = 2 items mỗi lượt)."""
        max_items = MAX_HISTORY * 2
        if len(self.history) > max_items:
            self.history = self.history[-max_items:]

    def send_message(
        self,
        user_text: str,
        on_success: Callable[[str], None],
        on_error: Callable[[str], None],
    ):
        """
        Gửi tin nhắn đến Claude API bất đồng bộ (thread riêng).
        on_success(reply_text) được gọi khi thành công.
        on_error(error_msg) được gọi khi thất bại.
        """
        self.history.append({"role": "user", "content": user_text})
        self._trim_history()

        def _call():
            payload = {
                "model": MODEL,
                "max_tokens": MAX_TOKENS,
                "system": self.system_prompt,
                "messages": self.history.copy(),
            }

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                CLAUDE_API_URL,
                data=data,
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                },
            )

            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
                    reply = body["content"][0]["text"]
                    self.history.append({"role": "assistant", "content": reply})
                    on_success(reply)

            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace")
                try:
                    err_json = json.loads(err_body)
                    msg = err_json.get("error", {}).get("message", err_body)
                except Exception:
                    msg = err_body
                # Xóa tin nhắn user vừa thêm vì thất bại
                if self.history and self.history[-1]["role"] == "user":
                    self.history.pop()
                on_error(f"Lỗi API ({e.code}): {msg}")

            except Exception as e:
                if self.history and self.history[-1]["role"] == "user":
                    self.history.pop()
                on_error(f"Lỗi kết nối: {str(e)}")

        thread = threading.Thread(target=_call, daemon=True)
        thread.start()
