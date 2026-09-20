"""
side_effect_checker.py — matches a reported symptom against the adverse
reactions section of the bundled FDA drug labels (14,259 labels) to answer
"is this symptom a side effect of my medication?".
Educational information only; the final call belongs to a doctor.
"""
from __future__ import annotations

import gzip
import json
import os
import re
from typing import Any

from common_2077 import DATA_DIR, normalize, first_sentences
from i18n import is_fa

_LABELS_PATH = os.path.join(DATA_DIR, "drug_labels.json.gz")
_labels_cache: dict[str, dict[str, str]] | None = None

_SYMPTOMS: list[dict[str, Any]] = [
    {"key": "cough", "en": "cough", "fa": "سرفه", "terms": ["cough", "سرفه"]},
    {"key": "nausea", "en": "nausea", "fa": "تهوع", "terms": ["nausea", "تهوع", "حالت تهوع"]},
    {"key": "vomiting", "en": "vomiting", "fa": "استفراغ", "terms": ["vomit", "emesis", "استفراغ"]},
    {"key": "diarrhea", "en": "diarrhea", "fa": "اسهال", "terms": ["diarrhea", "diarrhoea", "اسهال"]},
    {"key": "constipation", "en": "constipation", "fa": "یبوست", "terms": ["constipation", "یبوست"]},
    {"key": "dizziness", "en": "dizziness", "fa": "سرگیجه", "terms": ["dizzy", "dizziness", "vertigo", "سرگیجه"]},
    {"key": "headache", "en": "headache", "fa": "سردرد", "terms": ["headache", "سردرد"]},
    {"key": "insomnia", "en": "insomnia", "fa": "بی‌خوابی", "terms": ["insomnia", "sleepless", "بی خوابی", "بی‌خوابی"]},
    {"key": "drowsiness", "en": "drowsiness", "fa": "خواب‌آلودگی", "terms": ["drows", "somnolence", "sedation", "خواب آلودگی", "خواب‌آلودگی"]},
    {"key": "rash", "en": "skin rash", "fa": "بثورات پوستی", "terms": ["rash", "eruption", "بثورات", "جوش", "خارش پوستی"]},
    {"key": "itching", "en": "itching", "fa": "خارش", "terms": ["pruritus", "itch", "خارش"]},
    {"key": "edema", "en": "swelling", "fa": "تورم", "terms": ["edema", "swelling", "تورم"]},
    {"key": "muscle_pain", "en": "muscle pain", "fa": "درد عضلانی", "terms": ["myalgia", "muscle pain", "درد عضله", "درد عضلانی"]},
    {"key": "weakness", "en": "weakness/fatigue", "fa": "ضعف و خستگی", "terms": ["fatigue", "asthenia", "weakness", "خستگی", "ضعف"]},
    {"key": "weight_gain", "en": "weight gain", "fa": "افزایش وزن", "terms": ["weight gain", "افزایش وزن", "چاق شدن"]},
    {"key": "weight_loss", "en": "weight loss", "fa": "کاهش وزن", "terms": ["weight loss", "کاهش وزن", "لاغر شدن"]},
    {"key": "dry_mouth", "en": "dry mouth", "fa": "خشکی دهان", "terms": ["dry mouth", "خشکی دهان"]},
    {"key": "blurred_vision", "en": "blurred vision", "fa": "تاری دید", "terms": ["blurred vision", "visual disturbance", "تاری دید"]},
    {"key": "tinnitus", "en": "tinnitus", "fa": "وزوز گوش", "terms": ["tinnitus", "وزوز"]},
    {"key": "tremor", "en": "tremor", "fa": "لرز", "terms": ["tremor", "لرز دست", "لرزش"]},
    {"key": "anxiety", "en": "anxiety", "fa": "اضطراب", "terms": ["anxiety", "nervousness", "اضطراب", "پریشانی"]},
    {"key": "depression", "en": "depression", "fa": "افسردگی", "terms": ["depression", "depressed", "افسردگی"]},
    {"key": "suicidal", "en": "suicidal thoughts", "fa": "افکار خودآزاری", "terms": ["suicid", "خودکشی", "خودآزاری"]},
    {"key": "sweating", "en": "sweating", "fa": "تعریق", "terms": ["sweating", "hyperhidrosis", "تعریق"]},
    {"key": "palpitations", "en": "palpitations", "fa": "تپش قلب", "terms": ["palpitation", "تپش قلب", "تپش"]},
    {"key": "hypotension", "en": "low blood pressure", "fa": "افت فشار خون", "terms": ["hypotension", "low blood pressure", "افت فشار"]},
    {"key": "chest_pain", "en": "chest pain", "fa": "درد قفسه سینه", "terms": ["chest pain", "درد قفسه سینه"]},
    {"key": "dyspnea", "en": "shortness of breath", "fa": "تنگی نفس", "terms": ["dyspnea", "shortness of breath", "تنگی نفس"]},
    {"key": "fever", "en": "fever", "fa": "تب", "terms": ["fever", "pyrexia", "تب"]},
    {"key": "photosensitivity", "en": "sun sensitivity", "fa": "حساسیت به نور", "terms": ["photosensitivity", "نور"]},
    {"key": "taste", "en": "taste changes", "fa": "تغییر چشایی", "terms": ["dysgeusia", "taste", "چشایی", "تلخی دهان"]},
    {"key": "appetite_up", "en": "increased appetite", "fa": "اشتها‌ی زیاد", "terms": ["increased appetite", "اشتها"]},
    {"key": "appetite_down", "en": "loss of appetite", "fa": "بی‌اشتهایی", "terms": ["anorexia", "decreased appetite", "loss of appetite", "بی اشتهایی", "بی‌اشتهایی"]},
    {"key": "heartburn", "en": "heartburn/reflux", "fa": "سوزش سر دل", "terms": ["heartburn", "reflux", "dyspepsia", "سوزش سر دل", "ترش کردن"]},
    {"key": "abdominal_pain", "en": "abdominal pain", "fa": "درد شکم", "terms": ["abdominal pain", "درد شکم", "دل درد", "دل‌درد"]},
    {"key": "joint_pain", "en": "joint pain", "fa": "درد مفاصل", "terms": ["arthralgia", "joint pain", "درد مفصل", "درد مفاصل"]},
    {"key": "numbness", "en": "numbness/tingling", "fa": "کرختی و بی‌حسی", "terms": ["paresthesia", "numbness", "tingling", "کرختی", "بی حسی", "بی‌حسی"]},
    {"key": "confusion", "en": "confusion", "fa": "گیجی", "terms": ["confusion", "گیجی", "منگی"]},
    {"key": "memory", "en": "memory problems", "fa": "مشکل حافظه", "terms": ["memory impairment", "amnesia", "حافظه", "فراموشی"]},
    {"key": "sexual", "en": "sexual side effects", "fa": "مشکلات جنسی", "terms": ["erectile", "libido", "impotence", "میل جنسی", "نزدیکی"]},
    {"key": "seizure", "en": "seizure", "fa": "تشنج", "terms": ["seizure", "convulsion", "تشنج"]},
    {"key": "syncope", "en": "fainting", "fa": "بی‌هوشی", "terms": ["syncope", "faint", "بی هوشی", "بی‌هوشی"]},
    {"key": "jaundice", "en": "jaundice", "fa": "زردی", "terms": ["jaundice", "زردی", "زردی پوست"]},
    {"key": "dark_urine", "en": "dark urine", "fa": "تیره شدن ادرار", "terms": ["dark urine", "ادرار تیره"]},
    {"key": "hypoglycemia", "en": "low blood sugar", "fa": "افت قند خون", "terms": ["hypoglycemia", "hypoglycaemia", "افت قند"]},
    {"key": "bleeding", "en": "bleeding", "fa": "خونریزی", "terms": ["bleeding", "hemorrhage", "خونریزی"]},
    {"key": "alopecia", "en": "hair loss", "fa": "ریزش مو", "terms": ["alopecia", "hair loss", "ریزش مو"]},
    {"key": "cramps", "en": "muscle cramps", "fa": "کرامپ عضله", "terms": ["cramp", "کرامپ"]},
]

