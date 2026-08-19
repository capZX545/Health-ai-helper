# -*- coding: utf-8 -*-
"""
auto_learning.py — یادگیری خودکار از هر پاسخ AI خارجی (حتی وقتی مغز داخلی خاموش است).
خروجی: learned_knowledge.json + به‌روزرسانی ai_behavior_profile.json + پاک‌کردن کش RAG.
"""
from __future__ import annotations

import os
import re
import threading
from typing import Any

from common_2077 import DATA_DIR, first_sentences, is_question, now_iso, read_json, write_json
from medical_engine import detect_symptoms, sym_name

LEARNED_PATH = os.path.join(DATA_DIR, "learned_knowledge.json")
MAX_ENTRIES = 500
_lock = threading.RLock()


def _load() -> dict[str, Any]:
    data = read_json(LEARNED_PATH, default=None)
    if not isinstance(data, dict):
        data = {"version": 1, "entries": []}
    data.setdefault("entries", [])
    return data


def _extract_topic(user_text: str, ai_text: str) -> str:
    from semantic_rag import search
    hits = search(user_text or ai_text, k=1)
    if hits and hits[0].get("title"):
        return hits[0]["title"]
    return first_sentences(user_text, 1, 60) or "مکالمه پزشکی"


def _extract_advice(ai_text: str) -> list[str]:
    out = []
    for ln in ai_text.splitlines():
        s = ln.strip()
        if not s:
            continue
        if s.startswith(("•", "-", "*")) or re.match(r"^\d+[.)]", s):
            clean = s.lstrip("•-*0123456789.) ").strip()
            if 8 <= len(clean) <= 200:
                out.append(clean)
    return out[:8]


def _extract_followups(ai_text: str) -> list[str]:
    out = []
    for ln in ai_text.splitlines():
        if is_question(ln) and 8 <= len(ln.strip()) <= 200:
            out.append(ln.strip().lstrip("•-*?0123456789.) ").strip())
    return out[:6]


def _dedupe_signature(user_text: str, ai_text: str) -> str:
    return f"{hash(user_text.strip()[:200])}:{hash(ai_text.strip()[:200])}"


def learn_from_exchange(user_text: str, ai_text: str, provider: str = "", model: str = "",
                        red_flag: bool = False, meta: dict | None = None) -> dict[str, Any] | None:
    """ثبت یک تبادل چت با AI خارجی در حافظه‌ی یادگیری. همیشه اجرا می‌شود."""
    if not ai_text or len(ai_text.strip()) < 20:
        return None
    with _lock:
        det = detect_symptoms(user_text or "")
        entry = {
            "ts": now_iso(),
            "provider": provider,
            "model": model,
            "red_flag": red_flag,
            "topic": _extract_topic(user_text, ai_text),
            "user_summary": first_sentences(user_text, 1, 160),
            "symptoms": [sym_name(s) for s, i in det["present"].items() if not i.get("denied")][:12],
            "symptoms_fa": [sym_name(s) for s, i in det["present"].items() if not i.get("denied")][:12],
            "ai_summary": first_sentences(ai_text, 3, 420),
            "advice_fa": _extract_advice(ai_text),
            "followups_fa": _extract_followups(ai_text),
            "style_len": len(ai_text),
            "sig": _dedupe_signature(user_text or "", ai_text),
        }
        if meta:
            entry["meta"] = {k: str(v)[:80] for k, v in list(meta.items())[:6]}
        data = _load()
        if any(e.get("sig") == entry["sig"] for e in data["entries"][-30:]):
            return None
        data["entries"].append(entry)
        if len(data["entries"]) > MAX_ENTRIES:
            data["entries"] = data["entries"][-MAX_ENTRIES:]
        data["updated_at"] = now_iso()
        write_json(LEARNED_PATH, data)
    # تقلید سبک (فقط لحن/ساختار) — حتی در پاسخ‌های اورژانسی سبک بازنویسی نمی‌شود
    try:
        if not red_flag:
            from behavior_imitation import update_profile
            update_profile(ai_text)
    except Exception:
        pass
    # کش RAG پاک شود تا دانش جدید بلافاصله قابل استفاده باشد
    try:
        from semantic_rag import invalidate
        invalidate()
    except Exception:
        pass
    return entry


def stats() -> dict[str, Any]:
    data = _load()
    entries = data.get("entries", [])
    topics: dict[str, int] = {}
    for e in entries:
        t = str(e.get("topic", ""))[:40]
        if t:
            topics[t] = topics.get(t, 0) + 1
    top = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]
    return {"entries": len(entries), "max": MAX_ENTRIES, "top_topics": [t[0] for t in top]}


def recent(n: int = 5) -> list[dict[str, Any]]:
    return _load().get("entries", [])[-n:][::-1]


def reset() -> bool:
    return write_json(LEARNED_PATH, {"version": 1, "entries": [], "updated_at": now_iso()})
