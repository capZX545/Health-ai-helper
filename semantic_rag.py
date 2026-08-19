# -*- coding: utf-8 -*-
"""
semantic_rag.py — RAG داخلی با TF-IDF (حروف n-gram؛ مناسب فارسی بدون توکنایزر).
منابع: پایه‌ی دانش داخلی + diseases_extra.json + diseases_offline.db + learned_knowledge.json
بعد از یادگیری جدید، کش باید پاک شود (تابع invalidate).
"""
from __future__ import annotations

import os
import sqlite3
import threading
from typing import Any

from common_2077 import DATA_DIR, normalize, read_json
from medical_engine import DISEASES

EXTRA_PATH = os.path.join(DATA_DIR, "diseases_extra.json")
DB_PATH = os.path.join(DATA_DIR, "diseases_offline.db")
LEARNED_PATH = os.path.join(DATA_DIR, "learned_knowledge.json")

_lock = threading.RLock()
_cache: dict[str, Any] = {"docs": [], "vec": None, "matrix": None, "sig": None}


def _doc(text: str, source: str, title: str = "") -> dict:
    return {"text": text, "source": source, "title": title}


def _collect_docs() -> list[dict]:
    docs: list[dict] = []
    for d in DISEASES:
        body = d["fa"] + " | " + d["en"] + " | " + \
               "، ".join(k for k in d["symptoms"]) + " | " + \
               "؛ ".join(d.get("advice", [])) + " | " + d.get("doctor_when", "")
        docs.append(_doc(body, "smart_brain", d["fa"]))
    for d in (read_json(EXTRA_PATH, default=[]) or []):
        if isinstance(d, dict):
            body = " ".join(str(d.get(k, "")) for k in ("fa", "en", "symptoms_fa", "advice_fa", "doctor_when_fa"))
            docs.append(_doc(body, "diseases_extra.json", d.get("fa", "")))
    if os.path.exists(DB_PATH):
        try:
            con = sqlite3.connect(DB_PATH)
            cur = con.cursor()
            cur.execute("SELECT name_fa, name_en, symptoms, advice, doctor_when FROM diseases")
            for row in cur.fetchall():
                docs.append(_doc(" | ".join(str(x) for x in row), "diseases_offline.db", row[0]))
            con.close()
        except Exception:
            pass
    for e in (read_json(LEARNED_PATH, default={"entries": []}) or {}).get("entries", []):
        if isinstance(e, dict):
            body = " ".join(filter(None, [e.get("topic", ""), e.get("user_summary", ""), e.get("ai_summary", ""),
                                          "، ".join(e.get("symptoms_fa", [])), "؛ ".join(e.get("advice_fa", []))]))
            if body.strip():
                docs.append(_doc(body, "learned", e.get("topic", "")))
    return [d for d in docs if d["text"] and d["text"].strip()]


def _signature() -> tuple:
    sig = []
    for p in (EXTRA_PATH, DB_PATH, LEARNED_PATH):
        try:
            sig.append(os.path.getmtime(p))
        except OSError:
            sig.append(0)
    sig.append(len(DISEASES))
    return tuple(sig)


def _ensure_index():
    with _lock:
        sig = _signature()
        if _cache["sig"] == sig and _cache["vec"] is not None:
            return True
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
        except Exception:
            _cache["vec"] = None
            return False
        docs = _collect_docs()
        texts = [normalize(d["text"]) for d in docs]
        try:
            vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=1, max_features=60000)
            matrix = vec.fit_transform(texts)
        except ValueError:
            _cache["vec"] = None
            return False
        _cache.update(docs=docs, vec=vec, matrix=matrix, sig=sig)
        return True


def search(query: str, k: int = 4) -> list[dict[str, Any]]:
    """جست‌وجوی معنایی؛ خروجی: اسناد مرتبط با امتیاز."""
    if not query or not query.strip():
        return []
    if not _ensure_index():
        return _fallback_search(query, k)
    try:
        from sklearn.metrics.pairwise import cosine_similarity
        q = _cache["vec"].transform([normalize(query)])
        sims = cosine_similarity(q, _cache["matrix"]).ravel()
        order = sims.argsort()[::-1][:k]
        out = []
        for i in order:
            if sims[i] > 0.05:
                d = _cache["docs"][int(i)]
                out.append({"text": d["text"][:400], "source": d["source"], "title": d["title"],
                            "score": round(float(sims[i]), 3)})
        return out
    except Exception:
        return _fallback_search(query, k)


def _fallback_search(query: str, k: int = 4) -> list[dict[str, Any]]:
    """جست‌وجوی کلیدواژه‌ای ساده در نبود sklearn."""
    nq = set(normalize(query).split())
    scored = []
    for d in _collect_docs():
        nt = set(normalize(d["text"]).split())
        inter = len(nq & nt)
        if inter:
            scored.append((inter, d))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"text": d["text"][:400], "source": d["source"], "title": d["title"], "score": s} for s, d in scored[:k]]


def invalidate():
    """پاک‌کردن کش RAG بعد از یادگیری جدید."""
    with _lock:
        _cache.update(docs=[], vec=None, matrix=None, sig=None)


def status() -> dict:
    _ensure_index()
    with _lock:
        return {"indexed_docs": len(_cache["docs"]), "vectorizer": "tfidf_char_wb" if _cache["vec"] is not None else "keyword_fallback"}
