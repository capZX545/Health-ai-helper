"""
pregnancy_tracker.py — offline bilingual period tracker + week-by-week
pregnancy guide. Personal data stays in cycle_log.json. Calendar-based
estimates only (not contraception guidance); medical decisions belong
to a doctor, and any warning sign means calling one immediately.
"""
from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from typing import Any

from common_2077 import DATA_DIR, read_json, write_json
from i18n import is_fa

CYCLE_FILE = os.path.join(DATA_DIR, "cycle_log.json")

_WEEKS: list[tuple[str, str, str, str]] = [
    ("poppy seed", "دانه‌ی خشخاش", "the neural tube starts forming; take folic acid", "لوله‌ی عصبی شکل می‌گیرد؛ اسید فولیک مصرف کن"),
    ("sesame seed", "دانه‌ی کنجد", "heart tube begins to form", "لوله‌ی قلب شروع به شکل‌گیری می‌کند"),
    ("lentil", "عدس", "heartbeats can sometimes be seen on ultrasound", "ضربان قلب گاهی روی سونوگرافی دیده می‌شود"),
    ("blueberry", "زغال‌آسته", "limb buds appear", "جوانه‌ی دست و پا ظاهر می‌شود"),
    ("raspberry", "تمشک", "basic brain sections form", "بخش‌های اصلی مغز شکل می‌گیرد"),
    ("grape", "انگور", "facial features become visible", "اجزای صورت پیدا می‌شوند"),
    ("kumquat", "نارنج کوچک", "tooth buds and fingers form", "جوانه‌ی دندان و انگشت‌ها شکل می‌گیرد"),
    ("strawberry", "توت‌فرنگی", "vital organs are working", "اندام‌های حیاتی کار می‌کنند"),
    ("lime", "لیمو", "first screening tests window opens", "پنجره‌ی غربالگری‌های اولین سه‌ماهه باز می‌شود"),
    ("plum", "آلو", "fingernails start forming", "ناخن‌ها شروع به رشد می‌کنند"),
    ("lemon", "لیموترش", "kidneys produce urine", "کلیه‌ها ادرار می‌سازند"),
    ("peach", "هلو", "NT scan window (11-14 weeks)", "پنجره‌ی سونوگرافی NT (هفته‌ی ۱۱ تا ۱۴)"),
    ("apricot", "زردآلو", "vocal cords form; first trimester screening ends", "بندهای صوتی شکل می‌گیرد؛ غربالگری سه‌ماهه‌ی اول تمام می‌شود"),
    ("lemon", "لیموترش", "second trimester begins", "سه‌ماهه‌ی دوم شروع می‌شود"),
    ("apple", "سیب", "bones harden on ultrasound", "استخوان‌ها در سونوگرافی سخت‌تر دیده می‌شوند"),
    ("avocado", "آووکادو", "tiny movements may be felt", "حرکات کوچک ممکن است حس شود"),
    ("pear", "گلابی", "fat starts to form", "چربی زیر پوست شروع به شکل‌گیری می‌کند"),
    ("bell pepper", "فلفل دلمه‌ای", "hearing develops", "شنوایی رشد می‌کند"),
    ("mango", "انبه", "anatomy scan window (18-22 weeks)", "پنجره‌ی سونوگرافی آناتومی (هفته‌ی ۱۸ تا ۲۲)"),
    ("banana", "موز", "halfway point", "نصف راه رسیدی"),
    ("carrot", "هویج", "taste buds form", "جوانه‌های چشایی شکل می‌گیرند"),
    ("papaya", "پاپایا", "eyebrows and lids appear", "ابرو و پلک ظاهر می‌شوند"),
    ("grapefruit", "گریپ‌فروت", "hearing is sharp; responds to sound", "شنوایی تیز است؛ به صدا واکنش نشان می‌دهد"),
    ("corn", "بذرت ذرت", "lungs make surfactant", "شش‌ها سورفکتانت می‌سازند"),
    ("cauliflower", "گل‌کلم", "hair color and texture set", "رنگ و بافت مو مشخص می‌شود"),
    ("lettuce head", "کاهو", "eyes open", "چشم‌ها باز می‌شوند"),
    ("cauliflower", "گل‌کلم", "regular sleep-wake cycles", "چرخه‌ی خواب و بیداری منظم می‌شود"),
    ("eggplant", "بادمجان", "third trimester; count movements daily", "سه‌ماهه‌ی سوم؛ شمارش حرکات روزانه را شروع کن"),
    ("butternut squash", "کدوحلوایی", "bones fully develop; need calcium", "استخوان‌ها کامل می‌شوند؛ کلسیم لازم است"),
    ("cabbage", "کلم", "about 1.3 kg and gaining fast", "حدود ۱٫۳ کیلو و سریع سنگین‌تر می‌شود"),
    ("coconut", "نارگیل", "all five senses work", "هر پنج حس کار می‌کنند"),
    ("jicama", "شکرقندی", "weight gain accelerates", "افزایش وزن سریع‌تر می‌شود"),
    ("pineapple", "آناناس", "brain grows fast", "مغز سریع رشد می‌کند"),
    ("cantaloupe", "طالبی", "fat layers smooth the skin", "لایه‌های چربی پوست را صاف می‌کنند"),
    ("honeydew melon", "خربزه", "kidneys are mature; almost fully developed", "کلیه‌ها بالغ‌اند؛ تقریباً کامل توسعه‌یافته"),
    ("romaine lettuce", "کاهو", "dropping into the pelvis may start", "سر ممکن است به سمت لگن پایین بیاید"),
    ("leek", "تره‌فرنگی", "practicing breathing; full term at 39", "تمرین تنفس؛ کامل‌رسیده در هفته‌ی ۳۹"),
    ("rhubarb", "ریواس", "brain and lungs keep maturing", "مغز و شش‌ها هنوز در حال رسیدن هستند"),
    ("mini watermelon", "هندوانه‌ی کوچک", "packed and ready; watch for labor signs", "جمع‌وجور و آماده؛ علائم زایمان را زیر نظر بگیر"),
    ("small pumpkin", "کدوی کوچک", "due week - full term", "هفته‌ی موعد — تمام‌ماهه"),
]

