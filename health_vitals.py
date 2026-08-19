# -*- coding: utf-8 -*-
"""
health_vitals.py — bilingual vitals: BMI, blood pressure categories and a
history log. History is personal data and stays in vitals_history.json.
"""
from __future__ import annotations

import os
from typing import Any

from common_2077 import DATA_DIR, now_iso, read_json, write_json
from i18n import is_fa

HISTORY_PATH = os.path.join(DATA_DIR, "vitals_history.json")


def bmi_info(weight_kg: float, height_cm: float) -> dict[str, Any]:
    fa = is_fa()
    try:
        w, h = float(weight_kg), float(height_cm) / 100.0
        if w <= 0 or h <= 0:
            return {"ok": False, "message_fa": "وزن و قد معتبر وارد کنید." if fa else "Enter a valid weight and height."}
        val = w / (h * h)
        if fa:
            cat = ("کمبود وزن" if val < 18.5 else "محدوده‌ی طبیعی" if val < 25 else "اضافه‌وزن" if val < 30
                   else "چاقی درجه ۱" if val < 35 else "چاقی درجه ۲" if val < 40 else "چاقی شدید (درجه ۳)")
            tip = {"کمبود وزن": "با پزشک/متخصص تغذیه برای افزایش وزن سالم برنامه بچین.",
                   "محدوده‌ی طبیعی": "عالی است؛ تغذیه‌ی متعادل و فعالیت هوازی منظم را ادامه بده.",
                   "اضافه‌وزن": "کاهش ۵ تا ۱۰ درصد وزن، خطر فشار/قند/چربی را محسوس کم می‌کند.",
                   }.get(cat, "کنترل وزن با برنامه‌ی پزشک/متخصص تغذیه توصیه می‌شود.")
        else:
            cat = ("underweight" if val < 18.5 else "normal range" if val < 25 else "overweight" if val < 30
                   else "obesity class 1" if val < 35 else "obesity class 2" if val < 40 else "severe obesity (class 3)")
            tip = {"underweight": "Work with a doctor or dietitian on healthy weight gain.",
                   "normal range": "Great; keep balanced eating and regular aerobic activity.",
                   "overweight": "Losing 5-10% of weight measurably cuts blood pressure, sugar and lipid risk.",
                   }.get(cat, "Weight control with a doctor or dietitian is recommended.")
        return {"ok": True, "bmi": round(val, 1), "category_fa": cat, "tip_fa": tip}
    except (TypeError, ValueError):
        return {"ok": False, "message_fa": "وزن و قد معتبر وارد کنید." if fa else "Enter a valid weight and height."}


def bp_category(systolic: int | float, diastolic: int | float) -> dict[str, Any]:
    fa = is_fa()
    try:
        s, d = int(systolic), int(diastolic)
    except (TypeError, ValueError):
        return {"ok": False, "message_fa": "اعداد فشار خون معتبر نیستند." if fa else "Invalid blood pressure numbers."}
    rows = [
        (s >= 180 or d >= 120, "red",
         ("بحران فشار خون — اورژانسی", "خطر آسیب ارگان؛ فوراً اورژانس ۱۱۵/۱۱۲"),
         ("hypertensive crisis - emergency", "risk of organ damage; call emergency services 115/112 now")),
        (s >= 140 or d >= 90, "red",
         ("فشار خون بالا (مرحله ۲)", "در اسرع وقت با پزشک مشورت کن؛ اندازه‌گیری را تکرار کن."),
         ("high blood pressure (stage 2)", "See a doctor promptly; repeat the measurement.")),
        (s >= 130 or d >= 80, "orange",
         ("فشار خون بالا (مرحله ۱)", "با پزشک مشورت کن؛ نمک و استرس را کم کن."),
         ("high blood pressure (stage 1)", "Talk to a doctor; cut salt and stress.")),
        (s >= 120, "yellow",
         ("فشار بالاتر از حد نرمال", "سبک زندگی سالم و پایش دوره‌ای توصیه می‌شود."),
         ("elevated blood pressure", "Healthy lifestyle and periodic monitoring advised.")),
        (s < 90 or d < 60, "yellow",
         ("فشار پایین‌تر از حد معمول", "اگر با سرگیجه/ضعف همراه است با پزشک مشورت کن."),
         ("lower than usual blood pressure", "If it comes with dizziness/weakness, consult a doctor.")),
    ]
    for cond, color, fa_pair, en_pair in rows:
        if cond:
            cat, act = fa_pair if fa else en_pair
            return {"ok": True, "systolic": s, "diastolic": d, "category_fa": cat, "level": color, "action_fa": act}
    cat, act = ("محدوده‌ی طبیعی", "وضعیت خوب است؛ پایش سالانه کافی است.") if fa else \
               ("normal range", "All good; yearly checks are enough.")
    return {"ok": True, "systolic": s, "diastolic": d, "category_fa": cat, "level": "green", "action_fa": act}


def record(vitals: dict[str, Any]) -> dict[str, Any]:
    hist = read_json(HISTORY_PATH, default=[]) or []
    entry = {"ts": now_iso()}
    for k in ("systolic_bp", "diastolic_bp", "weight_kg", "height_cm", "heart_rate", "temp_c", "spo2", "glucose"):
        if vitals.get(k) not in (None, ""):
            try:
                entry[k] = round(float(vitals[k]), 1)
            except (TypeError, ValueError):
                pass
    res: dict[str, Any] = {"ok": True, "entry": entry}
    if entry.get("weight_kg") and entry.get("height_cm"):
        res["bmi"] = bmi_info(entry["weight_kg"], entry["height_cm"])
    if entry.get("systolic_bp") and entry.get("diastolic_bp"):
        res["bp"] = bp_category(entry["systolic_bp"], entry["diastolic_bp"])
    hist.append(entry)
    hist = hist[-500:]
    write_json(HISTORY_PATH, hist)
    res["history_len"] = len(hist)
    return res


def history(limit: int = 20) -> list[dict[str, Any]]:
    h = read_json(HISTORY_PATH, default=[]) or []
    return h[-limit:][::-1]


def trend() -> dict[str, Any]:
    h = read_json(HISTORY_PATH, default=[]) or []
    out = {}
    labels = {"systolic_bp": ("فشار سیستولیک", "systolic BP"), "weight_kg": ("وزن", "weight"), "glucose": ("قند خون", "blood glucose")}
    for key in ("systolic_bp", "weight_kg", "glucose"):
        vals = [e[key] for e in h if key in e][-8:]
        if len(vals) >= 2:
            diff = vals[-1] - vals[0]
            dir_word = ("افزایش" if diff > 0 else "کاهش" if diff < 0 else "ثابت") if is_fa() else \
                       ("up" if diff > 0 else "down" if diff < 0 else "steady")
            fa_lbl, en_lbl = labels.get(key, (key, key))
            out[key] = {"label": fa_lbl if is_fa() else en_lbl, "first": vals[0], "last": vals[-1],
                        "diff": round(diff, 1), "dir_fa": dir_word}
    return out
