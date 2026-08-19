# -*- coding: utf-8 -*-
"""
sleep_analyzer.py — تحلیل خواب: STOP-BANG (خطر آپنه‌ی خواب) + PSQI ساده‌شده (غربالگری).
"""
from __future__ import annotations

from typing import Any

STOPBANG = [
    ("S", "خروپف بلند دارم", "snoring"),
    ("T", "روزها خسته/خواب‌آلوده‌ام", "tired"),
    ("O", "کسی گفته در خواب نفسم قطع می‌شود/خفه می‌شوم", "observed"),
    ("P", "فشار خون بالا دارم یا تحت درمانم", "pressure"),
    ("B", "BMI من بالای ۳۵ است", "bmi"),
    ("A", "سنم بالای ۵۰ است", "age"),
    ("N", "دور گردنم درشت است (بیش از ۴۰ سانتی‌متر / یقه‌ی بزرگ)", "neck"),
    ("G", "جنسیت مرد", "gender"),
]

PSQI_LITE = [
    "معمولاً بیش از ۳۰ دقیقه طول می‌کشد تا بخوابم (در ماه اخیر)",
    "معمولاً شبانه کمتر از ۶ ساعت می‌خوابم",
    "شب‌ها چند بار بیدار می‌شوم و دوباره خوابیدن سخت است",
    "صبح‌ها سرحال از خواب بیدار نمی‌شوم",
    "روزها خواب‌آلودگی مزاحم دارم",
    "قبل خواب از صفحه‌نمایش (موبایل/تلویزیون) استفاده می‌کنم",
    "کافئین (چای/قهوه) بعد از ساعت ۴ بعدازظهر مصرف می‌کنم",
    "ورزش سنگین یا غذای سنگین نزدیک خواب دارم",
    " برنامه‌ی خواب و بیداری‌ام نامنظم است",
]


def stopbang(answers: list | dict) -> dict[str, Any]:
    """answers: ۸ مقدار 0/1 به ترتیب S,T,O,P,B,A,N,G"""
    if isinstance(answers, dict):
        vals = [1 if answers.get(k.replace("_", ""), False) or answers.get(k) else 0 for _, _, k in STOPBANG]
    else:
        vals = [1 if str(a) in ("1", "true", "True", "بله") else 0 for a in answers[:8]]
    total = sum(vals)
    if total <= 2:
        risk, fa = "low", "خطر پایین آپنه‌ی خواب 🟢"
    elif total <= 4:
        risk, fa = "intermediate", "خطر متوسط آپنه‌ی خواب 🟠 — غربالگری کامل توصیه می‌شود"
    else:
        risk, fa = "high", "خطر بالای آپنه‌ی خواب 🔴 — ارزیابی تخصصی خواب (تست خواب) توصیه می‌شود"
    rec = ["کاهش وزن در صورت اضافه‌وزن (مؤثرترین اقدام)", "خوابیدن به پهلو، پرهیز از الکل/آرام‌بخش شبانه",
           "پرهیز از کافئین عصرانه", "در ریسک متوسط/بالا: مشورت پزشک و در صورت نیاز تست پلی‌سومنوگرافی"]
    return {"ok": True, "total": total, "risk": risk, "risk_fa": fa, "answers_fa":
            [STOPBANG[i][1] for i, v in enumerate(vals) if v], "recommendations_fa": rec,
            "note": "STOP-BANG ابزار غربالگری است، نه تشخیص قطعی."}


def psqi_lite(answers: list) -> dict[str, Any]:
    total = sum(1 for a in answers[:9] if str(a) in ("1", "true", "True", "بله"))
    if total <= 2:
        band, fa = "good", "کیفیت خواب نسبتاً خوب 🟢"
    elif total <= 4:
        band, fa = "mild", "مشکل خواب خفیف 🟡"
    else:
        band, fa = "poor", "مشکل خواب قابل توجه 🟠 — در صورت تداوم بیش از ۱ ماه ارزیابی پزشک"
    rec = ["ساعت خواب/بیداری ثابت حتی تعطیلات", "اتاق تاریک و خنک؛ تخت فقط برای خواب",
           "صفحه‌نمایش ۱ ساعت قبل خواب خاموش", "کافئین بعد از ظهر ممنوع", "اگر ۲۰ دقیقه خواب نداشتید، از تخت خارج شوید و کار آرام انجام دهید"]
    return {"ok": True, "total": total, "band": band, "band_fa": fa, "recommendations_fa": rec,
            "note": "نسخه‌ی ساده‌شده‌ی PSQI برای غربالگری؛ نمره‌ی رسمی با فرم کامل PSQI متفاوت است."}


def questions() -> dict[str, Any]:
    return {"stopbang": [{"letter": l, "q_fa": q, "key": k} for l, q, k in STOPBANG],
            "psqi_lite": PSQI_LITE}
