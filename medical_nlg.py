# -*- coding: utf-8 -*-
"""
medical_nlg.py — تولید پاسخ فارسی محاوره‌ای به سبک پزشک دلسوز.
هرگز تشخیص قطعی نمی‌دهد؛ همیشه احتمالات + سوال پیگیری + هشدار.
"""
from __future__ import annotations

import random
from typing import Any

from common_2077 import MEDICAL_DISCLAIMER, fa_digits, safe_percent

OPENERS = [
    "درکت می‌کنم؛ بذار مرحله‌به‌مرحله بررسی کنیم.",
    "ممنون که دقیق گفتی؛ با هم مرورش کنیم.",
    "خب، بذار با هم نگاهی بیندازیم.",
]

URGENCY_FA = {
    "emergency": "فوری — اورژانس",
    "urgent": "نیاز به بررسی پزشک در اولین فرصت",
    "routine": "قابل پیگیری سرپایی",
}


def _pct(p) -> str:
    return fa_digits(f"{safe_percent(p)}٪")


def compose_offline_answer(analysis: dict[str, Any], dialogue_summary: dict[str, Any],
                           profile: dict[str, Any], ml_preds: list[dict] | None,
                           rag_hits: list[dict] | None, followup_question: str | None) -> dict[str, list[str] | str]:
    """ساخت بخش‌های پاسخ (بدون سبک) — سبک در behavior_imitation اعمال می‌شود."""
    from medical_engine import SYMPTOM_NAMES_FA
    sections: dict[str, Any] = {}
    p = profile or {}
    name = (p.get("name") or "").strip()
    greet = f"{name} عزیز، " if name else ""

    sections["empathy"] = random.choice(OPENERS) if not name else greet + random.choice(OPENERS)

    findings: list[str] = []
    syms = analysis.get("symptoms_fa", [])
    if syms:
        findings.append("علائمی که گفتی: "+ "، ".join(syms))
    denied = analysis.get("denied_fa", [])
    if denied:
        findings.append("این موارد را رد کردی: "+ "، ".join(denied))
    det = analysis.get("detected", {})
    if det.get("duration_days") is not None:
        findings.append("مدت علائم: حدود "+ fa_digits(str(det["duration_days"])) + "روز")
    if det.get("temp_c") is not None:
        findings.append("تب گزارش‌شده: "+ fa_digits(str(det["temp_c"])) + "درجه")
    if p.get("age") or p.get("gender"):
        bits = []
        if p.get("age"):
            bits.append("سن "+ fa_digits(str(p["age"])) + "سال")
        if p.get("gender"):
            bits.append("جنسیت "+ str(p["gender"]))
        findings.append("پروفایل: "+ "، ".join(bits))
    if not findings:
        findings.append("هنوز علامت مشخصی ثبت نشده؛ کمی بیشتر توضیح بده.")
    sections["findings"] = findings

    cands = analysis.get("candidates", [])
    probables: list[str] = []
    if cands:
        for c in cands[:3]:
            line = f"{c['fa']} — حدود {_pct(c['percent'])} احتمال نسبی ({URGENCY_FA.get(c['urgency'], c['urgency'])})"
            probables.append(line)
        probables.append("این درصد فقط اولویت‌بندی برای مراقبت است؛ «تشخیص قطعی» فقط با معاینه‌ی پزشک ممکن است.")
    if ml_preds:
        tops = [f"{m['label']} (~{_pct(m['percent'])})" for m in ml_preds[:2]]
        probables.append("سیگنال طبقه‌بند ML (روی دیتاست مصنوعی تستی): "+ "، ".join(tops))
    if not probables:
        probables = ["با این اطلاعات هنوز احتمال مشخصی نمی‌شود گفت؛ به سوال پایین جواب بده تا دقیق‌تر شوم."]
    sections["probables"] = probables

    advice: list[str] = []
    for c in cands[:2]:
        advice.extend(c.get("advice", [])[:3])
    if not advice:
        advice = ["استراحت کافی و آب فراوان", "ثبت تغییر علائم (شدت/مدت) برای ارائه به پزشک"]
    if rag_hits:
        for h in rag_hits[:1]:
            if h.get("title"):
                advice.append(f"از حافظه‌ی آموخته‌شده‌ی قبلی برنامه: موضوع مشابه «{h['title']}» بررسی شد.")
    advice.append("داروی خاصی را بدون تجویز پزشک شروع یا قطع نکن.")
    sections["advice"] = advice

    doctor: list[str] = []
    for c in cands[:2]:
        if c.get("doctor_when"):
            doctor.append(f"برای «{c['fa']}»: {c['doctor_when']}")
    if doctor:
        sections["doctor"] = doctor

    sections["warning"] = "اگر درد قفسه سینه، تنگی نفس شدید، خونریزی، بیهوشی، تشنج، ضعف یک‌طرفه یا اختلال تکلم داری، همین حالا با اورژانس تماس بگیر (ایران: ۱۱۵ | اروپا: ۱۱۲)."

    if followup_question:
        sections["followup"] = followup_question
    else:
        sections["followup"] = "چیز دیگری که لازم بدانی می‌دانی در مورد علائمت اضافه کنی؟ (مثلاً شروع ناگهانی، محرک، داروهای فعلی)"
    return sections