_EXTRA_DRUG_TOKENS = [
    ("losartan", "لوزارتان"), ("amlodipine", "آملودیپین"), ("levothyroxine", "لووتیروکسین"),
    ("levothyroxine", "اتروکسین"), ("omeprazole", "امپرازول"), ("pantoprazole", "پانتوپرازول"),
    ("cetirizine", "سیتریزین"), ("loratadine", "لوراتادین"), ("prednisolone", "پردنیزولون"),
    ("hydrochlorothiazide", "هیدروکلروتیازید"), ("simvastatin", "سیمواستاتین"),
    ("gabapentin", "گاباپنتین"), ("tramadol", "ترامادول"), ("venlafaxine", "ونلافاکسین"),
    ("citalopram", "سیتالوپرام"), ("fluoxetine", "فلوکستین"), ("propranolol", "پروپرانولول"),
    ("metoprolol", "متوپرولول"), ("alprazolam", "آلپرازولام"), ("diazepam", "دیازپام"),
    ("clopidogrel", "کلوپیدوگرل"), ("sildenafil", "سیلدنافیل"), ("tamsulosin", "تامسولوزین"),
]


def _load_labels() -> dict[str, dict[str, str]]:
    global _labels_cache
    if _labels_cache is None:
        try:
            with gzip.open(_LABELS_PATH, "rt", encoding="utf-8") as f:
                _labels_cache = json.load(f)
        except Exception:
            _labels_cache = {}
    return _labels_cache


