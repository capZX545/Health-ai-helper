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


def get_all_symptoms() -> list[dict]:
    """
    All symptoms with fa/en names and keywords.
    """
    from medical_engine import SYMPTOM_KEYWORDS, SYMPTOM_NAMES_FA, SYMPTOM_NAMES_EN, DISEASES
    out = []
    for sid in sorted(SYMPTOM_KEYWORDS.keys()):
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

    if _re.match(r"^[A-TV-Za-tv-z]\d{2}", q):
        seen = {r.get("icd10") for r in results}
        for r in search_by_code_prefix(q, limit):
            if r.get("icd10") not in seen:
                seen.add(r.get("icd10"))
                results.append(r)

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


def get_all_drugs() -> list[dict]:
    """
    All drugs with name, category, properties and interactions.
    """
    from drug_interaction import DRUGS, INTERACTIONS, SEV_FA
    from drugbank_connector import DRUG_DATABASE
    from drug_interaction import INTERACTIONS_EN as _INTER_EN
    fa = is_fa()
    drug_db_map = {k: v for k, v in DRUG_DATABASE.items()}
    out = []
    for d in DRUGS:
        did = d["id"]
        interactions = []
        for it in INTERACTIONS:
            if did in (it["a"], it["b"]):
                other_id = it["b"] if it["a"] == did else it["a"]
                other = next((x for x in DRUGS if x["id"] == other_id), None)
                interactions.append({
                    "other": other["fa"] if other and fa else (other["en"][0] if other else other_id),
                    "severity": it["sev"],
                    "severity_fa": SEV_FA()[it["sev"]],
                    "detail": it["fa"] if fa else (
                        _INTER_EN.get((it["a"], it["b"])) or _INTER_EN.get((it["b"], it["a"]))
                        or {"major": "Combining these two significantly increases the risk of serious side effects; use only with a doctor's supervision.",
                            "moderate": "Combined use may need dose adjustment or monitoring; ask your doctor or pharmacist.",
                            "minor": "Mild possible interaction; usually manageable."}.get(it["sev"], "Possible interaction — consult your doctor.")),
                })
        db_info = drug_db_map.get(did, {})
        out.append({
            "id": did,
            "fa": d["fa"][0] if d["fa"] else did,
            "en": d["en"][0] if d["en"] else did,
            "category": d["cat"],
            "category_en": cat_en(d["cat"]),
            **_drug_en_fields(db_info),
            "aliases_fa": d["fa"],
            "aliases_en": d["en"],
            "interactions": interactions,
            "atc": db_info.get("atc", ""),
            "class": db_info.get("class_fa", ""),
            "half_life": db_info.get("half_life", ""),
            "metabolism": db_info.get("metabolism", ""),
            "routes": db_info.get("routes", []),
            "pregnancy": db_info.get("pregnancy", ""),
            "contra": db_info.get("contra_fa", "") if fa else "",
            "notes": db_info.get("notes_fa", "") if fa else "",
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
            v = m.get("icd_fa", {}).get(code[:3], "")
        if v:
            return v
    if en:
        return m.get("disease_en_fa", {}).get(en.strip().lower(), "")
    return ""


def _norm_key(s: str) -> str:
    """Loose name key: lowercase letters and digits only."""
    return "".join(ch for ch in (s or "").lower() if ch.isalnum())


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
                    v += 1
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
    ("مدر", "diuretic"), ("برونکودیلاتور", "bronchodilator"), ("اسپری", "inhaler"),
    ("کورتون", "corticosteroid inhaler"), ("کورتیکواستروئید", "corticosteroid"),
    ("استنشاقی", "inhaled"), ("بینی", "nasal"), ("قلب", "cardiac"), ("خلق", "mood stabilizer"),
    ("نقرس", "gout"), ("میگرن", "migraine prophylaxis"), ("آسم", "asthma"),
    ("انسولین", "insulin"), ("بیولوژیک", "biologic"), ("وازودیلاتور", "vasodilator"),
    ("ضربان", "rate control"), ("بازکننده", "decongestant"), ("پیشگیری", "prophylaxis"),
    ("ضد", "anti-"),
]


ATC_L2_EN = {
    "A03": "functional gastrointestinal disorders", "A10": "antidiabetic",
    "B01": "antithrombotic", "B03": "antianemic", "C01": "cardiac therapy",
    "C03": "diuretic", "C10": "lipid-modifying", "G04": "urologicals",
    "H02": "corticosteroid", "H03": "thyroid therapy", "J01": "antibacterial",
    "L01": "antineoplastic", "M04": "antigout", "M05": "bone disease drugs",
    "N02": "analgesic/antipyretic", "N05": "psycholeptic", "N06": "psychoanaleptic",
    "R03": "respiratory (obstructive airway)",
}
ROUTES_EN = {"خوراکی": "oral", "زیرجلدی": "subcutaneous", "وریدی": "intravenous",
             "ورودی": "intravenous", "استنشاق": "inhaled", "موضعی": "topical", "بینی": "nasal"}


def _drug_en_fields(rec: dict) -> dict:
    """English versions of the persian drugbank-style fields (ATC-derived)."""
    out = {}
    atc = str(rec.get("atc", "") or "")
    cls_fa = str(rec.get("class_fa", "") or rec.get("class", "") or "")
    if atc:
        out["class_en"] = ATC_L2_EN.get(atc[:3], atc)
    elif cls_fa:
        out["class_en"] = cat_en(cls_fa)
    out["routes_en"] = [ROUTES_EN.get(r, r) for r in (rec.get("routes") or [])]
    p = str(rec.get("pregnancy", "") or "")
    out["pregnancy_en"] = (p[:1] if p[:1] in "ABCDX" else "") + (" category" if p[:1] in "ABCDX" else "")
    met = str(rec.get("metabolism", "") or "")
    if met and any("\u0600" <= ch <= "\u06ff" for ch in met):
        m2 = met
        for k, v in (("کبدی", "hepatic"), ("کلیوی", "renal"), ("بدون متابولیسم", "no metabolism, excreted unchanged"),
                     ("دفع", "excretion"), ("متابولیسم", "metabolism")):
            m2 = m2.replace(k, v)
        out["metabolism_en"] = m2
    return out


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
    words = [w for w in q.split() if len(w) > 2]
    out = []
    for d in _load_doid():
        hay = d["_hay"] + " " + d.get("icd", "").lower()
        if q in hay or (words and all(w in hay for w in words)):
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
    words = [w for w in q.split() if len(w) > 2]
    if not q:
        return []
    out = []
    for k, e in _load_wiki().items():
        _en, _fa = normalize(e.get("en", "")), normalize(e.get("fa", ""))
        _hay = _en + " " + _fa
        if ((q in _en or q in _fa
                or qe == str(e.get("icd", "")).strip().lower())
                or (words and all(w in _hay for w in words))):
            out.append({"qid": k, **e})
            if len(out) >= limit:
                break
    return out


def get_wiki_disease(en: str = "", icd: str = "", doid: str = "") -> dict | None:
    """Find the wiki entry (with symptoms/treatments) for a disease.

    Match priority: exact english name > ICD-10 category prefix (e.g. E11)
    > DOID. The ICD prefix only matches when the wiki entry's own ICD code
    starts with the same 3-character category (E11 vs E11, not E11 vs E23).
    """
    ne = normalize(en or "")
    code = (icd or "").strip().upper()
    cat = ""
    if code:
        c = code[0]
        digits = "".join(ch for ch in code[1:] if ch.isdigit())[:2]
        if c.isalpha() and len(digits) == 2:
            cat = c + digits
    dnum = str(doid or "").strip()
    best = None
    for k, e in _load_wiki().items():
        if ne and normalize(e.get("en", "")) == ne:
            return {"qid": k, **e}
        if cat:
            wc = str(e.get("icd", "")).strip().upper()
            if wc[:3] == cat and (e.get("sym") or e.get("drug")):
                if best is None:
                    best = {"qid": k, **e}
                elif ne and any(w in normalize(e.get("en", "")) for w in ne.split() if len(w) > 4):
                    best = {"qid": k, **e}
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
                         "omim": str(d.get("omim", "") or "").replace("MIM:", ""),
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
        if not r.get("sym"):
            _hl = _load_hpo_links()
            hs = _hl.get((r.get("name") or "").strip().lower())
            if not hs and _hl:
                _k = _norm_key(r.get("name") or "")
                if _k:
                    hs = _hl.get(_k)
                    if not hs and len(_k) > 12:
                        hs = _hl.get(_k[:24])
            if not hs and r.get("omim"):
                hs = _hl.get("omim" + str(r["omim"])) or _hl.get(_norm_key("OMIM:" + str(r["omim"])))
            if hs:
                r["sym"] = hs[:12]
        if not r.get("drug") and b["drug"]:
            r["drug"] = b["drug"]

    from synth_desc import synthesize_description as _synth
    for r in seen.values():
        if not (r.get("def") or r.get("sym") or r.get("drug")):
            fa_s, en_s = _synth(r.get("name", ""), r.get("code", ""), r.get("ch", ""))
            r["note_en"] = en_s
            r["note_fa"] = fa_s
            if not r.get("nsym_en"):
                r["nsym_en"] = "see the Symptoms module"
                r["nsym_fa"] = "ببینید ماژول علائم"
        elif not r.get("def") and (r.get("sym") or r.get("drug")):
            fa_s, en_s = _synth(r.get("name", ""), r.get("code", ""), r.get("ch", ""))
            if not r.get("note_en"):
                r["note_en"] = en_s
                r["note_fa"] = fa_s
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
    if chapter_en:
        return {"note_en": f"A condition classified in the ICD-10 chapter '{chapter_en}'. No open-data description or symptom list is recorded for this specific code yet; if you have symptoms, the Symptoms module can rank likely causes.",
                "note_fa": f"حالتی طبقه‌بندی‌شده در فصل «{chapter_fa or chapter_en}»ی ICD-10 است. هنوز توضیح یا فهرست علامت برای این کد خاص در داده‌های آزاد ثبت نشده؛ اگر علامت داری، ماژول «علائم» می‌تواند احتمالات را رتبه‌بندی کند.",
                "sym_en": "not recorded in open data", "sym_fa": "در داده‌های آزاد ثبت نشده", "family": False}
    from synth_desc import synthesize_description as _s2
    fa_s, en_s = _s2(name, code, "")
    return {"note_en": en_s, "note_fa": fa_s, "sym_en": "see the Symptoms module",
            "sym_fa": "ببینید ماژول علائم", "family": False}


_HPO_LINKS_CACHE: dict | None = None


def _load_hpo_links() -> dict:
    """disease name (lower) -> [symptom names] from official HPO annotations."""
    global _HPO_LINKS_CACHE
    if _HPO_LINKS_CACHE is None:
        import gzip
        import json as _json
        import os
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "disease_symptoms_hpo.json.gz")
        try:
            with gzip.open(path, "rt", encoding="utf-8") as f:
                _HPO_LINKS_CACHE = _json.load(f)
        except Exception as e:
            print("[knowledge_browser] HPO links not loaded:", e)
            _HPO_LINKS_CACHE = {}
    return _HPO_LINKS_CACHE


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
    from common_2077 import normalize as _n2
    _seen_dis = set()
    for dname, syms in _load_hpo_links().items():
        if dname.startswith("omim") or dname.startswith("orpha") or dname.startswith("decipher"):
            continue
        pretty = dname.strip()
        pk = _norm_key(pretty)
        if not pk or pk in _seen_dis or len(pretty) < 4:
            continue
        _seen_dis.add(pk)
        for s in syms[:14]:
            k = _n2(s)
            if not k:
                continue
            ent = idx.setdefault(k, {"en": s, "fa": "", "diseases": []})
            if len(ent["diseases"]) < 12 and {"en": pretty, "fa": ""} not in ent["diseases"]:
                ent["diseases"].append({"en": pretty, "fa": ""})

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


