# -*- coding: utf-8 -*-
"""
doctor_referral.py — printable bilingual referral report (referral_report.html).
Sections: profile, vitals, current symptoms, probabilistic assessment, labs,
requests to the physician, disclaimer.
"""
from __future__ import annotations

import os
from typing import Any

from common_2077 import APP_VERSION, DATA_DIR, MEDICAL_DISCLAIMER, fa_digits, now_iso
from i18n import is_fa

OUT_PATH = os.path.join(DATA_DIR, "referral_report.html")

_CSS = """
@page{size:A4;margin:16mm}
body{font-family:Tahoma,'Segoe UI',sans-serif;color:#12203a;margin:24px;line-height:1.9}
h1{color:#0a5bd3;font-size:20px;margin-bottom:2px}
h2{font-size:15px;color:#0a5bd3;border-bottom:2px solid #dce7ff;padding-bottom:4px;margin-top:22px}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border:1px solid #d5e0f2;padding:6px 8px;text-align:start}
th{background:#eef4ff;width:28%}
.muted{color:#7a8aa5}
.labs{background:#f6f9ff;border:1px solid #d5e0f2;padding:10px;white-space:pre-wrap;font-family:inherit}
.meta{font-size:12px;color:#7a8aa5}
.sign{margin-top:36px;display:flex;justify-content:space-between}
@media print{.noprint{display:none}}
"""


