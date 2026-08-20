# -*- coding: utf-8 -*-
"""
bayesian_engine.py — استدلال بیزین ساده برای رتبه‌بندی احتمال بیماری‌ها.
خروجی‌ها همیشه «احتمالی» هستند و جایگزین معاینه پزشک نیستند.
"""
from __future__ import annotations

import math
from typing import Any

from medical_engine import DISEASES, sym_name

SMOOTH = 1e-6
_RARE: set = set()  # lazy — در اولین rank پر می‌شود
_RARE_COUNTS: dict = {}


def _rare_counts() -> dict:
    global _RARE_COUNTS
    if not _RARE_COUNTS:
        counts: dict[str, int] = {}
        for dis in DISEASES:
            for sid, p in dis["symptoms"].items():
                if p >= 0.7:
                    counts[sid] = counts.get(sid, 0) + 1
        _RARE_COUNTS = counts
    return _RARE_COUNTS


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
    rare_counts = _rare_counts()
    present = {s: info for s, info in detected.get("present", {}).items() if not info.get("denied")}
    denied = {s: info for s, info in detected.get("present", {}).items() if info.get("denied")}
    logp = math.log(max(d["prior"] * _age_sex_factor(d, profile), SMOOTH))
    rare = _RARE
    for sid, p in d["symptoms"].items():
        if sid in present:
            boost = 1.25 if present[sid]["severity"] == "severe" else 1.0
            logp += math.log(min(p * boost, 0.98))
            # علامتِ کمیابِ پراحتمال (شبیه pathognomonic) بر علامت عمومی مثل تب غلبه می‌کند
            if p >= 0.9 and rare_counts.get(sid, 9) == 1:
                logp += math.log(3.5)
            elif p >= 0.8 and sid in rare:
                logp += math.log(2.0)
        elif sid in denied:
            logp += math.log(max(1.0 - p, SMOOTH))
        elif p >= 0.8:
            # علامت کلیدی که اصلاً ذکر نشده، احتمال را به‌نرمی کم می‌کند
            logp += math.log(1.0 - p * 0.5)
    # جریمه‌ی پوشش: علامتِ حاضرِ بیمار که این بیماری اصلاً توضیحش نمی‌دهد
    for sid in present:
        if sid not in d["symptoms"]:
            logp += math.log(0.7)
    # مدت بیماری: سرماخوردگی/آنفلوآنزا ۳ هفته طول نمی‌کشد؛ سل/COPD ماه‌ها است
    dur = detected.get("duration_days")
    if dur is not None:
        if dur >= 21 and d["id"] in ("common_cold", "influenza", "gastroenteritis"):
            logp -= 2.0
        if dur >= 21 and d["id"] in ("tuberculosis", "copd", "osteoarthritis", "cataract", "psoriasis", "acne"):
            logp += 0.7
        if dur <= 3 and d["id"] in ("sinusitis", "pneumonia"):
            logp -= 0.3
        if dur >= 14 and d["id"] in ("common_cold", "influenza"):
            logp -= 0.5
    return logp


def _rare_symptoms() -> set[str]:
    """علائمی که فقط در ۱-۲ بیماری با احتمال بالا می‌آیند (مثل درد گوش در عفونت گوش)."""
    counts: dict[str, int] = {}
    for d in DISEASES:
        for sid, p in d["symptoms"].items():
            if p >= 0.7:
                counts[sid] = counts.get(sid, 0) + 1
    return {s for s, c in counts.items() if c <= 2}


def rank_diseases(detected: dict, profile: dict, top_n: int = 5) -> list[dict[str, Any]]:
    global _RARE
    if not _RARE:
        _RARE = _rare_symptoms()
    # اورژانس‌ها همیشه صدر بمانند حتی اگر احتمال عددی کمتری بگیرند
    present_now = {s for s, i in detected.get("present", {}).items() if not i.get("denied")}
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
    top = scored[:max(top_n, 8)]
    # کاندیدهای اورژانسی که علامت کمیاب اختصاصی‌شان حاضر است را به صدر بیاور
    emergency_boost = []
    rest = []
    for s, d, ov in top:
        is_em = d.get("urgency") == "emergency"
        has_spec = any(p >= 0.9 and sid in present_now for sid, p in d["symptoms"].items())
        (emergency_boost if (is_em and has_spec) else rest).append((s, d, ov))
    top = (emergency_boost + rest)[:top_n]
    mx = top[0][0]
    exps = [math.exp(s - mx) for s, _, _ in top]
    total = sum(exps)
    from i18n import is_fa
    out = []
    for (s, d, overlap), e in zip(top, exps):
        pct = e / total * 100.0
        out.append({
            "id": d["id"], "fa": d["fa"], "en": d["en"], "name": d["fa"] if is_fa() else d["en"],
            "urgency": d["urgency"], "percent": round(pct, 1),
            "matched_symptoms": [sym_name(x) for x in overlap],
            "advice": list(d.get("advice" if is_fa() else "advice_en", d.get("advice", []))),
            "doctor_when": d.get("doctor_when" if is_fa() else "doctor_when_en", d.get("doctor_when", "")),
        })
    return out
