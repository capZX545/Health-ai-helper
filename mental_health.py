# -*- coding: utf-8 -*-
"""
mental_health.py — سلامت روان: PHQ-9، GAD-7، تمرین تنفسی، هشدار افکار آسیب به خود.
"""
from __future__ import annotations

from typing import Any

PHQ9 = [
    ("کم‌ علاقه یا لذت نبردن از کارها", "little interest or pleasure in doing things"),
    ("احساس غم، ناامیدی یا افسردگی", "feeling down, depressed, or hopeless"),
    ("مشکل در به‌خواب‌رفتن، پایدار ماندن در خواب یا خواب زیاد", "trouble falling/staying asleep"),
    ("احساس خستگی یا کم‌انرژی بودن", "feeling tired or having little energy"),
    ("کم‌اشتهایی یا پرخوری", "poor appetite or overeating"),
    ("احساس بد نسبت به خودتان — شکست‌خورده یا ناامید", "feeling bad about yourself"),
    ("مشکل تمرکز (تلویزیون، مطالعه، کار)", "trouble concentrating"),
    ("حرکت/صحبت کند یا برعکس بی‌قرار زیاد", "moving/speaking slowly or being fidgety"),
    ("افکار به اینکه به خودتان آسیب بزنید یا بهتر بودنِ نبودنتان", "thoughts of being better off dead or hurting yourself"),
]

GAD7 = [
    ("احساس عصبانیت، اضطراب یا دل‌درد", "feeling nervous, anxious"),
    ("ناتوانی در توقف یا کنترل نگرانی", "not being able to stop worrying"),
    ("نگرانی زیاد درباره‌ی چیزهای مختلف", "worrying too much"),
    ("مشکل در آسوده‌شدن", "trouble relaxing"),
    ("بی‌قراری زیاد (سخت بیکار نشستن)", "being so restless"),
    ("زودرنجی یا کم‌طاقتی", "becoming easily annoyed"),
    ("ترس از اتفاق بد افتادن", "feeling afraid something awful might happen"),
]

ANSWERS = ["هرگز (۰)", "چند روز (۱)", "بیش از نیمی از روزها (۲)", "تقریباً هر روز (۳)"]

CRISIS_TEXT = """🚨 پاسخ شما به سوال ۹ (افکار آسیب به خود) مهم است.
لطفاً همین حالا با یک انسان صحبت کن:
• ایران: مشاوره‌ی تلفنی سلامت ۱۴۸۰ — اورژانس اجتماعی ۱۲۳ — اورژانس پزشکی ۱۱۵
• اروپا/فنلاند: اورژانس ۱۱۲ — خط بحران MIELI ۱۱۳
• اگر در خطر فوری هستی، از کسی کنارت کمک بخواه. تو ارزشمندی و این حالت قابل درمان است؛ تنها نمان."""

BREATHING_478 = {
    "name_fa": "تنفس ۴-۷-۸",
    "inhale_sec": 4, "hold_sec": 7, "exhale_sec": 8,
    "steps": [
        "زبان پشت دندان‌های جلویی؛ از بینی ۴ ثانیه دم بگیر.",
        "۷ ثانیه نگه دار.",
        "آرام از دهان ۸ ثانیه بازدم.",
        "چرخه را ۴ بار تکرار کن؛ روزانه ۲ نوبت.",
    ],
    "note_fa": "اگر سرگیجه شد، مدت را کوتاه‌تر کن (۳-۵-۶).",
}

GROUNDING_54321 = {
    "name_fa": "زمین‌گیری حسی ۵-۴-۳-۲-۱",
    "steps": [
        "۵ چیز که می‌بینی، ۴ چیز که لمس می‌کنی، ۳ صدا که می‌شنوی، ۲ بوی که حس می‌کنی، ۱ چیز که چشایی می‌کنی — یکی‌یکی نام ببر.",
    ],
}


def _score(answers: list) -> int:
    total = 0
    for a in answers:
        try:
            total += max(0, min(3, int(a)))
        except (TypeError, ValueError):
            pass
    return total


def phq9(answers: list) -> dict[str, Any]:
    """answers: ۹ عدد ۰..۳"""
    total = _score(answers[:9])
    q9 = int(answers[8]) if len(answers) >= 9 and str(answers[8]).isdigit() else 0
    if total <= 4:
        band, fa = "minimal", "علائم افسردگی در حد حداقل ✅"
    elif total <= 9:
        band, fa = "mild", "افسردگی خفیف 🟡"
    elif total <= 14:
        band, fa = "moderate", "افسردگی متوسط 🟠 — ارزیابی توسط متخصص توصیه می‌شود"
    elif total <= 19:
        band, fa = "mod_severe", "افسردگی متوسط تا شدید 🔶 — مراجعه به متخصص لازم است"
    else:
        band, fa = "severe", "افسردگی شدید 🔴 — حتماً به متخصص سلامت روان مراجعه کن"
    crisis = q9 >= 1
    rec = [
        "خواب منظم، فعالیت بدنی سبک روزانه، ارتباط با افراد مورد اعتماد",
        "پرکردن مجدد این پرسش‌نامه هر ۲ هفته برای پیگیری روند",
    ]
    if band in ("moderate", "mod_severe", "severe"):
        rec.append("جلسه با روان‌شناس/روان‌پزشک برای ارزیابی کامل (این آزمون فقط غربالگری است)")
    return {"ok": True, "total": total, "band": band, "band_fa": fa, "crisis": crisis,
            "crisis_text": CRISIS_TEXT if crisis else "", "recommendations_fa": rec,
            "note": "PHQ-9 ابزار غربالگری است، نه تشخیص."}


def gad7(answers: list) -> dict[str, Any]:
    total = _score(answers[:7])
    if total <= 4:
        band, fa = "minimal", "اضطراب در حد حداقل ✅"
    elif total <= 9:
        band, fa = "mild", "اضطراب خفیف 🟡"
    elif total <= 14:
        band, fa = "moderate", "اضطراب متوسط 🟠"
    else:
        band, fa = "severe", "اضطراب شدید 🔴 — ارزیابی متخصص توصیه می‌شود"
    rec = ["تمرین تنفس ۴-۷-۸ روزانه (در همین برنامه)", "کاهش کافئین/نیکوتین", "درج نگرانی‌ها روی کاغذ قبل خواب"]
    if band in ("moderate", "severe"):
        rec.append("مشورت با متخصص سلامت روان (این آزمون فقط غربالگری است)")
    return {"ok": True, "total": total, "band": band, "band_fa": fa, "recommendations_fa": rec}


def breathing() -> dict[str, Any]:
    out = dict(BREATHING_478)
    out["extra"] = GROUNDING_54321
    return out
