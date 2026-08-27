"""
Visual lab results: an RTL-friendly HTML bar chart plus text output,
no external dependencies.
"""
from __future__ import annotations

import os
from typing import Any

from common_2077 import DATA_DIR, fa_digits, write_json
from lab_tests import interpret, parse_lines

from i18n import is_fa as _is_fa, pick as _pick

STATUS_COLOR = {"low": "#4da3ff", "normal": "#3bff9e", "high": "#ffb020", "critical": "#ff2a6d"}


def _num(v) -> str:
    return fa_digits(v) if _is_fa() else str(v)


def STATUS_FA() -> dict:
    return _pick({"en": {"low": "low", "normal": "normal", "high": "high", "critical": "critical"},
                  "fa": {"low": "پایین", "normal": "نرمال", "high": "بالا", "critical": "بحرانی"}})

_HTML_HEAD = """<DOCTYPE html><html lang="fa"dir="rtl"><head><meta charset="utf-8">
<title>NexusMed 2077 — گزارش آزمایش</title><style>
body{font-family:Tahoma,'Segoe UI',sans-serif;background:#0b1220;color:#d7e3ff;margin:0;padding:24px}
h1{color:#00f0ff;font-size:20px}.card{background:#111a2e;border:1px solid #1e2c4d;border-radius:12px;padding:14px;margin:10px 0}
.bar{height:14px;border-radius:7px;background:#1e2c4d;position:relative;overflow:hidden;margin-top:8px}
.fill{height:100%;border-radius:7px}
.range{position:absolute;top:-4px;width:2px;height:22px;background:#3bff9e88}
.v{font-size:18px;font-weight:bold}.sm{color:#6b7fa3;font-size:12px}
.crit{border-color:#ff2a6d}.warn{color:#ffd60a}
</style></head><body>
<h1> NexusMed 2077 — نمایشگر آزمایش</h1>"""

_HTML_FOOT = """<p class="sm"> تفسیر عمومی؛ ملاک نهایی نظر پزشک شماست. محدوده‌ها بین آزمایشگاه‌ها متفاوت است.</p>
</body></html>"""


def _pos_pct(val: float, lo: float, hi: float) -> float:
    span = max(hi - lo, 1e-9)
    return max(2.0, min(98.0, (val - lo + span * 0.15) / (span * 1.3) * 100.0))


_TITLE_FA = "نمایشگر آزمایش"
_TITLE_EN = "lab report viewer"


def _head() -> str:
    return _HTML_HEAD.replace("_TITLE_", _TITLE_FA if _is_fa() else _TITLE_EN)


def render_html(results: list[dict[str, Any]]) -> str:
    rows = []
    for r in results:
        try:
            lo, hi = [float(x) for x in (r.get("range") or "").split("–")]
        except Exception:
            lo, hi = 0.0, max(r.get("value", 1) * 1.5, 1.0)
        pct = _pos_pct(float(r["value"]), lo, hi)
        sf = STATUS_FA()
        color = STATUS_COLOR.get("critical" if r.get("critical_fa") else r["status"], "#3bff9e")
        zone = f"<div class='warn'>{r['zone_fa']}</div>" if r.get("zone_fa") else ""
        crit = f"<div class='warn' style='color:#ff2a6d'> {r['critical_fa']}</div>" if r.get("critical_fa") else ""
        rows.append(f"""<div class="card {'crit' if r.get('critical_fa') else ''}">
<b>{r['name_fa']}</b> — <span class="v"style="color:{color}">{_num(r['value'])} {r.get('unit','')}</span>
<span class="sm">({sf.get('critical' if r.get('critical_fa') else r['status'])} | ref {fa_digits(r.get('range',''))})</span>
<div class="bar"><div class="fill"style="width:{pct:.0f}%;background:{color}"></div></div>
{zone}{crit}</div>""")
    foot = ("General interpretation; your own doctor has the final word. Ranges differ between labs." if not _is_fa()
            else "تفسیر عمومی؛ ملاک نهایی نظر پزشک شماست. محدوده‌ها بین آزمایشگاه‌ها متفاوت است.")
    return _head() + "\n".join(rows) + _HTML_FOOT.replace("_FOOT_", foot)


def render_text(results: list[dict[str, Any]]) -> str:
    lines = []
    marks = ({"low": "[پایین]", "normal": "[نرمال]", "high": "[بالا]", "crit": "[بحرانی]"} if _is_fa()
             else {"low": "[low]", "normal": "[normal]", "high": "[high]", "crit": "[CRITICAL]"})
    for r in results:
        mark = marks.get(r["status"], "•")
        if r.get("critical_fa"):
            mark = marks["crit"]
        lines.append(f"{mark} {r['name_fa']}: {_num(r['value'])} {r.get('unit','')} — {r['status_fa']}"
                     + (f"| {r['zone_fa']}" if r.get("zone_fa") else "")
                     + (f"|  {r['critical_fa']}" if r.get("critical_fa") else ""))
    return "\n".join(lines)


def analyze_text(text: str, save_html: bool = False) -> dict[str, Any]:
    results = parse_lines(text)
    out = interpret(results)
    out["text_report"] = render_text(results)
    if save_html and results:
        html = render_html(results)
        path = os.path.join(DATA_DIR, "lab_report.html")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            out["html_path"] = path
        except Exception:
            pass
    return out
