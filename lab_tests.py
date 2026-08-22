# -*- coding: utf-8 -*-
"""
Parses lab text/lines, compares against reference ranges, explains in Persian.
Example input: "FBS 132" or "hemoglobin 10.5" or "TSH 6.2 mIU/L"
"""
from __future__ import annotations

import re
from typing import Any

from common_2077 import fa_digits
from lab_catalog import find_test
from lab_catalog import RANGE_NOTE  # noqa: F401  (callable)

_NUM = r"(\d{1,5}(?:[.,]\d{1,2})?)"
LINE_RE = re.compile(r"([A-Za-z0-9\- آ-ی‌]{2,30}?)\s*[:=]?\s*"+ _NUM + r"\s*([A-Za-z/%µ×°]*.*)?")
NUM_ONLY = re.compile(_NUM)

CRITICAL_RULES = [
    # (key, high threshold, (high msg en, fa), low threshold, (low msg en, fa))
    ("k", 6.5, ("critically high potassium - heart rhythm danger; emergency", "پتاسیم بحرانی بالا — خطر ریتم قلب؛ اورژانس"),
     2.5, ("critically low potassium - heart rhythm danger; emergency", "پتاسیم بحرانی پایین — خطر ریتم قلب؛ اورژانس")),
    ("na", 155, ("critically high sodium - emergency", "سدیم بحرانی بالا — اورژانس"),
     120, ("critically low sodium - emergency", "سدیم بحرانی پایین — اورژانس")),
    ("glucose", 400.0, ("very high sugar - possible ketoacidosis; emergency", "قند بسیار بالا — احتمال کتواسیدوز/هایپراسمولار؛ اورژانس"),
     50.0, ("very low sugar - emergency", "قند بسیار پایین — اورژانس")),
    ("hb", None, ("", ""), 7.0, ("very low hemoglobin - urgent assessment", "هموگلوبین بسیار پایین — ارزیابی فوری")),
    ("plt", 1000.0, ("", ""), 50.0, ("very low platelets - bleeding risk; urgent", "پلاکت بسیار پایین — خطر خونریزی؛ فوری")),
]

from i18n import is_fa as _is_fa

ZONES = {
    "fbs": [(100, 125, ("prediabetes range (100-125). Repeat the test and talk to a doctor.", "محدوده‌ی پیش‌دیابت (۱۰۰–۱۲۵). تکرار آزمایش و مشورت پزشک.")),
            (126, 10**9, ("diabetes range (126+ on two measurements). Follow up with a doctor.", "در محدوده‌ی دیابت (≥۱۲۶ در دو نوبت اندازه‌گیری). حتماً با پزشک پیگیری کن."))],
    "hba1c": [(5.7, 6.4, ("prediabetes (5.7-6.4).", "پیش‌دیابت (۵٫۷–۶٫۴).")),
              (6.5, 10**9, ("diabetes range (6.5+) - needs medical assessment.", "در محدوده‌ی دیابت (≥۶٫۵) — نیاز به ارزیابی پزشک."))],
    "ldl": [(100, 129, ("above target for average people.", "بالاتر از هدف برای افراد معمولی.")),
            (160, 10**9, ("high - heart risk assessment with a doctor.", "بالا — ارزیابی ریسک قلبی با پزشک."))],
    "tg": [(150, 199, ("slightly high.", "کمی بالا.")),
           (200, 499, ("high - lifestyle change plus medical follow-up.", "بالا — سبک زندگی + پیگیری پزشک.")),
           (500, 10**9, ("very high - pancreatitis risk; urgent.", "بسیار بالا — خطر پانکراتیت؛ فوری"))],
    "tsh": [(0.1, 0.39, ("below range - possible overactive thyroid; follow up.", "پایین‌تر از حد — احتمال پرکاری تیروئید؛ پیگیری.")),
            (4.6, 10.0, ("above range - possible underactive thyroid; follow up.", "بالاتر از حد — احتمال کم‌کاری تیروئید؛ پیگیری.")),
            (10.01, 10**9, ("above range - thyroid assessment needed.", "بالاتر از حد — ارزیابی تیروئید لازم است."))],
    "vitd": [(0, 20, ("vitamin D deficiency - supplement per doctor.", "کمبود ویتامین D — مکمل با نظر پزشک.")),
             (20, 29.9, ("insufficient - talk to a doctor.", "کافی نیست (نارسایی) — با پزشک مشورت کن."))],
    "ferritin": [(0, 15, ("low iron stores - talk to a doctor.", "کمبود ذخایر آهن — با پزشک مشورت کن."))],
}


