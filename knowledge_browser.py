# -*- coding: utf-8 -*-
"""
knowledge_browser.py — ماژول مرور دانش‌نامه:
- علائم: همه‌ی علائم قابل جستجو با انتخاب
- بیماری‌ها: همه‌ی بیماری‌ها با علائم و مشخصات
- داروها: همه‌ی داروها با خواص و عوارض
"""
from __future__ import annotations

from typing import Any

from common_2077 import normalize
from i18n import is_fa


# ============================ علائم ============================

def get_all_symptoms() -> list[dict]:
    """همه‌ی علائم با نام فارسی/انگلیسی و کلیدواژه‌ها."""
    from medical_engine import SYMPTOM_KEYWORDS, SYMPTOM_NAMES_FA, SYMPTOM_NAMES_EN, DISEASES
    out = []
    for sid in sorted(SYMPTOM_KEYWORDS.keys()):
        # کدام بیماری‌ها این علامت را دارند
        related = []
        for d in DISEASES:
            if sid in d.get("symptoms", {}):
                p = d["symptoms"][sid]
                if p >= 0.3:
                    related.append({"id": d["id"], "name": d["fa"] if is_fa() else d["en"], "p": p})
        related.sort(key=lambda x: x["p"], reverse=True)
        out.append({
            "id": sid,
            "fa": SYMPTOM_NAMES_FA.get(sid, sid),
            "en": SYMPTOM_NAMES_EN.get(sid, sid),
            "keywords_count": len(SYMPTOM_KEYWORDS[sid]),
            "related_diseases": related[:8],
        })
    return out


def search_symptoms(query: str) -> list[dict]:
    """جستجوی علائم بر اساس نام یا کلیدواژه."""
    if not query or not query.strip():
        return get_all_symptoms()
    nq = normalize(query)
    all_syms = get_all_symptoms()
    return [s for s in all_syms if nq in normalize(s["fa"]) or nq in normalize(s["en"]) or nq in s["id"]]


# ============================ بیماری‌ها ============================

def get_all_diseases() -> list[dict]:
    """همه‌ی بیماری‌های موتور تشخیص با علائم و مشخصات."""
    from medical_engine import DISEASES, SYMPTOM_NAMES_FA, SYMPTOM_NAMES_EN
    fa = is_fa()
    out = []
    for d in DISEASES:
        symptoms = []
        for sid, p in d.get("symptoms", {}).items():
            if p >= 0.2:
                symptoms.append({
                    "id": sid,
                    "name": SYMPTOM_NAMES_FA.get(sid, sid) if fa else SYMPTOM_NAMES_EN.get(sid, sid),
                    "probability": p,
                })
        symptoms.sort(key=lambda x: x["probability"], reverse=True)
        out.append({
            "id": d["id"],
            "fa": d["fa"],
            "en": d["en"],
            "name": d["fa"] if fa else d["en"],
            "urgency": d.get("urgency", "routine"),
            "prior": d.get("prior", 0),
            "symptoms": symptoms,
            "advice": d.get("advice" if fa else "advice_en", d.get("advice", [])),
            "doctor_when": d.get("doctor_when" if fa else "doctor_when_en", d.get("doctor_when", "")),
        })
    return out


def search_diseases(query: str) -> list[dict]:
    if not query or not query.strip():
        return get_all_diseases()
    nq = normalize(query)
    return [d for d in get_all_diseases() if nq in normalize(d["fa"]) or nq in normalize(d["en"]) or nq in d["id"]]


def get_catalog_diseases(query: str = "", limit: int = 50) -> dict:
    """جستجو در کاتالوگ ICD-10-CM (۲۷,۰۰۰+ بیماری)."""
    from medical_catalog import search_conditions, stats, get_chapter_fa
    st = stats()
    if not query or not query.strip():
        return {"ok": True, "total": st["conditions"], "results": [], "query": ""}
    results = search_conditions(query, limit)
    return {
        "ok": True,
        "total": st["conditions"],
        "results": [{"name": r["name"], "icd10": r["icd10"], "chapter": get_chapter_fa(r["icd10"])} for r in results],
        "query": query,
    }


# ============================ داروها ============================

def get_all_drugs() -> list[dict]:
    """همه‌ی داروها با نام، دسته، خواص و تداخل‌ها."""
    from drug_interaction import DRUGS, INTERACTIONS, SEV_FA
    from drugbank_connector import DRUG_DATABASE
    fa = is_fa()
    drug_db_map = {k: v for k, v in DRUG_DATABASE.items()}
    out = []
    for d in DRUGS:
        did = d["id"]
        # تداخل‌های این دارو
        interactions = []
        for it in INTERACTIONS:
            if did in (it["a"], it["b"]):
                other_id = it["b"] if it["a"] == did else it["a"]
                other = next((x for x in DRUGS if x["id"] == other_id), None)
                interactions.append({
                    "other": other["fa"] if other and fa else (other["en"][0] if other else other_id),
                    "severity": it["sev"],
                    "severity_fa": SEV_FA()[it["sev"]],
                    "detail": it["fa"] if fa else it["fa"],  # فعلا فقط فارسی
                })
        # اطلاعات DrugBank
        db_info = drug_db_map.get(did, {})
        out.append({
            "id": did,
            "fa": d["fa"][0] if d["fa"] else did,
            "en": d["en"][0] if d["en"] else did,
            "category": d["cat"],
            "aliases_fa": d["fa"],
            "aliases_en": d["en"],
            "interactions": interactions,
            "atc": db_info.get("atc", ""),
            "class": db_info.get("class_fa", ""),
            "half_life": db_info.get("half_life", ""),
            "metabolism": db_info.get("metabolism", ""),
            "routes": db_info.get("routes", []),
            "pregnancy": db_info.get("pregnancy", ""),
            "contra": db_info.get("contra_fa", ""),
            "notes": db_info.get("notes_fa", ""),
        })
    return out


def search_drugs(query: str) -> list[dict]:
    if not query or not query.strip():
        return get_all_drugs()
    nq = normalize(query)
    results = []
    for d in get_all_drugs():
        if (nq in normalize(d["fa"]) or nq in normalize(d["en"])
                or nq in normalize(d["category"])
                or any(nq in normalize(a) for a in d["aliases_fa"] + d["aliases_en"])):
            results.append(d)
    return results


def get_drug_count() -> int:
    from drug_interaction import DRUGS
    return len(DRUGS)


def get_interaction_count() -> int:
    from drug_interaction import INTERACTIONS
    return len(INTERACTIONS)
