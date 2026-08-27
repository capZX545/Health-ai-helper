"""
medical_nlg.py — builds the offline engine's reply, English or Persian.
Never a definitive diagnosis: always possibilities, a follow-up question
and the safety warning.
"""
from __future__ import annotations

import random
from typing import Any

from common_2077 import fa_digits, safe_percent
from i18n import is_fa

OPENERS_EN = [
    "I hear you. Let's work through this step by step.",
    "Thanks for describing it clearly. Let's go over it together.",
    "Okay, let's take a careful look at this.",
]
OPENERS_FA = [
    "درکت می‌کنم؛ بذار مرحله‌به‌مرحله بررسی کنیم.",
    "ممنون که دقیق گفتی؛ با هم مرورش کنیم.",
    "خب، بذار با هم نگاهی بیندازیم.",
]

URGENCY_FA = {
    "emergency": "فوری — اورژانس",
    "urgent": "نیاز به بررسی پزشک در اولین فرصت",
    "routine": "قابل پیگیری سرپایی",
}
URGENCY_EN = {
    "emergency": "urgent - emergency care",
    "urgent": "see a clinician at the first opportunity",
    "routine": "can be followed up as an outpatient",
}


def _pct(p) -> str:
    if is_fa():
        return fa_digits(f"{safe_percent(p)}٪")
    return f"{safe_percent(p)}%"


def compose_offline_answer(analysis: dict[str, Any], dialogue_summary: dict[str, Any],
                           profile: dict[str, Any], ml_preds: list[dict] | None,
                           rag_hits: list[dict] | None, followup_question: str | None) -> dict[str, list[str] | str]:
    """Concise GPT-style reply: symptom summary, likely conditions, one next question."""
    sections: dict[str, Any] = {}
    fa = is_fa()
    syms = analysis.get("symptoms", [])
    denied = analysis.get("denied", [])
    cands = analysis.get("candidates", [])
    det = analysis.get("detected", {}) or {}

    findings: list[str] = []
    if syms:
        _s = [_clean_fa(str(x)) if fa else str(x) for x in syms[:8]]
        _s = [x for x in _s if x.strip()]
        findings.append(("علائم: " if fa else "Symptoms: ") + ("، ".join(_s) if fa else ", ".join(_s)))
    if denied:
        findings.append(("ردشده: " if fa else "Ruled out: ") + ("، ".join(denied[:4]) if fa else ", ".join(denied[:4])))
    bits = []
    if det.get("duration_days") is not None:
        bits.append((f"~{fa_digits(str(det['duration_days']))} روز" if fa else f"~{det['duration_days']}d"))
    if det.get("temp_c") is not None:
        bits.append((f"تب {fa_digits(str(det['temp_c']))}°" if fa else f"fever {det['temp_c']}°C"))
    if bits:
        findings.append(" | ".join(bits))
    sections["findings"] = findings or [""]
    if not findings:
        sections["findings"] = [""]

    probables: list[str] = []
    urg = URGENCY_FA if fa else URGENCY_EN
    if cands:
        for c in cands[:4]:
            short = str(c.get("name", "")).split("(")[0].strip()
            u = urg.get(c.get("urgency", ""), "")
            line = f"{short} {_pct(c['percent'])}" + (f" [{u}]" if u else "")
            probables.append(line)
    if not probables:
        probables = [("" if fa else "")]
    sections["probables"] = probables

    advice: list[str] = []
    seen: set[str] = set()
    for c in cands[:2]:
        for a in c.get("advice", [])[:2]:
            k = a.strip()[:50]
            if k not in seen and len(advice) < 2:
                seen.add(k)
                advice.append(a)
        if advice:
            break
    advice = [_clean_fa(a) if fa else a for a in advice]
    advice = [a for a in advice if a.strip()]
    if not advice:
        advice = ["استراحت و آب کافی" if fa else "Rest and hydrate"]
    sections["advice"] = advice

    doctor: list[str] = []
    for c in cands[:1]:
        if c.get("doctor_when"):
            doctor.append(str(c["doctor_when"])[:120])
    sections["doctor"] = doctor

    sections["warning"] = ""
    for c in cands[:2]:
        if c.get("urgency") == "emergency":
            sections["warning"] = (" اورژانس: ۱۱۵ / ۱۱۲" if fa else " Emergency: 115 / 112")
            break

    if followup_question:
        sections["followup"] = str(followup_question).strip()
    else:
        sections["followup"] = "علامت دیگری هم داری؟" if fa else "Any other symptoms?"

    return sections


def _clean_fa(text: str) -> str:
    """Strip obviously corrupted segments (foreign words mixed into farsi)."""
    import re as _re
    keep = {"mg", "dl", "mmol", "kg", "cm", "ph", "ecg", "mri", "ct", "copd", "aids",
            "hiv", "cpr", "icd", "who", "fda", "hpo", "doid", "tsh", "fbs", "hba1c",
            "ldl", "hdl", "nsaid", "ssri", "acei", "arb", "pPI", "utI", "bp", "bmi"}
    def _sub(m):
        w = m.group(0)
        return w if w.lower() in keep else ""
    cleaned = _re.sub(r"[A-Za-z]{3,}", _sub, text)
    cleaned = _re.sub(r"\s{2,}", " ", cleaned)
    cleaned = _re.sub(r"\(\s*", "(", cleaned)
    cleaned = _re.sub(r"\s*\)", ")", cleaned)
    return cleaned.strip()
