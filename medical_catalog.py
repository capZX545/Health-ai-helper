# -*- coding: utf-8 -*-
"""
Catalog of conditions (NIH/NLM) and drugs (FDA), built from free official
US government APIs:
- conditions: NLM Clinical Tables API (2,177 entries with ICD-10 codes)
- drugs: openFDA drug labels API (201 generics)

This module is just a search/lookup layer on top of that data.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

from common_2077 import DATA_DIR, normalize

_DATA: dict[str, Any] = {"loaded": False, "conditions": [], "drugs": [],
                          "conditions_by_name": {}, "conditions_by_icd": {}}


def _load():
    if _DATA["loaded"]:
        return
    cond_path = os.path.join(DATA_DIR, "nlm_conditions.json")
    drug_path = os.path.join(DATA_DIR, "fda_drugs.json")
    if os.path.exists(cond_path):
        try:
            with open(cond_path, "r", encoding="utf-8") as f:
                _DATA["conditions"] = json.load(f)
        except Exception:
            _DATA["conditions"] = []
    if os.path.exists(drug_path):
        try:
            with open(drug_path, "r", encoding="utf-8") as f:
                _DATA["drugs"] = json.load(f)
        except Exception:
            _DATA["drugs"] = []
    for c in _DATA["conditions"]:
        _DATA["conditions_by_name"][normalize(c.get("name", ""))] = c
        icd = c.get("icd10", "")
        if icd:
            _DATA["conditions_by_icd"][icd] = c
    _DATA["loaded"] = True


def search_conditions(query: str, limit: int = 20) -> list[dict]:
    """
    Search conditions by name or ICD-10 code.
    """
    _load()
    nq = normalize(query)
    if not nq:
        return []
    results = []
    # exact match
    if nq in _DATA["conditions_by_name"]:
        results.append(_DATA["conditions_by_name"][nq])
    # ICD lookup
    if query.upper() in _DATA["conditions_by_icd"]:
        results.append(_DATA["conditions_by_icd"][query.upper()])
    # substring match
    for c in _DATA["conditions"]:
        if len(results) >= limit:
            break
        cn = normalize(c.get("name", ""))
        if cn != nq and nq in cn:
            results.append(c)
    return results[:limit]


def search_drugs(query: str, limit: int = 20) -> list[str]:
    """
    Search drugs by name.
    """
    _load()
    nq = normalize(query)
    if not nq:
        return []
    return [d for d in _DATA["drugs"] if nq in normalize(d)][:limit]


def get_by_icd(code: str) -> dict | None:
    _load()
    return _DATA["conditions_by_icd"].get(code.upper(), None)


def get_condition_categories() -> dict[str, int]:
    """
    Condition counts grouped by the first ICD-10 letter.
    """
    _load()
    cats: dict[str, int] = {}
    for c in _DATA["conditions"]:
        icd = c.get("icd10", "")
        if icd:
            letter = icd[0]
            cats[letter] = cats.get(letter, 0) + 1
    return cats


def stats() -> dict:
    _load()
    return {"conditions": len(_DATA["conditions"]), "drugs": len(_DATA["drugs"])}


# ICD-10 letter -> persian chapter label
ICD10_CHAPTERS = {
    "A": "عفونی و انگلی",
    "B": "عفونی و انگلی",
    "C": "سرطان",
    "D": "خون و سرطان",
    "E": "هورمونی، تغذیه و متابولیک",
    "F": "روانی و رفتاری",
    "G": "عصبی",
    "H": "چشم و گوش",
    "I": "قلب و عروق",
    "J": "تنفسی",
    "K": "گوارش",
    "L": "پوست",
    "M": "عضلانی-اسکلتی",
    "N": "ادراری-تناسلی",
    "O": "بارداری و زایمان",
    "P": "دوره‌ی پری‌ناتال",
    "Q": "مادرزادی",
    "R": "علائم و نشانه‌ها",
    "S": "آسیب و مسمومیت",
    "T": "آسیب و مسمومیت",
    "U": "کدهای ویژه",
    "V": "علل خارجی",
    "W": "علل خارجی",
    "X": "علل خارجی",
    "Y": "علل خارجی",
    "Z": "عوامل مؤثر بر وضعیت سلامت",
}


def get_chapter_fa(icd_code: str) -> str:
    """
    ICD-10 chapter label in Persian.
    """
    if not icd_code:
        return "نامشخص"
    letter = icd_code[0].upper()
    return ICD10_CHAPTERS.get(letter, "نامشخص")


def search_by_code_prefix(prefix: str, limit: int = 30) -> list[dict]:
    """
    Search diseases by ICD-10 prefix (E11 -> every E11.*).
    """
    _load()
    p = prefix.strip().upper()
    if not p:
        return []
    out = []
    for c in _DATA["conditions"]:
        if c.get("icd10", "").startswith(p):
            out.append(c)
            if len(out) >= limit:
                break
    return out
