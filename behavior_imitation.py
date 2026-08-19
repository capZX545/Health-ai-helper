# -*- coding: utf-8 -*-
"""
behavior_imitation.py — یادگیری «سبک» پاسخ‌دهی AI خارجی و تقلید فقط لحن/ساختار
(نه محتوای پزشکی!). خروجی ai_behavior_profile.json
"""
from __future__ import annotations

import os
import re
import statistics
from typing import Any

from common_2077 import DATA_DIR, is_question, normalize, read_json, write_json
from i18n import pick

PROFILE_PATH = os.path.join(DATA_DIR, "ai_behavior_profile.json")

DEFAULT_STYLE: dict[str, Any] = {
    "samples": 0,
    "avg_len_chars": 900,
    "sections": [
        {"key": "empathy", "header": ""},
        {"key": "findings", "header": {"fa": "چیزی که از علائمت متوجه شدم", "en": "What I picked up from your symptoms"}},
        {"key": "probables", "header": {"fa": "چند احتمال مطرح است", "en": "A few possibilities to consider"}},
        {"key": "advice", "header": {"fa": "کارهایی که فعلاً می‌توانی انجام بدهی", "en": "Things you can do for now"}},
        {"key": "followup", "header": {"fa": "برای اینکه دقیق‌تر کمک کنم", "en": "So I can help more precisely"}},
    ],
    "bullet": "•",
    "use_percent": True,
    "openers": ["درکت می‌کنم؛ بذار مرحله‌به‌مرحله بررسی کنیم."],
    "closers": ["اگر علائم بدتر شد، حتماً به پزشک مراجعه کن."],
    "empathy_words": ["درکت می‌کنم", "متأسفم", "نگران نباش"],
    "avg_questions": 2,
}

# تشخیص نوع بخش از روی کلیدواژه‌های عنوان فارسی و انگلیسی (بدون وابستگی به ایموجی)
HEADER_HINTS: list[tuple[str, tuple[str, ...]]] = [
    ("warning", ("هشدار", "خطر", "قرمز", "اورژانس", "warning", "danger", "red flag", "emergency")),
    ("probables", ("احتمال", "تشخیص", "افتراقی", "possib", "likehood", "likely", "differential", "could be")),
    ("findings", ("علائم", "یافته", "چیزی که از", "مرور", "symptom", "noticed", "found", "what i")),
    ("followup", ("سوال", "پرسش", "برای اینکه دقیق", "question", "ask", "to help", "wondering")),
    ("advice", ("توصیه", "مراقبت", "کارهایی که", "اقدام", "چه کاری", "درمان خانگی", "برنامه", "advice", "you can do", "care", "tips", "try")),
    ("doctor", ("پزشک", "مراجعه", "ارجاع", "doctor", "clinician", "see a", "refer")),
    ("empathy", ("درک", "همدلی", "متوجه شدم", "خوش آمدی", "understand", "sorry", "hear you")),
]


def _classify_header(header: str) -> str:
    h = normalize(header)
    for key, words in HEADER_HINTS:
        if any(w in h for w in words):
            return key
    return "note"


def _split_sections(text: str) -> list[dict[str, str]]:
    """تفکیک پاسخ به بخش‌ها بر اساس خطوط عنوان کوتاه (خطی که با «:» تمام می‌شود
    یا کاملاً بولد است و سوال نیست)."""
    secs: list[dict[str, str]] = []
    current = {"header": "", "body": []}
    for line in (text or "").splitlines():
        s = line.strip().strip("*").strip()
        is_header = (
            bool(s)
            and len(s) < 90
            and not is_question(s)
            and (line.strip().endswith((":", "：")) or (line.strip().startswith("**") and line.strip().endswith("**")))
        )
        if is_header:
            if current["body"] or current["header"]:
                secs.append(current)
            current = {"header": s.rstrip(":：* ").strip(), "body": []}
        else:
            current["body"].append(line)
    secs.append(current)
    return [s for s in secs if s["body"] or s["header"]]


_BAD_OPENER_MARKS = ("offline", "تحلیل تصویر", "offline image", "emergency", "هشدار اورژانسی", "image type", "نوع تصویر")


def _valid_opener(s: str) -> bool:
    s = (s or "").strip()
    if not (15 <= len(s) <= 160):
        return False
    if "\n" in s:
        return False
    low = s.lower()
    return not any(m in low for m in _BAD_OPENER_MARKS)


