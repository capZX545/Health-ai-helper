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
        try:
            from lab_full import labs_for_disease
            out[-1]["labs"] = labs_for_disease(d.get("en", ""), d.get("id", ""))
        except Exception:
            pass
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
    out_rows = []
    for r in results:
        ch_fa = get_chapter_fa(r["icd10"])
        ex = explain_disease_entry(r["name"], r["icd10"])
        out_rows.append({"name": r["name"], "icd10": r["icd10"], "chapter": ch_fa,
                         "fa": fa_disease_name(icd=r["icd10"], en=r["name"]),
                         "note_en": ex["note_en"], "note_fa": ex["note_fa"],
                         "nsym_en": ex["sym_en"], "nsym_fa": ex["sym_fa"]})
    return {
        "ok": True,
        "total": st["conditions"],
        "results": out_rows,
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
            "category_en": cat_en(d["cat"]),
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
        from common_2077 import normalize as _n
        from translit import translit
        _fa_drugs = _load_fa_names().get("drug_en_fa", {})
        for i, d in enumerate(_FDA_CACHE):
            hay = " ".join([d.get("g", "")] + (d.get("brands") or []) + (d.get("ing") or [])).lower()
            d["_i"], d["_hay"] = i, hay
            if "fa" not in d:
                human = _fa_drugs.get(_n(d.get("g", "")), "")
                d["fa"] = human or translit(d.get("g", ""))
            if "cat" not in d:
                d["cat"] = classify_drug(d.get("class") or [])
            if "cat_en" not in d:
                d["cat_en"] = DRUG_CATS_EN.get(d["cat"], d["cat"])
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


def fa_disease_full(en: str = "", icd: str = "", doid: str = "", mesh: str = "") -> str:
    """Try every key we have (icd, doid, mesh, en) until a farsi name shows up."""
    v = fa_disease_name(icd=icd, en=en)
    m = _load_fa_names()
    if not v and doid:
        v = m.get("doid_fa", {}).get(str(doid).lstrip("DOID:").strip(), "")
    if not v and mesh:
        v = m.get("mesh_fa", {}).get(str(mesh).strip(), "")
    if not v and en:
        v = m.get("disease_en_fa", {}).get(en.strip().lower(), "")
    return v


# icd-10 chapters: (range, english, farsi)
ICD_CHAPTERS = [
    ("A00-B99", "Infectious & parasitic diseases", "بیماری‌های عفونی و انگلی"),
    ("C00-D49", "Neoplasms", "بدخیمی‌ها (تومورها)"),
    ("D50-D89", "Blood & immune disorders", "بیماری‌های خون و ایمنی"),
    ("E00-E89", "Endocrine, nutritional, metabolic", "غدد، تغذیه و متابولیسم"),
    ("F01-F99", "Mental & behavioral disorders", "اختلالات روانی و رفتاری"),
    ("G00-G99", "Nervous system", "بیماری‌های سیستم عصبی"),
    ("H00-H59", "Eye", "بیماری‌های چشم"),
    ("H60-H95", "Ear", "بیماری‌های گوش"),
    ("I00-I99", "Circulatory system", "بیماری‌های قلب و عروق"),
    ("J00-J99", "Respiratory system", "بیماری‌های تنفسی"),
    ("K00-K95", "Digestive system", "بیماری‌های گوارش"),
    ("L00-L99", "Skin", "بیماری‌های پوست"),
    ("M00-M99", "Musculoskeletal system", "بیماری‌های عضله و استخوان"),
    ("N00-N99", "Genitourinary system", "بیماری‌های ادراری و تناسلی"),
    ("O00-O9A", "Pregnancy & childbirth", "بارداری و زایمان"),
    ("P00-P96", "Perinatal conditions", "دوره‌ی نوزادی"),
    ("Q00-Q99", "Congenital malformations", "ناهنجاری‌های مادرزادی"),
    ("R00-R99", "Symptoms & abnormal findings", "علائم و یافته‌های غیرطبیعی"),
    ("S00-T88", "Injury & poisoning", "آسیب و مسمومیت"),
    ("V00-Y99", "External causes", "علل خارجی"),
    ("Z00-Z99", "Health status factors", "عوامل وضعیت سلامت"),
    ("U00-U85", "Special codes", "کدهای خاص"),
]


def icd_chapter(code: str) -> dict:
    """Chapter info {key, en, fa} for an ICD-10 code, empty dict if unknown."""
    c = (code or "").strip().upper()
    if not c or not c[0].isalpha():
        return {}
    # the category is the letter + the next two digits ("G912" -> G91, "Z3A10" -> Z3)
    n = 0
    got = 0
    for ch in c[1:]:
        if ch.isdigit() and got < 2:
            n = n * 10 + int(ch)
            got += 1
        else:
            break
    if got == 0:
        return {}
    for rng, en, fa in ICD_CHAPTERS:
        a, b = rng.split("-")

        def num(s):
            v = 0
            taken = 0
            for ch in s[1:]:
                if ch.isdigit() and taken < 2:
                    v = v * 10 + int(ch)
                    taken += 1
                elif ch.isalpha() and taken:
                    v += 1  # 7th character style (O9A)
                if taken >= 2 and not ch.isdigit():
                    break
            return v

        if a[0] == b[0] == c[0]:
            if num(a) <= n <= num(b):
                return {"key": rng, "en": en, "fa": fa}
        elif a[0] == c[0]:
            if n >= num(a):
                return {"key": rng, "en": en, "fa": fa}
        elif b[0] == c[0]:
            if n <= num(b):
                return {"key": rng, "en": en, "fa": fa}
        elif a[0] < c[0] < b[0]:
            return {"key": rng, "en": en, "fa": fa}
    return {}


# drug categories: (farsi, english, keywords in the pharm class)
DRUG_CATS = [
    ("درد و تب (مسکن)", "Analgesics & antipyretics", ["analges", "anti-inflammatory", "antipyretic", "non-steroidal"]),
    ("آنتی‌بیوتیک", "Antibacterials", ["antibacterial", "antibiotic"]),
    ("ضدویروس", "Antivirals", ["antiviral"]),
    ("ضدقارچ", "Antifungals", ["antifungal"]),
    ("انگل‌کش", "Antiparasitics", ["antiparasitic", "anthelmintic", "antimalarial"]),
    ("قلب و فشار خون", "Cardiovascular", ["angiotensin", "beta block", "calcium channel", "diuretic", "cardiac", "antiarrhyth", "antihypertensive", "vasodilat", "statin", "lipid"]),
    ("لختگی خون", "Anticoagulants & antiplatelets", ["anticoagul", "antiplatelet", "thrombolytic", "factor xa"]),
    ("دیابت", "Antidiabetics", ["hypoglycemic", "insulin", "biguanide", "sulfonylurea", "gliptin", "glp-1"]),
    ("هورمون و تیروئید", "Hormones", ["hormone", "thyroid", "corticosteroid", "steroid", "estrogen", "testosterone"]),
    ("گوارش", "Gastrointestinal", ["proton pump", "antacid", "antiemetic", "laxative", "antidiarrheal", "h2 block"]),
    ("تنفسی و آلرژی", "Respiratory & allergy", ["bronchodilat", "corticosteroid inhal", "antihistamine", "leukotriene", "decongestant"]),
    ("اعصاب و روان", "Nervous system & psychiatric", ["antidepress", "antipsychotic", "anxiolytic", "sedative", "anticonvuls", "antiepileptic", "dopamine", "serotonin", "opioid", "cns"]),
    ("بی‌حسی", "Anesthetics", ["anesthetic", "anaesthetic"]),
    ("ایمنی و سرطان", "Immunology & oncology", ["immunosuppress", "kinase inhibitor", "antineoplastic", "checkpoint", "monoclonal", "immunomodulat"]),
    ("واکسن", "Vaccines", ["vaccine", "toxoid"]),
    ("مکمل و ویتامین", "Vitamins & supplements", ["vitamin", "mineral", "iron", "calcium", "supplement"]),
    ("چشم و گوش", "Eye & ear", ["ophthalmic", "otic", "miotic", "mydriatic"]),
    ("پوست", "Dermatological", ["dermat", "topical anti-acne", "keratolytic", "emollient"]),
    ("ادراری و تناسلی", "Urological & gynecological", ["urinary", "urologic", "contraceptive", "vaginal", "prostate"]),
]


CAT_KW = [
    ("گیاه", "herbal medicine"), ("آنتی‌بیوتیک", "antibiotic"), ("مسکن", "painkiller / NSAID"),
    ("ضدافسردگی", "antidepressant"), ("افسردگی", "antidepressant"), ("بتابلاکر", "beta-blocker"),
    ("دیابت", "antidiabetic"), ("چربی", "lipid-lowering"), ("اسید معده", "stomach acid reducer"),
    ("فشار خون", "antihypertensive"), ("روان‌پریشی", "antipsychotic"), ("ایمنی", "immunosuppressant"),
    ("تشنج", "antiepileptic"), ("آنتی‌هیستامین", "antihistamine"), ("مکمل", "supplement"),
    ("آنژین", "antianginal"), ("اضطراب", "anxiolytic"), ("استخوان", "bone / osteoporosis"),
    ("ملین", "laxative"), ("پروستات", "prostate"), ("نعوظ", "erectile dysfunction"),
    ("ضدپلاکت", "antiplatelet"), ("انعقاد", "anticoagulant"), ("تیروئید", "thyroid"),
    ("خواب", "sleep"), ("چشم", "eye drop"), ("حساسیت", "allergy"), ("قارچ", "antifungal"),
    ("ویروس", "antiviral"), ("تب", "antipyretic"), ("سرفه", "cough"), ("هورمون", "hormone"),
    ("ضد درد", "analgesic"), ("کاهنده", "lowering agent"), ("رقیق", "blood thinner"),
    ("ضد", "anti-"),
]


def cat_en(fa_cat: str) -> str:
    if fa_cat in DRUG_CATS_EN:
        return DRUG_CATS_EN[fa_cat]
    for k, en in CAT_KW:
        if k in (fa_cat or ""):
            base = DRUG_CATS_EN.get(en, en)
            extra = fa_cat[fa_cat.index(k) + len(k):].strip(" ()‌")
            return base + ((" (" + extra + ")") if extra and extra.isascii() else "")
    return fa_cat or "medication"


DRUG_CATS_EN = {
    "درد و تب (مسکن)": "Analgesics & antipyretics", "آنتی‌بیوتیک": "Antibacterials",
    "ضدویروس": "Antivirals", "ضدقارچ": "Antifungals", "انگل‌کش": "Antiparasitics",
    "قلب و فشار خون": "Cardiovascular", "لختگی خون": "Anticoagulants & antiplatelets",
    "دیابت": "Antidiabetics", "هورمون و تیروئید": "Hormones", "گوارش": "Gastrointestinal",
    "تنفسی و آلرژی": "Respiratory & allergy", "اعصاب و روان": "Nervous system & psychiatric",
    "بی‌حسی": "Anesthetics", "ایمنی و سرطان": "Immunology & oncology", "واکسن": "Vaccines",
    "مکمل و ویتامین": "Vitamins & supplements", "چشم و گوش": "Eye & ear",
    "پوست": "Dermatological", "ادراری و تناسلی": "Urological & gynecological", "سایر": "Other",
}


def classify_drug(class_list) -> str:
    """Map a pharm-class list to a farsi category name."""
    hay = " ".join(class_list or []).lower()
    for fa, _en, keys in DRUG_CATS:
        if any(k in hay for k in keys):
            return fa
    return "سایر"


def drug_categories() -> list:
    return [{"fa": fa, "en": en} for fa, en, _k in DRUG_CATS] + [{"fa": "سایر", "en": "Other"}]


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


# ---------- unified paged browsing over every bank ----------

_UNIFIED_CACHE: list | None = None


def _build_unified() -> list:
    """One merged, deduplicated, alphabetical list over all disease banks."""
    global _UNIFIED_CACHE
    if _UNIFIED_CACHE is not None:
        return _UNIFIED_CACHE
    seen: dict[str, dict] = {}
    import medical_catalog as _mc
    _mc._load()
    for c in (_mc._DATA.get("conditions") or []):
        key = normalize(c.get("name", ""))
        code = c.get("icd10", "")
        ch = icd_chapter(code)
        seen[key] = {"name": c.get("name", ""), "fa": fa_disease_full(icd=code),
                     "code": code, "src": "icd10",
                     "ch": ch.get("key", ""), "ch_fa": ch.get("fa", ""), "ch_en": ch.get("en", ""),
                     "cat": code[:3] if len(code) >= 4 else ""}
    for d in _load_doid():
        key = normalize(d.get("name", ""))
        if key not in seen:
            code = d.get("icd", "")
            ch = icd_chapter(code) if code else {}
            seen[key] = {"name": d.get("name", ""), "code": "DOID:" + d.get("doid", ""),
                         "src": "doid", "def": d.get("def", ""),
                         "fa": fa_disease_full(en=d.get("name", ""), doid=d.get("doid", ""), mesh=d.get("mesh", "")),
                         "ch": ch.get("key", ""), "ch_fa": ch.get("fa", ""), "ch_en": ch.get("en", ""),
                         "cat": code[:3] if len(code) >= 4 else ""}
    for qid, e in _load_wiki().items():
        key = normalize(e.get("en", ""))
        row = seen.get(key)
        if row is None:
            wcode = e.get("icd", "")
            wch = icd_chapter(wcode) if wcode else {}
            row = seen[key] = {"name": e.get("en", ""), "fa": e.get("fa", ""),
                               "code": wcode, "src": "wiki",
                               "ch": wch.get("key", ""), "ch_fa": wch.get("fa", ""), "ch_en": wch.get("en", ""),
                               "cat": wcode[:3] if len(wcode) >= 4 else ""}
        if e.get("fa") and not row.get("fa"):
            row["fa"] = e["fa"]
        if e.get("sym") and not row.get("sym"):
            row["sym"] = e["sym"][:10]
        if e.get("drug") and not row.get("drug"):
            row["drug"] = e["drug"][:10]
        if e.get("icd") and not row.get("code"):
            row["code"] = e["icd"]
    for d in get_all_diseases():
        key = normalize(d.get("name", ""))
        if key not in seen:
            seen[key] = {"name": d.get("name", ""), "fa": d.get("fa", ""), "code": "",
                         "src": "engine", "sym": [s.get("name") for s in (d.get("symptoms") or [])][:8]}
    # icd -> farsi crosswalk from the DOID/wiki rows (real data, no machine guessing)
    xwalk: dict[str, str] = {}
    for r in seen.values():
        code = str(r.get("code", ""))
        if r.get("fa") and code and ":" not in code and "-" not in code and len(code) >= 3:
            xwalk.setdefault(code[:3].upper(), r["fa"])
            xwalk.setdefault(code.upper(), r["fa"])
    for r in seen.values():
        if not r.get("fa"):
            code = str(r.get("code", "")).upper()
            if code in xwalk:
                r["fa"] = xwalk[code]
            elif len(code) >= 3 and code[:3] in xwalk:
                r["fa"] = xwalk[code[:3]]
    # category-level inheritance: ICD subcodes (E11.x, J45.x ...) inherit the
    # definition/symptoms of a sibling that has real data (DOID/wiki/engine)
    cat_best: dict[str, dict] = {}
    for r in seen.values():
        c = r.get("cat", "")
        if not c:
            continue
        b = cat_best.setdefault(c, {"def": "", "sym": [], "drug": []})
        if r.get("def") and not b["def"]:
            b["def"] = r["def"]
        for s in r.get("sym") or []:
            if s not in b["sym"] and len(b["sym"]) < 10:
                b["sym"].append(s)
        for d in r.get("drug") or []:
            if d not in b["drug"] and len(b["drug"]) < 8:
                b["drug"].append(d)
    inherited = 0
    for r in seen.values():
        b = cat_best.get(r.get("cat", "") or "")
        if not b:
            continue
        if not r.get("def") and b["def"]:
            r["def"] = b["def"]
            inherited += 1
        if not r.get("sym") and b["sym"]:
            r["sym"] = b["sym"]
        if not r.get("drug") and b["drug"]:
            r["drug"] = b["drug"]

    # entries with no definition, no symptoms and no treatments get an
    # auto explanation from their title family (bilingual, honest)
    for r in seen.values():
        if not (r.get("def") or r.get("sym") or r.get("drug")):
            ex = explain_disease_entry(r.get("name", ""), r.get("code", ""),
                                       r.get("ch_en", ""), r.get("ch_fa", ""))
            r["note_en"] = ex["note_en"]
            r["note_fa"] = ex["note_fa"]
            r["nsym_en"] = ex["sym_en"]
            r["nsym_fa"] = ex["sym_fa"]
    out = list(seen.values())
    out.sort(key=lambda r: (r.get("name") or "").lower())
    _UNIFIED_CACHE = out
    return out


def browse_diseases(src: str = "all", page: int = 1, per: int = 40, q: str = "",
                    chapter: str = "", cat: str = "") -> dict:
    rows = _build_unified()
    if src and src != "all":
        rows = [r for r in rows if r.get("src") == src]
    if chapter:
        rows = [r for r in rows if r.get("ch") == chapter or (chapter == "other" and not r.get("ch"))]
    if cat:
        rows = [r for r in rows if r.get("cat", "").upper() == cat.upper()]
    if q:
        nq = normalize(q)
        rows = [r for r in rows if nq in normalize(r.get("name", "")) or nq in normalize(r.get("fa", ""))]
    total = len(rows)
    pages = max(1, (total + per - 1) // per)
    page = max(1, min(page, pages))
    return {"total": total, "page": page, "pages": pages, "per": per,
            "rows": rows[(page - 1) * per: page * per]}


def disease_levels(chapter: str = "") -> dict:
    """Chapters (or categories inside a chapter) with counts, for the level dropdowns."""
    rows = _build_unified()
    if chapter:
        cnt: dict[str, int] = {}
        for r in rows:
            if r.get("ch") == chapter and r.get("cat"):
                cnt[r["cat"]] = cnt.get(r["cat"], 0) + 1
        cats = [{"code": c, "count": n} for c, n in sorted(cnt.items())]
        return {"cats": cats}
    ch_cnt: dict[str, int] = {}
    for r in rows:
        k = r.get("ch") or "other"
        ch_cnt[k] = ch_cnt.get(k, 0) + 1
    out = []
    for _rng, en, fa in ICD_CHAPTERS:
        if ch_cnt.get(_rng):
            out.append({"key": _rng, "en": en, "fa": fa, "count": ch_cnt[_rng]})
    if ch_cnt.get("other"):
        out.append({"key": "other", "en": "Uncategorized", "fa": "دسته‌بندی نشده", "count": ch_cnt["other"]})
    out.sort(key=lambda x: -x["count"])
    return {"chapters": out}


def browse_fda_drugs(page: int = 1, per: int = 40, q: str = "", cat: str = "") -> dict:
    rows = _load_fda()
    if cat:
        rows = [r for r in rows if r.get("cat", "سایر") == cat]
    if q:
        nq = normalize(q)
        rows = [r for r in rows if nq in normalize(r.get("g", ""))]
    total = len(rows)
    pages = max(1, (total + per - 1) // per)
    page = max(1, min(page, pages))
    return {"total": total, "page": page, "pages": pages, "per": per,
            "rows": rows[(page - 1) * per: page * per]}


def drug_levels() -> list:
    """Drug category counts over the FDA bank."""
    rows = _load_fda()
    cnt: dict[str, int] = {}
    for r in rows:
        cnt[r.get("cat", "سایر")] = cnt.get(r.get("cat", "سایر"), 0) + 1
    order = [c["fa"] for c in drug_categories()]
    out = [{"fa": c, "count": cnt.get(c, 0)} for c in order if cnt.get(c)]
    return out


# ---------- auto explanations for entries with no description ----------

import re as _re

DISEASE_FAMILY_PATTERNS = [
    (_re.compile(r"abnormal cytological finding", _re.I),
     "A LAB RESULT code, not a disease: the cytology smear taken from the named organ/site showed abnormal cells under the microscope. By itself it has no symptoms; the sample needs a doctor's review, often with repeat sampling, imaging or a biopsy to find the cause (inflammation, infection, benign growth or, less often, a tumor).",
     "کدِ یک «نتیجه‌ی آزمایش» است، نه یک بیماری: در نمونه‌ی سیتولوژی گرفته‌شده از اندام/ناحیه‌ی ذکرشده، سلول‌های غیرطبیعی زیر میکروسکوپ دیده شده است. خودش علامتی ندارد؛ نمونه باید توسط پزشک بررسی شود و معمولاً تکرار آزمایش، تصویربرداری یا بیوپسی برای یافتن علت (التهاب، عفونت، توده‌ی خوش‌خیم یا به‌ندرت تومور) لازم می‌شود.",
     "none by itself — follow-up tests decide", "خودش علامت ندارد — آزمایش‌های تکمیلی مشخص می‌کنند"),
    (_re.compile(r"abnormal (radiological|ultrasound|imaging|mri|ct|x-?ray).*finding|abnormal finding.*(imaging|radiolog)", _re.I),
     "An IMAGING RESULT code: something unusual was seen on a scan (ultrasound/CT/MRI/X-ray). It is a finding, not a diagnosis. Common causes are benign (cysts, calcification, normal variants) but a doctor should compare it with your symptoms and sometimes repeat or further image it.",
     "کد «نتیجه‌ی تصویربرداری» است: در سونوگرافی/سی‌تی/ام‌آر‌ی/رادیوگرافی نکته‌ی غیرمعمولی دیده شده. این یک یافته است نه تشخیص قطعی. علل شایع خوش‌خیم‌اند (کیست، کلسیفیکاسیون، تنوع طبیعی) اما پزشک باید آن را با علائم شما تطبیق دهد و گاهی تصویربرداری تکراری یا تکمیلی بدهد.",
     "none by itself", "خودش علامت ندارد"),
    (_re.compile(r"abnormal finding", _re.I),
     "A LAB/EXAM FINDING code: something outside the normal range showed up in a specimen or examination. It is a result, not a disease by itself. The meaning depends completely on which test and how abnormal — a doctor interprets it together with your symptoms.",
     "کد «یافته‌ی آزمایش/معاینه» است: موردی خارج از بازه‌ی طبیعی در نمونه یا بررسی دیده شده. این یک نتیجه است، نه بیماری مستقل. معنای آن کاملاً به نوع آزمایش و میزان انحراف بستگی دارد و پزشک آن را همراه علائم شما تفسیر می‌کند.",
     "depends on the underlying cause", "بسته به علت زمینه‌ای"),
    (_re.compile(r"personal history of", _re.I),
     "A HISTORY code: it records that you had this condition in the past. It matters for future care (risk of recurrence, follow-up, medication choices) but it is not an active illness right now.",
     "کد «سابقه‌ی شخصی» است: ثبت می‌کند که در گذشته این مشکل را داشته‌ای. برای مراقبت آینده (خطر عود، پیگیری، انتخاب دارو) مهم است اما الان یک بیماری فعال نیست.",
     "no current symptoms required", "لازم نیست علامت فعلی داشته باشد"),
    (_re.compile(r"family history of", _re.I),
     "A FAMILY HISTORY code: a close relative had this condition. It does not mean you have it; it usually raises attention so screening can start earlier.",
     "کد «سابقه‌ی خانوادگی» است: یکی از بستگان این مشکل را داشته. به این معنا نیست که شما آن را دارید؛ معمولاً فقط یعنی غربالگری زودتر و دقیق‌تری توصیه می‌شود.",
     "none — it is a risk marker", "هیچ — فقط نشانگر ریسک است"),
    (_re.compile(r"encounter for (.*screening|screening)", _re.I),
     "A SCREENING VISIT code: the visit happened to check for a disease before any symptoms. Screening is preventive care; the result decides the next step.",
     "کد «ویزیت غربالگری» است: مراجعه برای بررسی یک بیماری قبل از بروز علامت انجام شده. غربالگری مراقبت پیشگیرانه است؛ نتیجه‌ی آن قدم بعدی را مشخص می‌کند.",
     "none — preventive check", "هیچ — بررسی پیشگیرانه"),
    (_re.compile(r"encounter for (vaccination|immunization)", _re.I),
     "A VACCINATION VISIT code: the visit was for receiving a vaccine. Expected effects are a sore arm or mild fever for a day or two.",
     "کد «ویزیت واکسیناسیون» است: مراجعه برای تزریق واکسن انجام شده. اثرات مورد انتظار: درد بازو یا تب خفیف برای یک دو روز.",
     "sore arm, mild fever (normal)", "درد بازو، تب خفیف (طبیعی)"),
    (_re.compile(r"encounter for|follow-?up|aftercare|routine", _re.I),
     "An ADMINISTRATIVE VISIT code: a check-up, follow-up or aftercare contact. It documents the reason for the visit, not a new disease.",
     "کد «ویزیت اداری» است: چکاپ، پیگیری یا مراقبت بعدی. فقط دلیل مراجعه را ثبت می‌کند، نه یک بیماری جدید.",
     "none by itself", "خودش علامت ندارد"),
    (_re.compile(r"suspected|rule out|probable", _re.I),
     "A 'SUSPECTED' code: this condition was being investigated as a possibility. It is not a confirmed diagnosis.",
     "کد «مشکوک» است: این حالت به‌عنوان یک احتمال بررسی شده. تشخیص قطعی نیست.",
     "depends on the final diagnosis", "بسته به تشخیص نهایی"),
    (_re.compile(r"sequela|late effect", _re.I),
     "A SEQUELA code: a late, lasting effect of a previous disease or injury (for example weakness after a stroke).",
     "کد «عوارض دیررس» است: اثر باقی‌مانده‌ی یک بیماری یا آسیب قبلی (مثلاً ضعف بعد از سکته).",
     "varies with the original condition", "بسته به بیماری اولیه"),
    (_re.compile(r"(unspecified|other specified|not otherwise)", _re.I),
     "An UNSPECIFIED variant of this condition: the diagnosis was not narrowed down further. The symptoms and care follow the parent condition.",
     "نوع «مشخص‌نشده»ی این بیماری: تشخیص دقیق‌تر از این سطح ثبت نشده. علائم و درمان تابع همان بیماری اصلی است.",
     "same as the parent condition", "مثل بیماری اصلی"),
    (_re.compile(r"(neoplasm|carcinoma|tumor|tumour|lymphoma|leukemia|melanoma|sarcoma|adenoma|metasta|cancer)", _re.I),
     "A CANCER-RELATED entry. General signs that push people to get checked: unexplained weight loss, night sweats, persistent fatigue, a lump, bleeding or pain in the affected area. Diagnosis needs imaging and tissue sampling; treatment is planned by an oncologist.",
     "مورد مرتبط با «بدخیمی/تومور». نشانه‌های عمومی که فرد را وادار به بررسی می‌کند: کاهش وزن بی‌دلیل، عرق شبانه، خستگی مداوم، توده، خونریزی یا درد در ناحیه‌ی درگیر. تشخیص نیازمند تصویربرداری و نمونه‌برداری است و درمان توسط متخصص انکولوژی برنامه‌ریزی می‌شود.",
     "weight loss, night sweats, fatigue, lump, local pain/bleeding",
     "کاهش وزن، عرق شبانه، خستگی، توده، درد/خونریزی موضعی"),
    (_re.compile(r"fracture", _re.I),
     "A FRACTURE entry: a broken bone, usually from trauma or a fall (in osteoporosis even from minor force). Typical signs: pain, swelling, bruising, deformity and inability to bear weight. Needs imaging and orthopedic care.",
     "مورد «شکستگی استخوان»: معمولاً در اثر ضربه یا زمین‌خوردن (در پوکی استخوان حتی با ضربه‌ی خفیف). نشانه‌های معمول: درد، تورم، کبودی، تغییر شکل و ناتوانی در تحمل وزن. نیاز به تصویربرداری و مراقبت ارتوپدی دارد.",
     "pain, swelling, deformity, can't bear weight", "درد، تورم، تغییر شکل، عدم تحمل وزن"),
    (_re.compile(r"(poisoning|toxic effect|overdose)", _re.I),
     "A POISONING/TOXICITY entry: harm from a drug, chemical or substance. Depending on the substance it can be an emergency — call 115/112 with confusion, breathing trouble or loss of consciousness.",
     "مورد «مسمومیت»: آسیب ناشی از دارو، ماده‌ی شیمیایی یا مواد. بسته به ماده ممکن است اورژانسی باشد — با گیجی، تنگی نفس یا کاهش هوشیاری با ۱۱۵/۱۱۲ تماس بگیر.",
     "nausea, vomiting, confusion, breathing changes", "تهوع، استفراغ، گیجی، تغییر تنفس"),
    (_re.compile(r"burn|corrosion", _re.I),
     "A BURN/CORROSIVE injury entry. Depth and size decide severity; large, deep, face/hand/genital or chemical burns need emergency care.",
     "مورد «سوختگی/اسید». عمق و وسعت، شدت را تعیین می‌کند؛ سوختگی وسیع، عمیق، صورت/دست/ناحیه‌ی تناسلی یا شیمیایی نیاز به مراقبت اورژانسی دارد.",
     "pain, redness, blisters, skin loss", "درد، قرمزی، تاول، از دست رفتن پوست"),
    (_re.compile(r"(pregnan|delivery|birth|puerperium|gravid|obstetric)", _re.I),
     "A PREGNANCY/CHILDBIRTH-related entry. Care is shared between the mother-care team; warning signs during pregnancy are bleeding, severe headache, swelling and reduced fetal movement.",
     "مورد مرتبط با «بارداری/زایمان». مراقبت با تیم مراقبت مادر است؛ علائم خطر در بارداری: خونریزی، سردرد شدید، تورم و کاهش حرکات جنین.",
     "context: pregnancy care", "در چارچوب مراقبت بارداری"),
    (_re.compile(r"(injury|laceration|wound|contusion|sprain|strain|dislocation)", _re.I),
     "An INJURY entry: physical damage from trauma. Typical signs are pain, swelling, bruising and limited movement; care depends on the injured part and severity.",
     "مورد «آسیب/ضربه»: آسیب فیزیکی ناشی از تروما. نشانه‌های معمول: درد، تورم، کبودی و محدودیت حرکت؛ مراقبت بسته به ناحیه و شدت است.",
     "pain, swelling, bruising, limited movement", "درد، تورم، کبودی، محدودیت حرکت"),
    (_re.compile(r"congenital|malformation|birth defect", _re.I),
     "A CONGENITAL entry: a condition present from birth. Some are found on newborn screening, others later; many need specialist follow-up.",
     "مورد «مادرزادی»: حالتی که از بدو تولد وجود دارد. بعضی در غربالگری نوزادی و بعضی دیرتر پیدا می‌شوند؛ بسیاری نیاز به پیگیری تخصصی دارند.",
     "varies by the specific condition", "بسته به نوع آن"),
]


def explain_disease_entry(name: str, code: str = "", chapter_en: str = "", chapter_fa: str = "") -> dict:
    """Bilingual explanation + 'symptoms' line for entries with no recorded data."""
    n = name or ""
    for pat, en, fa, sym_en, sym_fa in DISEASE_FAMILY_PATTERNS:
        if pat.search(n):
            return {"note_en": en, "note_fa": fa, "sym_en": sym_en, "sym_fa": sym_fa, "family": True}
    # توضیح عمومی مبتنی بر فصل
    if chapter_en:
        return {"note_en": f"A condition classified in the ICD-10 chapter '{chapter_en}'. No open-data description or symptom list is recorded for this specific code yet; if you have symptoms, the Symptoms module can rank likely causes.",
                "note_fa": f"حالتی طبقه‌بندی‌شده در فصل «{chapter_fa or chapter_en}»ی ICD-10 است. هنوز توضیح یا فهرست علامت برای این کد خاص در داده‌های آزاد ثبت نشده؛ اگر علامت داری، ماژول «علائم» می‌تواند احتمالات را رتبه‌بندی کند.",
                "sym_en": "not recorded in open data", "sym_fa": "در داده‌های آزاد ثبت نشده", "family": False}
    return {"note_en": "No open-data description recorded for this entry yet.",
            "note_fa": "هنوز توضیحی برای این مورد در داده‌های آزاد ثبت نشده است.",
            "sym_en": "not recorded", "sym_fa": "ثبت نشده", "family": False}


# ---------- symptom -> diseases index (wiki + engine data) ----------

_SYM_DIS_CACHE: dict | None = None


def _sym_index() -> dict:
    """symptom name -> {en, fa, diseases:[{en, fa}]} from wikidata + engine."""
    global _SYM_DIS_CACHE
    if _SYM_DIS_CACHE is not None:
        return _SYM_DIS_CACHE
    from medical_engine import SYMPTOM_NAMES_FA, SYMPTOM_NAMES_EN
    from common_2077 import normalize
    idx: dict[str, dict] = {}
    for qid, e in _load_wiki().items():
        for s in e.get("sym") or []:
            k = normalize(s)
            if not k:
                continue
            ent = idx.setdefault(k, {"en": s, "fa": "", "diseases": []})
            if len(ent["diseases"]) < 15:
                ent["diseases"].append({"en": e.get("en", ""), "fa": e.get("fa", "")})
    # فارسی‌سازی نام علائم wiki از طریق دیکشنری موتور (en -> fa)
    rev_en = {}
    for sid, en in SYMPTOM_NAMES_EN.items():
        rev_en[normalize(en)] = SYMPTOM_NAMES_FA.get(sid, "")
    for k, ent in idx.items():
        fa = rev_en.get(k, "")
        if fa:
            ent["fa"] = fa
        else:
            for sid, fa_name in SYMPTOM_NAMES_FA.items():
                if normalize(fa_name) == k:
                    ent["fa"] = fa_name
                    break
    _SYM_DIS_CACHE = idx
    return idx


def search_symptom_diseases(query: str, limit: int = 25) -> list[dict]:
    """Find symptoms by name (fa/en) and return their diseases."""
    q = normalize(query)
    out = []
    for k, ent in _sym_index().items():
        if (q in k) or (q in normalize(ent.get("fa", ""))):
            out.append(ent)
            if len(out) >= limit:
                break
    return out


def symptom_index_count() -> int:
    return len(_sym_index())