def symptom_checklist(limit: int = 240) -> list[dict]:
    """Engine symptoms first, then the most common HPO/wiki symptoms."""
    out = []
    seen = set()
    for s in get_all_symptoms():
        if s["id"] not in seen:
            seen.add(s["id"])
            out.append({"id": s["id"], "en": s["en"], "fa": s["fa"], "engine": True})
    idx = _sym_index()
    ranked = sorted(idx.items(), key=lambda kv: -len(kv[1]["diseases"]))
    for k, ent in ranked:
        if len(out) >= limit:
            break
        kk = _norm_key(ent["en"])
        if kk in seen or not ent.get("en") or len(ent["en"]) < 4:
            continue
        low = ent["en"].lower()
        if any(b in low for b in ("abnormality of", "abnormal ", "morphology", "shape", "size of",
                                  "position", "pigmentation", "ncg_", "increased circulating",
                                  "decreased circulating", "abnormal level")):
            continue
        seen.add(kk)
        out.append({"id": "hpo_" + kk[:24], "en": ent["en"], "fa": ent.get("fa", ""),
                    "engine": False, "count": len(ent["diseases"])})
    return out


def match_diseases_by_symptoms(sym_names: list, limit: int = 12) -> list:
    """Rank bank diseases by how many of the ticked symptoms they carry."""
    from common_2077 import normalize
    want = {normalize(s) for s in sym_names if s}
    if not want:
        return []
    scored = []
    for r in _build_unified():
        syms = r.get("sym") or []
        if not syms:
            continue
        keys = {normalize(s) for s in syms}
        hit = want & keys
        if not hit:
            continue
        cov = len(hit) / max(1, len(keys))
        strength = len(hit) / max(1, len(want))
        score = round(strength * 0.65 + cov * 0.35, 3)
        if score < 0.15:
            continue
        scored.append({"name": r.get("name", ""), "fa": r.get("fa", ""), "src": r.get("src", ""),
                       "code": r.get("code", ""), "score": score, "hits": len(hit),
                       "matched": [s for s in syms if normalize(s) in hit][:8], "total_syms": len(syms)})
    scored.sort(key=lambda x: -x["score"])
    return scored[:limit]


