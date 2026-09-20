"""
second_opinion.py — asks the same medical question to two AI providers at
the same time and puts the answers side by side for comparison.
Runs the two calls in parallel threads; works with OpenRouter, OpenAI,
DeepSeek and LM Studio.
"""
from __future__ import annotations

import threading
from typing import Any

from i18n import is_fa

_TIMEOUT_JOIN = 95


def _ask(provider: str, question: str, out: dict, key: str, model: str = "") -> None:
    try:
        msgs = [
            {"role": "system", "content": "You are NexusMed, a careful bilingual medical assistant. "
                                          "Answer in the user's language. Be concise, structured and "
                                          "safety-first; never give a definitive diagnosis."},
            {"role": "user", "content": question},
        ]
        if provider == "lmstudio":
            from local_lm_connector import chat as lm_chat
            r = lm_chat(msgs)
        else:
            from ai_client import chat as ext_chat
            r = ext_chat(provider, msgs, model=(model or None))
        out[key] = r
    except Exception as e:
        out[key] = {"ok": False, "error_fa": str(e)[:150], "message_fa": str(e)[:150]}


def ask(question: str, provider_a: str = "openrouter", provider_b: str = "lmstudio",
        model_a: str = "") -> dict[str, Any]:
    fa = is_fa()
    question = str(question or "").strip()
    if not question:
        return {"ok": False, "message_fa": "سؤالت را بنویس." if fa else "Type your question."}
    out: dict[str, Any] = {}
    t1 = threading.Thread(target=_ask, args=(provider_a, question, out, "a", model_a), daemon=True)
    t2 = threading.Thread(target=_ask, args=(provider_b, question, out, "b"), daemon=True)
    t1.start()
    t2.start()
    t1.join(_TIMEOUT_JOIN)
    t2.join(_TIMEOUT_JOIN)
    ra = out.get("a") or {"ok": False, "message_fa": "پاسخی دریافت نشد." if fa else "No response."}
    rb = out.get("b") or {"ok": False, "message_fa": "پاسخی دریافت نشد." if fa else "No response."}
    return {
        "ok": True,
        "a": {"provider": provider_a, "ok": bool(ra.get("ok")), "text": ra.get("text", ""),
              "message_fa": ra.get("error_fa") or ra.get("message_fa") or ""},
        "b": {"provider": provider_b, "ok": bool(rb.get("ok")), "text": rb.get("text", ""),
              "message_fa": rb.get("error_fa") or rb.get("message_fa") or ""},
        "message_fa": "",
    }
