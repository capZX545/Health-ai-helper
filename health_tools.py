# -*- coding: utf-8 -*-
"""
health_tools.py — practical tools: unit converter, dose calculator,
pregnancy safety, multi-drug check, due date, symptom diary, backup.
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import date, datetime, timedelta
from typing import Any

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================ unit converter ============================

# factor: mg/dL * factor = mmol/L
UNITS = {
    "glucose": {"name_en": "Glucose", "name_fa": "قند خون", "mgdl_to_mmol": 0.0555,
                "ref_en": "70-99 mg/dL (fasting)", "ref_fa": "۷۰-۹۹ mg/dL (ناشتا)"},
    "cholesterol": {"name_en": "Total cholesterol", "name_fa": "کلسترول تام", "mgdl_to_mmol": 0.0259,
                    "ref_en": "<200 mg/dL", "ref_fa": "کمتر از ۲۰۰ mg/dL"},
    "ldl": {"name_en": "LDL", "name_fa": "کلسترول بد (LDL)", "mgdl_to_mmol": 0.0259,
            "ref_en": "<100 mg/dL", "ref_fa": "کمتر از ۱۰۰ mg/dL"},
    "hdl": {"name_en": "HDL", "name_fa": "کلسترول خوب (HDL)", "mgdl_to_mmol": 0.0259,
            "ref_en": ">40 mg/dL", "ref_fa": "بیشتر از ۴۰ mg/dL"},
    "triglyceride": {"name_en": "Triglycerides", "name_fa": "تری‌گلیسرید", "mgdl_to_mmol": 0.0113,
                     "ref_en": "<150 mg/dL", "ref_fa": "کمتر از ۱۵۰ mg/dL"},
    "creatinine": {"name_en": "Creatinine", "name_fa": "کراتینین", "mgdl_to_umol": 88.4,
                   "ref_en": "0.6-1.3 mg/dL", "ref_fa": "۰٫۶-۱٫۳ mg/dL"},
    "urea": {"name_en": "BUN", "name_fa": "اوره خون", "mgdl_to_mmol": 0.357,
             "ref_en": "7-20 mg/dL", "ref_fa": "۷-۲۰ mg/dL"},
    "uric_acid": {"name_en": "Uric acid", "name_fa": "اسید اوریک", "mgdl_to_umol": 59.48,
                  "ref_en": "3.5-7.2 mg/dL", "ref_fa": "۳٫۵-۷٫۲ mg/dL"},
    "calcium": {"name_en": "Calcium", "name_fa": "کلسیم", "mgdl_to_mmol": 0.2495,
                "ref_en": "8.6-10.3 mg/dL", "ref_fa": "۸٫۶-۱۰٫۳ mg/dL"},
    "bilirubin": {"name_en": "Bilirubin", "name_fa": "بیلی‌روبین", "mgdl_to_umol": 17.1,
                  "ref_en": "0.2-1.2 mg/dL", "ref_fa": "۰٫۲-۱٫۲ mg/dL"},
}


def convert_unit(test_key: str, value: float, from_unit: str) -> dict:
    t = UNITS.get(test_key)
    if not t:
        return {"ok": False, "message_en": "Unknown test", "message_fa": "آزمایش ناشناخته"}
    try:
        v = float(value)
    except (ValueError, TypeError):
        return {"ok": False, "message_en": "Enter a number", "message_fa": "عدد وارد کن"}
    if "mgdl_to_mmol" in t:
        factor = t["mgdl_to_mmol"]
        if from_unit == "mgdl":
            result = round(v * factor, 2)
            return {"ok": True, "test": t["name_en"], "input": f"{v} mg/dL",
                    "output": f"{result} mmol/L", "factor": factor, "ref": t["ref_en"], "ref_fa": t["ref_fa"]}
        result = round(v / factor, 1)
        return {"ok": True, "test": t["name_en"], "input": f"{v} mmol/L",
                "output": f"{result} mg/dL", "factor": factor, "ref": t["ref_en"], "ref_fa": t["ref_fa"]}
    if "mgdl_to_umol" in t:
        factor = t["mgdl_to_umol"]
        if from_unit == "mgdl":
            result = round(v * factor, 1)
            return {"ok": True, "test": t["name_en"], "input": f"{v} mg/dL",
                    "output": f"{result} µmol/L", "factor": factor, "ref": t["ref_en"], "ref_fa": t["ref_fa"]}
        result = round(v / factor, 1)
        return {"ok": True, "test": t["name_en"], "input": f"{v} µmol/L",
                "output": f"{result} mg/dL", "factor": factor, "ref": t["ref_en"], "ref_fa": t["ref_fa"]}
    return {"ok": False}


# ============================ dose calculator ============================

DOSE_TABLE = {
    "paracetamol": {"name_en": "Paracetamol/Acetaminophen", "name_fa": "استامینوفن",
                    "mg_per_kg": 15, "max_daily_mg_per_kg": 75, "interval_h": 6,
                    "forms": {"syrup_120": "syrup 120mg/5mL", "syrup_160": "syrup 160mg/5mL", "tab_500": "tablet 500mg"}},
    "ibuprofen": {"name_en": "Ibuprofen", "name_fa": "ایبوپروفن",
                  "mg_per_kg": 10, "max_daily_mg_per_kg": 40, "interval_h": 8,
                  "forms": {"syrup_100": "syrup 100mg/5mL", "tab_200": "tablet 200mg", "tab_400": "tablet 400mg"}},
    "amoxicillin": {"name_en": "Amoxicillin", "name_fa": "آموکسی‌سیلین",
                    "mg_per_kg": 25, "max_daily_mg_per_kg": 100, "interval_h": 8,
                    "forms": {"syrup_125": "syrup 125mg/5mL", "syrup_250": "syrup 250mg/5mL", "cap_500": "capsule 500mg"}},
    "azithromycin": {"name_en": "Azithromycin", "name_fa": "آزیترومایسین",
                     "mg_per_kg": 10, "max_daily_mg_per_kg": 10, "interval_h": 24,
                     "forms": {"syrup_200": "syrup 200mg/5mL", "tab_250": "tablet 250mg"}},
    "cefixime": {"name_en": "Cefixime", "name_fa": "سفیکسیم",
                 "mg_per_kg": 8, "max_daily_mg_per_kg": 8, "interval_h": 24,
                 "forms": {"syrup_100": "syrup 100mg/5mL", "tab_100": "tablet 100mg", "tab_200": "tablet 200mg"}},
    "metformin": {"name_en": "Metformin", "name_fa": "متفورمین",
                  "mg_per_kg": None, "max_daily_mg_per_kg": None, "interval_h": None,
                  "note": "Not weight-based; adult dosing: 500-1000mg BID, max 2550mg/day",
                  "forms": {"tab_500": "tablet 500mg", "tab_850": "tablet 850mg", "tab_1000": "tablet 1000mg"}},
}


def calculate_dose(drug_key: str, weight_kg: float) -> dict:
    d = DOSE_TABLE.get(drug_key)
    if not d:
        return {"ok": False, "message_en": "Drug not in calculator", "message_fa": "دارو در ماشین‌حساب نیست"}
    if d.get("note") and not d.get("mg_per_kg"):
        return {"ok": True, "drug": d["name_en"], "drug_fa": d["name_fa"], "note": d["note"],
                "note_fa": "دوز ثابت بزرگسال — به وزن وابسته نیست"}
    try:
        w = float(weight_kg)
    except (ValueError, TypeError):
        return {"ok": False, "message_en": "Enter weight in kg", "message_fa": "وزن به کیلوگرم وارد کن"}
    if w <= 0 or w > 200:
        return {"ok": False, "message_en": "Unrealistic weight", "message_fa": "وزن نامعتبر"}
    single_dose = round(d["mg_per_kg"] * w)
    max_daily = round(d["max_daily_mg_per_kg"] * w)
    doses_per_day = round(24 / d["interval_h"])
    # شکل دارویی
    forms_info = []
    for fk, fname in d.get("forms", {}).items():
        conc = 0
        if "syrup" in fk:
            mg = int(fk.split("_")[1])
            ml = round(single_dose / mg * 5, 1)
            forms_info.append(f"{d['name_fa']}: {ml} mL از {fname}")
        elif "tab" in fk or "cap" in fk:
            mg = int(fk.split("_")[1])
            tabs = round(single_dose / mg, 1)
            forms_info.append(f"{d['name_fa']}: {tabs} عدد {fname}")
    return {"ok": True, "drug": d["name_en"], "drug_fa": d["name_fa"],
            "weight": f"{w} kg", "single_dose_mg": single_dose,
            "interval_h": d["interval_h"], "doses_per_day": doses_per_day,
            "max_daily_mg": max_daily, "forms": forms_info,
            "warning": f"Max {max_daily} mg/day. Always confirm with a doctor.",
            "warning_fa": f"حداکثر {max_daily} میلی‌گرم در روز. همیشه با پزشک تأیید کن."}


# ============================ pregnancy safety ============================

PREGNANCY_CATEGORIES = {
    "A": {"en": "Safe — controlled studies show no risk", "fa": "ایمن — مطالعات کنترل‌شده خطری نشان نداده"},
    "B": {"en": "Probably safe — animal studies show no risk", "fa": "احتمالاً ایمن — مطالعات حیوانی خطری نشان نداده"},
    "C": {"en": "Use only if clearly needed — risk cannot be ruled out", "fa": "فقط در صورت ضرورت — ریسک رد نشده"},
    "D": {"en": "Known risk — use only in life-threatening situations", "fa": "ریسک شناخته‌شده — فقط در مواقع خطرناک"},
    "X": {"en": "Contraindicated — do NOT use in pregnancy", "fa": "ممنوع در بارداری — استفاده نکن"},
}

PREGNANCY_DRUGS = {
    "paracetamol": "B", "acetaminophen": "B", "ibuprofen": "D", "aspirin": "D",
    "naproxen": "D", "diclofenac": "D", "warfarin": "X", "heparin": "B",
    "enoxaparin": "B", "metformin": "B", "insulin": "B", "glyburide": "B",
    "glibenclamide": "B", "atenolol": "D", "metoprolol": "C", "labetalol": "C",
    "amlodipine": "C", "enalapril": "D", "lisinopril": "D", "losartan": "D",
    "amoxicillin": "B", "penicillin": "B", "azithromycin": "B", "ciprofloxacin": "C",
    "tetracycline": "D", "doxycycline": "D", "cephalexin": "B", "cefixime": "B",
    "omeprazole": "C", "pantoprazole": "B", "ranitidine": "B",
    "sertraline": "C", "fluoxetine": "C", "paroxetine": "D",
    "levothyroxine": "A", "prednisolone": "C", "dexamethasone": "C",
    "folic acid": "A", "iron": "A", "vitamin d": "A",
    "isotretinoin": "X", "thalidomide": "X", "methotrexate": "X",
    "valproic acid": "D", "carbamazepine": "D", "phenytoin": "D", "lamotrigine": "C",
    "albuterol": "C", "salbutamol": "C",
}

# شیردهی
LACTATION_NOTES = {
    "ibuprofen": {"en": "Safe in breastfeeding", "fa": "در شیردهی ایمن است"},
    "paracetamol": {"en": "Safe in breastfeeding", "fa": "در شیردهی ایمن است"},
    "aspirin": {"en": "Avoid — risk of Reye syndrome in infant", "fa": "اجتناب کن — خطر سندرم رای در نوزاد"},
    "warfarin": {"en": "Generally safe in breastfeeding", "fa": "معمولاً در شیردهی ایمن است"},
    "metformin": {"en": "Safe in breastfeeding", "fa": "در شیردهی ایمن است"},
    "codeine": {"en": "Avoid — risk of respiratory depression in infant", "fa": "اجتناب کن — خطر افسردگی تنفسی نوزاد"},
    "amoxicillin": {"en": "Safe in breastfeeding", "fa": "در شیردهی ایمن است"},
    "sertraline": {"en": "Preferred SSRI in breastfeeding", "fa": "SSRI ترجیحی در شیردهی"},
    "isotretinoin": {"en": "Contraindicated in breastfeeding", "fa": "در شیردهی ممنوع است"},
}


def check_pregnancy(drug_name: str) -> dict:
    n = (drug_name or "").strip().lower()
    cat = None
    for k, v in PREGNANCY_DRUGS.items():
        if k in n or n in k:
            cat = v
            break
    if not cat:
        return {"ok": True, "found": False,
                "message_en": "Not in the pregnancy database; ask your doctor.",
                "message_fa": "در بانک بارداری نیست؛ از پزشکت بپرس."}
    info = PREGNANCY_CATEGORIES[cat]
    lact = LACTATION_NOTES.get(n, None)
    return {"ok": True, "found": True, "drug": n, "category": cat,
            "pregnancy_en": info["en"], "pregnancy_fa": info["fa"],
            "lactation_en": lact["en"] if lact else "Ask your doctor",
            "lactation_fa": lact["fa"] if lact else "از پزشکت بپرس"}


# ============================ multi-drug interaction ============================


def check_multi_drugs(drug_list: list[str]) -> dict:
    """Check interactions between 2+ drugs simultaneously."""
    from drug_interaction import check_interaction, search_drug, SEV_FA
    from i18n import is_fa
    fa = is_fa()
    if len(drug_list) < 2:
        return {"ok": False, "message_en": "Enter at least 2 drugs", "message_fa": "حداقل ۲ دارو وارد کن"}
    pairs = []
    for i in range(len(drug_list)):
        for j in range(i + 1, len(drug_list)):
            a, b = drug_list[i].strip(), drug_list[j].strip()
            if not a or not b:
                continue
            r = check_interaction(a, b)
            if r.get("ok"):
                for it in r.get("interactions", []):
                    if it.get("severity") != "none":
                        pairs.append({"a": a, "b": b, "severity": it.get("severity", ""),
                                      "detail": it.get("detail_fa", "")})
    severity_order = {"major": 0, "moderate": 1, "minor": 2}
    pairs.sort(key=lambda x: severity_order.get(x["severity"], 3))
    return {"ok": True, "count": len(pairs), "pairs": pairs[:20],
            "message_fa": f"{len(pairs)} تداخل یافت شد" if pairs else "تداخل مهمی یافت نشد",
            "message_en": f"{len(pairs)} interaction(s) found" if pairs else "No significant interaction found"}


# ============================ due date calculator ============================


def due_date(lmp: str, cycle_length: int = 28) -> dict:
    """Naegele's rule + ultrasound adjustment."""
    try:
        d = datetime.strptime(lmp, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        try:
            d = datetime.strptime(lmp, "%d/%m/%Y").date()
        except (ValueError, TypeError):
            return {"ok": False, "message_en": "Date format: YYYY-MM-DD", "message_fa": "فرمت تاریخ: YYYY-MM-DD"}
    adjustment = (cycle_length - 28) if cycle_length else 0
    dd = d + timedelta(days=280 + adjustment)
    today = date.today()
    days_pregnant = (today - d).days
    weeks = days_pregnant // 7
    days = days_pregnant % 7
    trimester = 1 if weeks < 13 else (2 if weeks < 27 else 3)
    return {"ok": True, "due_date": dd.isoformat(), "weeks": weeks, "days": days,
            "trimester": trimester, "total_days": days_pregnant,
            "message_fa": f"هفته‌ی {weeks} و {days} روز — سه‌ماهه‌ی {trimester}",
            "message_en": f"{weeks} weeks {days} days — trimester {trimester}"}


# ============================ symptom diary ============================

DIARY_FILE = os.path.join(DATA_DIR, "symptom_diary.json")


def diary_add(date_str: str, symptom: str, severity: int, note: str = "") -> dict:
    entries = _diary_load()
    e = {"date": date_str, "symptom": symptom, "severity": max(1, min(10, severity)), "note": note or "",
         "ts": datetime.now().isoformat()[:19]}
    entries.append(e)
    entries = entries[-500:]  # آخرین ۵۰۰
    _diary_save(entries)
    return {"ok": True, "total": len(entries)}


def diary_list(limit: int = 50) -> list[dict]:
    entries = _diary_load()
    return entries[-limit:]


def diary_clear() -> dict:
    _diary_save([])
    return {"ok": True}


def _diary_load() -> list[dict]:
    try:
        return json.load(open(DIARY_FILE, encoding="utf-8"))
    except Exception:
        return []


def _diary_save(entries: list[dict]) -> None:
    json.dump(entries, open(DIARY_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


# ============================ medication reminder ============================

REMINDERS_FILE = os.path.join(DATA_DIR, "med_reminders.json")


def reminders_add(drug: str, times: list[str], days: str = "daily") -> dict:
    rem = _rem_load()
    r = {"id": len(rem) + 1, "drug": drug, "times": times, "days": days,
         "active": True, "created": datetime.now().isoformat()[:19]}
    rem.append(r)
    _rem_save(rem)
    return {"ok": True, "id": r["id"], "total": len(rem)}


def reminders_list() -> list[dict]:
    return _rem_load()


def reminders_remove(rid: int) -> dict:
    rem = _rem_load()
    rem = [r for r in rem if r["id"] != rid]
    _rem_save(rem)
    return {"ok": True, "total": len(rem)}


def _rem_load() -> list[dict]:
    try:
        return json.load(open(REMINDERS_FILE, encoding="utf-8"))
    except Exception:
        return []


def _rem_save(rem: list[dict]) -> None:
    json.dump(rem, open(REMINDERS_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


# ============================ backup / restore ============================

BACKUP_FILES = ["patient_profile.json", "vitals_history.json", "learned_knowledge.json",
                "ai_behavior_profile.json", "local_llm_config.json", "app_settings.json",
                "symptom_diary.json", "med_reminders.json", "conversation_history.json"]


def backup_all(dest_dir: str) -> dict:
    os.makedirs(dest_dir, exist_ok=True)
    copied = []
    for f in BACKUP_FILES:
        src = os.path.join(DATA_DIR, f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dest_dir, f))
            copied.append(f)
    return {"ok": True, "files": copied, "dest": dest_dir}


def restore_all(src_dir: str) -> dict:
    restored = []
    for f in BACKUP_FILES:
        src = os.path.join(src_dir, f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(DATA_DIR, f))
            restored.append(f)
    return {"ok": True, "files": restored}


# ============================ growth chart (child) ============================

# WHO percentile data (approximate, boys, height cm)
WHO_HEIGHT_BOYS = {1: [46.1, 48.9, 50.8, 52.7, 54.7], 6: [63.4, 66.6, 68.0, 69.3, 70.7],
                   12: [71.0, 74.5, 76.0, 77.6, 79.2], 24: [81.7, 86.4, 88.5, 90.7, 92.9],
                   36: [89.4, 94.9, 97.5, 100.0, 102.7], 60: [102.7, 109.2, 112.0, 115.0, 118.0]}
WHO_HEIGHT_GIRLS = {1: [45.4, 48.2, 49.9, 51.7, 53.5], 6: [61.8, 64.8, 66.2, 67.6, 69.0],
                    12: [69.8, 73.3, 74.9, 76.5, 78.1], 24: [80.4, 84.9, 87.0, 89.2, 91.4],
                    36: [88.6, 93.9, 96.5, 99.1, 101.7], 60: [101.6, 108.0, 110.9, 113.9, 116.9]}
# weight kg
WHO_WEIGHT_BOYS = {1: [2.9, 3.6, 3.9, 4.3, 4.7], 6: [6.4, 7.4, 7.9, 8.4, 8.9],
                   12: [8.0, 9.2, 9.6, 10.3, 10.9], 24: [10.5, 12.2, 12.7, 13.7, 14.8],
                   36: [12.7, 14.7, 15.3, 16.5, 17.7], 60: [15.9, 18.3, 19.0, 20.5, 22.0]}
WHO_WEIGHT_GIRLS = {1: [2.8, 3.4, 3.7, 4.0, 4.4], 6: [5.7, 6.7, 7.1, 7.6, 8.1],
                    12: [7.3, 8.5, 8.9, 9.6, 10.2], 24: [9.8, 11.3, 11.9, 12.9, 13.9],
                    36: [12.2, 13.9, 14.6, 15.8, 17.2], 60: [15.1, 17.5, 18.2, 20.0, 21.9]}

PERCENTILE_LABELS = ["3rd", "15th", "50th", "85th", "97th"]


def growth_percentile(age_months: int, sex: str, height_cm: float = 0, weight_kg: float = 0) -> dict:
    s = "boys" if sex.lower().startswith("m") or sex == "پسر" else "girls"
    h_table = WHO_HEIGHT_BOYS if s == "boys" else WHO_HEIGHT_GIRLS
    w_table = WHO_WEIGHT_BOYS if s == "boys" else WHO_WEIGHT_GIRLS
    # نزدیک‌ترین سن موجود
    closest = min(h_table.keys(), key=lambda x: abs(x - age_months))
    result = {"ok": True, "age_months": age_months, "sex": s, "reference_age": closest}
    if height_cm > 0:
        vals = h_table[closest]
        pct = _find_percentile(height_cm, vals)
        result["height"] = height_cm
        result["height_percentile"] = pct
        result["height_label"] = PERCENTILE_LABELS[max(0, min(4, pct))]
    if weight_kg > 0:
        vals = w_table[closest]
        pct = _find_percentile(weight_kg, vals)
        result["weight"] = weight_kg
        result["weight_percentile"] = pct
        result["weight_label"] = PERCENTILE_LABELS[max(0, min(4, pct))]
    return result


def _find_percentile(val: float, ref: list) -> int:
    if val <= ref[0]:
        return 0
    if val >= ref[-1]:
        return 4
    for i in range(len(ref) - 1):
        if ref[i] <= val <= ref[i + 1]:
            frac = (val - ref[i]) / (ref[i + 1] - ref[i]) if ref[i + 1] > ref[i] else 0
            return i + (1 if frac > 0.5 else 0)
    return 2


# ============================ chat history search ============================


def search_chat_history(query: str, limit: int = 20) -> list[dict]:
    try:
        hist = json.load(open(os.path.join(DATA_DIR, "conversation_history.json"), encoding="utf-8"))
    except Exception:
        return []
    q = query.lower()
    hits = []
    for conv in hist:
        for msg in conv.get("messages", []):
            if q in str(msg.get("content", "")).lower():
                hits.append({"role": msg.get("role", ""), "text": str(msg.get("content", ""))[:300],
                             "ts": conv.get("ts", "")})
                if len(hits) >= limit:
                    return hits
    return hits
