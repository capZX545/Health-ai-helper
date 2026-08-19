# -*- coding: utf-8 -*-
"""
behavior_imitation.py — یادگیری «سبک» پاسخ‌دهی AI خارجی و تقلید فقط لحن/ساختار
(نه محتوای پزشکی!). خروجی ai_behavior_profile.json
"""
from __future__ import annotations

import re
import statistics
from typing import Any

from common_2077 import DATA_DIR, is_question, normalize, read_json, write_json
import os

PROFILE_PATH = os.path.join(DATA_DIR, "ai_behavior_profile.json")

DEFAULT_STYLE: dict[str, Any] = {
    "samples": 0,
    "avg_len_chars": 900,
    "sections": [
        {"key": "empathy", "header": "", "emoji": "🤝"},
        {"key": "findings", "header": "چیزی که از علائمت متوجه شدم", "emoji": "🔎"},
        {"key": "probables", "header": "چند احتمال مطرح است", "emoji": "🎯"},
        {"key": "advice", "header": "کارهایی که فعلاً می‌توانی انجام بدهی", "emoji": "💊"},
        {"key": "followup", "header": "برای اینکه دقیق‌تر کمک کنم", "emoji": "❓"},
    ],
    "bullet": "•",
    "use_percent": True,
    "openers": ["درکت می‌کنم؛ بذار مرحله‌به‌مرحله بررسی کنیم."],
    "closers": ["اگر علائم بدتر شد، حتماً به پزشک مراجعه کن."],
    "empathy_words": ["درکت می‌کنم", "متأسفم", "نگران نباش"],
    "emoji_density": 0.5,
    "avg_questions": 2,
}

KNOWN_HEADERS = {
    "🔎": "findings", "🎯": "probables", "💊": "advice", "❓": "followup", "🤝": "empathy",
    "⚠": "warning", "🚨": "warning", "🩺": "doctor", "📌": "note", "✅": "advice", "🏠": "advice",
}

_EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")


def _split_sections(text: str) -> list[dict[str, str]]:
    secs: list[dict[str, str]] = []
    current = {"emoji": "", "header": "intro", "body": []}
    for line in (text or "").splitlines():
        m = re.match(r"^\s*([^\w\sآ-ی]{1,3})?\s*([^:：「」*#]{2,60})[:：]", line.strip())
        emoji = ""
        first = line.strip()[:4]
        for ch in first:
            if _EMOJI_RE.match(ch):
                emoji = ch
                break
        is_header = bool(emoji and len(line.strip()) < 90) or bool(m and m.group(1) is None and len(line.strip()) < 80 and not is_question(line))
        if is_header and (emoji in KNOWN_HEADERS or (m and m.group(2))):
            if current["body"] or current["header"] != "intro":
                secs.append(current)
            current = {"emoji": emoji, "header": (m.group(2) if m else line.strip().strip(emoji).strip(" :："))[:60], "body": []}
        else:
            current["body"].append(line)
    secs.append(current)
    return [s for s in secs if s["body"] or s["header"] != "intro"]