def update_profile(ai_text: str) -> dict[str, Any]:
    """استخراج سبک از پاسخ AI خارجی و ادغام در پروفایل (میانگین متحرک)."""
    prof = load_profile()
    if not ai_text or len(ai_text) < 40:
        return prof
    n = prof.get("samples", 0) + 1
    secs = _split_sections(ai_text)
    # مقدمه‌ی پاسخ به‌عنوان opener ذخیره می‌شود، نه به‌عنوان یک «بخش»
    opener = ""
    if secs and not secs[0]["header"]:
        body = " ".join(secs[0]["body"]).strip()
        if 10 < len(body) < 200:
            opener = body
    learned_sections = []
    for idx, s in enumerate(secs):
        if idx == 0 and not s["header"]:
            continue
        header = s["header"] or " ".join(s["body"][:1])[:60]
        if not header or normalize(header) == normalize(opener):
            continue
        learned_sections.append({"key": _classify_header(header), "header": header[:60]})
    openers = [opener] if opener else []
    closers = []
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
    prof["avg_questions"] = round(statistics.mean([prof.get("avg_questions", 2), sum(1 for l in ai_text.splitlines() if is_question(l))]), 1) if n > 1 else sum(1 for l in ai_text.splitlines() if is_question(l))
    prof["openers"] = [o for o in prof.get("openers", []) if _valid_opener(o)]
    if openers and _valid_opener(openers[0]):
        prof["openers"] = list(dict.fromkeys(openers + prof["openers"]))[:8]
    prof["closers"] = [c for c in prof.get("closers", []) if _valid_opener(c)]
    if closers and _valid_opener(closers[0]):
        prof["closers"] = list(dict.fromkeys(closers + prof["closers"]))[:8]
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
    # پاک‌سازی هنگام خواندن: فایل‌های مسمومِ قدیمی خودشان شفا یابند
    merged["openers"] = [o for o in merged.get("openers", []) if _valid_opener(o)]
    merged["closers"] = [c for c in merged.get("closers", []) if _valid_opener(c)]
    merged["sections"] = [s for s in merged.get("sections", [])
                          if isinstance(s, dict) and s.get("key") and s.get("header") and _valid_opener(s["header"])]
    if not merged["openers"]:
        merged["openers"] = list(DEFAULT_STYLE["openers"])
    if not merged["closers"]:
        merged["closers"] = list(DEFAULT_STYLE["closers"])
    if not merged["sections"]:
        merged["sections"] = [dict(s) for s in DEFAULT_STYLE["sections"]]
    return merged


def apply_style(sections: dict[str, list[str] | str], opener: str | None = None) -> str:
    """رندر پاسخ مغز داخلی با سبک آموخته‌شده. فقط قالب/لحن تغییر می‌کند، نه محتوا.

    sections کلیدهای مجاز: empathy, findings, probables, advice, followup, warning, doctor, note
    """
    from i18n import tt
    prof = load_profile()
    order = [s for s in prof["sections"]] if prof.get("sections") else DEFAULT_STYLE["sections"]
    seen = set()
    blocks: list[str] = []
    if prof.get("samples") and prof.get("openers"):
        op = opener or prof["openers"][0]
    else:
        op = opener or tt("I hear you. Let's work through this step by step.",
                          "درکت می‌کنم؛ بذار مرحله‌به‌مرحله بررسی کنیم.")
    parts_out: list[str] = []
    # جلوگیری از تکرار: اگر بخش empathy همان جمله‌ی شروع باشد، فقط یک‌بار بیاید
    emp = sections.get("empathy")
    if isinstance(emp, str) and normalize(emp) == normalize(op):
        sections = dict(sections)
        sections.pop("empathy", None)
    op_norm = normalize(op)
    for s in order:
        if normalize(s.get("header") or "") == op_norm:
            continue  # سرتیتری که همان جمله‌ی شروع است تکرار نشود
        key = s.get("key") or "note"
        if key in seen or key not in sections or not sections[key]:
            continue
        seen.add(key)
        content = sections[key]
        header = s.get("header") or ""
        if isinstance(content, str):
            body = content
        else:
            b = prof.get("bullet", "•")
            body = "\n".join(f"{b} {str(line)}" for line in content)
        header_text = pick(header) if isinstance(header, (dict, tuple, list)) else header
        if header_text:
            blocks.append(f"{header_text}:\n{body}".strip())
        else:
            blocks.append(body.strip())
    for k in sections:  # کلیدهای خارج از قالب آموخته‌شده
        if k not in seen and sections[k]:
            content = sections[k]
            body = content if isinstance(content, str) else "\n".join(f"• {c}" for c in content)
            blocks.append(body.strip())
    if prof.get("samples") and prof.get("closers"):
        closer = prof["closers"][0]
    else:
        closer = tt("If anything gets worse, do see a doctor.",
                    "اگر علائم بدتر شد، حتماً به پزشک مراجعه کن.")
    parts_out.append(op)
    parts_out.extend(blocks)
    if closer:
        parts_out.append(closer)
    return "\n\n".join(p for p in parts_out if p and p.strip())
