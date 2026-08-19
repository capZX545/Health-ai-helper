# -*- coding: utf-8 -*-
"""
prescription_scanner.py — اسکن متن نسخه/آزمایش: ترجمه‌ی اختصارات پزشکی به فارسی،
تشخیص داروها و هشدار حساسیت/تداخل.
"""
from __future__ import annotations

import re
from typing import Any

from common_2077 import normalize

from i18n import pick as _pick

# مقدار هر اختصار: (انگلیسی، فارسی)
SIG_ABBREV: dict[str, tuple[str, str]] = {
    "BID": ("twice a day (every 12 hours)", "دو بار در روز (هر ۱۲ ساعت)"),
    "TID": ("three times a day (every 8 hours)", "سه بار در روز (هر ۸ ساعت)"),
    "QID": ("four times a day (every 6 hours)", "چهار بار در روز (هر ۶ ساعت)"),
    "QD": ("once a day", "روزی یک بار"),
    "OD": ("once a day (European reading)", "روزی یک بار (طبق روایت اروپایی)"),
    "PO": ("by mouth (oral)", "خوراکی (از راه دهان)"),
    "PRN": ("as needed", "در صورت نیاز"),
    "SOS": ("as needed (once at most)", "در صورت نیاز (یک‌بار حداکثر)"),
    "AC": ("before meals", "قبل از غذا"),
    "PC": ("after meals", "بعد از غذا"),
    "HS": ("at bedtime", "قبل از خواب"),
    "QHS": ("every night at bedtime", "هر شب قبل از خواب"),
    "QAM": ("every morning", "هر روز صبح"),
    "Q4H": ("every 4 hours", "هر ۴ ساعت"),
    "Q6H": ("every 6 hours", "هر ۶ ساعت"),
    "Q8H": ("every 8 hours", "هر ۸ ساعت"),
    "QOD": ("every other day", "یک روز در میان"),
    "IV": ("intravenous (into a vein)", "داخل ورید"),
    "IM": ("intramuscular (into a muscle)", "داخل عضله"),
    "SC": ("subcutaneous (under the skin)", "زیر جلدی"),
    "SQ": ("subcutaneous (under the skin)", "زیر جلدی"),
    "SL": ("sublingual (under the tongue)", "زیرزبانی"),
    "PR": ("per rectum", "از راه مقعد"),
    "PV": ("vaginal", "داخل واژن"),
    "NPO": ("nothing by mouth / fasting", "ناشتایی / هیچ‌چیز از دهان"),
    "STAT": ("immediately", "فوراً"),
    "GTT": ("guttae / drops", "قطره‌چکان"),
    "TAB": ("tablet", "قرص"),
    "CAP": ("capsule", "کپسول"),
    "SYP": ("syrup", "شربت"),
    "SUSP": ("suspension", "سوسپانسیون"),
    "OINT": ("ointment", "پماد"),
    "DROPS": ("drops", "قطره"),
    "INH": ("inhaler", "اسپری استنشاقی"),
    "SUPP": ("suppository", "شیاف"),
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

LAB_EN: dict[str, str] = {
    "WBC": "white blood cells (CBC)", "RBC": "red blood cells", "Hb": "hemoglobin", "HGB": "hemoglobin",
    "HCT": "hematocrit", "MCV": "mean corpuscular volume", "PLT": "platelets", "FBS": "fasting blood sugar",
    "BS": "blood sugar", "HbA1c": "glycated hemoglobin (3-month sugar average)", "TSH": "thyroid stimulating hormone",
    "T3": "thyroid hormone T3", "T4": "thyroid hormone T4", "ALT": "liver enzyme ALT (SGPT)",
    "AST": "liver enzyme AST (SGOT)", "ALP": "alkaline phosphatase", "BUN": "blood urea nitrogen (kidney)",
    "Cr": "creatinine (kidney)", "UA": "uric acid", "LDL": "bad cholesterol", "HDL": "good cholesterol",
    "TG": "triglycerides", "TC": "total cholesterol", "PSA": "prostate specific antigen",
    "CRP": "inflammation marker", "ESR": "erythrocyte sedimentation rate", "PT": "prothrombin time (clotting)",
    "INR": "international normalized ratio (anticoagulation)", "PTT": "partial thromboplastin time",
    "ANA": "antinuclear antibody (autoimmune)", "RF": "rheumatoid factor", "TROPONIN": "troponin (heart injury)",
    "D-DIMER": "D-dimer (clotting/thrombosis)", "U/A": "urinalysis", "CXR": "chest X-ray",
    "ECG": "electrocardiogram", "EEG": "electroencephalogram", "EMG": "nerve and muscle test",
    "MRI": "magnetic resonance imaging", "CT": "computed tomography scan", "US": "ultrasound",
    "CBC": "complete blood count", "LFT": "liver function tests", "TFT": "thyroid function tests",
}


def _lab_fa(abbr: str) -> str:
    from i18n import is_fa
    if is_fa():
        return LAB_ABBREV.get(abbr, abbr)
    return LAB_EN.get(abbr, LAB_ABBREV.get(abbr, abbr))

DISCLAIMER_BI = ("This is an educational translation; ask your doctor or pharmacist about the real dose. Never start or stop a drug on your own.",
                  "ترجمه‌ی آموزشی است؛ دوز و نحوه‌ی مصرف واقعی را فقط از پزشک/داروساز بپرس. دارو را خودسرانه شروع/قطع نکن.")


def DISCLAIMER() -> str:
    return _pick(DISCLAIMER_BI)


def scan(text: str) -> dict[str, Any]:
    """ورودی: متن نسخه یا برگه‌ی آزمایش. خروجی: ترجمه‌ها + داروهای شناسایی + هشدارها."""
    t = (text or "").strip()
    if not t:
        from i18n import tt
        return {"ok": False, "message_fa": tt("No text to scan was provided.", "متنی برای اسکن وارد نشده.")}
    translations: list[dict[str, str]] = []
    seen = set()
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9\-/]{1,10}", t)
    for tok in tokens:
        up = tok.upper()
        type_rx, type_lab = _pick(("direction", "دستور مصرف")), _pick(("lab test", "آزمایش"))
        if up in SIG_ABBREV and up not in seen:
            seen.add(up)
            translations.append({"abbr": tok, "type": type_rx, "fa": _pick(SIG_ABBREV[up])})
        elif tok in LAB_ABBREV and tok not in seen and tok.upper() not in seen:
            seen.add(tok)
            translations.append({"abbr": tok, "type": type_lab, "fa": _lab_fa(tok)})
        elif up in LAB_ABBREV and up not in seen:
            seen.add(up)
            translations.append({"abbr": tok, "type": type_lab, "fa": _lab_fa(up)})
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
            "alerts": alerts, "disclaimer": DISCLAIMER()}
