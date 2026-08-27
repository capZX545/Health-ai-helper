"""
mental_health.py — bilingual mental health module: PHQ-9, GAD-7, breathing
exercise, and a hard crisis path for self-harm thoughts.
"""
from __future__ import annotations

from typing import Any

from i18n import is_fa, pick

PHQ9 = [
    {"fa": "کم‌علاقه یا لذت نبردن از کارها", "en": "Little interest or pleasure in doing things"},
    {"fa": "احساس غم، ناامیدی یا افسردگی", "en": "Feeling down, depressed, or hopeless"},
    {"fa": "مشکل در به‌خواب‌رفتن، پایدار ماندن در خواب یا خواب زیاد", "en": "Trouble falling or staying asleep, or sleeping too much"},
    {"fa": "احساس خستگی یا کم‌انرژی بودن", "en": "Feeling tired or having little energy"},
    {"fa": "کم‌اشتهایی یا پرخوری", "en": "Poor appetite or overeating"},
    {"fa": "احساس بد نسبت به خودتان — شکست‌خورده یا ناامید", "en": "Feeling bad about yourself, like a failure"},
    {"fa": "مشکل تمرکز (تلویزیون، مطالعه، کار)", "en": "Trouble concentrating (TV, reading, work)"},
    {"fa": "حرکت/صحبت کند یا برعکس بی‌قرار زیاد", "en": "Moving/speaking slowly, or being fidgety and restless"},
    {"fa": "افکار به اینکه به خودتان آسیب بزنید یا بهتر بودنِ نبودنتان", "en": "Thoughts of hurting yourself or being better off dead"},
]

GAD7 = [
    {"fa": "احساس عصبانیت، اضطراب یا دل‌درد", "en": "Feeling nervous, anxious or on edge"},
    {"fa": "ناتوانی در توقف یا کنترل نگرانی", "en": "Not being able to stop or control worrying"},
    {"fa": "نگرانی زیاد درباره‌ی چیزهای مختلف", "en": "Worrying too much about different things"},
    {"fa": "مشکل در آسوده‌شدن", "en": "Trouble relaxing"},
    {"fa": "بی‌قراری زیاد (سخت بیکار نشستن)", "en": "Being so restless it is hard to sit still"},
    {"fa": "زودرنجی یا کم‌طاقتی", "en": "Becoming easily annoyed or irritable"},
    {"fa": "ترس از اتفاق بد افتادن", "en": "Being afraid something awful might happen"},
]

ANSWERS = {
    "fa": ["هرگز (۰)", "چند روز (۱)", "بیش از نیمی از روزها (۲)", "تقریباً هر روز (۳)"],
    "en": ["Not at all (0)", "Several days (1)", "More than half the days (2)", "Nearly every day (3)"],
}

CRISIS_TEXT = {
    "fa": """هشدار: پاسخ شما به سوال ۹ (افکار آسیب به خود) مهم است.
لطفاً همین حالا با یک انسان صحبت کن:
• ایران: مشاوره‌ی تلفنی سلامت ۱۴۸۰ — اورژانس اجتماعی ۱۲۳ — اورژانس پزشکی ۱۱۵
• اروپا/فنلاند: اورژانس ۱۱۲ — خط بحران MIELI ۱۱۳
• اگر در خطر فوری هستی، از کسی کنارت کمک بخواه. تو ارزشمندی و این حالت قابل درمان است؛ تنها نمان.""",
    "en": """Warning: your answer to question 9 (thoughts of self-harm) matters.
Please talk to another person right now:
• Iran: mental health hotline 1480 - social emergency 123 - medical emergency 115
• Europe/Finland: emergency 112 - MIELI crisis line 113
• If you are in immediate danger, ask someone near you for help. You matter, this state is treatable, and you do not have to face it alone.""",
}

BREATHING_478 = {
    "name": {"fa": "تنفس ۴-۷-۸", "en": "4-7-8 breathing"},
    "inhale_sec": 4, "hold_sec": 7, "exhale_sec": 8,
    "steps": {
        "fa": ["زبان پشت دندان‌های جلویی؛ از بینی ۴ ثانیه دم بگیر.", "۷ ثانیه نگه دار.",
               "آرام از دهان ۸ ثانیه بازدم.", "چرخه را ۴ بار تکرار کن؛ روزانه ۲ نوبت."],
        "en": ["Tongue behind the front teeth; inhale through the nose for 4 seconds.", "Hold for 7 seconds.",
               "Exhale slowly through the mouth for 8 seconds.", "Repeat the cycle 4 times; twice a day."],
    },
    "note": {"fa": "اگر سرگیجه شد، مدت را کوتاه‌تر کن (۳-۵-۶).", "en": "If you feel dizzy, shorten the counts (3-5-6)."},
}