def _norm_key(s: str) -> str:
    s = normalize(s)
    s = re.sub(r"\b\d+(\.\d+)?\s*(mg|mcg|g|ml|%)\b", " ", s)
    s = re.sub(r"\b(er|xr|sr|dr|tablet|tablets|capsule|capsules|injection|oral|film)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def has_fa(s: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", str(s or "")))


def detect_symptom(text: str) -> dict[str, Any] | None:
    n = normalize(text)
    if not n:
        return None
    for s in _SYMPTOMS:
        for term in s["terms"]:
            tn = normalize(term)
            if tn and tn in n:
                return s
    return None


def detect_drug(text: str) -> tuple[str, str] | None:
    n = normalize(text)
    if not n:
        return None
    try:
        from drug_interaction import DRUGS
        for d in DRUGS:
            for alias in d.get("en", []) + d.get("fa", []):
                an = normalize(alias)
                if an and an in n:
                    return str(d.get("en", [""])[0]).lower(), str(alias)
    except Exception:
        pass
    for en, fa in _EXTRA_DRUG_TOKENS:
        if normalize(en) in n:
            return en, en
        if normalize(fa) in n:
            return en, fa
    return None


def find_label(drug_query: str) -> tuple[str, dict[str, str]] | None:
    q = _norm_key(drug_query or "")
    if not q:
        return None
    labels = _load_labels()
    best_key = ""
    best_len = 10 ** 9
    for key in labels:
        nk = _norm_key(key)
        if not nk:
            continue
        if q == nk or nk.startswith(q) or (q in nk and len(nk.split()) <= len(q.split()) + 3):
            if len(nk) < best_len:
                best_len = len(nk)
                best_key = key
    if not best_key:
        return None
    return best_key, labels[best_key]


