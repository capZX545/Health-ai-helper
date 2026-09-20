# -*- coding: utf-8 -*-
import json, os
from datetime import datetime

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
VITALS_FILE = os.path.join(DATA_DIR, "vitals_history.json")


def _load() -> list:
    try:
        return json.load(open(VITALS_FILE, encoding="utf-8"))
    except Exception:
        return []


def _svg_chart(points: list[tuple[str, float]], color: str, label: str,
               lo: float | None = None, hi: float | None = None,
               w: int = 600, h: int = 260, fa: bool = True) -> str:
    if not points:
        return ""
    vals = [v for _, v in points]
    vmin = min(vals + ([lo - 2] if lo else []))
    vmax = max(vals + ([hi + 2] if hi else []))
    if vmin == vmax:
        vmin, vmax = vmin - 1, vmax + 1
    pad_l, pad_r, pad_t, pad_b = 50, 20, 30, 40
    cw, ch = w - pad_l - pad_r, h - pad_t - pad_b
    n = len(points)

    def x(i):
        return pad_l + (cw * i / max(1, n - 1)) if n > 1 else pad_l + cw / 2

    def y(v):
        return pad_t + ch - (ch * (v - vmin) / (vmax - vmin))

    grid_lines = ""
    for gi in range(5):
        gv = vmin + (vmax - vmin) * gi / 4
        gy = y(gv)
        grid_lines += f'<line x1="{pad_l}" y1="{gy:.1f}" x2="{w-pad_r}" y2="{gy:.1f}" stroke="#16213e" stroke-width="1"/>'
        grid_lines += f'<text x="{pad_l-8}" y="{gy+4:.1f}" fill="#6b7fa3" font-size="11" text-anchor="end">{gv:.0f}</text>'

    ref = ""
    if lo is not None:
        ref += f'<line x1="{pad_l}" y1="{y(lo):.1f}" x2="{w-pad_r}" y2="{y(lo):.1f}" stroke="#3bff9e" stroke-width="1" stroke-dasharray="6,4" opacity="0.5"/>'
    if hi is not None:
        ref += f'<line x1="{pad_l}" y1="{y(hi):.1f}" x2="{w-pad_r}" y2="{y(hi):.1f}" stroke="#3bff9e" stroke-width="1" stroke-dasharray="6,4" opacity="0.5"/>'

    path = ""
    dots = ""
    labels = ""
    for i, (dt, v) in enumerate(points):
        px, py = x(i), y(v)
        if i == 0:
            path = f"M {px:.1f} {py:.1f}"
        else:
            path += f" L {px:.1f} {py:.1f}"
        dots += f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.5" fill="{color}" stroke="#04060c" stroke-width="1.5"/>'
        if n <= 12 or i % (n // 8 + 1) == 0:
            labels += f'<text x="{px:.1f}" y="{h-10}" fill="#6b7fa3" font-size="9" text-anchor="middle">{dt[5:10]}</text>'
        labels += f'<title>{dt} — {v}</title>'

    area = f'<path d="{path} L {x(n-1):.1f} {pad_t+ch} L {x(0):.1f} {pad_t+ch} Z" fill="{color}" opacity="0.08"/>'

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<rect width="{w}" height="{h}" fill="#070d18" rx="10"/>
{grid_lines}{ref}
<text x="{pad_l}" y="18" fill="{color}" font-size="13" font-weight="bold">{label}</text>
{area}
<path d="{path}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
{dots}{labels}
</svg>'''


def chart_systolic(n: int = 30, fa: bool = True) -> str:
    pts = [(r.get("date", r.get("ts", ""))[:10], r["bp"]["systolic"])
           for r in _load() if r.get("bp", {}).get("systolic")][-n:]
    return _svg_chart(pts, "#ff2a6d", "فشار سیستول / Systolic" if fa else "Systolic", None, 130, fa=fa)


def chart_diastolic(n: int = 30, fa: bool = True) -> str:
    pts = [(r.get("date", r.get("ts", ""))[:10], r["bp"]["diastolic"])
           for r in _load() if r.get("bp", {}).get("diastolic")][-n:]
    return _svg_chart(pts, "#ffd60a", "فشار دیاستول / Diastolic" if fa else "Diastolic", None, 85, fa=fa)


def chart_glucose(n: int = 30, fa: bool = True) -> str:
    pts = [(r.get("date", r.get("ts", ""))[:10], r["glucose"])
           for r in _load() if r.get("glucose")][-n:]
    return _svg_chart(pts, "#00f0ff", "قند خون / Glucose" if fa else "Glucose (mg/dL)", 70, 110, fa=fa)


def chart_weight(n: int = 30, fa: bool = True) -> str:
    pts = [(r.get("date", r.get("ts", ""))[:10], r["weight"])
           for r in _load() if r.get("weight")][-n:]
    return _svg_chart(pts, "#3bff9e", "وزن / Weight (kg)" if fa else "Weight (kg)", None, None, fa=fa)


def all_charts(n: int = 30, fa: bool = True) -> list[str]:
    return [c for c in (chart_systolic(n, fa), chart_diastolic(n, fa),
                        chart_glucose(n, fa), chart_weight(n, fa)) if c]


def charts_html(n: int = 30, fa: bool = True) -> str:
    charts = all_charts(n, fa)
    if not charts:
        return ""
    return "\n".join(charts)


def save_chart_html(path: str, n: int = 30, fa: bool = True) -> bool:
    body = charts_html(n, fa)
    if not body:
        return False
    html = f"""<!DOCTYPE html><html dir="{'rtl' if fa else 'ltr'}"><head><meta charset="utf-8">
<title>NexusMed — {'روند علائم حیاتی' if fa else 'Vitals Trends'}</title>
<style>body{{background:#04060c;font-family:'Vazirmatn','Segoe UI',Tahoma,sans-serif;padding:20px;display:flex;flex-wrap:wrap;gap:16px;justify-content:center}}
svg{{max-width:100%}}</style></head><body>{body}</body></html>"""
    open(path, "w", encoding="utf-8").write(html)
    return True
