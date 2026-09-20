"""
risk_scores.py — validated clinical risk calculators:
Framingham 10-year coronary heart disease risk (ATP III point system,
NCEP) and FINDRISC 10-year type 2 diabetes risk.
Educational estimates only; the final decision belongs to a doctor.
"""
from __future__ import annotations

from typing import Any

from i18n import is_fa

_AGE_M = [(20, -9), (35, -4), (40, 0), (45, 3), (50, 6), (55, 8), (60, 10), (65, 11), (70, 12), (75, 13)]
_AGE_F = [(20, -7), (35, -3), (40, 0), (45, 3), (50, 6), (55, 8), (60, 10), (65, 12), (70, 14), (75, 16)]
_TC_BANDS = [(160, 200, 240, 280)]
_TC_M = [
    [0, 0, 0, 0, 0],
    [4, 3, 2, 1, 0],
    [7, 5, 3, 1, 0],
    [9, 6, 4, 2, 1],
    [11, 8, 5, 3, 1],
]
_TC_F = [
    [0, 0, 0, 0, 0],
    [4, 3, 2, 1, 1],
    [8, 6, 4, 2, 1],
    [11, 8, 5, 3, 2],
    [13, 10, 7, 4, 2],
]
_SMOKE_M = [8, 5, 3, 1, 1]
_SMOKE_F = [9, 7, 4, 2, 1]
_HDL = [(60, -1), (50, 0), (40, 1), (0, 2)]
_SBP_M = [(120, 0, 0), (130, 0, 1), (140, 1, 2), (160, 1, 2), (99999, 2, 3)]
_SBP_F = [(120, 0, 0), (130, 1, 3), (140, 2, 4), (160, 3, 5), (99999, 4, 6)]
_RISK_M = {0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 2, 6: 2, 7: 3, 8: 4, 9: 5, 10: 6,
           11: 8, 12: 10, 13: 12, 14: 16, 15: 20, 16: 25}
_RISK_F = {9: 1, 10: 1, 11: 1, 12: 1, 13: 2, 14: 2, 15: 3, 16: 4, 17: 5, 18: 6,
           19: 8, 20: 11, 21: 14, 22: 17, 23: 22, 24: 27}


def _num(v, default: float = 0.0) -> float:
    try:
        return float(str(v).replace(",", ".").strip())
    except (TypeError, ValueError):
        return default


def _age_points(age: int, female: bool) -> int:
    pts = 0
    for lo, p in (_AGE_F if female else _AGE_M):
        if age >= lo:
            pts = p
    return pts


def _age_band(age: int) -> int:
    if age < 40:
        return 0
    if age < 50:
        return 1
    if age < 60:
        return 2
    if age < 70:
        return 3
    return 4


def _tc_points(tc: float, band: int, female: bool) -> int:
    table = _TC_F if female else _TC_M
    if tc < 160:
        return table[0][band]
    if tc < 200:
        return table[1][band]
    if tc < 240:
        return table[2][band]
    if tc < 280:
        return table[3][band]
    return table[4][band]


def _hdl_points(hdl: float) -> int:
    for lo, p in _HDL:
        if hdl >= lo:
            return p
    return 2


def _sbp_points(sbp: float, treated: bool, female: bool) -> int:
    for lo, ut, t in (_SBP_F if female else _SBP_M):
        if sbp < lo:
            return t if treated else ut
    return 3


def _risk_from_points(points: int, female: bool) -> Any:
    table = _RISK_F if female else _RISK_M
    if points < min(table):
        return "<1"
    if points > max(table):
        return ">=30"
    return table.get(points, ">=30" if points > max(table) else "<1")


def _band_text(pct: Any) -> tuple[str, str]:
    if pct == ">=30":
        return ("high", 30)
    if pct == "<1":
        return ("low", 1)
    return ("auto", int(pct))


