# -*- coding: utf-8 -*-
"""
ml_classifier.py — طبقه‌بند Scikit-Learn آموزش‌دیده روی دیتاست مصنوعی
(medical_ml_test_dataset.csv). دیتاست فقط برای تست ML است، نه کاربرد بالینی.
"""
from __future__ import annotations

import csv
import os
import threading
from typing import Any

from common_2077 import DATA_DIR

DATASET_PATH = os.path.join(DATA_DIR, "medical_ml_test_dataset.csv")

FEATURE_COLS = [
    "age", "gender", "duration_days", "temp_c", "heart_rate", "systolic_bp",
    "diastolic_bp", "glucose_mg_dl", "cough", "fever", "sore_throat", "runny_nose",
    "body_ache", "headache", "nausea", "vomiting", "diarrhea", "abdominal_pain",
    "dysuria", "urinary_frequency", "skin_itch", "rash", "sneezing", "anxiety",
    "chest_pain", "shortness_of_breath", "red_flag",
]

_lock = threading.Lock()
_state: dict[str, Any] = {"dx_model": None, "urg_model": None, "ready": False, "error": None}


def _ensure_dir_numeric(v: str) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _load_rows():
    rows, labels, urg = [], [], []
    with open(DATASET_PATH, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                rows.append([_ensure_dir_numeric(r[c]) for c in FEATURE_COLS])
                labels.append(r["diagnosis_label"].strip())
                urg.append(r["urgency_level"].strip())
            except KeyError:
                continue
    return rows, labels, urg


def _train(force: bool = False) -> bool:
    with _lock:
        if _state["ready"] and not force:
            return True
        if not os.path.exists(DATASET_PATH):
            _state["error"] = "dataset_missing"
            return False
        try:
            from sklearn.ensemble import RandomForestClassifier
            X, y, y2 = _load_rows()
            if len(X) < 50:
                _state["error"] = "dataset_too_small"
                return False
            m1 = RandomForestClassifier(n_estimators=160, max_depth=14, random_state=2077, n_jobs=1)
            m1.fit(X, y)
            m2 = RandomForestClassifier(n_estimators=120, max_depth=12, random_state=77, n_jobs=1)
            m2.fit(X, y2)
            _state.update(dx_model=m1, urg_model=m2, ready=True, error=None)
            return True
        except Exception as e:  # pragma: no cover
            _state["error"] = str(e)
            return False


def is_ready() -> bool:
    return _state["ready"] or _train()


def build_features(detected: dict, profile: dict, vitals: dict | None = None) -> list[float]:
    """ساخت بردار ویژگی از متن کاربر (detect_symptoms) + پروفایل."""
    p = profile or {}
    present = detected.get("present", {})
    gender = 1.0 if str(p.get("gender", "")).strip() in ("مرد", "male", "m", "1") else 0.0
    try:
        age = float(p.get("age") or 35)
    except (TypeError, ValueError):
        age = 35.0
    v = vitals or {}
    get = lambda k, d: float(v.get(k) or d) if v.get(k) else d
    red = 1.0 if detected.get("red_flag") else 0.0
    has = lambda sid: 1.0 if sid in present and not present[sid].get("denied") else 0.0
    temp = detected.get("temp_c") or (37.0 if not has("fever") else 38.0)
    return [
        age, gender, float(detected.get("duration_days") or 2.0), temp,
        get("heart_rate", 80 if has("fever") else 74),
        get("systolic_bp", 118), get("diastolic_bp", 76),
        get("glucose_mg_dl", 95 if not has("thirst") else 120),
        has("cough"), has("fever"), has("sore_throat"), has("runny_nose"),
        has("body_ache"), has("headache"), has("nausea"), has("vomiting"),
        has("diarrhea"), has("abdominal_pain"), has("dysuria"), has("urinary_frequency"),
        has("skin_itch"), has("rash"), has("sneezing"), has("anxiety"),
        has("chest_pain"), has("shortness_of_breath"), red,
    ]


def predict(detected: dict, profile: dict, vitals: dict | None = None, top_k: int = 3) -> list[dict[str, Any]] | None:
    """پیش‌بینی لیبل از دیتاست مصنوعی؛ None یعنی مدل در دسترس نیست."""
    if not is_ready():
        return None
    if not any(not i.get("denied") for i in detected.get("present", {}).values()):
        return []
    try:
        X = [build_features(detected, profile, vitals)]
        probs = _state["dx_model"].predict_proba(X)[0]
        classes = _state["dx_model"].classes_
        pairs = sorted(zip(classes, probs), key=lambda z: z[1], reverse=True)[:top_k]
        urg = str(_state["urg_model"].predict(X)[0])
        return [{"label": c, "percent": round(float(p) * 100.0, 1), "urgency": urg} for c, p in pairs]
    except Exception:
        return None


def retrain() -> bool:
    """آموزش مجدد (بعد از تغییر دیتاست)."""
    with _lock:
        _state["ready"] = False
    return _train(force=True)


def status() -> dict:
    return {"ready": _state["ready"], "error": _state["error"], "dataset": os.path.basename(DATASET_PATH)}