_DANGER = {
    1: [("vaginal bleeding", "خونریزی واژینال"),
        ("severe one-sided pain", "درد شدید یک‌طرفه"),
        ("heavy vomiting with no intake", "استفراغ شدید بدون توان خوردن")],
    2: [("bleeding", "خونریزی"),
        ("severe headache or vision changes", "سردرد شدید یا تغییر بینایی"),
        ("marked swelling of face and hands", "تورم شدید صورت و دست‌ها"),
        ("decreased fetal movement", "کاهش حرکات جنین"),
        ("fluid leakage", "خروج مایع")],
    3: [("bleeding", "خونریزی"),
        ("no movement for hours", "قطع حرکات ساعت‌ها"),
        ("severe headache, vision changes, upper stomach pain", "سردرد شدید، تغییر بینایی، درد بالای شکم"),
        ("water breaking", "پارده‌ی آب"),
        ("regular painful contractions before 37 weeks", "انقباضات منظم دردناک قبل از هفته‌ی ۳۷")],
}


def _load() -> dict[str, Any]:
    d = read_json(CYCLE_FILE, default=None)
    if not isinstance(d, dict):
        return {"periods": [], "lmp": ""}
    return d


def _save(d: dict[str, Any]) -> None:
    write_json(CYCLE_FILE, d)


def _parse(s: str) -> date | None:
    s = str(s or "").strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def log_period(day: str) -> dict[str, Any]:
    fa = is_fa()
    d = _parse(day)
    if d is None:
        return {"ok": False, "message_fa": "تاریخ را به شکل YYYY-MM-DD وارد کن." if fa else "Enter the date as YYYY-MM-DD."}
    data = _load()
    periods = sorted(set(data.get("periods") or []) | {d.isoformat()})
    data["periods"] = periods
    _save(data)
    return {"ok": True, "periods": periods,
            "message_fa": ("ثبت شد." if fa else "Logged.")}


def remove_period(day: str) -> dict[str, Any]:
    data = _load()
    data["periods"] = [p for p in (data.get("periods") or []) if p != str(day or "").strip()]
    _save(data)
    return {"ok": True, "periods": data["periods"]}


