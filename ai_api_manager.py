# -*- coding: utf-8 -*-
"""
ai_api_manager.py — مدیریت کلیدها و تنظیمات API. کلیدها فقط از .env یا متغیر محیطی
خوانده می‌شوند و هرگز داخل کد یا ZIP قرار نمی‌گیرند. بعد از ذخیره، بدون ری‌استارت اعمال می‌شوند.
"""
from __future__ import annotations

import os
from typing import Any

from common_2077 import DATA_DIR, env_get, env_set, load_env, mask_secret, read_json, write_json
import os.path

SETTINGS_PATH = os.path.join(DATA_DIR, "app_settings.json")

PROVIDERS = ["openrouter", "openai", "deepseek", "local"]
KEY_FIELDS = {
    "openrouter": "OPENROUTER_API_KEY",
    "openai": "OPENAI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}

DEFAULT_SETTINGS: dict[str, Any] = {
    "provider_order": ["openrouter", "openai", "deepseek", "local"],
    "openrouter_model": "openai/gpt-oss-120b:free",
    "reasoning_enabled": False,
    "brain_enabled": True,
    "language": "en",
    "local_first": False,
}


def get_settings() -> dict[str, Any]:
    s = dict(DEFAULT_SETTINGS)
    stored = read_json(SETTINGS_PATH, default=None)
    if isinstance(stored, dict):
        s.update({k: v for k, v in stored.items() if k in DEFAULT_SETTINGS})
    # reasoning از .env هم خوانده می‌شود (پیش‌فرض خاموش)
    if env_get("OPENROUTER_REASONING_ENABLED", "0") in ("1", "true", "True"):
        s["reasoning_enabled"] = True
    return s


def save_settings(updates: dict[str, Any]) -> dict[str, Any]:
    s = get_settings()
    clean = {k: v for k, v in updates.items() if k in DEFAULT_SETTINGS}
    s.update(clean)
    write_json(SETTINGS_PATH, s)
    if "reasoning_enabled" in clean:
        env_set("OPENROUTER_REASONING_ENABLED", "1" if clean["reasoning_enabled"] else "0")
    return s


def get_api_key(provider: str) -> str:
    field = KEY_FIELDS.get(provider)
    return env_get(field, "") if field else ""


def set_api_key(provider: str, key: str) -> bool:
    """ذخیره‌ی کلید در .env (نه در کد، نه در تنظیمات JSON)."""
    field = KEY_FIELDS.get(provider)
    if not field:
        return False
    return env_set(field, key.strip())


def masked_keys() -> dict[str, str]:
    return {p: mask_secret(get_api_key(p)) for p in KEY_FIELDS}


def has_any_external() -> bool:
    return any(get_api_key(p) for p in KEY_FIELDS)


def test_connection(provider: str) -> dict[str, Any]:
    """تست اتصال با پیام فارسی واضح؛ بدون نیاز به ری‌استارت."""
    from i18n import tt
    key = get_api_key(provider)
    if not key:
        return {"ok": False, "message": tt(f"No API key set for {provider}. Add it in the settings panel.",
                                           f"کلید {provider} وارد نشده است. از پنل تنظیمات وارد کنید.")}
    try:
        from ai_client import chat as ai_chat
        s = get_settings()
        model = {"openrouter": s["openrouter_model"], "openai": "gpt-4o-mini", "deepseek": "deepseek-chat"}[provider]
        res = ai_chat(provider, [{"role": "user", "content": tt("Hello", "سلام")}], model=model, max_tokens=20, timeout=25)
        if res.get("ok"):
            return {"ok": True, "message": tt(f"Connection is working - the model replied ({model}).",
                                              f"اتصال برقرار است — پاسخ مدل دریافت شد ({model}).")}
        return {"ok": False, "message": res.get("error_fa", tt("Unknown error", "خطای نامشخص")), "detail": res.get("error", "")}
    except Exception as e:
        return {"ok": False, "message": tt("Connection test failed: ", "خطا در تست اتصال: ")+ str(e)[:120]}


def env_summary() -> dict[str, Any]:
    env = load_env()
    return {
        "env_file_exists": os.path.exists(os.path.join(DATA_DIR, ".env")),
        "openrouter_model_env": env.get("OPENROUTER_MODEL", ""),
        "reasoning_env": env.get("OPENROUTER_REASONING_ENABLED", "0"),
        "masked": masked_keys(),
    }
