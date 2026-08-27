"""
sleep_analyzer.py — bilingual sleep screening: STOP-BANG (obstructive sleep
apnea risk) and a simplified PSQI (screening only).
"""
from __future__ import annotations

from typing import Any

from i18n import is_fa

STOPBANG = [
    ("S", {"fa": "خروپف بلند دارم", "en": "I snore loudly"}),
    ("T", {"fa": "روزها خسته/خواب‌آلوده‌ام", "en": "I am tired or sleepy during the day"}),
    ("O", {"fa": "کسی گفته در خواب نفسم قطع می‌شود", "en": "Someone has seen my breathing stop in sleep"}),
    ("P", {"fa": "فشار خون بالا دارم یا تحت درمانم", "en": "I have or am treated for high blood pressure"}),
    ("B", {"fa": "BMI من بالای ۳۵ است", "en": "My BMI is over 35"}),
    ("A", {"fa": "سنم بالای ۵۰ است", "en": "I am over 50"}),
    ("N", {"fa": "دور گردنم درشت است (بیش از ۴۰ سانتی‌متر)", "en": "My neck is large (over 40 cm)"}),
    ("G", {"fa": "جنسیت مرد", "en": "Male sex"}),
]

PSQI_LITE = [
    {"fa": "معمولاً بیش از ۳۰ دقیقه طول می‌کشد تا بخوابم", "en": "It usually takes me over 30 minutes to fall asleep"},
    {"fa": "معمولاً شبانه کمتر از ۶ ساعت می‌خوابم", "en": "I usually sleep less than 6 hours a night"},
    {"fa": "شب‌ها چند بار بیدار می‌شوم و دوباره خوابیدن سخت است", "en": "I wake several times and struggle to fall back asleep"},
    {"fa": "صبح‌ها سرحال از خواب بیدار نمی‌شوم", "en": "I do not wake up refreshed"},
    {"fa": "روزها خواب‌آلودگی مزاحم دارم", "en": "Daytime sleepiness interferes with my day"},
    {"fa": "قبل خواب از صفحه‌نمایش استفاده می‌کنم", "en": "I use screens right before bed"},
    {"fa": "کافئین بعد از ساعت ۴ بعدازظهر مصرف می‌کنم", "en": "I have caffeine after 4 pm"},
    {"fa": "ورزش یا غذای سنگین نزدیک خواب دارم", "en": "Heavy exercise or food close to bedtime"},
    {"fa": "برنامه‌ی خواب و بیداری‌ام نامنظم است", "en": "My sleep and wake times are irregular"},
]


def questions() -> dict[str, Any]:
    lang = "fa" if is_fa() else "en"
    return {"stopbang": [{"letter": l, "q_fa": q[lang], "key": l.lower()} for l, q in STOPBANG],
            "psqi_lite": [q[lang] for q in PSQI_LITE]}


def stopbang(answers: list | dict) -> dict[str, Any]:
    fa = is_fa()
    if isinstance(answers, dict):
        vals = [1 if answers.get(k.replace("_", ""), False) or answers.get(k) else 0 for _, _, k in
                [(l, q, l.lower()) for l, q in STOPBANG]]
    else:
        vals = [1 if str(a) in ("1", "true", "True", "بله", "yes") else 0 for a in answers[:8]]
    total = sum(vals)
    lang = "fa" if fa else "en"
    if total <= 2:
        risk, txt = "low", ("خطر پایین آپنه‌ی خواب" if fa else "Low risk of sleep apnea")
    elif total <= 4:
        risk, txt = "intermediate", ("خطر متوسط آپنه‌ی خواب — غربالگری کامل توصیه می‌شود" if fa else "Intermediate risk - full screening recommended")
    else:
        risk, txt = "high", ("خطر بالای آپنه‌ی خواب — ارزیابی تخصصی خواب توصیه می‌شود" if fa else "High risk - a specialist sleep evaluation is recommended")
    rec = ([ "کاهش وزن در صورت اضافه‌وزن (مؤثرترین اقدام)", "خوابیدن به پهلو، پرهیز از الکل/آرام‌بخش شبانه",
             "پرهیز از کافئین عصرانه", "در ریسک متوسط/بالا: مشورت پزشک و در صورت نیاز تست خواب"]
           if fa else ["Weight loss if above range (the most effective step)", "Sleep on your side; no alcohol or sedatives at night",
                      "No late-afternoon caffeine", "Intermediate/high risk: see a doctor, possibly a sleep study"])
    return {"ok": True, "total": total, "risk": risk, "risk_fa": txt,
            "answers_fa": [STOPBANG[i][1][lang] for i, v in enumerate(vals) if v],
            "recommendations_fa": rec,
            "note": "STOP-BANG ابزار غربالگری است، نه تشخیص قطعی." if fa else "STOP-BANG is a screening tool, not a diagnosis."}


def psqi_lite(answers: list) -> dict[str, Any]:
    fa = is_fa()
    total = sum(1 for a in answers[:9] if str(a) in ("1", "true", "True", "بله", "yes"))
    if total <= 2:
        band, txt = "good", ("کیفیت خواب نسبتاً خوب" if fa else "Fairly good sleep quality")
    elif total <= 4:
        band, txt = "mild", ("مشکل خواب خفیف" if fa else "Mild sleep problem")
    else:
        band, txt = "poor", ("مشکل خواب قابل توجه — در صورت تداوم بیش از ۱ ماه ارزیابی پزشک" if fa
                             else "Notable sleep problem - see a doctor if it lasts beyond a month")
    rec = ([ "ساعت خواب/بیداری ثابت حتی تعطیلات", "اتاق تاریک و خنک؛ تخت فقط برای خواب",
             "صفحه‌نمایش ۱ ساعت قبل خواب خاموش", "کافئین بعد از ظهر ممنوع",
             "اگر ۲۰ دقیقه خواب نداشتید، از تخت خارج شوید و کار آرام انجام دهید"]
           if fa else ["Fixed sleep and wake times, even weekends", "Dark, cool room; bed only for sleep",
                      "Screens off 1 hour before bed", "No afternoon caffeine",
                      "If not asleep in 20 minutes, get up and do something calm"])
    return {"ok": True, "total": total, "band": band, "band_fa": txt, "recommendations_fa": rec,
            "note": ("نسخه‌ی ساده‌شده‌ی PSQI برای غربالگری؛ نمره‌ی رسمی با فرم کامل PSQI متفاوت است." if fa
                     else "A simplified PSQI for screening; official scores use the full PSQI.")}