def _esc(s: Any) -> str:
    return (str(s or "")).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generate(profile: dict | None = None, vitals: list[dict] | None = None,
             symptoms: list[str] | None = None, candidates: list[dict] | None = None,
             dialogue_summary: dict | None = None, labs_text: str = "") -> dict[str, Any]:
    from health_vitals import history, trend
    from patient_profile import load_profile
    fa = is_fa()
    p = profile or load_profile()
    vit = vitals if vitals is not None else history(8)
    tr = trend()
    dlg = dialogue_summary or {}
    syms = symptoms or dlg.get("symptoms") or dlg.get("symptoms_fa") or []

    L = {
        "title": "گزارش ارجاع پزشکی" if fa else "Medical Referral Report",
        "h_profile": "۱) مشخصات بیمار" if fa else "1) Patient details",
        "h_vitals": "۲) علائم حیاتی اخیر" if fa else "2) Recent vitals",
        "h_symptoms": "۳) علائم فعلی گزارش‌شده" if fa else "3) Current symptoms reported",
        "h_assess": "۴) ارزیابی احتمالی دستیار (غیرتشخیصی)" if fa else "4) Assistant's probabilistic assessment (not a diagnosis)",
        "h_labs": "۵) نتایج آزمایش (متن بیمار)" if fa else "5) Lab results (patient's text)",
        "h_req": "۶) درخواست از پزشک محترم" if fa else "6) Request to the physician",
        "th_likely": "احتمال مطرح" if fa else "Possibility",
        "th_prob": "احتمال نسبی" if fa else "Relative likelihood",
        "th_urg": "اهمیت" if fa else "Urgency",
        "th_match": "علائم منطبق" if fa else "Matched symptoms",
        "th_bp": "فشار (سیس/دیاس)" if fa else "BP (sys/dia)",
        "th_hr": "نبض" if fa else "Pulse",
        "th_temp": "دمای بدن" if fa else "Temp",
        "th_weight": "وزن" if fa else "Weight",
        "th_glucose": "قند" if fa else "Glucose",
        "not_recorded": "ثبت نشده" if fa else "not recorded",
        "print_hint": "برای چاپ: Ctrl+P" if fa else "To print: Ctrl+P",
        "sign_doc": "امضای پزشک: .................." if fa else "Physician signature: ..................",
        "sign_date": "تاریخ: .................." if fa else "Date: ..................",
    }
    URG = {"emergency": "فوری" if fa else "urgent", "urgent": "اهمیت بالا" if fa else "high priority",
           "routine": "روتین" if fa else "routine"}

    fields = (("name", "نام"), ("age", "سن"), ("gender", "جنسیت"), ("weight_kg", "وزن (kg)"),
              ("height_cm", "قد (cm)"), ("conditions", "بیماری زمینه‌ای"),
              ("allergies", "حساسیت‌ها"), ("medications", "داروهای فعلی")) if fa else \
             (("name", "Name"), ("age", "Age"), ("gender", "Sex"), ("weight_kg", "Weight (kg)"),
              ("height_cm", "Height (cm)"), ("conditions", "Conditions"),
              ("allergies", "Allergies"), ("medications", "Current medications"))
    rows_p = "".join(f"<tr><th>{lbl}</th><td>{_esc(p.get(k, '—'))}</td></tr>" for k, lbl in fields)

    rows_v = ""
    for v in vit[:8]:
        cells = []
        for key in ("systolic_bp", "diastolic_bp", "heart_rate", "temp_c", "weight_kg", "glucose"):
            raw = v.get(key, "—")
            cells.append(fa_digits(raw) if fa else str(raw))
        rows_v += "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"

    sym_txt = "، ".join(_esc(s) for s in syms) if fa else ", ".join(_esc(s) for s in syms)

    def _pct(c):
        return f"{fa_digits(c.get('percent', 0))}٪" if fa else f"{c.get('percent', 0)}%"

    rows_c = "".join(
        f"<tr><td>{_esc(c.get('name') or c.get('fa'))}</td><td>{_pct(c)}</td>"
        f"<td>{_esc(URG.get(c.get('urgency'), '—'))}</td>"
        f"<td>{_esc(('، ' if fa else ', ').join(c.get('matched_symptoms', [])))}</td></tr>"
        for c in (candidates or [])[:5]) or f"<tr><td colspan='4'>{L['not_recorded']}</td></tr>"

    def _tr_li(label, v):
        if not v:
            return ""
        if fa:
            return f"<li>{label}: از {fa_digits(v['first'])} به {fa_digits(v['last'])} ({_esc(v['dir_fa'])})</li>"
        return f"<li>{label}: from {v['first']} to {v['last']} ({_esc(v['dir_fa'])})</li>"

    tr_html = (_tr_li("فشار سیستولیک" if fa else "Systolic BP", tr.get("systolic_bp", {}))
               + _tr_li("وزن" if fa else "Weight", tr.get("weight_kg", {}))
               + _tr_li("قند خون" if fa else "Blood glucose", tr.get("glucose", {})))

    open_q = ""
    if syms:
        open_q += "<li>" + ("توضیح بیشتر درباره: " if fa else "Further assessment of: ") + _esc("، ".join(syms[:8]) if fa else ", ".join(syms[:8])) + "</li>"
    open_q += "<li>" + ("بررسی معاینه‌ای و در صورت نیاز آزمایش/تصویربرداری" if fa
                        else "Physical examination, and labs or imaging if indicated") + "</li>"

    labs_html = f"<pre class='labs'>{_esc(labs_text)}</pre>" if labs_text else f"<p class='muted'>{L['not_recorded']}</p>"
    lang, direction = ("fa", "rtl") if fa else ("en", "ltr")
    tail = ("این گزارش صرفاً جمع‌بندی اطلاعاتی بیمار است و جایگزین معاینه، پرسش‌های بالینی و نظر پزشک نیست." if fa
            else "This report is only a summary of patient-reported information; it does not replace examination, clinical questions or medical judgment.")

    html = f"""<!DOCTYPE html><html lang="{lang}" dir="{direction}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Referral - NexusMed 2077</title>
<style>{_CSS}</style></head><body>
<h1>{L['title']}</h1>
<p class="meta">NexusMed 2077 v{fa_digits(APP_VERSION) if fa else APP_VERSION} - {now_iso()}</p>
<h2>{L['h_profile']}</h2><table>{rows_p}</table>
<h2>{L['h_vitals']}</h2>
<table><tr><th>{L['th_bp']}</th><th>{L['th_hr']}</th><th>{L['th_temp']}</th><th>{L['th_weight']}</th><th>{L['th_glucose']}</th></tr>
{rows_v or f"<tr><td colspan='5'>{L['not_recorded']}</td></tr>"}</table>
<ul>{tr_html}</ul>
<h2>{L['h_symptoms']}</h2><p>{sym_txt or L['not_recorded']}</p>
<h2>{L['h_assess']}</h2>
<table><tr><th>{L['th_likely']}</th><th>{L['th_prob']}</th><th>{L['th_urg']}</th><th>{L['th_match']}</th></tr>{rows_c}</table>
<h2>{L['h_labs']}</h2>{labs_html}
<h2>{L['h_req']}</h2><ul>{open_q}</ul>
<p class="sign"><span>{L['sign_doc']}</span><span>{L['sign_date']}</span></p>
<hr><p class="muted">{_esc(MEDICAL_DISCLAIMER())} {tail}</p>
<p class="noprint muted">{L['print_hint']}</p>
</body></html>"""
    try:
        with open(OUT_PATH, "w", encoding="utf-8") as f:
            f.write(html)
        return {"ok": True, "path": OUT_PATH, "html": html}
    except Exception as e:
        return {"ok": False, "message_fa": "Error saving the report: " + str(e)[:100], "html": html}
