# -*- coding: utf-8 -*-
"""
doctor_referral.py — گزارش ارجاع قابل چاپ برای پزشک (referral_report.html).
گزارش شامل: پروفایل، علائم حیاتی، علائم فعلی، ارزیابی احتمالی، سوالات باز، سلب مسئولیت.
"""
from __future__ import annotations

import os
from typing import Any

from common_2077 import APP_VERSION, DATA_DIR, MEDICAL_DISCLAIMER, fa_digits, now_iso

OUT_PATH = os.path.join(DATA_DIR, "referral_report.html")


def _esc(s: Any) -> str:
    return (str(s or "")).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generate(profile: dict | None = None, vitals: list[dict] | None = None,
             symptoms_fa: list[str] | None = None, candidates: list[dict] | None = None,
             dialogue_summary: dict | None = None, labs_text: str = "") -> dict[str, Any]:
    from health_vitals import history, trend
    from patient_profile import load_profile
    p = profile or load_profile()
    vit = vitals if vitals is not None else history(8)
    tr = trend()

    rows_p = "".join(
        f"<tr><th>{fa}</th><td>{_esc(p.get(k, '—'))}</td></tr>"
        for k, fa in (("name", "نام"), ("age", "سن"), ("gender", "جنسیت"), ("weight_kg", "وزن (kg)"),
                      ("height_cm", "قد (cm)"), ("conditions", "بیماری زمینه‌ای"),
                      ("allergies", "حساسیت‌ها"), ("medications", "داروهای فعلی")))
    rows_v = ""
    for v in vit[:8]:
        rows_v += "<tr>"+ "".join(f"<td>{fa_digits(v.get(key, '—'))}</td>" for key in
                                   ("systolic_bp", "diastolic_bp", "heart_rate", "temp_c", "weight_kg", "glucose")) + "</tr>"
    sym = "، ".join(_esc(s) for s in (symptoms_fa or [])) or "—"
    cands = candidates or []
    rows_c = "".join(
        f"<tr><td>{_esc(c.get('fa'))}</td><td>{fa_digits(c.get('percent', 0))}٪</td>"
        f"<td>{_esc({'emergency': 'فوری', 'urgent': 'اهمیت بالا', 'routine': 'روتین'}.get(c.get('urgency'), '—'))}</td>"
        f"<td>{_esc('، '.join(c.get('matched_symptoms_fa', [])))}</td></tr>"
        for c in cands[:5]) or "<tr><td colspan='4'>ارزیابی احتمالی ثبت نشده</td></tr>"
    dlg = dialogue_summary or {}
    open_q = ""
    if dlg.get("symptoms_fa"):
        open_q += "<li>توضیح بیشتر درباره: "+ _esc("، ".join(dlg["symptoms_fa"][:8])) + "</li>"
    open_q += "<li>بررسی معاینه‌ای و در صورت نیاز آزمایش/تصویربرداری</li>"
    tr_html = "".join(f"<li>{fa}: از {fa_digits(v['first'])} به {fa_digits(v['last'])} ({_esc(v['dir_fa'])})</li>"
                      for fa, v in (("فشار سیستولیک", tr.get("systolic_bp", {})), ("وزن", tr.get("weight_kg", {})),
                                    ("قند خون", tr.get("glucose", {}))) if v)
    labs_html = f"<pre class='labs'>{_esc(labs_text)}</pre>" if labs_text else "<p class='muted'>ثبت نشده</p>"

    html = f"""<!DOCTYPE html><html lang="fa"dir="rtl"><head><meta charset="utf-8">
<meta name="viewport"content="width=device-width, initial-scale=1">
<title>گزارش ارجاع — NexusMed 2077</title>
<style>
@page{{size:A4;margin:16mm}}
body{{font-family:Tahoma,'Segoe UI',sans-serif;color:#12203a;margin:24px;line-height:1.9}}
h1{{color:#0a5bd3;font-size:20px;margin-bottom:2px}} h2{{font-size:15px;color:#0a5bd3;border-bottom:2px solid #dce7ff;padding-bottom:4px;margin-top:22px}}
table{{width:100%;border-collapse:collapse;font-size:13px}} th,td{{border:1px solid #d5e0f2;padding:6px 8px;text-align:right}}
th{{background:#eef4ff;width:28%}} .muted{{color:#7a8aa5}} .labs{{background:#f6f9ff;border:1px solid #d5e0f2;padding:10px;white-space:pre-wrap;font-family:inherit}}
.meta{{font-size:12px;color:#7a8aa5}} .sign{{margin-top:36px;display:flex;justify-content:space-between}}
@media print{{.noprint{{display:none}}}}
</style></head><body>
<h1> گزارش ارجاع پزشکی</h1>
<p class="meta">تولیدشده توسط NexusMed 2077 (نسخه {fa_digits(APP_VERSION)}) — {now_iso()}</p>
<h2>۱) مشخصات بیمار</h2><table>{rows_p}</table>
<h2>۲) علائم حیاتی اخیر</h2>
<table><tr><th>سیستول</th><th>دیاستول</th><th>نبض</th><th>دمای بدن</th><th>وزن</th><th>قند</th></tr>
{rows_v or "<tr><td colspan='6'>ثبت نشده</td></tr>"}</table>
<ul>{tr_html}</ul>
<h2>۳) علائم فعلی گزارش‌شده توسط بیمار</h2><p>{sym}</p>
<h2>۴) ارزیابی احتمالی دستیار هوشمند (غیرتشخیصی)</h2>
<table><tr><th>احتمال مطرح</th><th>احتمال نسبی</th><th>اهمیت</th><th>علائم منطبق</th></tr>{rows_c}</table>
<h2>۵) نتایج آزمایش (متن بیمار)</h2>{labs_html}
<h2>۶) درخواست از پزشک محترم</h2><ul>{open_q}</ul>
<p class="sign"><span>امضای پزشک: ..................</span><span>تاریخ: ..................</span></p>
<hr><p class="muted">{_esc(MEDICAL_DISCLAIMER)} این گزارش صرفاً جمع‌بندی اطلاعاتی بیمار است و جایگزین معاینه، پرسش‌های بالینی و نظر پزشک نیست.</p>
<p class="noprint muted"> برای چاپ: Ctrl+P</p>
</body></html>"""
    try:
        with open(OUT_PATH, "w", encoding="utf-8") as f:
            f.write(html)
        return {"ok": True, "path": OUT_PATH, "html": html}
    except Exception as e:
        return {"ok": False, "message_fa": "خطا در ذخیره‌ی گزارش: "+ str(e)[:100], "html": html}