def framingham(age, sex, total_cholesterol, hdl, systolic_bp, smoker,
               bp_treated=False, diabetes=False) -> dict[str, Any]:
    fa = is_fa()
    try:
        age_i = int(round(_num(age)))
        tc = _num(total_cholesterol)
        hdl_v = _num(hdl)
        sbp = _num(systolic_bp)
    except (TypeError, ValueError):
        return {"ok": False, "message_fa": "اطلاعات وارد‌شده معتبر نیست." if fa else "Invalid input values."}
    if not (20 <= age_i <= 79):
        return {"ok": False, "message_fa": "سن باید بین ۲۰ تا ۷۹ باشد." if fa else "Age must be between 20 and 79."}
    if tc <= 0 or hdl_v <= 0 or sbp <= 0:
        return {"ok": False, "message_fa": "چربی خون، HDL و فشار را وارد کن." if fa else "Enter cholesterol, HDL and blood pressure."}
    female = str(sex).strip().lower() in ("f", "female", "زن", "w", "2")
    band = _age_band(age_i)
    parts = {
        "age": _age_points(age_i, female),
        "cholesterol": _tc_points(tc, band, female),
        "hdl": _hdl_points(hdl_v),
        "sbp": _sbp_points(sbp, bool(bp_treated), female),
        "smoking": (_SMOKE_F if female else _SMOKE_M)[band] if smoker else 0,
    }
    points = sum(parts.values())
    pct = _risk_from_points(points, female)
    kind, val = _band_text(pct)
    if diabetes:
        kind = "high"
        val = max(val, 20)
    if kind == "auto":
        kind = "low" if val < 10 else ("moderate" if val < 20 else "high")
    labels = {
        "low": ("low risk", "کم‌خطر"),
        "moderate": ("moderate risk", "خطر متوسط"),
        "high": ("high risk", "پرخطر"),
    }
    advice = {
        "low": ("Keep up the healthy lifestyle; re-check lipids and blood pressure regularly.",
                "سبک زندگی سالم را ادامه بده؛ چربی خون و فشار را دوره‌ای چک کن."),
        "moderate": ("Discuss risk factors with a doctor; quitting smoking, blood pressure control and exercise measurably lower this score.",
                     "عوامل خطر را با پزشک بررسی کن؛ ترک سیگار، کنترل فشار و ورزش این امتیاز را محسوس پایین می‌آورد."),
        "high": ("This level usually means medication (for example statins) must be discussed with a doctor.",
                 "این سطح معمولاً یعنی باید درباره‌ی دارو (مثلاً استاتین) با پزشک مشورت شود."),
    }
    return {
        "ok": True,
        "points": points,
        "point_parts": parts,
        "risk_percent": pct,
        "category": kind,
        "category_fa": labels[kind][1] if fa else labels[kind][0],
        "advice_fa": advice[kind][1] if fa else advice[kind][0],
        "diabetes_note_fa": ("Diabetes counts as a heart-disease risk equivalent."
                             if fa else "دیابت معادل بیماری قلبی محسوب می‌شود.") if diabetes else "",
        "message_fa": "",
    }


_FR_AGE = [(45, 2), (55, 3)]
_FR_BMI = [(25, 1)]
_FR_WAIST = [(94, 80, 3), (102, 88, 4)]


def findrisc(age, bmi, waist_cm, sex, activity_daily=True, veggies_daily=True,
             bp_medication=False, high_glucose=False, family_history=0) -> dict[str, Any]:
    fa = is_fa()
    try:
        age_i = int(round(_num(age)))
        bmi_v = _num(bmi)
        waist = _num(waist_cm)
    except (TypeError, ValueError):
        return {"ok": False, "message_fa": "اطلاعات وارد‌شده معتبر نیست." if fa else "Invalid input values."}
    if age_i < 18 or waist <= 0:
        return {"ok": False, "message_fa": "این پرسشنامه برای بزرگسال است و دور کمر لازم است."
                if fa else "This questionnaire is for adults and needs the waist circumference."}
    female = str(sex).strip().lower() in ("f", "female", "زن", "w", "2")
    p_age = 0
    for lo, p in _FR_AGE:
        if age_i >= lo:
            p_age = p
    if age_i >= 65:
        p_age = 4
    p_bmi = 0
    for lo, p in _FR_BMI:
        if bmi_v >= lo:
            p_bmi = p
    if bmi_v >= 30:
        p_bmi = 3
    p_waist = 0
    lo_m, lo_f, mid = _FR_WAIST[0]
    hi_m, hi_f, hi = _FR_WAIST[1]
    low_cut, hi_cut = (lo_f, hi_f) if female else (lo_m, hi_m)
    if waist >= hi_cut:
        p_waist = hi
    elif waist >= low_cut:
        p_waist = mid
    p_pa = 0 if activity_daily else 2
    p_veg = 0 if veggies_daily else 1
    p_bp = 2 if bp_medication else 0
    p_glu = 5 if high_glucose else 0
    p_fam = {0: 0, 1: 3, 2: 5}.get(int(family_history or 0), 0)
    score = p_age + p_bmi + p_waist + p_pa + p_veg + p_bp + p_glu + p_fam
    if score <= 6:
        cat, risk = ("low", 1)
    elif score <= 11:
        cat, risk = ("slightly elevated", 4)
    elif score <= 14:
        cat, risk = ("moderate", 17)
    elif score <= 20:
        cat, risk = ("high", 33)
    else:
        cat, risk = ("very high", 50)
    cats_fa = {"low": "کم", "slightly elevated": "کمی بالا", "moderate": "متوسط",
               "high": "بالا", "very high": "خیلی بالا"}
    advice = ("The good news: up to 58% of type 2 diabetes cases are preventable with weight control, "
              "30 minutes of daily activity and healthy eating. With this score a fasting glucose or "
              "HbA1c test is worth discussing with a doctor."
              if not fa else
              "خبر خوب: تا ۵۸ درصد موارد دیابت نوع ۲ با کنترل وزن، ۳۰ دقیقه فعالیت روزانه و تغذیه‌ی سالم "
              "قابل پیشگیری است. با این امتیاز، انجام آزمایش قند ناشتا یا HbA1c را با پزشک بررسی کن.")
    return {
        "ok": True,
        "score": score,
        "max_score": 26,
        "risk_percent": risk,
        "category": cat,
        "category_fa": cats_fa[cat] if fa else cat,
        "point_parts": {"age": p_age, "bmi": p_bmi, "waist": p_waist, "activity": p_pa,
                        "vegetables": p_veg, "bp_medication": p_bp, "high_glucose": p_glu,
                        "family_history": p_fam},
        "advice_fa": advice,
        "message_fa": "",
    }
