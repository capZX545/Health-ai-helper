# -*- coding: utf-8 -*-
"""
checkup_calendar.py — تقویم چکاپ و واکسن بر اساس سن/جنسیت پروفایل بیمار.
یادآورهای کاربر در reminders.json ذخیره می‌شود (فایل شخصی).
"""
from __future__ import annotations

import os
from typing import Any

from common_2077 import DATA_DIR, now_iso, read_json, write_json

REMINDERS_PATH = os.path.join(DATA_DIR, "reminders.json")


def _load() -> list[dict]:
    return read_json(REMINDERS_PATH, default=[]) or []


def recommendations(profile: dict | None = None) -> dict[str, Any]:
    from patient_profile import load_profile
    p = profile or load_profile()
    try:
        age = int(float(p.get("age") or 0))
    except (TypeError, ValueError):
        age = 0
    gender = str(p.get("gender") or "").strip()
    is_f = gender in ("زن", "female", "f")

    items: list[dict[str, str]] = []
    add = lambda t, i, r: items.append({"title": t, "interval_fa": i, "reason_fa": r})

    if age >= 18:
        add("اندازه‌گیری فشار خون", "حداقل سالی یک بار", "غربالگری پرفشاری خون")
    if (age >= 35 and not is_f) or (age >= 45 and is_f) or age >= 65:
        add("پروفایل چربی خون (کلسترول/LDL/HDL/TG)", "هر ۴–۶ سال یا طبق نظر پزشک", "غربالگری دیس‌لیپیدمی")
    if age >= 35 or (p.get("conditions") and ("دیابت" in str(p.get("conditions")) or "چاق" in str(p.get("conditions")))):
        add("قند خون ناشتا یا HbA1c", "هر ۱–۳ سال بسته به ریسک", "غربالگری دیابت/پیش‌دیابت")
    if 21 <= age <= 65 and is_f:
        add("پاپ‌اسمیر (سرطان دهانه‌ی رحم)", "هر ۳ سال (یا هر ۵ سال با تست HPV)", "غربالگری دوره‌ای")
    if age >= 40 and is_f:
        add("ماموگرافی", "هر ۱–۲ سال از ۴۰ تا ۷۴ سالگی (بر اساس پروتکل محلی)", "غربالگری سرطان پستان")
    if 50 <= age <= 75:
        add("غربالگری سرطان روده (کولونوسکوپی یا تست خون مخفی مدفوع)", "کولونوسکوپی هر ۱۰ سال یا FOBT سالانه", "غربالگری سرطان کولون")
    if age >= 65 and is_f:
        add("سنجش تراکم استخوان (DEXA)", "طبق نظر پزشک", "غربالگری پوکی استخوان")
    if p.get("conditions") and "دیابت" in str(p.get("conditions")):
        add("معاینه‌ی چشم (فتوگرافی شبکیه)", "سالانه", "عوارض دیابتی چشم")
        add("آزمایش عملکرد کلیه و ادرار (Alb/Cr)", "سالانه", "عوارض دیابتی کلیه")
        add("معاینه‌ی پا", "سالانه", "زخم دیابتی/نبض پا")

    vaccines = [
        {"title": "واکسن آنفلوآنزا (فصلی)", "interval_fa": "هر سال پاییز", "reason_fa": "به‌ویژه سالمندان، بارداران، بیماری زمینه‌ای"},
        {"title": "واکسن کووید-۱۹ (دوز یادآور)", "interval_fa": "طبق توصیه‌ی به‌روز وزارت بهداشت", "reason_fa": "به‌روز نگه‌داشتن ایمنی"},
        {"title": "واکسن تتانوس", "interval_fa": "هر ۱۰ سال", "reason_fa": "پیشگیری از کزاز"},
    ]
    if age <= 26:
        vaccines.append({"title": "واکسن HPV", "interval_fa": "طبق پروتکل (معمولاً ۲–۳ دوز)", "reason_fa": "پیشگیری از سرطان‌های مرتبط HPV"})
    if age >= 65 or (p.get("conditions") and any(x in str(p.get("conditions")) for x in ("قلب", "ریه", "دیابت"))):
        vaccines.append({"title": "واکسن پنوموکوک", "interval_fa": "طبق نظر پزشک", "reason_fa": "پیشگیری از پنومونی باکتریایی"})

    if not age:
        note = "برای پیشنهاد دقیق، سن (و ترجیحاً جنسیت) را در پروفایل بیمار ثبت کن."
    else:
        note = f"بر اساس سن {age} و پروفایل ثبت‌شده. فواصل واقعی را پزشک شما تعیین می‌کند."
    return {"ok": True, "age": age, "gender": gender, "checkups": items, "vaccines": vaccines, "note_fa": note}


def add_reminder(title: str, when: str = "") -> dict[str, Any]:
    rem = _load()
    rem.append({"id": str(len(rem) + 1), "title": str(title)[:120], "when": str(when)[:40], "created": now_iso(), "done": False})
    write_json(REMINDERS_PATH, rem)
    return {"ok": True, "count": len(rem)}


def list_reminders() -> list[dict]:
    return _load()


def complete_reminder(rid: str) -> dict[str, Any]:
    rem = _load()
    for r in rem:
        if r.get("id") == rid:
            r["done"] = True
    write_json(REMINDERS_PATH, rem)
    return {"ok": True}
