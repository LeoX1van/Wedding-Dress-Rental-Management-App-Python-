"""
SETTINGS - Lưu trữ cấu hình AI Chat (API key, preferences)
API key được lưu vào file .ai_chat_config (ẩn) trong thư mục project.
"""

import os
import json

_CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),  # thư mục gốc project
    ".ai_chat_config",
)


def load_api_key() -> str:
    """Đọc API key từ file config. Trả về chuỗi rỗng nếu chưa có."""
    try:
        if os.path.exists(_CONFIG_FILE):
            with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("anthropic_api_key", "")
    except Exception:
        pass
    return ""


def save_api_key(api_key: str):
    """Lưu API key vào file config."""
    try:
        data = {}
        if os.path.exists(_CONFIG_FILE):
            with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        data["anthropic_api_key"] = api_key.strip()
        with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[AI Chat] Không thể lưu API key: {e}")