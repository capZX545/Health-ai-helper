# -*- coding: utf-8 -*-
"""
patient_profile.py — پروفایل بیمار: نام، سن، جنسیت، وزن، قد، بیماری زمینه‌ای، حساسیت‌ها.
ذخیره در patient_profile.json (داده‌ی شخصی — هرگز داخل ZIP/Setup قرار نمی‌گیرد).
"""
from __future__ import annotations

import os
from typing import Any

from common_2077 import DATA_DIR, read_json, write_json

PROFILE_PATH = os.path.join(DATA_DIR, "patient_profile.json")

FIELDS = ["name", "age", "gender", "weight_kg", "height_cm", "conditions", "allergies", "medications", "notes"]

GENDERS = ["مرد", "زن", "سایر"]


def load_profile() -> dict[str, Any]:
    p = read_json(PROFILE_PATH, default=None)
    if not isinstance(p, dict):
        return {}
    return {k: p.get(k, "") for k in FIELDS if k in p}


def save_profile(updates: dict[str, Any]) -> dict[str, Any]:
    p = load_profile()
    for k in FIELDS:
        if k in updates:
            v = updates[k]
            if k == "age":
                try:
                    v = int(float(v))
                except (TypeError, ValueError):
                    v = ""
            elif k in ("weight_kg", "height_cm"):
                try:
                    v = round(float(v), 1)
                except (TypeError, ValueError):
                    v = ""
            else:
                v = str(v).strip() if v is not None else ""
            p[k] = v
    write_json(PROFILE_PATH, p)
    return p


def clear_profile() -> bool:
    return write_json(PROFILE_PATH, {})


def summary_for_prompt() -> str:
    p = load_profile()
    if not p or not any(p.get(k) for k in FIELDS):
        return "پروفایل بیمار ثبت نشده."
    bits = []
    if p.get("name"):
        bits.append("نام: "+ p["name"])
    if p.get("age"):
        bits.append("سن: "+ str(p["age"]))
    if p.get("gender"):
        bits.append("جنسیت: "+ p["gender"])
    if p.get("weight_kg"):
        bits.append("وزن: "+ str(p["weight_kg"]) + "کیلوگرم")
    if p.get("height_cm"):
        bits.append("قد: "+ str(p["height_cm"]) + "سانتی‌متر")
    if p.get("conditions"):
        bits.append("بیماری زمینه‌ای: "+ p["conditions"])
    if p.get("allergies"):
        bits.append("حساسیت‌ها: "+ p["allergies"])
    if p.get("medications"):
        bits.append("داروهای فعلی: "+ p["medications"])
    return "؛ ".join(bits)


def bmi() -> dict[str, Any] | None:
    p = load_profile()
    try:
        w = float(p.get("weight_kg") or 0)
        h = float(p.get("height_cm") or 0) / 100.0
        if w <= 0 or h <= 0:
            return None
        val = w / (h * h)
        cat = ("کمبود وزن" if val < 18.5 else "نرمال" if val < 25 else "اضافه وزن" if val < 30 else "چاقی")
        return {"value": round(val, 1), "category_fa": cat}
    except (TypeError, ValueError):
        return None
