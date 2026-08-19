# -*- coding: utf-8 -*-
"""
free_ai.py — لیست مدل‌های رایگان/پیشنهادی OpenRouter و انتخاب پشتیبان.
"""
from __future__ import annotations

from typing import Any

OPENROUTER_FREE_MODELS: list[dict[str, str]] = [
    {"id": "openai/gpt-oss-120b:free", "fa": "GPT-OSS 120B (رایگان) — پیش‌فرض", "vision": False},
    {"id": "qwen/qwen3-next-80b-a3b-instruct:free", "fa": "Qwen3 Next 80B (رایگان) — پشتیبان", "vision": False},
    {"id": "meta-llama/llama-3.3-70b-instruct:free", "fa": "Llama 3.3 70B (رایگان)", "vision": False},
    {"id": "deepseek/deepseek-chat-v3-0324:free", "fa": "DeepSeek V3 (رایگان)", "vision": False},
    {"id": "google/gemini-2.0-flash-exp:free", "fa": "Gemini 2.0 Flash (رایگان)", "vision": True},
    {"id": "mistralai/mistral-small-3.1-24b-instruct:free", "fa": "Mistral Small 3.1 (رایگان)", "vision": True},
    {"id": "qwen/qwen2.5-vl-72b-instruct:free", "fa": "Qwen2.5 VL 72B (رایگان، تصویری)", "vision": True},
    {"id": "openai/gpt-4o-mini", "fa": "GPT-4o Mini (پولی، سریع)", "vision": True},
    {"id": "anthropic/claude-3.5-haiku", "fa": "Claude 3.5 Haiku (پولی)", "vision": True},
]

DEFAULT_MODEL = "openai/gpt-oss-120b:free"
BACKUP_MODEL = "qwen/qwen3-next-80b-a3b-instruct:free"


def model_ids() -> list[str]:
    return [m["id"] for m in OPENROUTER_FREE_MODELS]


def vision_models() -> list[str]:
    return [m["id"] for m in OPENROUTER_FREE_MODELS if m.get("vision")]


def is_vision_model(model: str) -> bool:
    m = (model or "").lower()
    return any(v in m for v in ("vl", "vision", "gpt-4o", "gemini", "llava", "pixtral", "claude-3"))


def free_chat(messages: list[dict], **kw) -> dict[str, Any]:
    """گفتگو با مدل پیش‌فرض و در صورت خطا، مدل پشتیبان (هر دو رایگان)."""
    from ai_api_manager import get_api_key
    from ai_client import chat
    if not get_api_key("openrouter"):
        return {"ok": False, "error": "missing_key", "error_fa": "کلید OpenRouter تنظیم نشده است."}
    res1 = chat("openrouter", messages, model=DEFAULT_MODEL, **kw)
    if res1.get("ok"):
        return res1
    res2 = chat("openrouter", messages, model=BACKUP_MODEL, **kw)
    if res2.get("ok"):
        return res2
    res1.setdefault("error_fa", "هیچ‌کدام از مدل‌های رایگان پاسخ ندادند.")
    res1["fallback_error"] = res2.get("error_fa")
    return res1
