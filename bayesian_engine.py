# -*- coding: utf-8 -*-
"""
Simple Bayesian reasoning to rank disease likelihoods.
Everything it outputs is a 'possible', never a replacement for an exam.
"""
from __future__ import annotations

import math
from typing import Any

from medical_engine import DISEASES, sym_name

SMOOTH = 1e-6
_RARE: set = set()  # lazy, filled on the first rank() call
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
    """
    Slight prior adjustment by age/sex, only for the diseases where it matters.
    """
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
    _n_matches = len([1 for x in present if x in d["symptoms"]])
    for sid, p in d["symptoms"].items():
        if sid in present:
            boost = 1.25 if present[sid]["severity"] == "severe" else 1.0
            logp += math.log(min(p * boost, 0.98))
            # a rare high-probability symptom beats generic ones like fever;
            # boost fades when multiple other symptoms also match (broader picture)
            _mult = 1.0 if _n_matches <= 1 else 0.0
            if p >= 0.9 and rare_counts.get(sid, 9) == 1:
                logp += math.log(1 + (3.5 - 1) * _mult)
            elif p >= 0.8 and sid in rare:
                logp += math.log(1 + (2.0 - 1) * _mult)
        elif sid in denied:
            logp += math.log(max(1.0 - p, SMOOTH))
        elif p >= 0.8:
            # a key symptom that wasn't mentioned lowers the score,
            # but less when several symptoms already match (partial picture)
            _n_present = len([1 for x in present if x in d["symptoms"]])
            _penalty = 0.5 if _n_present < 2 else 0.18
            logp += math.log(1.0 - p * _penalty)
    # coverage penalty: the patient has it but this disease never explains it
    _overlap_n = len([1 for x in present if x in d["symptoms"]])
    _total_n = max(1, len(present))
    _frac = _overlap_n / _total_n
    # covering only 1 of 5 symptoms should hurt more than 4 of 5
    _cov = 0.45 + 0.45 * _frac  # 1/5 → 0.54; 4/5 → 0.81; 5/5 → 0.9
    for sid in present:
        if sid not in d["symptoms"]:
            logp += math.log(_cov)
    # duration: a cold doesn't last 3 weeks; TB/COPD run for months
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
    """
    Symptoms that appear with high probability in only 1-2 diseases
    (ear pain in an ear infection, for example).
    """
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
    # emergencies stay on top even with a lower numeric score
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
    # push emergency candidates with their specific rare symptom present to the top
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