def update_profile(ai_text: str) -> dict[str, Any]:
    """استخراج سبک از پاسخ AI خارجی و ادغام در پروفایل (running average)."""
    prof = load_profile()
    if not ai_text or len(ai_text) < 40:
        return prof
    n = prof.get("samples", 0) + 1
    secs = _split_sections(ai_text)
    learned_sections = []
    for s in secs:
        key = KNOWN_HEADERS.get(s["emoji"])
        if not key:
            head = normalize(s["header"])
            for word, mapped in (("احتمال", "probables"), ("علائم", "findings"), ("کار", "advice"), ("سوال", "followup"), ("پرسش", "followup")):
                if word in head:
                    key = mapped
                    break
        learned_sections.append({"key": key or "note", "header": s["header"][:60], "emoji": s["emoji"]})
    openers, closers = [], []
    if secs and secs[0]["header"] == "intro":
        body = " ".join(secs[0]["body"]).strip()
        if 10 < len(body) < 200:
            openers = [body]
    tail = secs[-1]["body"] if secs else []
    for ln in reversed([l for l in tail if l.strip()]):
        if is_question(ln):
            break
        if 10 < len(ln.strip()) < 200:
            closers = [ln.strip()]
            break
    empathy = [w for w in DEFAULT_STYLE["empathy_words"] if normalize(w) in normalize(ai_text)]
    prof["samples"] = n
    prof["avg_len_chars"] = int(statistics.mean([prof.get("avg_len_chars", 900), len(ai_text)]) if n > 1 else len(ai_text))
    prof["emoji_density"] = round(statistics.mean([prof.get("emoji_density", 0.5), min(len(_EMOJI_RE.findall(ai_text)) / 10.0, 1.0)]), 2) if n > 1 else round(min(len(_EMOJI_RE.findall(ai_text)) / 10.0, 1.0), 2)
    prof["avg_questions"] = round(statistics.mean([prof.get("avg_questions", 2), sum(1 for l in ai_text.splitlines() if is_question(l))]), 1) if n > 1 else sum(1 for l in ai_text.splitlines() if is_question(l))
    if openers:
        prof["openers"] = list(dict.fromkeys(openers + prof.get("openers", [])))[:8]
    if closers:
        prof["closers"] = list(dict.fromkeys(closers + prof.get("closers", [])))[:8]
    if empathy:
        prof["empathy_words"] = list(dict.fromkeys(empathy + prof.get("empathy_words", [])))[:12]
    if any(s["key"] in ("findings", "probables", "advice", "followup") for s in learned_sections):
        prof["sections"] = learned_sections[:6]
    prof["bullet"] = "•" if ai_text.count("•") >= ai_text.count("- ") else ("-" if "- " in ai_text else prof.get("bullet", "•"))
    prof["updated_at"] = __import__("common_2077", fromlist=["now_iso"]).now_iso()
    write_json(PROFILE_PATH, prof)
    return prof


def load_profile() -> dict[str, Any]:
    data = read_json(PROFILE_PATH, default=None)
    if not isinstance(data, dict) or not data:
        import copy
        return copy.deepcopy(DEFAULT_STYLE)
    merged = dict(DEFAULT_STYLE)
    merged.update(data)
    return merged


def apply_style(sections: dict[str, list[str] | str], opener: str | None = None) -> str:
    """رندر پاسخ مغز داخلی با سبک آموخته‌شده. فقط قالب/لحن تغییر می‌کند، نه محتوا.

    sections کلیدهای مجاز: empathy, findings, probables, advice, followup, warning, doctor, note
    """
    prof = load_profile()
    order = [s for s in prof["sections"]] if prof.get("sections") else DEFAULT_STYLE["sections"]
    seen = set()
    blocks: list[str] = []
    op = opener or (prof["openers"][0] if prof.get("openers") else DEFAULT_STYLE["openers"][0])
    parts_out: list[str] = []
    # جلوگیری از تکرار: اگر بخش empathy همان جمله‌ی شروع باشد، فقط یک‌بار بیاید
    emp = sections.get("empathy")
    if isinstance(emp, str) and normalize(emp) == normalize(op):
        sections = dict(sections)
        sections.pop("empathy", None)
    for s in order:
        key = s.get("key") or "note"
        if key in seen or key not in sections or not sections[key]:
            continue
        seen.add(key)
        content = sections[key]
        header = s.get("header") or ""
        emoji = s.get("emoji") or ""
        if isinstance(content, str):
            body = content
        else:
            b = prof.get("bullet", "•")
            body = "\n".join(f"{b} {str(line)}" for line in content)
        if header:
            blocks.append(f"{emoji} {header}:\n{body}".strip())
        else:
            blocks.append((f"{emoji} {body}" if emoji else body).strip())
    for k in sections:  # کلیدهای خارج از قالب آموخته‌شده
        if k not in seen and sections[k]:
            content = sections[k]
            body = content if isinstance(content, str) else "\n".join(f"• {c}" for c in content)
            blocks.append(body)
    closer = prof["closers"][0] if prof.get("closers") else DEFAULT_STYLE["closers"][0]
    parts_out.append(op)
    parts_out.extend(blocks)
    if closer:
        parts_out.append(closer)
    return "\n\n".join(p for p in parts_out if p and p.strip())
