# -*- coding: utf-8 -*-
"""
lab_tests.py — تجزیه‌ی متن/خطوط آزمایش، مقایسه با محدوده‌ی مرجع و تفسیر فارسی.
مثال ورودی: «FBS 132» یا «هموگلوبین ۱۰.۵» یا «TSH 6.2 mIU/L»
"""
from __future__ import annotations

import re
from typing import Any

from common_2077 import fa_digits
from lab_catalog import RANGE_NOTE, find_test

_NUM = r"(\d{1,5}(?:[.,]\d{1,2})?)"
LINE_RE = re.compile(r"([A-Za-z0-9\- آ-ی‌]{2,30}?)\s*[:=]?\s*"+ _NUM + r"\s*([A-Za-z/%µ×°]*.*)?")
NUM_ONLY = re.compile(_NUM)

CRITICAL_RULES = [
    ("k", 6.5, "پتاسیم بحرانی بالا — خطر ریتم قلب؛ اورژانس", 2.5, "پتاسیم بحرانی پایین — خطر ریتم قلب؛ اورژانس"),
    ("na", 155, "سدیم بحرانی بالا — اورژانس", 120, "سدیم بحرانی پایین — اورژانس"),
    ("glucose", 400.0, "قند بسیار بالا — احتمال کتواسیدوز/هایپراسمولار؛ اورژانس", 50.0, "قند بسیار پایین — اورژانس"),
    ("hb", None, "", 7.0, "هموگلوبین بسیار پایین — ارزیابی فوری"),
    ("plt", 1000.0, "", 50.0, "پلاکت بسیار پایین — خطر خونریزی؛ فوری"),
]

ZONES = {
    "fbs": [(100, 125, "محدوده‌ی پیش‌دیابت (۱۰۰–۱۲۵). تکرار آزمایش و مشورت پزشک."),
            (126, 10**9, "در محدوده‌ی دیابت (≥۱۲۶ در دو نوبت اندازه‌گیری). حتماً با پزشک پیگیری کن.")],
    "hba1c": [(5.7, 6.4, "پیش‌دیابت (۵٫۷–۶٫۴)."), (6.5, 10**9, "در محدوده‌ی دیابت (≥۶٫۵) — نیاز به ارزیابی پزشک.")],
    "ldl": [(100, 129, "بالاتر از هدف برای افراد معمولی."), (160, 10**9, "بالا — ارزیابی ریسک قلبی با پزشک.")],
    "tg": [(150, 199, "کمی بالا."), (200, 499, "بالا — سبک زندگی + پیگیری پزشک."), (500, 10**9, "بسیار بالا — خطر پانکراتیت؛ فوری")],
    "tsh": [(0.1, 0.39, "پایین‌تر از حد — احتمال پرکاری تیروئید؛ پیگیری."), (4.6, 10.0, "بالاتر از حد — احتمال کم‌کاری تیروئید؛ پیگیری."), (10.01, 10**9, "بالاتر از حد — ارزیابی تیروئید لازم است.")],
    "vitd": [(0, 20, "کمبود ویتامین D — مکمل با نظر پزشک."), (20, 29.9, "کافی نیست (نارسایی) — با پزشک مشورت کن.")],
    "ferritin": [(0, 15, "کمبود ذخایر آهن — با پزشک مشورت کن.")],
}


def parse_lines(text: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        # ابتدا نام آزمایش را جدا از عدد تطبیق می‌دهیم (مثل «K 6.9» یا «هموگلوبین ۱۰.۵»)
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
    lo, hi = t.get("lo"), t.get("hi")
    status, fa = "normal", "در محدوده‌ی مرجع"
    if lo is not None and val < lo:
        status, fa = "low", "پایین‌تر از محدوده‌ی مرجع"
    elif hi is not None and val > hi:
        status, fa = "high", "بالاتر از محدوده‌ی مرجع"
    zone_note = ""
    for loz, hiz, note in ZONES.get(key, []):
        if loz <= val <= hiz:
            zone_note = note
            break
    critical = ""
    for ckey, hi_c, hi_msg, lo_c, lo_msg in CRITICAL_RULES:
        if ckey == key or (ckey == "glucose" and key in ("fbs", "bs_random")):
            if hi_c and val >= float(hi_c):
                critical = critical or hi_msg
            if lo_c and val <= float(lo_c):
                critical = critical or lo_msg
    return {"key": key, "name_fa": t.get("fa", key), "value": val, "unit": t.get("unit", ""),
            "range": f"{lo}–{hi}" if lo is not None else "", "status": status, "status_fa": fa,
            "zone_fa": zone_note, "critical_fa": critical}


def interpret(results: list[dict[str, Any]]) -> dict[str, Any]:
    highs = [r for r in results if r["status"] in ("high", "low")]
    crits = [r for r in results if r.get("critical_fa")]
    summary: list[str] = []
    if crits:
        summary.append("مقدار بحرانی شناسایی شد: "+ "؛ ".join(f"{r['name_fa']}={r['value']} — {r['critical_fa']}" for r in crits))
        summary.append("لطفاً همین حالا با اورژانس یا پزشک تماس بگیر.")
    if highs:
        summary.append("موارد خارج از محدوده: "+ "، ".join(f"{r['name_fa']} ({r['status_fa']})" for r in highs))
    if not summary:
        summary.append("همه‌ی موارد شناسایی‌شده در محدوده‌ی مرجع بودند.")
    summary.append("این تفسیر عمومی است؛ تشخیص نهایی فقط توسط پزشک با معاینه و در نظر گرفتن سابقه‌ی شما انجام می‌شود.")
    return {"ok": True, "results": results, "summary_fa": summary, "note": RANGE_NOTE}