_TREATMENT_FA = {
    "infection": "آنتی‌بیوتیک (با تجویز پزشک)", "viral": "درمان حمایتی و استراحت",
    "bacterial": "آنتی‌بیوتیک", "fungal": "ضدقارچ", "parasitic": "انگل‌کش",
    "cancer": "جراحی، شیمی‌درمانی یا پرتودرمانی (توسط متخصص انکولوژی)",
    "fracture": "گچ‌گیری یا جراحی ارتوپدی", "injury": "استراحت، سرما، بالا نگه‌داشتن و گچ‌بندی در صورت نیاز",
    "burn": "خنک‌کردن با آب، پماد و پوشش استریل", "poisoning": "شست‌شو و مراقبت اورژانسی فوری",
    "anemia": "مکمل آهن یا ویتامین B12 بر اساس علت", "diabetes": "رژیم، ورزش، قرص یا انسولین",
    "hypertension": "تغییر سبک زندگی + داروی ضدفشار خون", "asthma": "اسپری برونکودیلاتور و کورتون استنشاقی",
    "depression": "روان‌درمانی + داروهای ضدافسردگی", "anxiety": "شناخت‌درمانی و دارو در موارد شدید",
    "thyroid": "هورمون درمانی (لووتیروکسین) یا داروی ضددریوی",
    "allergy": "اجتناب از عامل حساسیت + آنتی‌هیستامین",
    "migraine": "مسکن حمله + داروی پیشگیری در تکرار زیاد",
    "pregnancy": "مراقبت زنان و ویزیت منظم",
    "surgery": "جراحی", "congenital": "پیگیری تخصصی و جراحی اصلاحی در صورت نیاز",
}
_TREATMENT_EN = {
    "infection": "antibiotics (as prescribed)", "viral": "supportive care and rest",
    "bacterial": "antibiotics", "fungal": "antifungals", "parasitic": "antiparasitics",
    "cancer": "surgery, chemotherapy or radiotherapy (oncologist-led)",
    "fracture": "casting or orthopedic surgery", "injury": "rest, ice, elevation, immobilization if needed",
    "burn": "cool with water, ointment and sterile dressing", "poisoning": "emergency decontamination and care",
    "anemia": "iron or B12 supplementation based on cause", "diabetes": "diet, exercise, tablets or insulin",
    "hypertension": "lifestyle change + antihypertensive medication", "asthma": "bronchodilator and inhaled steroid inhalers",
    "depression": "psychotherapy + antidepressants", "anxiety": "CBT and medication if severe",
    "thyroid": "hormone therapy (levothyroxine) or antithyroid drugs",
    "allergy": "avoiding the trigger + antihistamines",
    "migraine": "attack painkillers + preventive drugs if frequent",
    "pregnancy": "obstetric care and regular visits",
    "surgery": "surgery", "congenital": "specialist follow-up and corrective surgery when needed",
}
_TREAT_KEYWORDS = [
    ("infection", ("infection", "abscess", "cellulitis", "sepsis", "pneumonia", "UTI", "pyelonephritis")),
    ("viral", ("viral", "influenza", "common cold", "COVID", "measles", "chickenpox", "herpes", "hepatitis A")),
    ("bacterial", ("bacterial", "strep", "staph", "tuberculosis", "boreliosis")),
    ("fungal", ("fungal", "candid", "tinea", "dermatophyt")),
    ("parasitic", ("parasitic", "malaria", "worm", "helminth", "protozo")),
    ("cancer", ("cancer", "carcinoma", "neoplasm", "malignant", "lymphoma", "leukemia", "melanoma", "sarcoma", "myeloma", "tumor")),
    ("fracture", ("fracture", "broken bone", "fissure of")),
    ("injury", ("injury", "laceration", "contusion", "sprain", "strain", "dislocation", "wound")),
    ("burn", ("burn", "corrosion", "scald")),
    ("poisoning", ("poisoning", "toxic", "overdose")),
    ("anemia", ("anemia", "anemia", "thalassemia", "iron-deficiency")),
    ("diabetes", ("diabetes", "hyperglycemia", "glyc")),
    ("hypertension", ("hypertension", "high blood pressure")),
    ("asthma", ("asthma", "COPD", "bronchitis", "airway")),
    ("depression", ("depression", "depressive", "dysthymia")),
    ("anxiety", ("anxiety", "panic", "phobia", "GAD")),
    ("thyroid", ("thyroid", "goiter", "hyperthyroid", "hypothyroid", "graves", "hashimoto")),
    ("allergy", ("allergy", "allergic", "rhinitis", "urticaria", "eczema", "atopic")),
    ("migraine", ("migraine", "headache")),
    ("pregnancy", ("pregnancy", "delivery", "birth", "obstetric", "labor", "gravid")),
    ("surgery", ("hernia", "appendicitis", "cholecystitis", "obstruction")),
    ("congenital", ("congenital", "malformation", "birth defect", "syndrome")),
]


def guess_treatment(name: str) -> tuple[str, str]:
    """Guess a treatment line (fa, en) from the disease's name."""
    low = (name or "").lower()
    for key, words in _TREAT_KEYWORDS:
        if any(w.lower() in low for w in words):
            return _TREATMENT_FA.get(key, "مشاوره با پزشک"), _TREATMENT_EN.get(key, "consult a doctor")
    return "درمان بر اساس تشخیص پزشک", "treatment as determined by a doctor"


def disease_profile(row: dict) -> dict:
    """Full bilingual profile of a disease row from the unified bank."""
    from i18n import is_fa
    name = row.get("name", "")
    fa_name = row.get("fa", "")
    treat_fa, treat_en = guess_treatment(name)
    syms = [str(s) for s in (row.get("sym") or [])][:12]
    drugs = [str(d) for d in (row.get("drug") or [])][:12]
    definition = row.get("def") or ""
    note_fa = row.get("note_fa", "")
    note_en = row.get("note_en", "")
    ch_fa = row.get("ch_fa", "")
    ch_en = row.get("ch_en", "")
    return {
        "name": name, "fa_name": fa_name, "code": row.get("code", ""),
        "about": definition or (note_fa if is_fa() else note_en) or "",
        "symptoms": syms,
        "signs_fa": row.get("nsym_fa", ""), "signs_en": row.get("nsym_en", ""),
        "drugs": drugs, "treat_fa": treat_fa, "treat_en": treat_en,
        "ch_fa": ch_fa, "ch_en": ch_en,
        "labs": row.get("labs", []),
    }