def _snippets(text: str, terms: list[str], limit: int = 2) -> list[str]:
    out: list[str] = []
    if not text:
        return out
    parts = re.split(r"(?<=[.;])\s+", text)
    for p in parts:
        low = p.lower()
        hit_idx = -1
        for t in terms:
            i = low.find(t)
            if i >= 0:
                hit_idx = i
                break
        if hit_idx < 0:
            continue
        p = p.strip(" .;")
        if len(p) > 320:
            start = max(0, hit_idx - 120)
            p = ("..." if start > 0 else "") + p[start:start + 300] + "..."
        out.append(p)
        if len(out) >= limit:
            break
    return out


def check(drug: str, symptom: str, display: str = "") -> dict[str, Any]:
    fa = is_fa()
    sym = detect_symptom(symptom or "")
    drug_name = drug or ""
    if not drug_name:
        return {"ok": False, "message_fa": "نام دارو را بنویس." if fa else "Enter the medication name."}
    hit = find_label(drug_name)
    if hit is None:
        return {"ok": True, "known": False, "drug": drug_name,
                "message_fa": ("برچسب FDA برای این دارو در بانک آفلاین پیدا نشد؛ از پزشک یا داروساز بپرس."
                               if fa else "No FDA label found for this drug in the offline bank; ask your doctor or pharmacist.")}
    label_key, label = hit
    drug_show = display or drug_name or label_key
    if sym is None:
        adv = (label.get("adv") or "").strip()
        m = re.search(r"most common adverse reactions?[^.]*?(?:are|is)\s*([^.;]{5,300})", adv, re.I)
        common = m.group(1).strip(" .,") if m else ""
        return {"ok": True, "known": True, "drug": label_key, "drug_show": drug_show, "symptom": None,
                "common_fa": common[:300] if common else first_sentences(adv, 1, 240),
                "message_fa": ""}
    terms = [t.lower() for t in sym["terms"] if re.match(r"^[a-z]", t)]
    adv_hits = _snippets(label.get("adv") or "", terms)
    warn_hits = _snippets(label.get("warn") or "", terms)
    found = bool(adv_hits or warn_hits)
    sym_name = sym["fa"] if fa else sym["en"]
    if found:
        msg = (f"بله، {sym_name} در عوارض ثبت‌شده‌ی {drug_show} در برچسب FDA دیده می‌شود."
               if fa else f"Yes, {sym_name} appears in the FDA label adverse reactions of {drug_show}.")
    else:
        msg = (f"در برچسب FDA داروی {drug_show}، {sym_name} به‌عنوان عارضه‌ی شایع ذکر نشده است."
               if fa else f"{sym_name} is not listed as an adverse reaction in the FDA label of {drug_show}.")
    return {"ok": True, "known": True, "found": found, "drug": label_key, "drug_show": drug_show,
            "symptom": sym_name, "message_fa": msg,
            "adv_snippets": adv_hits, "warn_snippets": warn_hits}


def check_message(text: str) -> str | None:
    fa = is_fa()
    det = detect_drug(text or "")
    if not det:
        return None
    drug, alias = det
    sym = detect_symptom(text or "")
    if sym is None:
        return None
    display = alias if (fa and has_fa(alias)) else (alias if not fa else drug)
    r = check(drug, sym["key"], display=display)
    if not r.get("ok") or not r.get("known"):
        return None
    lines = [r["message_fa"]]
    if r.get("adv_snippets"):
        lines.append(r["adv_snippets"][0][:260])
    elif r.get("common_fa"):
        lines.append((f"عوارض شایع {r.get('drug_show', '')}: " if fa
                      else f"Common adverse reactions of {r.get('drug_show', '')}: ") + str(r["common_fa"])[:240])
    lines.append("اگر تازگی شروع شده، شدید است یا بدتر می‌شود، پیش از قطع یا ادامه‌ی دارو با پزشک مشورت کن."
                 if fa else "If it started recently, is severe or getting worse, consult a doctor before stopping or continuing the medication.")
    return "\n\n".join(lines)
