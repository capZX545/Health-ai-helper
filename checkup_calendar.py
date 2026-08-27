"""
checkup_calendar.py — bilingual checkup and vaccine suggestions based on the
patient profile. Personal reminders live in reminders.json.
"""
from __future__ import annotations

import os
from typing import Any

from common_2077 import DATA_DIR, now_iso, read_json, write_json
from i18n import is_fa

REMINDERS_PATH = os.path.join(DATA_DIR, "reminders.json")


def _load() -> list[dict]:
    return read_json(REMINDERS_PATH, default=[]) or []


def _item(title_en: str, title_fa: str, interval_en: str, interval_fa: str,
          reason_en: str = "", reason_fa: str = "") -> dict[str, str]:
    fa = is_fa()
    return {"title": title_fa if fa else title_en,
            "interval_fa": interval_fa if fa else interval_en,
            "reason_fa": reason_fa if fa else reason_en}


def recommendations(profile: dict | None = None) -> dict[str, Any]:
    from patient_profile import load_profile
    p = profile or load_profile()
    try:
        age = int(float(p.get("age") or 0))
    except (TypeError, ValueError):
        age = 0
    gender = str(p.get("gender") or "").strip()
    is_f = gender in ("زن", "female", "f", "woman")

    items: list[dict[str, str]] = []
    add = lambda en, fa, i_en, i_fa, r_en="", r_fa="": items.append(_item(en, fa, i_en, i_fa, r_en, r_fa))

    if age >= 18:
        add("Blood pressure measurement", "اندازه‌گیری فشار خون", "at least once a year", "حداقل سالی یک بار",
            "hypertension screening", "غربالگری پرفشاری خون")
    if (age >= 35 and not is_f) or (age >= 45 and is_f) or age >= 65:
        add("Lipid panel (cholesterol/LDL/HDL/TG)", "پروفایل چربی خون", "every 4-6 years or per doctor", "هر ۴–۶ سال یا طبق نظر پزشک",
            "dyslipidemia screening", "غربالگری دیس‌لیپیدمی")
    if age >= 35 or (p.get("conditions") and ("دیابت" in str(p.get("conditions")) or "diabet" in str(p.get("conditions")).lower())):
        add("Fasting blood sugar or HbA1c", "قند خون ناشتا یا HbA1c", "every 1-3 years by risk", "هر ۱–۳ سال بسته به ریسک",
            "diabetes/prediabetes screening", "غربالگری دیابت/پیش‌دیابت")
    if 21 <= age <= 65 and is_f:
        add("Pap smear (cervical cancer)", "پاپ‌اسمیر (سرطان دهانه‌ی رحم)", "every 3 years (or every 5 with HPV test)",
            "هر ۳ سال (یا هر ۵ سال با تست HPV)", "periodic screening", "غربالگری دوره‌ای")
    if age >= 40 and is_f:
        add("Mammography", "ماموگرافی", "every 1-2 years from 40 to 74 (local protocol)", "هر ۱–۲ سال از ۴۰ تا ۷۴ سالگی (پروتکل محلی)",
            "breast cancer screening", "غربالگری سرطان پستان")
    if 50 <= age <= 75:
        add("Colorectal cancer screening (colonoscopy or FOBT)", "غربالگری سرطان روده", "colonoscopy every 10 years or yearly FOBT",
            "کولونوسکوپی هر ۱۰ سال یا FOBT سالانه", "colorectal cancer screening", "غربالگری سرطان کولون")
    if age >= 65 and is_f:
        add("Bone density (DEXA)", "سنجش تراکم استخوان", "per doctor", "طبق نظر پزشک", "osteoporosis screening", "غربالگری پوکی استخوان")
    if p.get("conditions") and ("دیابت" in str(p.get("conditions")) or "diabet" in str(p.get("conditions")).lower()):
        add("Eye exam with retinal photography", "معاینه‌ی چشم (فتوگرافی شبکیه)", "yearly", "سالانه", "diabetic eye complications", "عوارض دیابتی چشم")
        add("Kidney function and urine (Alb/Cr)", "عملکرد کلیه و ادرار", "yearly", "سالانه", "diabetic kidney complications", "عوارض دیابتی کلیه")
        add("Foot exam", "معاینه‌ی پا", "yearly", "سالانه", "diabetic foot risk", "زخم دیابتی/نبض پا")

    vaccines = [
        _item("Seasonal influenza vaccine", "واکسن آنفلوآنزا (فصلی)", "every autumn", "هر سال پاییز",
              "especially elderly, pregnant, chronic conditions", "به‌ویژه سالمندان، بارداران، بیماری زمینه‌ای"),
        _item("COVID-19 booster", "دوز یادآور کووید-۱۹", "per current health authority advice", "طبق توصیه‌ی به‌روز وزارت بهداشت",
              "keep immunity current", "به‌روز نگه‌داشتن ایمنی"),
        _item("Tetanus vaccine", "واکسن تتانوس", "every 10 years", "هر ۱۰ سال", "tetanus prevention", "پیشگیری از کزاز"),
    ]
    if age <= 26:
        vaccines.append(_item("HPV vaccine", "واکسن HPV", "per protocol (usually 2-3 doses)", "طبق پروتکل (معمولاً ۲–۳ دوز)",
                              "HPV-related cancer prevention", "پیشگیری از سرطان‌های مرتبط با HPV"))
    if age >= 65 or (p.get("conditions") and any(x in str(p.get("conditions")) for x in ("قلب", "heart", "ریه", "lung", "دیابت", "diabet"))):
        vaccines.append(_item("Pneumococcal vaccine", "واکسن پنوموکوک", "per doctor", "طبق نظر پزشک",
                              "bacterial pneumonia prevention", "پیشگیری از پنومونی باکتریایی"))

    if not age:
        note = ("برای پیشنهاد دقیق، سن (و ترجیحاً جنسیت) را در پروفایل بیمار ثبت کن." if is_fa()
                else "Add your age (and ideally sex) to the patient profile for tailored suggestions.")
    else:
        note = (f"بر اساس سن {age} و پروفایل ثبت‌شده. فواصل واقعی را پزشک شما تعیین می‌کند." if is_fa()
                else f"Based on age {age} and the saved profile. Your doctor sets the real intervals.")
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
