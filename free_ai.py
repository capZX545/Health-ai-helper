# -*- coding: utf-8 -*-
"""
free_ai.py — لیست مدل‌های رایگان/پیشنهادی OpenRouter و انتخاب پشتیبان.
"""
from __future__ import annotations

from typing import Any

OPENROUTER_FREE_MODELS: list[dict[str, str]] = [
    {"id": "z-ai/glm-5.2:free", "fa": "GLM 5.2 (رایگان) — پشتیبان", "vision": False},
    {"id": "nvidia/nemotron-3-super-120b-a12b:free", "fa": "Nemotron 3 Super 120B (رایگان) — پیش‌فرض", "vision": False},
    {"id": "google/gemma-4-31b-it:free", "fa": "Gemma 4 31B (رایگان)", "vision": False},
    {"id": "nvidia/nemotron-3-nano-30b-a3b:free", "fa": "Nemotron 3 Nano 30B (رایگان، سریع)", "vision": False},
    {"id": "thinkingmachines/inkling-small:free", "fa": "Inkling Small (رایگان)", "vision": False},
    {"id": "nvidia/nemotron-nano-12b-v2-vl:free", "fa": "Nemotron Nano 12B VL (رایگان، تصویری)", "vision": True},
    {"id": "openrouter/free", "fa": "OpenRouter Auto Free (رایگان)", "vision": False},
    {"id": "openai/gpt-4o-mini", "fa": "GPT-4o Mini (پولی، سریع)", "vision": True},
]

DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
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
