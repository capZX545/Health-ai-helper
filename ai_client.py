# -*- coding: utf-8 -*-
"""
ai_client.py — کلاینت HTTP برای OpenRouter / OpenAI / DeepSeek.
پشتیبانی اختیاری از reasoning_details (بخش ۸ پرامپت): ذخیره و بازگرداندن بدون تغییر
در پیام بعدی همان مدل؛ هرگز به کاربر نمایش داده نمی‌شود.
"""
from __future__ import annotations

import json
import os
import threading
import time
from typing import Any

import requests

from common_2077 import DATA_DIR, env_get, read_json, write_json

ENDPOINTS = {
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "openai": "https://api.openai.com/v1/chat/completions",
    "deepseek": "https://api.deepseek.com/chat/completions",
}

REASONING_STATE_PATH = os.path.join(DATA_DIR, ".reasoning_state.json")
_reasoning_lock = threading.RLock()


def _headers(provider: str, key: str) -> dict[str, str]:
    h = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if provider == "openrouter":
        h["HTTP-Referer"] = "https://nexusmed2077.local"
        h["X-Title"] = "NexusMed 2077"
    return h


def _model_for(provider: str, model: str | None) -> str:
    if model:
        return model
    if provider == "openrouter":
        return env_get("OPENROUTER_MODEL", "openai/gpt-oss-120b:free")
    if provider == "openai":
        return "gpt-4o-mini"
    if provider == "deepseek":
        return "deepseek-chat"
    return model or ""


# ------------------------------------------------- reasoning_details (بخش ۸)

def _load_reasoning_state() -> dict:
    return read_json(REASONING_STATE_PATH, default={}) or {}


def get_saved_reasoning(model: str) -> list | None:
    with _reasoning_lock:
        st = _load_reasoning_state()
        v = st.get(model)
        return v if isinstance(v, list) and v else None


def save_reasoning(model: str, details: Any) -> None:
    if not model or not details:
        return
    with _reasoning_lock:
        st = _load_reasoning_state()
        st[model] = details
        # فقط آخرین ۵ مدل نگه داشته شود
        if len(st) > 5:
            for k in list(st.keys())[:-5]:
                st.pop(k, None)
        write_json(REASONING_STATE_PATH, st)


def clear_reasoning(model: str | None = None) -> None:
    with _reasoning_lock:
        if model:
            st = _load_reasoning_state()
            st.pop(model, None)
            write_json(REASONING_STATE_PATH, st)
        else:
            write_json(REASONING_STATE_PATH, {})


# ------------------------------------------------------------------- chat

