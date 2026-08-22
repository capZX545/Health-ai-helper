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


# پل فارسی → انگلیسی برای کاتالوگ ICD-10 (که انگلیسی است)
_FA_EN_MED = {
    "دیابت": "diabetes", "قند": "hyperglycemia", "سرطان": "cancer", "تومور": "tumor",
    "فشار خون": "hypertension", "پرفشاری": "hypertension", "کم‌خونی": "anemia",
    "آسم": "asthma", "آلرژی": "allergy", "حساسیت": "allergy", "تشدید آسم": "asthma",
    "سکته": "stroke", "قلب": "heart", "عفونت": "infection", "کرونا": "covid",
    "کووید": "covid", "آنفلوآنزا": "influenza", "سرماخوردگی": "common cold",
    "سردرد": "headache", "میگرن": "migraine", "صرع": "epilepsy", "مصر": "epilepsy",
    "کلیه": "kidney", "کبد": "liver", "ریه": "lung",
    "پنومونی": "pneumonia", "ذات‌الریه": "pneumonia", "سل": "tuberculosis",
    "آرتریت": "arthritis", "آرتروز": "osteoarthritis", "استخوان": "bone",
    "پوستی": "skin", "پوست": "skin", "چشم": "eye", "گوش": "ear",
    "گلو": "throat", "لثه": "gum", "دندان": "tooth", "معدة": "stomach",
    "معده": "stomach", "روده": "intestine", "اسهال": "diarrhea", "یبوست": "constipation",
    "زخم": "ulcer", "رفلاکس": "reflux", "استفراغ": "vomiting", "تهوع": "nausea",
    "تب": "fever", "سرفه": "cough", "تنگی نفس": "dyspnea", "سرگیجه": "dizziness",
    "افسردگی": "depression", "اضطراب": "anxiety", "بی‌خوابی": "insomnia",
    "بارداری": "pregnancy", "زایمان": "delivery", "قاعدگی": "menstruation",
    "تیروئید": "thyroid", "چاقی": "obesity", "لاغری": "weight loss",
    "التهاب": "inflammation", "سنگ": "calculus", "کیسه": "gallbladder",
    "خونریزی": "bleeding", "درد": "pain", "شکستگی": "fracture", "سوختگی": "burn",
    "مسمومیت": "poisoning", "الکلی": "alcohol", "محرک": "stimulant",
    "ویروسی": "viral", "باکتری": "bacterial", "قارچ": "fungal", "انگل": "parasitic",
    "کمبود ویتامین": "vitamin deficiency", "ویتامین": "vitamin", "پوکی استخوان": "osteoporosis",
    "آتیش accesses": "access", "هموروئید": "hemorrhoid", "بواسیر": "hemorrhoid",
    "سینه": "chest", "پستان": "breast", "پروستات": "prostate", "نازایی": "infertility",
    "نقرس": "gout", "لوپوس": "lupus", "ام‌اس": "multiple sclerosis",
    "پارکینسون": "parkinson", "آلزایمر": "alzheimer", "اوتیسم": "autism",
    "کرون": "crohn", "سلیاک": "celiac", "هپاتیت": "hepatitis", "ایدز": "hiv",
    "اچ‌آی‌وی": "hiv", "مالاریا": "malaria", "تب دنگ": "dengue",
}


def get_catalog_diseases(query: str = "", limit: int = 50) -> dict:
    """جستجو در کاتالوگ ICD-10-CM (۲۷,۰۰۰+ بیماری).
    پل فارسی→انگلیسی: اگر جستجو فارسی باشد، معادل انگلیسی از بیماری‌های موتور
    و دیکشنری پزشکی پیدا شده و در کاتالوگ هم جستجو می‌شود. کد ICD (مثل E11) هم کار می‌کند."""
    import re as _re
    from medical_catalog import search_conditions, stats, get_chapter_fa, search_by_code_prefix
    st = stats()
    if not query or not query.strip():
        return {"ok": True, "total": st["conditions"], "results": [], "query": ""}
    q = query.strip()
    results = search_conditions(q, limit)

    # جستجو با پیشوند کد ICD (مثل E11 یا J45.9)
    if _re.match(r"^[A-TV-Za-tv-z]\d{2}", q):
        seen = {r.get("icd10") for r in results}
        for r in search_by_code_prefix(q, limit):
            if r.get("icd10") not in seen:
                seen.add(r.get("icd10"))
                results.append(r)

    # پل فارسی → انگلیسی
    nq = normalize(q)
    en_terms: list[str] = []
    has_fa = any("\u0600" <= ch <= "\u06FF" for ch in q)
    if has_fa:
        from medical_engine import DISEASES, SYMPTOM_NAMES_FA, SYMPTOM_NAMES_EN
        for d in DISEASES:
            if nq in normalize(d.get("fa", "")):
                en = d.get("en", "").split("(")[0].strip()
                if en and en not in en_terms:
                    en_terms.append(en)
        for sid, fa in SYMPTOM_NAMES_FA.items():
            if nq in normalize(fa) and sid in SYMPTOM_NAMES_EN:
                en = SYMPTOM_NAMES_EN[sid]
                if en and en not in en_terms:
                    en_terms.append(en)
        for fa_term, en_term in _FA_EN_MED.items():
            if nq in normalize(fa_term) or normalize(fa_term) in nq:
                if en_term not in en_terms:
                    en_terms.append(en_term)
        seen = {r.get("icd10") for r in results}
        for term in en_terms[:5]:
            for r in search_conditions(term, limit):
                if r.get("icd10") not in seen:
                    seen.add(r.get("icd10"))
                    results.append(r)
        results = results[:limit]
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


# ============================ بانک کامل FDA ============================

_FDA_CACHE: dict | None = None


def _load_fda() -> list[dict]:
    """بارگذاری یک‌باره‌ی drugs_fda.json (۱۹ هزار+ داروی FDA)."""
    global _FDA_CACHE
    if _FDA_CACHE is None:
        import json
        import os
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "drugs_fda.json")
        try:
            with open(path, encoding="utf-8") as f:
                _FDA_CACHE = json.load(f).get("drugs", [])
        except Exception as e:
            print(f"[knowledge_browser] بانک FDA بارگذاری نشد: {e}")
            _FDA_CACHE = []
        # ایندکس جستجو
        for i, d in enumerate(_FDA_CACHE):
            hay = " ".join([d.get("g", "")] + (d.get("brands") or []) + (d.get("ing") or [])).lower()
            d["_i"], d["_hay"] = i, hay
    return _FDA_CACHE


def get_fda_drug_count() -> int:
    return len(_load_fda())


def search_fda_drugs(query: str, limit: int = 40) -> list[dict]:
    """جستجو در بانک کامل FDA (نام ژنریک/برند/ماده‌ی فعال)."""
    q = normalize(query)
    if not q:
        return []
    out = []
    for d in _load_fda():
        if q in d["_hay"]:
            out.append(d)
            if len(out) >= limit:
                break
    return out


def get_fda_drug(generic_name: str) -> dict | None:
    """دریافت کامل‌ترین ورودی برای یک نام ژنریک (برای جزئیات)."""
    key = normalize(generic_name)
    best = None
    for d in _load_fda():
        if normalize(d["g"]) == key:
            if best is None or d.get("n", 0) > best.get("n", 0):
                best = d
    return best
