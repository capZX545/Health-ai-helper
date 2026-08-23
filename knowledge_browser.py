# -*- coding: utf-8 -*-
"""
Knowledge browser module:
- symptoms: everything searchable
- diseases: full list with symptoms and details
- drugs: full list with properties and side effects
"""
from __future__ import annotations

from typing import Any

from common_2077 import normalize
from i18n import is_fa


# ============================ symptoms ============================

def get_all_symptoms() -> list[dict]:
    """
    All symptoms with fa/en names and keywords.
    """
    from medical_engine import SYMPTOM_KEYWORDS, SYMPTOM_NAMES_FA, SYMPTOM_NAMES_EN, DISEASES
    out = []
    for sid in sorted(SYMPTOM_KEYWORDS.keys()):
        # which diseases carry this symptom
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
    """
    Search symptoms by name or keyword.
    """
    if not query or not query.strip():
        return get_all_symptoms()
    nq = normalize(query)
    all_syms = get_all_symptoms()
    return [s for s in all_syms if nq in normalize(s["fa"]) or nq in normalize(s["en"]) or nq in s["id"]]


# ============================ diseases ============================

def get_all_diseases() -> list[dict]:
    """
    All engine diseases with symptoms and details.
    """
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


# fa -> en bridge for the ICD-10 catalog (which is english-only)
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
    """
    Search the ICD-10 catalog.
    The catalog is english-only, so a persian query first gets translated through
    our own disease names plus a small medical dictionary. ICD codes (E11) work too.
    """
    import re as _re
    from medical_catalog import search_conditions, stats, get_chapter_fa, search_by_code_prefix
    st = stats()
    if not query or not query.strip():
        return {"ok": True, "total": st["conditions"], "results": [], "query": ""}
    q = query.strip()
    results = search_conditions(q, limit)

    # ICD code prefix search (E11, J45.9, ...)
    if _re.match(r"^[A-TV-Za-tv-z]\d{2}", q):
        seen = {r.get("icd10") for r in results}
        for r in search_by_code_prefix(q, limit):
            if r.get("icd10") not in seen:
                seen.add(r.get("icd10"))
                results.append(r)

# fa -> en bridge
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
        "results": [{"name": r["name"], "icd10": r["icd10"], "chapter": get_chapter_fa(r["icd10"]),
                     "fa": fa_disease_name(icd=r["icd10"], en=r["name"])} for r in results],
        "query": query,
    }


# ============================ drugs ============================

def get_all_drugs() -> list[dict]:
    """
    All drugs with name, category, properties and interactions.
    """
    from drug_interaction import DRUGS, INTERACTIONS, SEV_FA
    from drugbank_connector import DRUG_DATABASE
    fa = is_fa()
    drug_db_map = {k: v for k, v in DRUG_DATABASE.items()}
    out = []
    for d in DRUGS:
        did = d["id"]
        # interactions of this drug
        interactions = []
        for it in INTERACTIONS:
            if did in (it["a"], it["b"]):
                other_id = it["b"] if it["a"] == did else it["a"]
                other = next((x for x in DRUGS if x["id"] == other_id), None)
                interactions.append({
                    "other": other["fa"] if other and fa else (other["en"][0] if other else other_id),
                    "severity": it["sev"],
                    "severity_fa": SEV_FA()[it["sev"]],
                    "detail": it["fa"] if fa else it["fa"],  # persian only for now
                })
        # drugbank record
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


# ============================ full FDA bank ============================

_FDA_CACHE: dict | None = None


def _load_fda() -> list[dict]:
    """
    Loads drugs_fda.json once and keeps it in memory.
    """
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
        # search index
        for i, d in enumerate(_FDA_CACHE):
            hay = " ".join([d.get("g", "")] + (d.get("brands") or []) + (d.get("ing") or [])).lower()
            d["_i"], d["_hay"] = i, hay
    return _FDA_CACHE


def get_fda_drug_count() -> int:
    return len(_load_fda())


def search_fda_drugs(query: str, limit: int = 40) -> list[dict]:
    """
    Search the FDA bank (generic/brand/ingredient).
    """
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
    """
    Best-matching entry for a generic name (for the detail view).
    """
    key = normalize(generic_name)
    best = None
    for d in _load_fda():
        if normalize(d["g"]) == key:
            if best is None or d.get("n", 0) > best.get("n", 0):
                best = d
    return best


# ============================ FDA labels + persian names ============================

_LABELS_CACHE: dict | None = None
_FA_NAMES_CACHE: dict | None = None


def _load_labels() -> dict:
    """
    Loads the gzipped FDA label sections, once.
    """
    global _LABELS_CACHE
    if _LABELS_CACHE is None:
        import gzip
        import json as _json
        import os as _os
        path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "drug_labels.json.gz")
        try:
            with gzip.open(path, "rt", encoding="utf-8") as f:
                _LABELS_CACHE = _json.load(f)
        except Exception as e:
            print(f"[knowledge_browser] لیبل‌های FDA بارگذاری نشد: {e}")
            _LABELS_CACHE = {}
    return _LABELS_CACHE