_ICD_ABOUT = {
    "E11": ("Type 2 diabetes: a chronic metabolic condition in which the body resists insulin or does not make enough of it, so blood sugar rises. Typical symptoms include thirst, frequent urination, fatigue and blurred vision; many cases have no symptoms for years. Managed with diet, exercise, tablets (metformin) and sometimes insulin.",
            "دیابت نوع ۲: بیماری مزمن متابولیک که در آن بدن به انسولین مقاوم می‌شود یا انسولین کافی تولید نمی‌کند و قند خون بالا می‌رود. علائم شایع: تشنگی، تکرر ادرار، خستگی و تار دید؛ بسیاری از موارد سال‌ها بدون علامت هستند. کنترل با رژیم، ورزش، قرص (متفورمین) و گاهی انسولین."),
    "E10": ("Type 1 diabetes: an autoimmune condition where the pancreas stops making insulin, usually starting in childhood or young adulthood. Symptoms come fast: thirst, weight loss, frequent urination, fatigue. Needs lifelong insulin.",
            "دیابت نوع ۱: بیماری خودایمنی که در آن پانکراس تولید انسولین را متوقف می‌کند، معمولاً از کودکی یا جوانی شروع می‌شود. علائم سریع ظاهر می‌شوند: تشنگی، کاهش وزن، تکرر ادرار، خستگی. نیاز به انسولین مادام‌العمر دارد."),
    "I10": ("Essential hypertension: persistently raised blood pressure without a single identifiable cause. Usually silent; found on measurement. Over time it raises the risk of heart attack, stroke and kidney disease. Managed with salt reduction, exercise, weight control and medication.",
            "فشار خون بالا (اساسی): افزایش مداوم فشار خون بدون علت واحد قابل‌شناسایی. معمولاً بی‌علامت است و در اندازه‌گیری کشف می‌شود. با گذشت زمان خطر سکته‌ی قلبی، مغزی و بیماری کلیه را بالا می‌برد. کنترل با کاهش نمک، ورزش، کنترل وزن و دارو."),
    "J45": ("Asthma: a chronic airway condition with episodes of wheeze, breathlessness, chest tightness and cough, often triggered by exercise, allergens or infections. Treated with reliever and preventer inhalers.",
            "آسم: بیماری مزمن راه‌های هوایی با حملات خس‌خس، تنگی نفس، فشار سینه و سرفه که اغلب با ورزش، آلرژن یا عفونت تحریک می‌شود. درمان با اسپری تسکین‌دهنده و پیشگیرانه."),
    "F32": ("Depressive episode: persistent low mood, loss of interest and energy, sleep and appetite changes for at least two weeks. Treated with psychotherapy and, when needed, antidepressants.",
            "اپیزود افسردگی: خلق پایین مداوم، بی‌علاقگی و کاهش انرژی، تغییر خواب و اشتها برای حداقل دو هفته. درمان با روان‌درمانی و در صورت نیاز ضدافسردگی‌ها."),
    "K29": ("Gastritis: inflammation of the stomach lining causing upper abdominal pain, nausea and bloating; often related to H. pylori infection, painkillers or alcohol.",
            "گاستریت: التهاب مخاط معده با درد فوقانی شکم، تهوع و نفخ؛ اغلب مرتبط با عفونت هلیکوباکتر، مسکن‌ها یا الکل."),
    "N39": ("Urinary tract infection: bacterial infection of the bladder or kidneys causing burning urination, frequency and pelvic pain; kidney involvement brings fever and flank pain. Treated with antibiotics.",
            "عفونت ادراری: عفونت باکتریایی مثانه یا کلیه با سوزش ادرار، تکرر و درد لگن؛ درگیری کلیه تب و درد پهلو می‌آورد. درمان با آنتی‌بیوتیک."),
    "M54": ("Dorsalgia (back pain): pain in the back, most often muscular or postural; most cases improve with movement, exercise and simple painkillers. Red flags are leg weakness, numbness or incontinence.",
            "درد کمر: درد ناحیه‌ی پشت که بیشتر عضلانی یا ناشی از وضعیت بدن است؛ اکثر موارد با حرکت، ورزش و مسکن ساده بهتر می‌شوند. علائم خطر: ضعف پا، بی‌حسی یا بی‌اختیاری."),
    "R51": ("Headache: pain in the head with many causes from tension and dehydration to migraine. Warning signs are sudden severe onset, fever with stiff neck, or neurological deficits.",
            "سردرد: درد سر با علل متعدد از تنش و کم‌آبی تا میگرن. علائم هشدار: شروع ناگهانی شدید، تب با سفتی گردن، یا اختلال عصبی."),
    "J06": ("Acute upper respiratory infection: the common cold and similar viral infections of nose, throat and sinuses with runny nose, sore throat and cough. Supportive care; antibiotics do not help.",
            "عفونت حاد تنفسی فوقانی: سرماخوردگی و عفونت‌های ویروسی مشابه بینی، گلو و سینوس با آبریزش، گلودرد و سرفه. درمان حمایتی؛ آنتی‌بیوتیک کمکی نمی‌کند."),
}


def icd_about(code: str) -> tuple[str, str] | None:
    """(en, fa) standard description for a well-known ICD category."""
    c = (code or "").strip().upper()
    if len(c) >= 3:
        return _ICD_ABOUT.get(c[:3])
    return None