def parse_lines(text: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        # first match the test name apart from the number ("K 6.9", "hemoglobin 10.5")
        line_en = line.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٫", "0123456789."))
        name_only = NUM_ONLY.sub("", line_en).strip(":=-–")
        t = find_test(name_only) or find_test(line_en)
        if not t:
            continue
        m = NUM_ONLY.search(line_en)
        if not m:
            continue
        try:
            val = float(m.group(1).replace(",", "."))
        except ValueError:
            continue
        results.append(evaluate(t["key"], val, t))
    return results


def evaluate(key: str, val: float, t: dict | None = None) -> dict[str, Any]:
    t = t or {}
    from i18n import is_fa, pick
    lo, hi = t.get("lo"), t.get("hi")
    fa_mode = is_fa()
    status = "normal"
    fa = "در محدوده‌ی مرجع" if fa_mode else "within reference range"
    if lo is not None and val < lo:
        status = "low"
        fa = "پایین‌تر از محدوده‌ی مرجع" if fa_mode else "below reference range"
    elif hi is not None and val > hi:
        status = "high"
        fa = "بالاتر از محدوده‌ی مرجع" if fa_mode else "above reference range"
    zone_note = ""
    for loz, hiz, note in ZONES.get(key, []):
        if loz <= val <= hiz:
            zone_note = pick(note)
            break
    critical = ""
    for ckey, hi_c, hi_msg, lo_c, lo_msg in CRITICAL_RULES:
        if ckey == key or (ckey == "glucose" and key in ("fbs", "bs_random")):
            if hi_c and val >= float(hi_c):
                critical = critical or pick(hi_msg)
            if lo_c and val <= float(lo_c):
                critical = critical or pick(lo_msg)
    name = t.get("fa", key) if fa_mode else (t.get("en") or t.get("fa", key))
    rng = (f"{lo}–{hi}" if fa_mode else f"{lo}-{hi}") if lo is not None else ""
    return {"key": key, "name_fa": name, "value": val, "unit": t.get("unit", ""),
            "range": rng, "status": status, "status_fa": fa,
            "zone_fa": zone_note, "critical_fa": critical}


def interpret(results: list[dict[str, Any]]) -> dict[str, Any]:
    highs = [r for r in results if r["status"] in ("high", "low")]
    crits = [r for r in results if r.get("critical_fa")]
    summary: list[str] = []
    fa_mode = _is_fa()
    if crits:
        summary.append(("Critical values detected: " if not fa_mode else "مقدار بحرانی شناسایی شد: ") +
                       ("; ".join(f"{r['name_fa']}={r['value']} - {r['critical_fa']}" for r in crits)))
        summary.append("Please contact emergency services or a doctor right now." if not fa_mode else "لطفاً همین حالا با اورژانس یا پزشک تماس بگیر.")
    if highs:
        summary.append(("Out-of-range items: " if not fa_mode else "موارد خارج از محدوده: ") +
                       (", ".join(f"{r['name_fa']} ({r['status_fa']})" for r in highs)))
    if not summary:
        summary.append("Everything detected was within the reference range." if not fa_mode else "همه‌ی موارد شناسایی‌شده در محدوده‌ی مرجع بودند.")
    summary.append("This is a general interpretation; the final call belongs to your doctor." if not fa_mode
                   else "این تفسیر عمومی است؛ تشخیص نهایی فقط توسط پزشک با معاینه و در نظر گرفتن سابقه‌ی شما انجام می‌شود.")
    return {"ok": True, "results": results, "summary_fa": summary, "note": RANGE_NOTE()}
