"""
health_correlator.py — looks for relationships between the user's own data:
symptom diary entries vs vitals history (blood pressure, glucose, weight),
symptom frequency patterns and severity trends. Descriptive statistics only,
plain language, no causal claims.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from common_2077 import DATA_DIR, read_json, normalize
from i18n import is_fa

import os

DIARY_PATH = os.path.join(DATA_DIR, "symptom_diary.json")
VITALS_PATH = os.path.join(DATA_DIR, "vitals_history.json")

MIN_SYMPTOM_DAYS = 3
MIN_OTHER_SAMPLES = 2
METRIC_LABELS = {
    "systolic_bp": ("systolic BP", "فشار سیستولیک"),
    "diastolic_bp": ("diastolic BP", "فشار دیاستولیک"),
    "glucose": ("blood glucose", "قند خون"),
    "heart_rate": ("heart rate", "ضربان قلب"),
    "weight_kg": ("weight", "وزن"),
    "spo2": ("blood oxygen", "اکسیژن خون"),
}


def _date_key(ts: str) -> str:
    return str(ts or "")[:10]


def _norm_sym(name: str) -> str:
    return normalize(name)[:40]


def analyze() -> dict[str, Any]:
    fa = is_fa()
    diary = read_json(DIARY_PATH, default=[]) or []
    vitals = read_json(VITALS_PATH, default=[]) or []
    diary = [d for d in diary if isinstance(d, dict) and d.get("symptom")]
    if not diary:
        return {"ok": True, "findings": [],
                "message_fa": ("هنوز داده‌ای برای تحلیل نیست — علائم را در دفترچه‌ی علائم (ابزار سلامت) و فشار/قند را در علائم حیاتی ثبت کن تا الگوها را پیدا کنم."
                               if fa else "No data to analyze yet - log symptoms in the symptom diary (Health tools) and BP/glucose in Vitals so patterns can be found.")}
    days_by_sym: dict[str, set] = defaultdict(set)
    sev_by_sym: dict[str, list] = defaultdict(list)
    for d in diary:
        key = _norm_sym(d["symptom"])
        days_by_sym[key].add(_date_key(d.get("date") or d.get("ts") or ""))
        try:
            sev_by_sym[key].append(int(d.get("severity") or 5))
        except (TypeError, ValueError):
            sev_by_sym[key].append(5)
    sym_display = {}
    for d in diary:
        key = _norm_sym(d["symptom"])
        if key not in sym_display:
            sym_display[key] = str(d["symptom"]).strip()
    vitals_by_day: dict[str, dict] = {}
    for v in vitals:
        k = _date_key(v.get("ts") or "")
        if k:
            vitals_by_day.setdefault(k, {}).update(
                {m: v[m] for m in METRIC_LABELS if isinstance(v.get(m), (int, float))})
    findings: list[dict[str, Any]] = []
    for key, days in days_by_sym.items():
        name = sym_display.get(key) or key
        n = len(days)
        line = (f"{name}: {n} " + ("روز ثبت‌شده" if fa else "logged day(s)"))
        sev = sev_by_sym.get(key) or []
        if len(sev) >= 3:
            first, last = sum(sev[:3]) / 3.0, sum(sev[-3:]) / 3.0
            if last - first >= 1.5:
                line += (" — " + ("شدت آن در ادامه بیشتر شده است." if fa else "severity has been increasing."))
            elif first - last >= 1.5:
                line += (" — " + ("شدت آن در ادامه کمتر شده است." if fa else "severity has been decreasing."))
        findings.append({"type": "count", "text": line})
        hit_vals: dict[str, list] = defaultdict(list)
        miss_vals: dict[str, list] = defaultdict(list)
        for day, metrics in vitals_by_day.items():
            if not metrics:
                continue
            for m, val in metrics.items():
                (hit_vals[m] if day in days else miss_vals[m]).append(val)
        for m, vals in hit_vals.items():
            others = miss_vals.get(m) or []
            if len(vals) >= MIN_SYMPTOM_DAYS and len(others) >= MIN_OTHER_SAMPLES:
                avg_hit = sum(vals) / len(vals)
                avg_miss = sum(others) / len(others)
                diff = avg_hit - avg_miss
                spread = max(abs(avg_miss) * 0.05, 1.0)
                lbl = METRIC_LABELS[m][1] if fa else METRIC_LABELS[m][0]
                if diff > spread:
                    findings.append({"type": "correlation", "metric": m, "symptom": name,
                                     "text": (f"در روزهای {name}، میانگین {lbl} {round(avg_hit, 1)} بوده در برابر {round(avg_miss, 1)} در بقیه‌ی روزها."
                                              if fa else
                                              f"On {name} days, average {lbl} was {round(avg_hit, 1)} versus {round(avg_miss, 1)} on other days.")})
                elif -diff > spread:
                    findings.append({"type": "correlation", "metric": m, "symptom": name,
                                     "text": (f"در روزهای {name}، میانگین {lbl} پایین‌تر بوده: {round(avg_hit, 1)} در برابر {round(avg_miss, 1)}."
                                              if fa else
                                              f"On {name} days, average {lbl} was lower: {round(avg_hit, 1)} versus {round(avg_miss, 1)}.")})
    counts = {sym_display.get(k, k): len(v) for k, v in days_by_sym.items()}
    top = sorted(counts.items(), key=lambda x: -x[1])[:5]
    if len(findings) > 6:
        findings = findings[:6]
    note = ("این‌ها هم‌ربتگی‌های توصیفی داده‌های خودت هستند، نه علت‌شناسی؛ علت نهایی را پزشک تعیین می‌کند."
            if fa else "These are descriptive correlations in your own data, not causes; the final interpretation belongs to a doctor.")
    return {"ok": True, "findings": findings, "counts": dict(top),
            "diary_entries": len(diary), "vitals_days": len(vitals_by_day),
            "note_fa": note, "message_fa": ""}