_CHAPTER_CLINICAL = {
    "A00-B99": ("An infectious disease caused by bacteria, viruses, fungi or parasites entering the body. General signs are fever, fatigue and local symptoms depending on the affected organ (cough, diarrhea, rash or pain). Most bacterial infections respond to antibiotics; viral ones need supportive care. Serious signs are high fever, confusion, spreading redness or breathing difficulty.",
                "بیماری عفونی ناشی از ورود باکتری، ویروس، قارچ یا انگل به بدن. نشانه‌های عمومی تب، خستگی و علائم موضعی بسته به اندام درگیر است (سرفه، اسهال، جوش یا درد). بیشتر عفونت‌های باکتریایی با آنتی‌بیوتیک بهتر می‌شوند و ویروسی‌ها نیاز به درمان حمایتی دارند. علائم جدی: تب بالا، گیجی، قرمزی گسترده یا تنگی نفس."),
    "C00-D49": ("A malignant tumor: uncontrolled growth of abnormal cells that can invade nearby tissue and spread. Warning signs include unexplained weight loss, night sweats, persistent fatigue, a lump, unusual bleeding or persistent pain. Diagnosis needs imaging and biopsy; treatment combines surgery, chemotherapy and radiotherapy planned by an oncologist.",
                "تومور بدخیم: رشد کنترل‌نشده‌ی سلول‌های غیرطبیعی که می‌تواند به بافت اطراف نفوذ و منتشر شود. علائم هشدار: کاهش وزن بی‌دلیل، عرق شبانه، خستگی مداوم، توده، خونریزی غیرطبیعی یا درد مداوم. تشخیص نیاز به تصویربرداری و بیوپسی دارد؛ درمان ترکیبی از جراحی، شیمی‌درمانی و پرتودرمانی با برنامه‌ی متخصص انکولوژی است."),
    "D50-D89": ("A disorder of the blood or immune system such as anemia, low/high white cells, clotting problems or immune dysfunction. Typical signs are fatigue and pallor (anemia), recurrent infections (immune problems), easy bruising or bleeding (clotting). Blood tests identify the type; treatment ranges from supplements to specialized drugs.",
                "اختلال خون یا سیستم ایمنی مانند کم‌خونی، کم/زیاد شدن گویچه‌های سفید، مشکلات انعقاد یا اختلال ایمنی. نشانه‌های معمول: خستگی و رنگ‌پریدی (کم‌خونی)، عفونت‌های مکرر (مشکل ایمنی)، کبودی یا خونریزی آسان (انعقاد). آزمایش خون نوع را مشخص می‌کند؛ درمان از مکمل تا داروهای تخصصی متغیر است."),
    "E00-E89": ("An endocrine, nutritional or metabolic condition — the system of hormones and chemistry that controls growth, energy, sugar, thyroid and more (for example diabetes or thyroid disease). Signs vary widely: thirst and weight change, heat/cold intolerance, fatigue, hair loss or growth problems. Diagnosis is with blood hormone/glucose tests; treatment replaces or balances the hormone.",
                "بیماری غدد، تغذیه یا متابولیک — سیستم هورمون‌ها و شیمی بدن که رشد، انرژی، قند، تیروئید و موارد دیگر را کنترل می‌کند (مثلاً دیابت یا بیماری تیروئید). علائم بسیار متنوع‌اند: تشنگی و تغییر وزن، عدم تحمل گرما/سرما، خستگی، ریزش مو یا مشکلات رشد. تشخیص با آزمایش خون هورمون/قند است؛ درمان جایگزینی یا تعادل هورمون."),
    "F01-F99": ("A mental or behavioral disorder affecting mood, thinking, anxiety or perception (such as depression, anxiety or psychosis). Signs include persistent low mood or worry, sleep and appetite change, loss of interest, or hearing/seeing things others do not. These are real, treatable medical conditions; treatment combines psychotherapy and medication.",
                "اختلال روانی یا رفتاری مؤثر بر خلق، فکر، اضطراب یا ادراک (مانند افسردگی، اضطراب یا سایکوز). نشانه‌ها: خلق پایین یا نگرانی مداوم، تغییر خواب و اشتها، بی‌علاقگی، یا شنیدن/دیدن چیزهایی که دیگران نمی‌بینند. این‌ها بیماری‌های واقعی و قابل‌درمان‌اند؛ درمان ترکیب روان‌درمانی و دارو."),
    "G00-G99": ("A disease of the brain, spinal cord, nerves or muscles. Signs include headache, seizures, weakness or numbness, loss of balance, memory or speech problems, and muscle stiffness or wasting. Diagnosis uses neurological exam, imaging (CT/MRI) and nerve tests; treatment depends on the specific condition and can include medication, physiotherapy or surgery.",
                "بیماری مغز، نخاع، اعصاب یا عضلات. نشانه‌ها: سردرد، تشنج، ضعف یا بی‌حسی، از دست دادن تعادل، مشکلات حافظه یا گفتار، و سفتی یا تحلیل عضله. تشخیص با معاینه عصبی، تصویربرداری (سی‌تی/ام‌آرآی) و آزمایش عصب؛ درمان بسته به بیماری شامل دارو، فیزیوتراپی یا جراحی است."),
    "H00-H59": ("An eye disorder affecting vision, the eyelids, orbit or eye surface. Signs include blurred or double vision, pain, redness, discharge, floaters or flashing lights. Sudden vision loss, eye trauma or painful red eye are urgent. Diagnosis is with vision tests and slit-lamp exam; treatment ranges from drops and glasses to surgery.",
                "بیماری چشم مؤثر بر بینایی، پلک، حفره یا سطح چشم. نشانه‌ها: تار یا دوبینی، درد، قرمزی، ترشح، مگس‌های ریز یا جرقه‌ی نور. کاهش ناگهانی بینایی، ضربه به چشم یا چشم قرمز دردناک اورژانسی است. تشخیص با تست بینایی و معاینه اسلیت‌لمپ؛ درمان از قطره و عینک تا جراحی."),
    "H60-H95": ("An ear or hearing disorder affecting the outer, middle or inner ear or hearing nerve. Signs include ear pain, discharge, hearing loss, ringing (tinnitus), dizziness or balance problems. Diagnosis is with ear exam and hearing tests; treatment ranges from drops and antibiotics to hearing aids or surgery.",
                "بیماری گوش یا شنوایی مؤثر بر گوش خارجی، میانی، داخلی یا عصب شنوایی. نشانه‌ها: درد گوش، ترشح، کاهش شنوایی، وزوز، سرگیجه یا مشکل تعادل. تشخیص با معاینه گوش و تست شنوایی؛ درمان از قطره و آنتی‌بیوتیک تا سمعک یا جراحی."),
    "I00-I99": ("A cardiovascular disease of the heart or blood vessels (such as hypertension, heart attack, heart failure or artery disease). Signs include chest pain or pressure, breathlessness, palpitations, leg swelling and fainting. Chest pain with sweating or at rest is an emergency — call 115/112. Diagnosis uses ECG, blood tests and imaging; treatment includes medication, stents or surgery.",
                "بیماری قلبی-عروقی قلب یا رگ‌ها (مانند فشار خون، سکته قلبی، نارسایی قلبی یا بیماری شریان). نشانه‌ها: درد یا فشار قفسه سینه، تنگی نفس، تپش قلب، تورم پا و غش. درد قفسه سینه با عرق سرد یا در حالت استراحت اورژانسی است — ۱۱۵/۱۱۲. تشخیص با نوار قلب، آزمایش خون و تصویربرداری؛ درمان شامل دارو، استنت یا جراحی."),
    "J00-J99": ("A respiratory disease of the airways or lungs (such as asthma, COPD, pneumonia or bronchitis). Signs include cough, sputum, wheeze, breathlessness and chest tightness. Severe breathlessness or blue lips are emergencies. Diagnosis uses listening to the chest, X-ray and spirometry; treatment includes inhalers, antibiotics (for bacterial infections) and oxygen when needed.",
                "بیماری تنفسی راه‌های هوایی یا ریه (مانند آسم، COPD، پنومونی یا برونشیت). نشانه‌ها: سرفه، خلط، خس‌خس، تنگی نفس و فشار سینه. تنگی نفس شدید یا لب‌های آبی اورژانسی است. تشخیص با گوش‌دادن به قفسه سینه، عکس قفسه سینه و اسپیرومتری؛ درمان شامل اسپری، آنتی‌بیوتیک (عفونت باکتریایی) و اکسیژن در صورت نیاز."),
    "K00-K95": ("A digestive disease of the esophagus, stomach, intestines, liver, pancreas or gallbladder. Signs include abdominal pain, heartburn, nausea, vomiting, diarrhea, constipation, blood in stool or jaundice. Diagnosis uses endoscopy, ultrasound and lab tests; treatment ranges from diet and medication to surgery.",
                "بیماری گوارشی مری، معده، روده، کبد، پانکراس یا کیسه صفرا. نشانه‌ها: درد شکم، سوزش سر دل، تهوع، استفراغ، اسهال، یبوست، خون در مدفوع یا زردی. تشخیص با آندوسکوپی، سونوگرافی و آزمایش؛ درمان از رژیم و دارو تا جراحی."),
    "L00-L99": ("A skin disease affecting the skin, hair or nails (such as eczema, psoriasis, acne or infections). Signs include rash, itching, redness, scaling, blisters, pigment change or hair loss. Diagnosis is by skin exam, sometimes biopsy; treatment includes creams, oral medication and phototherapy.",
                "بیماری پوست مؤثر بر پوست، مو یا ناخن (مانند اگزما، پسوریازیس، جوش یا عفونت). نشانه‌ها: بثورات، خارش، قرمزی، پوسته‌ریزی، تاول، تغییر رنگ یا ریزش مو. تشخیص با معاینه پوست و گاهی بیوپسی؛ درمان شامل کرم، داروی خوراکی و نوردرمانی."),
    "M00-M99": ("A musculoskeletal disease of joints, bones, muscles or spine (such as arthritis, back pain or osteoporosis). Signs include joint pain, swelling, stiffness, back pain, muscle weakness and fractures after minor injury. Diagnosis uses X-ray, blood tests and bone density scan; treatment includes painkillers, physiotherapy, exercise and surgery when needed.",
                "بیماری عضلانی-اسکلتی مفاصل، استخوان‌ها، عضلات یا ستون فقرات (مانند آرتروز، درد کمر یا پوکی استخوان). نشانه‌ها: درد مفصل، تورم، سفتی، درد کمر، ضعف عضلانی و شکستگی بعد از ضربه‌ی خفیف. تشخیص با رادیولوژی، آزمایش خون و تراکم‌سنجی استخوان؛ درمان شامل مسکن، فیزیوتراپی، ورزش و در صورت نیاز جراحی."),
    "N00-N99": ("A disease of the kidneys, urinary tract or genitals (such as kidney disease, UTI or prostate problems). Signs include changes in urination (burning, frequency, blood), flank pain, swelling, or sexual/reproductive symptoms. Diagnosis uses urine tests, blood creatinine and ultrasound; treatment depends on the cause.",
                "بیماری کلیه، مجاری ادراری یا اندام تناسلی (مانند بیماری کلیه، عفونت ادراری یا مشکل پروستات). نشانه‌ها: تغییر در ادرار (سوزش، تکرر، خون)، درد پهلو، تورم یا علائم جنسی/باروری. تشخیص با آزمایش ادرار، کراتینین خون و سونوگرافی؛ درمان بسته به علت."),
    "O00-O9A": ("A condition related to pregnancy, childbirth or the period after delivery. Warning signs during pregnancy are bleeding, severe headache with swelling, reduced fetal movement, fever or fluid loss — these need immediate medical care. Routine prenatal visits monitor the health of mother and baby.",
                "وضعیت مرتبط با بارداری، زایمان یا دوره پس از زایمان. علائم خطر در بارداری: خونریزی، سردرد شدید با تورم، کاهش حرکات جنین، تب یا خروج مایع — نیازمند مراقبت فوری. ویزیت‌های منظم دوران بارداری سلامت مادر و جنین را پایش می‌کنند."),
    "P00-P96": ("A condition of the newborn in the first weeks of life, such as prematurity, jaundice, breathing problems, feeding difficulty or infections. Newborns can deteriorate quickly; poor feeding, fever, lethargy, yellow skin or breathing difficulty need urgent pediatric assessment.",
                "وضعیت نوزاد در هفته‌های اول زندگی، مانند نارس بودن، زردی، مشکل تنفسی، مشکل تغذیه یا عفونت. نوزادان می‌توانند سریع بدتر شوند؛ تغذیه‌ی ضعیف، تب، بی‌حالی، زردی پوست یا تنگی نفس نیاز به ارزیابی فوری اطفال دارد."),
    "Q00-Q99": ("A congenital anomaly present from birth, caused by genetic or developmental factors. Depending on the organ involved it may be visible at birth or found later on screening. Many need specialist follow-up and some are treated with corrective surgery.",
                "ناهنجاری مادرزادی موجود از بدو تولد، ناشی از عوامل ژنتیکی یا رشدی. بسته به اندام درگیر ممکن است هنگام تولد دیده شود یا بعداً در غربالگری کشف شود. بسیاری نیاز به پیگیری تخصصی دارند و برخی با جراحی اصلاحی درمان می‌شوند."),
    "R00-R99": ("A symptom or abnormal finding rather than a disease itself — something noticed by the patient or found on a test (like pain, fever or an abnormal lab). Its meaning depends entirely on the underlying cause; a doctor interprets it together with examination and further tests.",
                "علامت یا یافته‌ی غیرطبیعی، نه یک بیماری مستقل — چیزی که بیمار حس می‌کند یا در آزمایش دیده می‌شود (مثل درد، تب یا آزمایش غیرطبیعی). معنای آن کاملاً به علت زمینه‌ای بستگی دارد و پزشک آن را با معاینه و آزمایش‌های تکمیلی تفسیر می‌کند."),
    "S00-T88": ("An injury such as a fracture, wound, burn or poisoning caused by trauma or external forces. Signs are pain, swelling, bruising, bleeding or loss of function. Severe bleeding, deformity, deep burns or poisoning are emergencies — call 115/112.",
                "آسیب مانند شکستگی، زخم، سوختگی یا مسمومیت ناشی از تروما یا نیروی خارجی. نشانه‌ها: درد، تورم، کبودی، خونریزی یا از دست دادن عملکرد. خونریزی شدید، تغییر شکل، سوختگی عمیق یا مسمومیت اورژانسی‌اند — ۱۱۵/۱۱۲."),
    "Z00-Z99": ("A health-status factor: a record of screening, vaccination, history or circumstance that influences healthcare rather than an active disease. It helps doctors plan prevention and follow-up.",
                "عامل وضعیت سلامت: ثبت غربالگری، واکسیناسیون، سابقه یا وضعیتی که بر مراقبت سلامت اثر دارد، نه یک بیماری فعال. به پزشکان برای برنامه‌ریزی پیشگیری و پیگیری کمک می‌کند."),
}

