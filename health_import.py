"""
health_import.py — imports health data from CSV exports of smartwatches
and fitness apps (Google Fit, Apple Health CSV exports, blood-pressure and
glucose meters) into the vitals history, with automatic column detection.
"""
from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any

from common_2077 import DATA_DIR, read_json, write_json, normalize
from i18n import is_fa

_METRICS = {
    "systolic_bp": ["systolic", "sbp", "فشار سیستولیک", "فشار بالا", "systolic blood pressure"],
    "diastolic_bp": ["diastolic", "dbp", "فشار دیاستولیک", "فشار پایین", "diastolic blood pressure"],
    "heart_rate": ["heart rate", "heart_rate", "pulse", "hr", "ضربان", "نبض"],
    "glucose": ["glucose", "blood sugar", "bs", "قند", "گلوکز", "fbs", "بالا قند"],
    "weight_kg": ["weight", "weight kg", "وزن", "kg"],
    "spo2": ["spo2", "sp o2", "oxygen", "o2 sat", "اکسیژن", "اشباع اکسیژن"],
    "temp_c": ["temperature", "temp", "دما", "حرارت", "تب"],
    "steps": ["steps", "قدم"],
}
_DATE_COLS = ["date", "time", "datetime", "timestamp", "تاریخ", "زمان", "تاریخ زمان", "date time"]
_DATE_FORMATS = ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S",
                 "%Y-%m-%d", "%Y/%m/%d %H:%M", "%Y/%m/%d", "%d/%m/%Y %H:%M", "%d/%m/%Y",
                 "%m/%d/%Y %H:%M", "%m/%d/%Y", "%d.%m.%Y", "%Y.%m.%d")


def _detect_dialect(sample: str) -> csv.Dialect:
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t")
    except Exception:
        class _Semi(csv.excel):
            delimiter = ";"
        return _Semi()


def _match_col(name: str, candidates: list[str]) -> bool:
    n = normalize(name)
    if not n:
        return False
    for c in candidates:
        cn = normalize(c)
        if cn and cn in n:
            return True
    return False


def _parse_date(s: str) -> str:
    s = str(s or "").strip()
    if not s:
        return ""
    s2 = normalize(s)
    s2 = s2.replace(" am", " AM").replace(" pm", " PM")
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s2, fmt).isoformat(timespec="minutes")
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s2.replace("Z", "+00:00")).astimezone().isoformat(timespec="minutes")
    except Exception:
        return ""


def _parse_val(s: str) -> float | None:
    s = str(s or "").strip()
    if not s or s in ("-", "--", "NA", "N/A", "null"):
        return None
    s = normalize(s).replace(" ", "")
    s = s.rstrip("%")
    try:
        v = float(s)
        return v
    except ValueError:
        return None


def _extract(text: str) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    text = text.lstrip("﻿")
    reader = csv.reader(io.StringIO(text), dialect=_detect_dialect(text[:4000]))
    rows = [r for r in reader if any((c or "").strip() for c in r)]
    if not rows:
        return [], [], []
    header = [h.strip() for h in rows[0]]
    col_map: dict[str, int] = {}
    date_idx = -1
    for i, h in enumerate(header):
        if date_idx < 0 and _match_col(h, _DATE_COLS):
            date_idx = i
            continue
        for metric, names in _METRICS.items():
            if metric not in col_map and _match_col(h, names):
                col_map[metric] = i
    entries: list[dict[str, Any]] = []
    for r in rows[1:]:
        if not any((c or "").strip() for c in r):
            continue
        e: dict[str, Any] = {}
        if date_idx >= 0 and date_idx < len(r):
            ts = _parse_date(r[date_idx])
            if ts:
                e["ts"] = ts
        for metric, i in col_map.items():
            if i < len(r):
                v = _parse_val(r[i])
                if v is not None:
                    e[metric] = round(v, 1)
        if len(e) >= 1 and (any(k in e for k in _METRICS) or "ts" in e):
            if any(k in e for k in _METRICS):
                entries.append(e)
    return header, list(col_map.keys()), entries


def preview(csv_text: str, limit: int = 5) -> dict[str, Any]:
    fa = is_fa()
    try:
        header, metrics, entries = _extract(str(csv_text or ""))
    except Exception as e:
        return {"ok": False, "message_fa": f"خطا در خواندن CSV: {e}" if fa else f"CSV parse error: {e}"}
    if not entries:
        return {"ok": False, "message_fa": ("هیچ ستون قابل تشخیصی پیدا نشد. ستون‌ها باید شامل تاریخ و یکی از این‌ها باشند: "
                                            "systolic, diastolic, heart rate, glucose, weight, spo2, temperature, steps."
                                            if fa else "No recognizable columns. Include a date column plus one of: "
                                            "systolic, diastolic, heart rate, glucose, weight, spo2, temperature, steps.")}
    return {"ok": True, "detected_columns": header, "detected_metrics": metrics,
            "total_rows": len(entries), "sample": entries[:max(1, int(limit))],
            "message_fa": (f"{len(entries)} ردیف پیدا شد — متریک‌ها: {', '.join(metrics)}"
                           if fa else f"{len(entries)} rows found - metrics: {', '.join(metrics)}")}


def commit(csv_text: str) -> dict[str, Any]:
    fa = is_fa()
    pv = preview(csv_text)
    if not pv.get("ok"):
        return pv
    _, _, entries = _extract(str(csv_text or ""))
    from health_vitals import HISTORY_PATH as VITALS_PATH
    hist = read_json(VITALS_PATH, default=[]) or []
    added = 0
    for e in entries:
        entry = dict(e)
        entry.setdefault("ts", datetime.now().isoformat(timespec="minutes"))
        hist.append(entry)
        added += 1
    hist = hist[-2000:]
    if write_json(VITALS_PATH, hist):
        return {"ok": True, "added": added, "message_fa": (f"{added} ردیف به تاریخچه‌ی علائم حیاتی اضافه شد."
                                                            if fa else f"{added} rows added to the vitals history.")}
    return {"ok": False, "message_fa": "نوشتن در فایل تاریخچه ناموفق بود." if fa
            else "Could not write the history file."}


def import_file(path: str, do_commit: bool = False) -> dict[str, Any]:
    fa = is_fa()
    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
            text = f.read()
    except Exception as e:
        return {"ok": False, "message_fa": f"{e}"}
    if do_commit:
        return commit(text)
    return preview(text)