def get_drug_label(generic_name: str) -> dict | None:
    """
    FDA label sections for a generic name: ind/warn/adv/box.
    """
    if not generic_name:
        return None
    return _load_labels().get(generic_name.strip().lower()) or None


def _load_fa_names() -> dict:
    global _FA_NAMES_CACHE
    if _FA_NAMES_CACHE is None:
        import json as _json
        import os as _os
        path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "fa_names.json")
        try:
            with open(path, encoding="utf-8") as f:
                _FA_NAMES_CACHE = _json.load(f)
        except Exception as e:
            print(f"[knowledge_browser] نام‌های فارسی بارگذاری نشد: {e}")
            _FA_NAMES_CACHE = {"icd_fa": {}, "disease_en_fa": {}, "drug_en_fa": {}}
    return _FA_NAMES_CACHE


def fa_drug_name(en_name: str) -> str:
    """
    Persian drug name from Wikidata, empty string if unknown.
    """
    if not en_name:
        return ""
    return _load_fa_names().get("drug_en_fa", {}).get(en_name.strip().lower(), "")


def fa_disease_name(icd: str = "", en: str = "") -> str:
    """
    Persian disease name, by ICD-10 code or english name.
    """
    m = _load_fa_names()
    if icd:
        code = icd.strip().upper()
        v = m.get("icd_fa", {}).get(code, "")
        if not v and len(code) >= 4:
            # category prefix (E11.9 -> E11)
            v = m.get("icd_fa", {}).get(code[:3], "")
        if v:
            return v
    if en:
        return m.get("disease_en_fa", {}).get(en.strip().lower(), "")
    return ""


# ---------- big open banks: DOID / Wikidata / HPO ----------

_DOID_CACHE: list | None = None
_WIKI_CACHE: dict | None = None
_HPO_CACHE: list | None = None


def _load_doid() -> list:
    global _DOID_CACHE
    if _DOID_CACHE is None:
        import json
        import os
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diseases_doid.json")
        try:
            _DOID_CACHE = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            print("[knowledge_browser] DOID not loaded:", e)
            _DOID_CACHE = []
        for i, d in enumerate(_DOID_CACHE):
            hay = " ".join([d.get("name", "")] + (d.get("syn") or [])).lower()
            d["_i"], d["_hay"] = i, hay
    return _DOID_CACHE


def search_doid(query: str, limit: int = 15) -> list:
    q = normalize(query)
    if not q:
        return []
    out = []
    for d in _load_doid():
        if q in d["_hay"] or q in d.get("icd", "").lower():
            out.append(d)
            if len(out) >= limit:
                break
    return out


def _load_wiki() -> dict:
    global _WIKI_CACHE
    if _WIKI_CACHE is None:
        import json
        import os
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wiki_diseases.json")
        try:
            _WIKI_CACHE = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            print("[knowledge_browser] wiki diseases not loaded:", e)
            _WIKI_CACHE = {}
    return _WIKI_CACHE


def search_wiki_diseases(query: str, limit: int = 15) -> list:
    q = normalize(query)
    qe = query.strip().lower()
    if not q:
        return []
    out = []
    for k, e in _load_wiki().items():
        if (q in normalize(e.get("en", "")) or q in normalize(e.get("fa", ""))
                or qe == str(e.get("icd", "")).strip().lower()):
            out.append({"qid": k, **e})
            if len(out) >= limit:
                break
    return out


def get_wiki_disease(en: str = "", icd: str = "", doid: str = "") -> dict | None:
    """Find the wiki entry (with symptoms/treatments) for a disease."""
    ne = normalize(en or "")
    code = (icd or "").strip().upper()
    dnum = str(doid or "").strip()
    best = None
    for k, e in _load_wiki().items():
        if ne and normalize(e.get("en", "")) == ne:
            return {"qid": k, **e}
        if code and str(e.get("icd", "")).upper().rstrip(".0123456789") == code.rstrip(".0123456789")[:3]:
            if e.get("sym") or e.get("drug"):
                best = best or {"qid": k, **e}
        if dnum and str(e.get("doid", "")).endswith(dnum):
            return {"qid": k, **e}
    return best


def _load_hpo() -> list:
    global _HPO_CACHE
    if _HPO_CACHE is None:
        import json
        import os
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "symptoms_hpo.json")
        try:
            _HPO_CACHE = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            print("[knowledge_browser] HPO not loaded:", e)
            _HPO_CACHE = []
        for i, t in enumerate(_HPO_CACHE):
            hay = " ".join([t.get("name", "")] + (t.get("syn") or [])).lower()
            t["_i"], t["_hay"] = i, hay
    return _HPO_CACHE


def hpo_count() -> int:
    return len(_load_hpo())


def search_hpo(query: str, limit: int = 30) -> list:
    q = normalize(query)
    if not q:
        return []
    out = []
    for t in _load_hpo():
        if q in t["_hay"]:
            out.append(t)
            if len(out) >= limit:
                break
    return out