_CHAPTER_SYMPTOMS = {
    "A00-B99": ("fever, fatigue, local pain or discharge depending on the organ", "تب، خستگی، درد یا ترشح موضعی بسته به اندام"),
    "C00-D49": ("unexplained weight loss, night sweats, fatigue, lump, unusual bleeding", "کاهش وزن بی‌دلیل، عرق شبانه، خستگی، توده، خونریزی غیرطبیعی"),
    "D50-D89": ("fatigue, pallor, recurrent infections, easy bruising or bleeding", "خستگی، رنگ‌پریدی، عفونت‌های مکرر، کبودی یا خونریزی آسان"),
    "E00-E89": ("thirst, weight change, heat/cold intolerance, fatigue, hair loss", "تشنگی، تغییر وزن، عدم تحمل گرما/سرما، خستگی، ریزش مو"),
    "F01-F99": ("low mood, worry, sleep problems, appetite change, loss of interest", "خلق پایین، نگرانی، مشکل خواب، تغییر اشتها، بی‌علاقگی"),
    "G00-G99": ("headache, weakness or numbness, balance problems, seizures, memory issues", "سردرد، ضعف یا بی‌حسی، مشکل تعادل، تشنج، مشکلات حافظه"),
    "H00-H59": ("blurred vision, eye pain, redness, discharge, floaters", "تار بینایی، درد چشم، قرمزی، ترشح، مگس‌های ریز"),
    "H60-H95": ("ear pain, hearing loss, ringing, dizziness, discharge", "درد گوش، کاهش شنوایی، وزوز، سرگیجه، ترشح"),
    "I00-I99": ("chest pain, breathlessness, palpitations, leg swelling, fainting", "درد قفسه سینه، تنگی نفس، تپش قلب، تورم پا، غش"),
    "J00-J99": ("cough, sputum, wheeze, breathlessness, chest tightness", "سرفه، خلط، خس‌خس، تنگی نفس، فشار سینه"),
    "K00-K95": ("abdominal pain, heartburn, nausea, diarrhea or constipation", "درد شکم، سوزش سر دل، تهوع، اسهال یا یبوست"),
    "L00-L99": ("rash, itching, redness, scaling, blisters, pigment change", "بثورات، خارش، قرمزی، پوسته‌ریزی، تاول، تغییر رنگ"),
    "M00-M99": ("joint pain, swelling, stiffness, back pain, muscle weakness", "درد مفصل، تورم، سفتی، درد کمر، ضعف عضلانی"),
    "N00-N99": ("burning urination, frequency, flank pain, swelling, blood in urine", "سوزش ادرار، تکرر، درد پهلو، تورم، خون در ادرار"),
    "O00-O9A": ("depends on the stage of pregnancy; warning: bleeding, severe headache, reduced fetal movement", "بسته به مرحله بارداری؛ هشدار: خونریزی، سردرد شدید، کاهش حرکات جنین"),
    "P00-P96": ("poor feeding, fever, lethargy, jaundice, breathing difficulty", "تغذیه ضعیف، تب، بی‌حالی، زردی، تنگی نفس"),
    "Q00-Q99": ("varies by the affected organ; often visible at birth or on screening", "بسته به اندام درگیر؛ اغلب هنگام تولد یا در غربالگری دیده می‌شود"),
    "R00-R99": ("the symptom itself is the finding; other signs depend on the cause", "خودِ علامت یافته است؛ نشانه‌های دیگر بسته به علت"),
    "S00-T88": ("pain, swelling, bruising, bleeding, loss of function", "درد، تورم، کبودی، خونریزی، از دست دادن عملکرد"),
    "Z00-Z99": ("no symptoms by itself; it records screening, history or prevention", "خودش علامتی ندارد؛ غربالگری، سابقه یا پیشگیری را ثبت می‌کند"),
}


