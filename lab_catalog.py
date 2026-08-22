# -*- coding: utf-8 -*-
"""
Catalog of common lab tests with general reference ranges.
Ranges differ between labs; your own lab sheet is what counts.
"""
from __future__ import annotations

from typing import Any

from i18n import pick as _pick


def _first_latin(aliases: list[str]) -> str:
    for a in aliases:
        if a and all(ord(c) < 128 for c in a):
            return a
    return ""

RANGE_NOTE_BI = ("Reference ranges differ between labs; the range printed on your own report is what counts.",
                 "محدوده‌ها بین آزمایشگاه‌ها متفاوت است؛ ملاک، بازه‌ی درج‌شده در برگه‌ی آزمایش شماست.")


def RANGE_NOTE() -> str:
    return _pick(RANGE_NOTE_BI)

TESTS: dict[str, dict[str, Any]] = {
    "wbc": {"fa": "گویچه‌های سفید (WBC)", "unit": "×10³/µL", "lo": 4.5, "hi": 11.0, "aliases": ["wbc", "گویچه سفید", "سلول سفید", "وبسی", "لکوسیت"]},
    "rbc": {"fa": "گویچه‌های قرمز (RBC)", "unit": "M/µL", "lo": 4.5, "hi": 5.9, "aliases": ["rbc", "گویچه قرمز", "لکوسیت قرمز", "اریتروسیت"]},
    "hb": {"fa": "هموگلوبین (Hb)", "unit": "g/dL", "lo": 12.0, "hi": 17.0, "aliases": ["hb", "hgb", "هموگلوبین", "همو گلوبین"]},
    "hct": {"fa": "هماتوکریت (Hct)", "unit": "%", "lo": 36.0, "hi": 52.0, "aliases": ["hct", "هماتوکریت"]},
    "mcv": {"fa": "حجم متوسط گویچه (MCV)", "unit": "fL", "lo": 80.0, "hi": 96.0, "aliases": ["mcv"]},
    "plt": {"fa": "پلاکت (Plt)", "unit": "×10³/µL", "lo": 150.0, "hi": 450.0, "aliases": ["plt", "پلاکت", "platelet"]},
    "fbs": {"fa": "قند خون ناشتا (FBS)", "unit": "mg/dL", "lo": 70.0, "hi": 99.0, "aliases": ["fbs", "قند ناشتا", "قند خون ناشتا", "گلوکز ناشتا", "فس", "glucose fasting"]},
    "bs_random": {"fa": "قند خون تصادفی", "unit": "mg/dL", "lo": 70.0, "hi": 140.0, "aliases": ["bs", "قند تصادفی", "گلوکز"]},
    "hba1c": {"fa": "هموگلوبین گلیکوزیله (HbA1c)", "unit": "%", "lo": 4.0, "hi": 5.6, "aliases": ["hba1c", "a1c", "هموگلوبین گلیکه", "ایوانک"]},
    "tchol": {"fa": "کلسترول تام", "unit": "mg/dL", "lo": 0.0, "hi": 200.0, "aliases": ["chol", "tc", "کلسترول", "کلسترول تام", "cholesterol"]},
    "ldl": {"fa": "LDL (لیبوپروتئین پرچگال)", "unit": "mg/dL", "lo": 0.0, "hi": 100.0, "aliases": ["ldl", "ال دی ال", "کلسترول بد"]},
    "hdl": {"fa": "HDL (لیبوپروتئین کم‌چگال)", "unit": "mg/dL", "lo": 40.0, "hi": 90.0, "aliases": ["hdl", "ای دی ال", "کلسترول خوب"]},
    "tg": {"fa": "تری‌گلیسرید (TG)", "unit": "mg/dL", "lo": 0.0, "hi": 150.0, "aliases": ["tg", "تری گلیسرید", "تریگلیسیرید", "triglyceride"]},
    "tsh": {"fa": "TSH (هورمون محرک تیروئید)", "unit": "mIU/L", "lo": 0.4, "hi": 4.5, "aliases": ["tsh", "تی اس اچ", "هورمون تیروئید"]},
    "t4": {"fa": "T4 آزاد", "unit": "ng/dL", "lo": 0.8, "hi": 1.8, "aliases": ["t4", "ft4", "تی چهار"]},
    "alt": {"fa": "ALT (SGPT)", "unit": "U/L", "lo": 0.0, "hi": 41.0, "aliases": ["alt", "sgpt", "ال ان تی", "آلانین آمینوترانسفراز"]},
    "ast": {"fa": "AST (SGOT)", "unit": "U/L", "lo": 0.0, "hi": 40.0, "aliases": ["ast", "sgot", "آسپارتات آمینوترانسفراز"]},
    "alp": {"fa": "ALP (آلکالن فسفاتاز)", "unit": "U/L", "lo": 44.0, "hi": 147.0, "aliases": ["alp"]},
    "bun": {"fa": "BUN (ازوت اوره‌ی خون)", "unit": "mg/dL", "lo": 7.0, "hi": 20.0, "aliases": ["bun", "اوره", "یوره"]},
    "cr": {"fa": "کراتینین (Cr)", "unit": "mg/dL", "lo": 0.6, "hi": 1.3, "aliases": ["cr", "creatinine", "کراتینین"]},
    "ua": {"fa": "اسید اوریک", "unit": "mg/dL", "lo": 3.5, "hi": 7.2, "aliases": ["ua", "uric", "اسید اوریک", "اوره اسید"]},
    "na": {"fa": "سدیم (Na)", "unit": "mEq/L", "lo": 135.0, "hi": 145.0, "aliases": ["na", "سدیم", "sodium"]},
    "k": {"fa": "پتاسیم (K)", "unit": "mEq/L", "lo": 3.5, "hi": 5.1, "aliases": ["k", "پتاسیم", "potassium"]},
    "ca": {"fa": "کلسیم (Ca)", "unit": "mg/dL", "lo": 8.6, "hi": 10.3, "aliases": ["ca", "کلسیم"]},
    "fe": {"fa": "آهن سرم", "unit": "µg/dL", "lo": 60.0, "hi": 160.0, "aliases": ["fe", "iron", "آهن"]},
    "ferritin": {"fa": "فریتین", "unit": "ng/mL", "lo": 30.0, "hi": 300.0, "aliases": ["ferritin", "فریتین"]},
    "vitd": {"fa": "ویتامین D (25-OH)", "unit": "ng/mL", "lo": 30.0, "hi": 100.0, "aliases": ["vitd", "vitamin d", "ویتامین دی", "ویتامین د", "25-oh"]},
    "b12": {"fa": "ویتامین B12", "unit": "pg/mL", "lo": 200.0, "hi": 900.0, "aliases": ["b12", "ویتامین ب ۱۲", "کوبالامین"]},
    "crp": {"fa": "CRP (پروتئین واکنشی C)", "unit": "mg/L", "lo": 0.0, "hi": 5.0, "aliases": ["crp", "سی آر پی"]},
    "esr": {"fa": "ESR (سرعت رسوب گویچه‌ها)", "unit": "mm/h", "lo": 0.0, "hi": 20.0, "aliases": ["esr", "سرعت ته‌نشینی"]},
    "psa": {"fa": "PSA (آنتی‌ژن اختصاصی پروستات)", "unit": "ng/mL", "lo": 0.0, "hi": 4.0, "aliases": ["psa", "پی اس ای"]},
    "tsh_note": None,
}


def find_test(token: str) -> dict[str, Any] | None:
    from common_2077 import normalize
    nq = normalize(token)
    for key, t in TESTS.items():
        if not t:
            continue
        for al in t["aliases"]:
            if normalize(al) == nq:
                out = {"key": key, **t}
                out.setdefault("en", _first_latin(t["aliases"]) or key)
                return out
    # fuzzy match
    for key, t in TESTS.items():
        if not t:
            continue
        for al in t["aliases"]:
            if nq and (nq in normalize(al) or normalize(al) in nq) and len(normalize(al)) >= 2:
                out = {"key": key, **t}
                out.setdefault("en", _first_latin(t["aliases"]) or key)
                return out
    return None


def all_tests() -> list[dict[str, Any]]:
    out = []
    for k, v in TESTS.items():
        if not v:
            continue
        row = {"key": k, **v}
        row.setdefault("en", _first_latin(v["aliases"]) or k)
        out.append(row)
    return out
