# -*- coding: utf-8 -*-
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
    """Builds the reply sections (no styling) - style is applied by behavior_imitation."""
    from medical_engine import sym_name
    sections: dict[str, Any] = {}
    fa = is_fa()
    p = profile or {}
    name = str(p.get("name") or "").strip()
    greet = (f"{name} عزیز، " if name else "") if fa else (f"{name}, " if name else "")
    sections["empathy"] = greet + random.choice(OPENERS_FA if fa else OPENERS_EN)

    findings: list[str] = []
    syms = analysis.get("symptoms", [])
    if syms:
        findings.append(("علائمی که گفتی: " if fa else "Symptoms you mentioned: ") + ("، ".join(syms) if fa else ", ".join(syms)))
    denied = analysis.get("denied", [])
    if denied:
        findings.append(("این موارد را رد کردی: " if fa else "Ruled out by you: ") + ("، ".join(denied) if fa else ", ".join(denied)))
    det = analysis.get("detected", {})
    if det.get("duration_days") is not None:
        findings.append(("مدت علائم: حدود " if fa else "Duration: about ") + (fa_digits(str(det["duration_days"])) if fa else str(det["duration_days"])) + (" روز" if fa else " days"))
    if det.get("temp_c") is not None:
        findings.append(("تب گزارش‌شده: " if fa else "Reported fever: ") + (fa_digits(str(det["temp_c"])) if fa else str(det["temp_c"])) + (" درجه" if fa else " C"))
    if p.get("age") or p.get("gender"):
        bits = []
        if p.get("age"):
            bits.append(("سن " if fa else "age ") + (fa_digits(str(p["age"])) if fa else str(p["age"])))
        if p.get("gender"):
            bits.append(("جنسیت " if fa else "sex ") + str(p["gender"]))
        findings.append(("پروفایل: " if fa else "Profile: ") + ("، ".join(bits) if fa else ", ".join(bits)))
    if not findings:
        findings.append("هنوز علامت مشخصی ثبت نشده؛ کمی بیشتر توضیح بده." if fa else "No concrete symptom recorded yet; tell me a bit more.")
    sections["findings"] = findings

    cands = analysis.get("candidates", [])
    probables: list[str] = []
    urg = URGENCY_FA if fa else URGENCY_EN
    if cands:
        for c in cands[:3]:
            line = (f"{c['name']} — حدود {_pct(c['percent'])} " if fa else f"{c['name']} — roughly {_pct(c['percent'])} ")
            line += ("احتمال نسبی" if fa else "relative likelihood")
            line += f" ({urg.get(c['urgency'], c['urgency'])})"
            probables.append(line)
        probables.append("این درصد فقط اولویت‌بندی برای مراقبت است؛ «تشخیص قطعی» فقط با معاینه‌ی پزشک ممکن است." if fa
                         else "These percentages only triage what to watch; a definite diagnosis needs an in-person exam.")
    if ml_preds:
        tops = [f"{m['label']} (~{_pct(m['percent'])})" for m in ml_preds[:2]]
        probables.append(("سیگنال طبقه‌بند ML (روی دیتاست مصنوعی تستی): " if fa else "ML classifier signal (synthetic test dataset, Persian labels): ") + ("، ".join(tops) if fa else ", ".join(tops)))
    if not probables:
        probables = ["با این اطلاعات هنوز احتمال مشخصی نمی‌شود گفت؛ به سوال پایین جواب بده تا دقیق‌تر شوم." if fa
                     else "Not enough information to weigh anything yet; answer the question below and I can be more precise."]
    sections["probables"] = probables

    advice: list[str] = []
    for c in cands[:2]:
        advice.extend(c.get("advice", [])[:3])
    if not advice:
        advice = ["استراحت کافی و آب فراوان", "ثبت تغییر علائم (شدت/مدت) برای ارائه به پزشک"] if fa else \
                 ["Rest and stay hydrated", "Track how symptoms change (severity/duration) for the doctor"]
    if rag_hits:
        for h in rag_hits[:1]:
            if h.get("title"):
                advice.append(f"از حافظه‌ی آموخته‌شده‌ی قبلی برنامه: موضوع مشابه «{h['title']}» بررسی شد." if fa
                              else f"From the assistant's learned memory: a similar topic '{h['title']}' was reviewed before.")
    advice.append("داروی خاصی را بدون تجویز پزشک شروع یا قطع نکن." if fa
                  else "Do not start or stop any medication without a prescription.")
    sections["advice"] = advice

    doctor: list[str] = []
    for c in cands[:2]:
        if c.get("doctor_when"):
            doctor.append((f"برای «{c['name']}»: " if fa else f"For '{c['name']}': ") + c["doctor_when"])
    if doctor:
        sections["doctor"] = doctor

    sections["warning"] = ("هشدار: اگر درد قفسه سینه، تنگی نفس شدید، خونریزی، بیهوشی، تشنج، ضعف یک‌طرفه یا اختلال تکلم داری، همین حالا با اورژانس تماس بگیر (ایران: ۱۱۵ | اروپا: ۱۱۲)." if fa
                           else "Warning: if you have chest pain, severe breathlessness, bleeding, unconsciousness, seizure, one-sided weakness or slurred speech, call emergency services now (Iran: 115 | Europe: 112).")

    if followup_question:
        sections["followup"] = followup_question
    else:
        sections["followup"] = "چیز دیگری در مورد علائمت اضافه می‌کنی؟ (مثلاً شروع ناگهانی، محرک، داروهای فعلی)" if fa \
                               else "Anything else about your symptoms? (sudden onset, triggers, current medications)"
    return sections