def full_profile(name: str, code: str = "", ch_key: str = "",
                 definition: str = "", syms=None, drugs=None,
                 note_en: str = "", note_fa: str = "") -> dict:
    """Guaranteed bilingual profile for ANY disease entry.

    Priority: specific scientific data > ICD-chapter clinical summary >
    synthesized description. Always returns about/symptoms/treatment in both
    languages."""
    ch = ch_key or ""
    if not ch and code:
        _c = icd_chapter(code)
        ch = _c.get("key", "")
    if not ch:
        _low = (name or "").lower()
        _guess = {
            "M00-M99": ("arthr", "joint", "muscle", "bone", "fracture", "back pain", "osteopor", "rheuma"),
            "I00-I99": ("heart", "cardiac", "coronary", "hypertens", "arrhythm", "atrial"),
            "J00-J99": ("asthma", "lung", "pulmonary", "bronch", "pneumon", "respirat", "copd"),
            "K00-K95": ("gastr", "ulcer", "colit", "hepat", "liver", "pancrea", "intestin", "esophag", "chole"),
            "C00-D49": ("cancer", "carcinoma", "neoplasm", "lymphoma", "leukemia", "melanoma", "sarcoma", "tumor", "myeloma"),
            "G00-G99": ("epilep", "seizure", "neuropathy", "myasthenia", "parkinson", "migraine", "encephal", "mening"),
            "E00-E89": ("diabet", "thyroid", "obes", "metabolic", "hormone", "adrenal", "pituitary"),
            "F01-F99": ("depress", "anxiety", "schizophren", "bipolar", "autism", "adhd"),
            "L00-L99": ("dermat", "eczema", "psoria", "skin", "urticaria", "alopecia"),
            "N00-N99": ("nephrit", "kidney", "renal", "urinary", "cystit", "prostat"),
            "H00-H59": ("retin", "cataract", "glaucoma", "conjunctiv", "myopia"),
            "H60-H95": ("otit", "hearing", "deaf", "tinnitus", "ear"),
            "D50-D89": ("anemia", "thalass", "hemophil", "leukopen", "thrombocyto"),
            "A00-B99": ("infect", "sepsis", "abscess", "tubercul", "malaria", "hepatitis"),
        }
        for _ck, _words in _guess.items():
            if any(_w in _low for _w in _words):
                ch = _ck
                break
    about_en, about_fa = definition, definition
    if about_en and not any("\u0600" <= _c2 <= "\u06ff" for _c2 in about_en):
        _cl = _CHAPTER_CLINICAL.get(ch)
        if _cl:
            about_fa = _cl[1]
    if not about_en:
        a = icd_about(code)
        if a:
            about_en, about_fa = a[0], a[1]
    if not about_en and note_en:
        about_en, about_fa = note_en, note_fa
    if not about_en:
        from synth_desc import synthesize_description
        about_fa, about_en = synthesize_description(name, code, ch)
    s_list = [str(s) for s in (syms or [])][:14]
    sym_fallback = _CHAPTER_SYMPTOMS.get(ch) or ("depends on the affected organ — check the Symptoms module", "بسته به اندام درگیر — از ماژول علائم بررسی کن")
    d_list = [str(d) for d in (drugs or [])][:14]
    drug_fb_fa, drug_fb_en = chapter_drugs(ch)
    tr_fa, tr_en = guess_treatment(name)
    ch_clin = _CHAPTER_CLINICAL.get(ch)
    if ch_clin and tr_en == "treatment as determined by a doctor":
        tr_en, tr_fa = "management per the specific condition — see the chapter summary above", "درمان بسته به بیماری خاص — به خلاصه‌ی فصل بالا مراجعه کن"
    return {
        "name": name, "code": code, "chapter_key": ch,
        "about_en": about_en, "about_fa": about_fa,
        "chapter_en": ch_clin[0] if ch_clin else "", "chapter_fa": ch_clin[1] if ch_clin else "",
        "symptoms": s_list,
        "sym_fb_en": sym_fallback[0] if sym_fallback else "",
        "sym_fb_fa": sym_fallback[1] if sym_fallback else "",
        "drugs": d_list,
        "drug_fb_fa": drug_fb_fa, "drug_fb_en": drug_fb_en,
        "treat_en": tr_en, "treat_fa": tr_fa,
    }