def chat(provider: str, messages: list[dict], model: str | None = None,
         temperature: float = 0.4, max_tokens: int = 1200,
         image_b64: str | None = None, image_mime: str = "image/jpeg",
         reasoning_enabled: bool = False, timeout: int = 90) -> dict[str, Any]:
    """
    خروجی: {ok, text, provider, model, reasoning_details, error, error_code, error_fa}
    """
    from ai_api_manager import get_api_key
    key = get_api_key(provider)
    if not key:
        from i18n import tt
        return {"ok": False, "error": "missing_key", "error_fa": tt(f"No API key configured for {provider}.", f"کلید API برای {provider} تنظیم نشده است.")}
    url = ENDPOINTS.get(provider)
    if not url:
        from i18n import tt
        return {"ok": False, "error": "unknown_provider", "error_fa": tt("Unknown provider.", "سرویس ناشناخته است.")}
    mdl = _model_for(provider, model)

    # ساخت پیام آخر + تصویر (vision)
    msgs = [dict(m) for m in messages]
    if image_b64 and msgs:
        last = msgs[-1]
        content = [{"type": "text", "text": str(last.get("content", ""))},
                   {"type": "image_url", "image_url": {"url": f"data:{image_mime};base64,{image_b64}"}}]
        msgs[-1] = {"role": "user", "content": content}

    # بازگرداندن reasoning_details ذخیره‌شده‌ی همان مدل (بدون تغییر)
    saved = get_saved_reasoning(mdl) if reasoning_enabled else None
    if saved and msgs and msgs[-1].get("role") == "user":
        msgs.append({"role": "assistant", "content": "", "reasoning_details": saved})

    payload: dict[str, Any] = {
        "model": mdl,
        "messages": msgs,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if provider == "openrouter" and reasoning_enabled:
        payload["reasoning"] = {"enabled": True}

    try:
        resp = requests.post(url, headers=_headers(provider, key), json=payload, timeout=timeout)
    except requests.exceptions.Timeout:
        from i18n import tt
        return {"ok": False, "error": "timeout", "error_fa": tt("The service took too long to respond. Try again.", "پاسخ سرویس بیش از حد انتظار طول کشید. دوباره تلاش کنید.")}
    except requests.exceptions.ConnectionError:
        from i18n import tt
        return {"ok": False, "error": "no_internet", "error_fa": tt("No internet connection, or the service is unreachable.", "اینترنت قطع است یا سرویس در دسترس نیست.")}
    except Exception as e:
        from i18n import tt
        return {"ok": False, "error": str(e)[:150], "error_fa": tt("Unknown connection error.", "خطای نامشخص در اتصال.")}

    if resp.status_code != 200:
        from i18n import tt
        codes = {
            401: ("Invalid API key.", "کلید API نامعتبر است."),
            402: ("Not enough credit on the account.", "اعتبار حساب کافی نیست."),
            403: ("Access to this model is not allowed.", "دسترسی به این مدل مجاز نیست."),
            404: ("Model not found; check the model id.", "مدل پیدا نشد؛ شناسه‌ی مدل را بررسی کنید."),
            429: ("Rate limited; try again in a moment.", "محدودیت درخواست (Rate limit)؛ کمی بعد دوباره تلاش کنید."),
            500: ("Server error on the provider side.", "خطای سرور سرویس دهنده."),
            502: ("Service temporarily unavailable.", "سرویس موقتاً در دسترس نیست."),
            503: ("Service temporarily overloaded.", "سرویس موقتاً شلوغ است."),
        }
        en, fa = codes.get(resp.status_code, (f"HTTP error {resp.status_code}", f"خطای HTTP {resp.status_code}"))
        fa = tt(en, fa)
        return {"ok": False, "error": resp.text[:200], "error_code": resp.status_code, "error_fa": fa}

    try:
        data = resp.json()
        msg = data["choices"][0]["message"]
        text = (msg.get("content") or "").strip()
        rdet = msg.get("reasoning_details") or msg.get("reasoning")
        if reasoning_enabled and rdet:
            save_reasoning(mdl, rdet)
        if not text:
            from i18n import tt
            return {"ok": False, "error": "empty_response", "error_fa": tt("The model returned an empty reply; try another model.", "پاسخ مدل خالی بود؛ مدل دیگری را امتحان کنید.")}
        return {"ok": True, "text": text, "provider": provider, "model": mdl,
                "reasoning_details": rdet if reasoning_enabled else None}
    except Exception as e:
        from i18n import tt
        return {"ok": False, "error": f"parse:{e}", "error_fa": tt("Could not read the service response.", "پاسخ سرویس قابل خواندن نبود.")}


def chat_with_fallbacks(messages: list[dict], models: list[dict[str, str]] | None = None,
                        **kw) -> dict[str, Any]:
    """امتحان ترتیبی چند سرویس/مدل تا اولین موفقیت."""
    from ai_api_manager import get_api_key, get_settings
    s = get_settings()
    order = [p for p in s["provider_order"] if p != "local" and get_api_key(p)]
    tries = []
    for p in order:
        mdl = s["openrouter_model"] if p == "openrouter"else None
        res = chat(p, messages, model=mdl, **kw)
        res["provider"] = p
        if res["ok"]:
            return res
        tries.append(f"{p}: {res.get('error_fa')}")
    return {"ok": False, "error": "all_failed", "error_fa": "هیچ سرویس خارجی پاسخ نداد:\n"+ "\n".join(tries),
            "tries": tries}