def set_pregnancy(lmp: str) -> dict[str, Any]:
    fa = is_fa()
    d = _parse(lmp)
    if d is None:
        return {"ok": False, "message_fa": "تاریخ اولین روز آخرین پریود را به شکل YYYY-MM-DD وارد کن." if fa
                else "Enter the first day of the last period as YYYY-MM-DD."}
    data = _load()
    data["lmp"] = d.isoformat()
    _save(data)
    return pregnancy_status()


def clear_pregnancy() -> dict[str, Any]:
    data = _load()
    data["lmp"] = ""
    _save(data)
    return {"ok": True, "message_fa": "حالت بارداری خاموش شد." if is_fa() else "Pregnancy mode turned off."}


def cycle_stats() -> dict[str, Any]:
    fa = is_fa()
    periods = sorted(_load().get("periods") or [])
    if not periods:
        return {"ok": True, "tracked": 0,
                "message_fa": ("هنوز پریودی ثبت نکردی — اولین روز چند پریود آخر را ثبت کن تا طول سیکل و تخمک‌گذاری بعدی را حساب کنم."
                               if fa else "No period logged yet - log the first day of your last few periods to estimate cycle length and ovulation.")}
    gaps = [(date.fromisoformat(b) - date.fromisoformat(a)).days
            for a, b in zip(periods, periods[1:])]
    normal = [g for g in gaps if 20 <= g <= 45]
    avg = round(sum(normal) / len(normal)) if normal else 28
    last = date.fromisoformat(periods[-1])
    nxt = last + timedelta(days=avg)
    ovulation = nxt - timedelta(days=14)
    fertile = (ovulation - timedelta(days=5), ovulation + timedelta(days=1))
    today = date.today()
    days_late = (today - nxt).days
    if days_late > 7:
        late_note = (f"پریود بعدی {days_late} روز عقب است — اگر احتمال بارداری می‌دهی، آزمایش خانگی بده."
                     if fa else f"The next period is {days_late} days late - if pregnancy is possible, take a home test.")
    else:
        late_note = ""
    return {
        "ok": True, "tracked": len(periods), "avg_cycle": avg,
        "last": last.isoformat(), "next_expected": nxt.isoformat(),
        "ovulation": ovulation.isoformat(),
        "fertile_from": fertile[0].isoformat(), "fertile_to": fertile[1].isoformat(),
        "days_late": max(0, days_late) if days_late > 0 else 0,
        "late_note_fa": late_note,
        "cycle_gaps": gaps[-6:],
        "message_fa": "",
    }


def pregnancy_status(today: date | None = None) -> dict[str, Any]:
    fa = is_fa()
    lmp_s = _load().get("lmp") or ""
    if not lmp_s:
        return {"ok": True, "pregnant": False,
                "message_fa": "حالت بارداری فعال نیست." if fa else "Pregnancy mode is not active."}
    lmp = _parse(lmp_s)
    if lmp is None:
        return {"ok": False, "message_fa": "تاریخ LMP نامعتبر است." if fa else "Invalid LMP date."}
    t = today or date.today()
    days = (t - lmp).days
    if days < 0 or days > 320:
        return {"ok": False, "message_fa": "تاریخ LMP معتبر به نظر نمی‌رسد." if fa else "The LMP date does not look valid."}
    week = days // 7 + 1
    week_idx = min(max(week, 1), 40) - 1
    size_en, size_fa, note_en, note_fa = _WEEKS[week_idx]
    due = lmp + timedelta(days=280)
    days_to_due = (due - t).days
    trimester = 1 if week <= 13 else (2 if week <= 27 else 3)
    danger = _DANGER[trimester]
    if fa:
        danger_txt = "، ".join(d[1] for d in danger)
        danger_head = "علائم خطر این سه‌ماهه — ببینی فوراً با پزشک/اورژانس تماس بگیر:"
    else:
        danger_txt = ", ".join(d[0] for d in danger)
        danger_head = "Danger signs this trimester - if any appears, call your doctor/emergency immediately:"
    return {
        "ok": True, "pregnant": True, "lmp": lmp.isoformat(),
        "week": week, "trimester": trimester,
        "due_date": due.isoformat(), "days_to_due": max(0, days_to_due),
        "size_fa": size_fa if fa else size_en,
        "note_fa": note_fa if fa else note_en,
        "danger_head_fa": danger_head, "danger_fa": danger_txt,
        "message_fa": "",
    }
