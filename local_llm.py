# -*- coding: utf-8 -*-
"""
local_llm.py — اتصال به Ollama (هوش مصنوعی محلی/GPU).
پیش‌فرض: http://localhost:11434 و مدل qwen2.5:7b-instruct
تنظیمات در local_llm_config.json ذخیره می‌شود.
"""
from __future__ import annotations

import os
from typing import Any

import requests

from common_2077 import DATA_DIR, read_json, write_json

CONFIG_PATH = os.path.join(DATA_DIR, "local_llm_config.json")

DEFAULT_CONFIG: dict[str, Any] = {
    "enabled": False,
    "base_url": "http://localhost:11434",
    "model": "qwen2.5:7b-instruct",
    "timeout": 180,
    "keep_context": True,
}


def get_config() -> dict[str, Any]:
    cfg = dict(DEFAULT_CONFIG)
    stored = read_json(CONFIG_PATH, default=None)
    if isinstance(stored, dict):
        cfg.update({k: v for k, v in stored.items() if k in DEFAULT_CONFIG})
    return cfg


def save_config(updates: dict[str, Any]) -> dict[str, Any]:
    cfg = get_config()
    cfg.update({k: v for k, v in updates.items() if k in DEFAULT_CONFIG})
    write_json(CONFIG_PATH, cfg)
    return cfg


def is_up(base_url: str | None = None, timeout: int = 4) -> bool:
    cfg = get_config()
    url = (base_url or cfg["base_url"]).rstrip("/")
    try:
        r = requests.get(f"{url}/api/tags", timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def list_models(base_url: str | None = None) -> list[str]:
    cfg = get_config()
    url = (base_url or cfg["base_url"]).rstrip("/")
    try:
        r = requests.get(f"{url}/api/tags", timeout=6)
        data = r.json()
        return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
    except Exception:
        return []


def chat(messages: list[dict], model: str | None = None, **kw) -> dict[str, Any]:
    """گفتگو با مدل محلی. خروجی هم‌شکل ai_client.chat"""
    cfg = get_config()
    if not cfg.get("enabled"):
        return {"ok": False, "error": "disabled", "error_fa": "هوش مصنوعی محلی در تنظیمات فعال نیست."}
    url = cfg["base_url"].rstrip("/")
    payload = {"model": model or cfg["model"], "messages": messages, "stream": False}
    try:
        r = requests.post(f"{url}/api/chat", json=payload, timeout=cfg.get("timeout", 180))
        if r.status_code != 200:
            return {"ok": False, "error": r.text[:150], "error_fa": f"خطای Ollama (کد {r.status_code})"}
        text = (r.json().get("message", {}) or {}).get("content", "").strip()
        if not text:
            return {"ok": False, "error": "empty", "error_fa": "پاسخ مدل محلی خالی بود."}
        return {"ok": True, "text": text, "provider": "local", "model": payload["model"]}
    except requests.exceptions.ConnectionError:
        return {"ok": False, "error": "no_ollama", "error_fa": "Ollama اجرا نیست (آدرس: " + url + ")"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:150], "error_fa": "خطا در ارتباط با مدل محلی."}


def test_setup() -> dict[str, Any]:
    """بررسی کامل: روشن بودن، وجود مدل، تست پاسخ."""
    cfg = get_config()
    up = is_up(cfg["base_url"])
    out: dict[str, Any] = {"up": up, "base_url": cfg["base_url"], "model": cfg["model"], "models": [], "test_ok": False}
    if not up:
        out["message_fa"] = "❌ Ollama در دسترس نیست. مطمئن شوید `ollama serve` اجراست."
        return out
    out["models"] = list_models(cfg["base_url"])
    if cfg["model"] not in out["models"]:
        out["message_fa"] = f"⚠️ مدل «{cfg['model']}» پیدا نشد. مدل‌های موجود: " + "، ".join(out["models"][:10])
        return out
    res = chat([{"role": "user", "content": "سلام، یک کلمه جواب بده."}])
    out["test_ok"] = bool(res.get("ok"))
    out["message_fa"] = "✅ Ollama و مدل محلی سالم هستند." if res.get("ok") else "❌ " + res.get("error_fa", "تست پاسخ شکست خورد.")
    return out