_CHAPTER_DRUGS = {
    "A00-B99": ("آنتی‌بیوتیک‌ها (مثل آموکسی‌سیلین)، آنتی‌ویروس‌ها، آنتی‌قارچ‌ها بسته به عامل", "antibiotics (e.g. amoxicillin), antivirals or antifungals depending on the organism"),
    "C00-D49": ("داروهای شیمی‌درمانی، داروهای هدف‌مندی و مسکن‌های اوپیوئید زیر نظر انکولوژیست", "chemotherapy, targeted therapy and opioid pain relief under an oncologist"),
    "D50-D89": ("مکمل آهن، ویتامین B12، داروهای تحریک‌کننده مغز استخوان", "iron supplements, vitamin B12, bone-marrow stimulating drugs"),
    "E00-E89": ("متفورمین/انسولین (دیابت)، لووتیروکسین (تیروئید)، هورمون‌ها بسته به غده", "metformin/insulin (diabetes), levothyroxine (thyroid), hormones per gland"),
    "F01-F99": ("سرترالین/فلوکستین (افسردگی)، بنزودیازپین‌ها کوتاه‌مدت، داروهای ضدروان‌پریشی", "sertraline/fluoxetine (depression), short-term benzodiazepines, antipsychotics"),
    "G00-G99": ("ضدتشنج‌ها (مثل کاربامازپین)، لوودوپا (پارکینسون)، کورتون (مولتیپل اسکلروزیس)", "antiepileptics (e.g. carbamazepine), levodopa (Parkinson's), steroids (MS)"),
    "H00-H59": ("قطره‌های چشمی (آنتی‌بیوتیک/استروئید)، داروهای کاهش فشار چشم (گلوکوما)", "eye drops (antibiotic/steroid), pressure-lowering drops (glaucoma)"),
    "H60-H95": ("قطره‌های گوش آنتی‌بیوتیک‌دار، مسکن‌ها، آنتی‌هیستامین‌ها برای سرگیجه", "antibiotic ear drops, painkillers, antihistamines for dizziness"),
    "I00-I99": ("آسپرین/استاتین‌ها، بتابلاکرها، مهارکننده‌های ACE، نیترات‌ها، داروهای ادرارآور", "aspirin/statins, beta-blockers, ACE inhibitors, nitrates, diuretics"),
    "J00-J99": ("اسپری‌های برونکودیلاتور و کورتونی (آسم)، آنتی‌بیوتیک (پنومونی)، اکسیژن", "bronchodilator and steroid inhalers (asthma), antibiotics (pneumonia), oxygen"),
    "K00-K95": ("مهارکننده‌های پمپ پروتون (امپرازول)، آنتی‌اسیدها، مسکن‌ها، داروهای ضدالتهابی روده", "proton pump inhibitors (omeprazole), antacids, analgesics, IBD drugs"),
    "L00-L99": ("کرم‌های کورتونی، مرطوب‌کننده‌ها، آنتی‌هیستامین‌ها، رتینوئیدها (آکنه)", "steroid creams, moisturizers, antihistamines, retinoids (acne)"),
    "M00-M99": ("مسکن‌ها (استامینوفن/ایبوپروفن)، داروهای ضدروماتیزمی (متوترکسات), کلسیم/ویتامین D", "painkillers (paracetamol/ibuprofen), DMARDs (methotrexate), calcium/vitamin D"),
    "N00-N99": ("آنتی‌بیوتیک‌های ادراری، آلفابلاکرها (پروستات)، داروهای کاهنده اوره اسید", "urinary antibiotics, alpha-blockers (prostate), uric-acid lowering drugs"),
    "O00-O9A": ("مکمل‌های بارداری (اسید فولیک، آهن)، داروهای تحت نظر متخصص زنان", "pregnancy supplements (folic acid, iron), obstetrician-prescribed drugs"),
    "P00-P96": ("داروهای تحت نظر نئوناتولوژیست — دوز دقیق نوزادی", "neonatologist-managed medications with precise newborn dosing"),
    "Q00-Q99": ("داروهای علامتی + جراحی اصلاحی در صورت نیاز", "symptom-directed drugs + corrective surgery when needed"),
    "R00-R99": ("درمان علت زمینه‌ای — علامت خودش بیماری نیست", "treat the underlying cause — the symptom itself is not a disease"),
    "S00-T88": ("مسکن‌ها، گچ/بی‌حرکتی، پماد سوختگی، آنتی‌بیوتیک prophylaxis", "painkillers, casting/immobilization, burn ointments, antibiotic prophylaxis"),
    "Z00-Z99": ("دارو ندارد — کد پیشگیری/سابقه است", "no medication — this is a prevention/history code"),
}


def chapter_drugs(ch_key: str) -> tuple[str, str]:
    """(fa, en) typical drug classes for the chapter."""
    return _CHAPTER_DRUGS.get(ch_key, ("داروها بسته به تشخیص دقیق — با پزشک مشورت کن", "medication depends on the exact diagnosis — consult a doctor"))
