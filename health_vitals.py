# -*- coding: utf-8 -*-
"""
health_vitals.py — علائم حیاتی: BMI، دسته‌بندی فشار خون، تاریخچه.
تاریخچه در vitals_history.json (فایل شخصی کاربر) ذخیره می‌شود.
"""
from __future__ import annotations

import os
from typing import Any

from common_2077 import DATA_DIR, now_iso, read_json, write_json

HISTORY_PATH = os.path.join(DATA_DIR, "vitals_history.json")


def bmi_info(weight_kg: float, height_cm: float) -> dict[str, Any]:
    try:
        w, h = float(weight_kg), float(height_cm) / 100.0
        if w <= 0 or h <= 0:
            return {"ok": False, "message_fa": "وزن و قد معتبر وارد کنید."}
        val = w / (h * h)
        cat = ("کمبود وزن" if val < 18.5 else "محدوده‌ی طبیعی" if val < 25
               else "اضافه‌وزن" if val < 30 else "چاقی درجه ۱" if val < 35
               else "چاقی درجه ۲" if val < 40 else "چاقی شدید (درجه ۳)")
        tip = {"کمبود وزن": "با پزشک/متخصص تغذیه برای افزایش وزن سالم برنامه بچین.",
               "محدوده‌ی طبیعی": "عالی است؛ تغذیه‌ی متعادل و فعالیت هوازی منظم را ادامه بده.",
               "اضافه‌وزن": "کاهش ۵ تا ۱۰ درصد وزن، خطر فشار/قند/چربی را محسوس کم می‌کند.",
               }.get(cat, "کنترل وزن با برنامه‌ی پزشک/متخصص تغذیه توصیه می‌شود.")
        return {"ok": True, "bmi": round(val, 1), "category_fa": cat, "tip_fa": tip}
    except (TypeError, ValueError):
        return {"ok": False, "message_fa": "وزن و قد معتبر وارد کنید."}


def bp_category(systolic: int | float, diastolic: int | float) -> dict[str, Any]:
    try:
        s, d = int(systolic), int(diastolic)
    except (TypeError, ValueError):
        return {"ok": False, "message_fa": "اعداد فشار خون معتبر نیستند."}
    if s >= 180 or d >= 120:
        cat, color, act = "بحران فشار خون — اورژانسی", "red", "فوراً با اورژانس تماس بگیر (۱۱۵/۱۱۲)؛ این محدوده خطر آسیب ارگان است."
    elif s >= 140 or d >= 90:
        cat, color, act = "فشار خون بالا (مرحله ۲)", "red", "در اسرع وقت با پزشک مشورت کن؛ اندازه‌گیری را تکرار کن."
    elif s >= 130 or d >= 80:
        cat, color, act = "فشار خون بالا (مرحله ۱)", "orange", "با پزشک مشورت کن؛ نمک و استرس را کم کن."
    elif s >= 120:
        cat, color, act = "فشار بالاتر از حد نرمال", "yellow", "سبک زندگی سالم و پایش دوره‌ای توصیه می‌شود."
    elif s < 90 or d < 60:
        cat, color, act = "فشار پایین‌تر از حد معمول", "yellow", "اگر با سرگیجه/ضعف همراه است با پزشک مشورت کن."
    else:
        cat, color, act = "محدوده‌ی طبیعی", "green", "وضعیت خوب است؛ پایش سالانه کافی است."
    return {"ok": True, "systolic": s, "diastolic": d, "category_fa": cat, "level": color, "action_fa": act}


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
    for key in ("systolic_bp", "weight_kg", "glucose"):
        vals = [e[key] for e in h if key in e][-8:]
        if len(vals) >= 2:
            diff = vals[-1] - vals[0]
            out[key] = {"first": vals[0], "last": vals[-1], "diff": round(diff, 1),
                        "dir_fa": ("افزایش" if diff > 0 else "کاهش" if diff < 0 else "ثابت")}
    return out