GROUNDING_54321 = {
    "name": {"fa": "زمین‌گیری حسی ۵-۴-۳-۲-۱", "en": "5-4-3-2-1 grounding"},
    "steps": {
        "fa": ["۵ چیز که می‌بینی، ۴ چیز که لمس می‌کنی، ۳ صدا، ۲ بو، ۱ مزه — یکی‌یکی نام ببر."],
        "en": ["Name 5 things you see, 4 you can touch, 3 you hear, 2 you smell, 1 you can taste - one by one."],
    },
}


def questions() -> dict[str, Any]:
    return {"phq9": [q["fa"] if is_fa() else q["en"] for q in PHQ9],
            "gad7": [q["fa"] if is_fa() else q["en"] for q in GAD7],
            "answers": ANSWERS["fa" if is_fa() else "en"]}


def _score(answers: list) -> int:
    total = 0
    for a in answers:
        try:
            total += max(0, min(3, int(a)))
        except (TypeError, ValueError):
            pass
    return total


def _bands(total: int) -> tuple[str, str]:
    fa = is_fa()
    if total <= 4:
        return "minimal", ("علائم در حد حداقل" if fa else "Minimal symptoms")
    if total <= 9:
        return "mild", ("خفیف" if fa else "Mild")
    if total <= 14:
        return "moderate", ("متوسط — ارزیابی توسط متخصص توصیه می‌شود" if fa else "Moderate - a professional assessment is recommended")
    if total <= 19:
        return "mod_severe", ("متوسط تا شدید — مراجعه به متخصص لازم است" if fa else "Moderately severe - see a professional")
    return "severe", ("شدید — حتماً به متخصص سلامت روان مراجعه کن" if fa else "Severe - please see a mental health professional")


def phq9(answers: list) -> dict[str, Any]:
    total = _score(answers[:9])
    band, fa_txt = _bands(total)
    q9 = int(answers[8]) if len(answers) >= 9 and str(answers[8]).isdigit() else 0
    crisis = q9 >= 1
    fa = is_fa()
    rec = ([ "خواب منظم، فعالیت بدنی سبک روزانه، ارتباط با افراد مورد اعتماد",
             "پرکردن مجدد این پرسش‌نامه هر ۲ هفته برای پیگیری روند"]
           if fa else ["Regular sleep, light daily activity, staying in touch with people you trust",
                      "Retake this questionnaire every 2 weeks to track progress"])
    if band in ("moderate", "mod_severe", "severe"):
        rec.append("جلسه با روان‌شناس/روان‌پزشک برای ارزیابی کامل (این آزمون فقط غربالگری است)" if fa
                   else "A session with a psychologist or psychiatrist for full assessment (this is only a screener)")
    return {"ok": True, "total": total, "band": band, "band_fa": fa_txt, "crisis": crisis,
            "crisis_text": CRISIS_TEXT["fa" if fa else "en"] if crisis else "",
            "recommendations_fa": rec,
            "note": "PHQ-9 ابزار غربالگری است، نه تشخیص." if fa else "PHQ-9 is a screening tool, not a diagnosis."}


def gad7(answers: list) -> dict[str, Any]:
    total = _score(answers[:7])
    fa = is_fa()
    if total <= 4:
        band, txt = "minimal", ("در حد حداقل" if fa else "Minimal")
    elif total <= 9:
        band, txt = "mild", ("خفیف" if fa else "Mild")
    elif total <= 14:
        band, txt = "moderate", ("متوسط" if fa else "Moderate")
    else:
        band, txt = "severe", ("شدید — ارزیابی متخصص توصیه می‌شود" if fa else "Severe - professional assessment recommended")
    rec = ([ "تمرین تنفس ۴-۷-۸ روزانه (در همین برنامه)", "کاهش کافئین/نیکوتین", "درج نگرانی‌ها روی کاغذ قبل خواب"]
           if fa else ["Daily 4-7-8 breathing (in this app)", "Less caffeine/nicotine", "Write worries down before bed"])
    if band in ("moderate", "severe"):
        rec.append("مشورت با متخصص سلامت روان (این آزمون فقط غربالگری است)" if fa
                   else "Consult a mental health professional (this is only a screener)")
    return {"ok": True, "total": total, "band": band, "band_fa": txt, "recommendations_fa": rec,
            "note": "GAD-7 ابزار غربالگری است، نه تشخیص." if fa else "GAD-7 is a screening tool, not a diagnosis."}


def breathing() -> dict[str, Any]:
    out = dict(BREATHING_478)
    out["name"] = pick(BREATHING_478["name"])
    out["steps"] = pick(BREATHING_478["steps"])
    out["note"] = pick(BREATHING_478["note"])
    out["extra"] = {"name": pick(GROUNDING_54321["name"]), "steps": pick(GROUNDING_54321["steps"])}
    return out
