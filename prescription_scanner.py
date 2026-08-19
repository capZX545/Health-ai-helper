# -*- coding: utf-8 -*-
"""
prescription_scanner.py — اسکن متن نسخه/آزمایش: ترجمه‌ی اختصارات پزشکی به فارسی،
تشخیص داروها و هشدار حساسیت/تداخل.
"""
from __future__ import annotations

import re
from typing import Any

from common_2077 import normalize

SIG_ABBREV: dict[str, str] = {
    "BID": "دو بار در روز (هر ۱۲ ساعت)",
    "TID": "سه بار در روز (هر ۸ ساعت)",
    "QID": "چهار بار در روز (هر ۶ ساعت)",
    "QD": "روزی یک بار",
    "OD": "روزی یک بار (طبق روایت اروپایی)",
    "PO": "خوراکی (از راه دهان)",
    "PRN": "در صورت نیاز",
    "SOS": "در صورت نیاز (یک‌بار حداکثر)",
    "AC": "قبل از غذا",
    "PC": "بعد از غذا",
    "HS": "قبل از خواب",
    "QHS": "هر شب قبل از خواب",
    "QAM": "هر روز صبح",
    "Q4H": "هر ۴ ساعت",
    "Q6H": "هر ۶ ساعت",
    "Q8H": "هر ۸ ساعت",
    "QOD": "یک روز در میان",
    "IV": "داخل ورید",
    "IM": "داخل عضله",
    "SC": "زیر جلدی",
    "SQ": "زیر جلدی",
    "SL": "زیرزبانی",
    "PR": "از راه مقعد",
    "PV": "داخل واژن",
    "NPO": "ناشتایی / هیچ‌چیز از دهان",
    "STAT": "فوراً",
    "GTT": "قطره‌چکان",
    "TAB": "قرص",
    "CAP": "کپسول",
    "SYP": "شربت",
    "SUSP": "سوسپانسیون",
    "OINT": "پماد",
    "DROPS": "قطره",
    "INH": "اسپری استنشاقی",
    "SUPP": "شیاف",
    "SQ": "زیر جلدی",
}

LAB_ABBREV: dict[str, str] = {
    "WBC": "گویچه‌های سفید — آزمایش CBC",
    "RBC": "گویچه‌های قرمز",
    "Hb": "هموگلوبین",
    "HGB": "هموگلوبین",
    "HCT": "هماتوکریت",
    "MCV": "حجم متوسط گویچه‌ی قرمز",
    "PLT": "پلاکت",
    "FBS": "قند خون ناشتا",
    "BS": "قند خون",
    "HbA1c": "هموگلوبین گلیکوزیله (میانگین ۳ ماهه قند)",
    "TSH": "هورمون محرک تیروئید",
    "T3": "هورمون تیروئید T3",
    "T4": "هورمون تیروئید T4",
    "ALT": "آنزیم کبدی ALT (SGPT)",
    "AST": "آنزیم کبدی AST (SGOT)",
    "ALP": "آلکالن فسفاتاز",
    "BUN": "ازوت اوره‌ی خون (عملکرد کلیه)",
    "Cr": "کراتینین (عملکرد کلیه)",
    "UA": "اسید اوریک",
    "LDL": "کلسترول بد",
    "HDL": "کلسترول خوب",
    "TG": "تری‌گلیسرید",
    "TC": "کلسترول تام",
    "PSA": "آنتی‌ژن اختصاصی پروستات",
    "CRP": "نشانگر التهاب",
    "ESR": "سرعت ته‌نشینی گلبولی",
    "PT": "پروترومبین تایم (انعقاد)",
    "INR": "نسبت نرمال‌شده‌ی بین‌المللی (ضد انعقاد)",
    "PTT": "ترومبوپلاستین جزئی",
    "ANA": "آنتی‌بادی ضد هسته‌ای (بیماری خودایمن)",
    "RF": "فاکتور روماتوئید",
    "TROPONIN": "تروپونین (آسیب قلبی)",
    "D-DIMER": "دی‌دایمر (لخته/ترومبوز)",
    "U/A": "آزمایش ادرار عمومی",
    "CXR": "عکس قفسه سینه",
    "ECG": "نوار قلب",
    "EEG": "نوار مغز",
    "EMG": "نوار عصب و عضله",
    "MRI": "ام‌آرآی (رزونانس مغناطیسی)",
    "CT": "سی‌تی‌اسکن (توموگرافی رایانه‌ای)",
    "US": "سونوگرافی",
    "CBC": "آزمایش کامل خون",
    "LFT": "آزمایش‌های عملکرد کبد",
    "TFT": "آزمایش‌های تیروئید",
}

DISCLAIMER = "⚠️ ترجمه‌ی آموزشی است؛ دوز و نحوه‌ی مصرف واقعی را فقط از پزشک/داروساز بپرس. دارو را خودسرانه شروع/قطع نکن."


def scan(text: str) -> dict[str, Any]:
    """ورودی: متن نسخه یا برگه‌ی آزمایش. خروجی: ترجمه‌ها + داروهای شناسایی + هشدارها."""
    t = (text or "").strip()
    if not t:
        return {"ok": False, "message_fa": "متنی برای اسکن وارد نشده."}
    translations: list[dict[str, str]] = []
    seen = set()
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9\-/]{1,10}", t)
    for tok in tokens:
        up = tok.upper()
        if up in SIG_ABBREV and up not in seen:
            seen.add(up)
            translations.append({"abbr": tok, "type": "دستور مصرف", "fa": SIG_ABBREV[up]})
        elif tok in LAB_ABBREV and tok not in seen and tok.upper() not in seen:
            seen.add(tok)
            translations.append({"abbr": tok, "type": "آزمایش", "fa": LAB_ABBREV[tok]})
        elif up in LAB_ABBREV and up not in seen:
            seen.add(up)
            translations.append({"abbr": tok, "type": "آزمایش", "fa": LAB_ABBREV[up]})
    # داروها
    drug_hits: list[dict] = []
    from drug_interaction import allergy_alert, check_interaction, search_drug
    for word in re.split(r"[،,\n؛;]+", t):
        w = word.strip()
        if not w:
            continue
        d = search_drug(w)
        if d and d[0]["score"] >= 100:
            drug_hits.append(d[0])
    # هشدار حساسیت پروفایل
    alerts: list[str] = []
    names = [d["fa"] for d in drug_hits]
    if names:
        aa = allergy_alert(names)
        alerts.extend(aa.get("alerts", []))
        if len(names) >= 2:
            inter = check_interaction(names[0], names[1])
            if inter.get("ok"):
                for it in inter["interactions"]:
                    alerts.append(f"{it['severity_fa']}: {it['detail_fa']}")
    # ترکیب‌های عددی رایج مثل 500mg
    doses = re.findall(r"(\d{2,4})\s*(?:mg|milligram|میلی‌گرام|میلی گرم)", t, re.IGNORECASE)
    return {"ok": True, "translations": translations, "drugs": drug_hits, "doses_mg": doses,
            "alerts": alerts, "disclaimer": DISCLAIMER}
