"""
vaccine_schedule.py — Iranian national immunization program (EPI) for
children: full schedule from birth, per-child status by birth date and
next-due calculation. The child's vaccination card and the health center
remain the final authority.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from i18n import is_fa

SCHEDULE: list[dict[str, Any]] = [
    {"age_months": 0, "en": "At birth", "fa": "بدو تولد",
     "vaccines": [("BCG (tuberculosis)", "ب.ث.ژ (سل)"),
                  ("Hepatitis B dose 1", "هپاتیت B نوبت ۱"),
                  ("Oral polio (OPV-0)", "فلج اطفال خوراکی نوبت صفر")]},
    {"age_months": 2, "en": "2 months", "fa": "۲ ماهگی",
     "vaccines": [("Pentavalent 1 (DTP-HepB-Hib)", "پنج‌گانه نوبت ۱"),
                  ("Oral polio (OPV-1)", "فلج اطفال خوراکی نوبت ۱"),
                  ("Rotavirus 1", "روتاویروس نوبت ۱"),
                  ("PCV 1 (pneumococcal)", "پنوموکوک نوبت ۱")]},
    {"age_months": 4, "en": "4 months", "fa": "۴ ماهگی",
     "vaccines": [("Pentavalent 2", "پنج‌گانه نوبت ۲"),
                  ("Oral polio (OPV-2)", "فلج اطفال خوراکی نوبت ۲"),
                  ("Injectable polio (IPV-1)", "فلج اطفال تزریقی نوبت ۱"),
                  ("Rotavirus 2", "روتاویروس نوبت ۲"),
                  ("PCV 2", "پنوموکوک نوبت ۲")]},
    {"age_months": 6, "en": "6 months", "fa": "۶ ماهگی",
     "vaccines": [("Pentavalent 3", "پنج‌گانه نوبت ۳"),
                  ("Oral polio (OPV-3)", "فلج اطفال خوراکی نوبت ۳"),
                  ("Rotavirus 3", "روتاویروس نوبت ۳"),
                  ("Injectable polio (IPV-2)", "فلج اطفال تزریقی نوبت ۲"),
                  ("Measles dose zero (selected provinces)", "سرخک نوبت صفر (استان‌های منتخب)")]},
    {"age_months": 12, "en": "12 months", "fa": "۱۲ ماهگی",
     "vaccines": [("MMR 1 (measles-rubella-mumps)", "MMR نوبت ۱ (سرخک، سرخجه، اوریون)"),
                  ("PCV 3", "پنوموکوک نوبت ۳")]},
    {"age_months": 18, "en": "18 months", "fa": "۱۸ ماهگی",
     "vaccines": [("DTP booster", "سه‌گانه یادآور"),
                  ("Oral polio (OPV-4)", "فلج اطفال خوراکی نوبت ۴"),
                  ("MMR 2", "MMR نوبت ۲")]},
    {"age_months": 72, "en": "5-6 years", "fa": "۵ تا ۶ سالگی",
     "vaccines": [("DTP booster 2", "سه‌گانه یادآور ۲"),
                  ("Oral polio (OPV-5)", "فلج اطفال خوراکی نوبت ۵")]},
]

CATCHUP_NOTE = (
    "If a dose is delayed there is no need to restart the series; the program simply continues from where it stopped,"
    " with the intervals set by the health center."
    if not is_fa() else
    "اگر نوبتی عقب افتاده باشد نیازی به شروع مجدد نیست؛ برنامه از همان‌جا با فاصله‌های تعیین‌شده‌ی مرکز بهداشت ادامه پیدا می‌کند."
)


def _parse_date(s: str) -> date | None:
    s = str(s or "").strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y", "%Y.%m.%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _months_between(b: date, t: date) -> int:
    m = (t.year - b.year) * 12 + (t.month - b.month)
    if t.day < b.day:
        m -= 1
    return m


def for_child(birth_date: str, today: date | None = None) -> dict[str, Any]:
    fa = is_fa()
    b = _parse_date(birth_date)
    if b is None:
        return {"ok": False, "message_fa": "تاریخ تولد را به شکل YYYY-MM-DD وارد کن." if fa
                else "Enter the birth date as YYYY-MM-DD."}
    t = today or date.today()
    if b > t:
        return {"ok": False, "message_fa": "تاریخ تولد در آینده است." if fa else "The birth date is in the future."}
    months = _months_between(b, t)
    age_txt = (f"{months} ماه" if fa else f"{months} months")
    visits: list[dict[str, Any]] = []
    for entry in SCHEDULE:
        am = entry["age_months"]
        due_date = None
        try:
            y = b.year + (b.month - 1 + am) // 12
            m = (b.month - 1 + am) % 12 + 1
            d = min(b.day, [31, 29 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 28,
                            31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])
            due_date = date(y, m, d)
        except Exception:
            due_date = None
        if months > am:
            status = "past"
        elif months == am:
            status = "due"
        elif months == am - 1:
            status = "due_soon"
        else:
            status = "upcoming"
        visits.append({
            "age_months": am, "label": entry["fa"] if fa else entry["en"],
            "date": due_date.isoformat() if due_date else "",
            "status": status,
            "vaccines": [v[1] if fa else v[0] for v in entry["vaccines"]],
            "vaccines_en": [v[0] for v in entry["vaccines"]],
        })
    nxt = next((v for v in visits if v["status"] != "past"), None)
    if nxt and nxt.get("date"):
        dd = date.fromisoformat(nxt["date"])
        days = (dd - t).days
        if days > 14:
            nxt["in_days"] = days
            nxt["label"] += (f" ({days} روز دیگر)" if fa else f" (in {days} days)")
        elif days >= -14:
            nxt["in_days"] = max(days, 0)
            nxt["label"] += (" (همین حالا)" if fa else " (due now)")
        else:
            nxt["overdue_days"] = -days
            nxt["label"] += (f" ({-days} روز عقب افتاده)" if fa else f" ({-days} days overdue)")
    return {"ok": True, "age_months": months, "age_fa": age_txt, "visits": visits,
            "next": nxt, "catchup_fa": CATCHUP_NOTE, "message_fa": ""}
