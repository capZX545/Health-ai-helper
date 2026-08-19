# -*- coding: utf-8 -*-
"""
bayesian_engine.py — استدلال بیزین ساده برای رتبه‌بندی احتمال بیماری‌ها.
خروجی‌ها همیشه «احتمالی» هستند و جایگزین معاینه پزشک نیستند.
"""
from __future__ import annotations

import math
from typing import Any

from medical_engine import DISEASES, SYMPTOM_NAMES_FA

SMOOTH = 1e-6


def _age_sex_factor(d: dict, profile: dict) -> float:
    """تعدیل جزئی احتمال پیشین بر اساس سن/جنسیت (فقط برای بیماری‌های وابسته)."""
    f = 1.0
    try:
        age = int(profile.get("age") or 0)
    except (TypeError, ValueError):
        age = 0
    sex = (profile.get("gender") or "").strip()
    did = d["id"]
    if did in ("hypertension_likely", "hyperglycemia_likely") and age >= 45:
        f *= 1.8
    if did == "uti" and sex in ("زن", "female", "f"):
        f *= 2.0
    if did == "sleep_apnea_likely" and age >= 40:
        f *= 1.4
    if did in ("iron_def_anemia",) and sex in ("زن", "female", "f"):
        f *= 1.6
    if did in ("gastroenteritis",) and age and age < 12:
        f *= 1.5
    return f


def score_disease(d: dict, detected: dict, profile: dict) -> float:
    present = {s: info for s, info in detected.get("present", {}).items() if not info.get("denied")}
    denied = {s: info for s, info in detected.get("present", {}).items() if info.get("denied")}
    logp = math.log(max(d["prior"] * _age_sex_factor(d, profile), SMOOTH))
    for sid, p in d["symptoms"].items():
        if sid in present:
            boost = 1.25 if present[sid]["severity"] == "severe"else 1.0
            logp += math.log(min(p * boost, 0.98))
        elif sid in denied:
            logp += math.log(max(1.0 - p, SMOOTH))
    # جریمه‌ی بیماری‌هایی که علائم کلیدی‌شان ذکر نشده
    dur = detected.get("duration_days")
    if dur is not None:
        if dur <= 3 and d["id"] in ("sinusitis", "pneumonia"):
            logp -= 0.3
        if dur >= 14 and d["id"] in ("common_cold", "influenza"):
            logp -= 0.5
    return logp


def rank_diseases(detected: dict, profile: dict, top_n: int = 5) -> list[dict[str, Any]]:
    """رتبه‌بندی با نرمال‌سازی softmax تقریبی؛ درصد = احتمال نسبی در بین کاندیدها."""
    if not any(not i.get("denied") for i in detected.get("present", {}).values()):
        return []
    scored = []
    for d in DISEASES:
        overlap = [s for s in d["symptoms"] if s in detected.get("present", {}) and not detected["present"][s].get("denied")]
        if not overlap:
            continue
        scored.append((score_disease(d, detected, profile), d, overlap))
    if not scored:
        return []
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_n]
    mx = top[0][0]
    exps = [math.exp(s - mx) for s, _, _ in top]
    total = sum(exps)
    out = []
    for (s, d, overlap), e in zip(top, exps):
        pct = e / total * 100.0
        out.append({
            "id": d["id"], "fa": d["fa"], "en": d["en"],
            "urgency": d["urgency"], "percent": round(pct, 1),
            "matched_symptoms_fa": [SYMPTOM_NAMES_FA.get(x, x) for x in overlap],
            "advice": list(d.get("advice", [])),
            "doctor_when": d.get("doctor_when", ""),
        })
    return out
