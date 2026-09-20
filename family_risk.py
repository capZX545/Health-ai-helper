"""
family_risk.py — stores close-relatives' conditions and turns them into
personal screening recommendations (age to start, which test, why).
Educational prompts based on common screening guidelines; the final plan
belongs to a doctor.
"""
from __future__ import annotations

import os
from typing import Any

from common_2077 import DATA_DIR, read_json, write_json, normalize
from i18n import is_fa

FAMILY_FILE = os.path.join(DATA_DIR, "family_history.json")

FIRST_DEGREE = ("mother", "father", "sister", "brother", "son", "daughter")
SECOND_DEGREE = ("grandmother", "grandfather", "aunt", "uncle", "niece", "nephew")

REL_LABELS = {
    "mother": ("mother", "مادر"), "father": ("father", "پدر"),
    "sister": ("sister", "خواهر"), "brother": ("brother", "برادر"),
    "son": ("son", "پسر"), "daughter": ("daughter", "دختر"),
    "grandmother": ("grandmother", "مادربزرگ"), "grandfather": ("grandfather", "پدربزرگ"),
    "aunt": ("aunt", "عمه/خاله"), "uncle": ("uncle", "عمو/دایی"),
}

_RULES: list[dict[str, Any]] = [
    {"match": ["colon cancer", "colorectal", "سرطان کولون", "سرطان روده", "کولون"],
     "test": ("colonoscopy", "کولونوسکوپی"),
     "first": ("Start colonoscopy at age 40 or 10 years before their age at diagnosis, whichever is earlier, and repeat every 5 years.",
               "کولونوسکوپی را از ۴۰ سالگی یا ۱۰ سال قبل از سن تشخیص آن‌ها، هر کدام زودتر باشد، شروع کن و هر ۵ سال تکرار کن."),
     "second": ("Tell your doctor about this family history; they may start screening earlier than the routine age of 45-50.",
                "این سابقه را به پزشکت بگو؛ ممکن است غربالگری را زودتر از سن معمول ۴۵-۵۰ شروع کند.")},
    {"match": ["breast cancer", "سرطان سینه", "سرطان پستان"],
     "test": ("earlier mammography", "ماموگرافی زودتر"),
     "first": ("With a first-degree relative with breast cancer, screening typically starts 10 years before their age at diagnosis - discuss the exact plan with your doctor.",
               "با سابقه‌ی سرطان سینه در درجه‌ی یک، غربالگری معمولاً ۱۰ سال قبل از سن تشخیص آن‌ها شروع می‌شود - برنامه‌ی دقیق را با پزشک بگذار."),
     "second": ("A second-degree history still matters; mention it at your next checkup.",
                "سابقه‌ی درجه‌ی دوم هم مهم است؛ در چکاپ بعدی ذکرش کن.")},
    {"match": ["ovarian cancer", "سرطان تخمدان"],
     "test": ("genetic counseling", "مشاوره ژنتیک"),
     "first": ("First-degree ovarian cancer in the family is an indication for genetic counseling (BRCA testing).",
               "سرطان تخمدان در درجه‌ی یک، نشانزده‌ی مشاوره‌ی ژنتیک (تست BRCA) است."),
     "second": ("Mention it to your doctor; genetic counseling may still be considered.",
                "به پزشکت اشاره کن؛ مشاوره‌ی ژنتیک ممکن است در نظر گرفته شود.")},
    {"match": ["heart attack", "mi ", "coronary", "سکته قلبی", "بیماری قلبی", "قلبی"],
     "test": ("lipid screening", "آزمایش چربی خون"),
     "first": ("A heart attack in a close relative before 55 (male) or 65 (female) means your cholesterol should be checked early - in your twenties - and heart risk calculated.",
               "سکته قلبی در بستگان درجه‌ی یک قبل از ۵۵ (مرد) یا ۶۵ (زن) یعنی چربی خونت را زود - از دهه‌ی بیست - چک کن و ریسک قلبی را حساب کن."),
     "second": ("A family history of early heart disease still raises your baseline risk; keep lipids and blood pressure in check.",
                "سابقه‌ی بیماری قلبی زودرس خانواده ریسک پایه‌ی تو را بالا می‌برد؛ چربی خون و فشار را مرتب چک کن.")},
    {"match": ["diabetes", "دیابت"],
     "test": ("fasting glucose / HbA1c", "قند ناشتا / HbA1c"),
     "first": ("A first-degree relative with type 2 diabetes means yearly fasting glucose or HbA1c - the FINDRISC score in this app shows your current risk.",
               "دیابت نوع ۲ در درجه‌ی یک یعنی قند ناشتا یا HbA1c سالانه - امتیاز FINDRISC همین برنامه ریسک فعلی تو را نشان می‌دهد."),
     "second": ("Screen every 1-3 years with fasting glucose.",
                "هر ۱ تا ۳ سال قند ناشتا چک شود.")},
    {"match": ["glaucoma", "گلوکوم", "آب سیاه"],
     "test": ("eye exam", "معاینه چشم"),
     "first": ("A first-degree relative with glaucoma means a full eye exam (with eye pressure check) every 1-2 years.",
               "گلوکوم در درجه‌ی یک یعنی معاینه‌ی کامل چشم (با چک فشار چشم) هر ۱ تا ۲ سال."),
     "second": ("Regular eye exams are still advised.",
                "معاینه‌ی منظم چشم توصیه می‌شود.")},
    {"match": ["osteoporosis", "پوکی استخوان"],
     "test": ("bone density", "تراکم استخوان"),
     "first": ("With a family history of osteoporosis (or a hip fracture after a minor fall), discuss bone density testing around menopause.",
               "با سابقه‌ی پوکی استخوان (یا شکستگی لگن با ضربه‌ی خفیف) در خانواده، تست تراکم استخوان را حدود یائسگی با پزشک بررسی کن."),
     "second": ("Keep calcium, vitamin D and weight-bearing exercise on your radar.",
                "کلسیم، ویتامین D و ورزش تحمل‌وزن را جدی بگیر.")},
    {"match": ["stroke", "سکته مغزی"],
     "test": ("blood pressure control", "کنترل فشار خون"),
     "first": ("Stroke in a close relative makes blood pressure control extra important - check it regularly.",
               "سکته‌ی مغزی در بستگان درجه‌ی یک کنترل فشار را خیلی مهم می‌کند - فشارت را منظم چک کن."),
     "second": ("Monitor blood pressure periodically.",
                "فشار خون را دوره‌ای پایش کن.")},
    {"match": ["prostate cancer", "سرطان پروستات"],
     "test": ("psa discussion", "بررسی PSA"),
     "first": ("A father or brother with prostate cancer means discussing PSA testing from about 40-45.",
               "پدر یا برادر با سرطان پروستات یعنی از حدود ۴۰-۴۵ درباره‌ی تست PSA با پزشک صحبت کن."),
     "second": ("Mention it at a routine checkup.",
                "در چکاپ معمول ذکرش کن.")},
]


def _load() -> list[dict]:
    d = read_json(FAMILY_FILE, default=None)
    if not isinstance(d, dict):
        return []
    return [m for m in (d.get("members") or []) if isinstance(m, dict)]


def _save(members: list[dict]) -> None:
    write_json(FAMILY_FILE, {"members": members})


def list_members() -> list[dict]:
    return _load()


def add_member(relation: str, condition: str, age_at_diagnosis: str = "") -> dict[str, Any]:
    fa = is_fa()
    relation = str(relation or "").strip().lower()
    if relation not in FIRST_DEGREE and relation not in SECOND_DEGREE:
        return {"ok": False, "message_fa": "نسبت را از لیست انتخاب کن." if fa else "Pick the relation from the list."}
    if not str(condition or "").strip():
        return {"ok": False, "message_fa": "بیماری را بنویس." if fa else "Enter the condition."}
    members = _load()
    members.append({"relation": relation, "condition": str(condition).strip()[:80],
                    "age": str(age_at_diagnosis or "").strip()[:4]})
    _save(members)
    return {"ok": True, "members": members}


def remove_member(idx: int) -> dict[str, Any]:
    members = _load()
    try:
        members.pop(int(idx))
        _save(members)
    except (IndexError, ValueError, TypeError):
        pass
    return {"ok": True, "members": members}


def _match_rule(condition: str) -> dict | None:
    n = " " + normalize(condition) + " "
    for rule in _RULES:
        for m in rule["match"]:
            mn = normalize(m)
            if not mn:
                continue
            if (mn in n) or (m.strip().lower() in str(condition).lower()):
                return rule
    return None


def recommendations() -> dict[str, Any]:
    fa = is_fa()
    members = _load()
    if not members:
        return {"ok": True, "members": [], "recommendations": [],
                "message_fa": ("هنوز سابقه‌ی خانوادگی ثبت نشده — والدین، خواهر/برادر و پدربزرگ/مادربزرگ‌ها را اضافه کن تا برنامه‌ی غربالگری شخصی‌ات را بسازم."
                               if fa else "No family history recorded yet - add parents, siblings and grandparents to build your personal screening plan.")}
    recs: list[dict[str, Any]] = []
    for m in members:
        rule = _match_rule(m.get("condition") or "")
        rel = str(m.get("relation") or "")
        rel_lbl = REL_LABELS.get(rel, (rel, rel))[1 if fa else 0]
        cond = str(m.get("condition") or "")
        age_txt = ""
        try:
            a = int(m.get("age") or 0)
            if a > 0:
                age_txt = (f" در سن {a}" if fa else f" at age {a}")
        except (TypeError, ValueError):
            pass
        if rule:
            first = rel in FIRST_DEGREE
            txt = (rule["first"][1] if fa else rule["first"][0]) if first else (rule["second"][1] if fa else rule["second"][0])
            recs.append({"relation": rel_lbl, "condition": cond, "test": rule["test"][1] if fa else rule["test"][0],
                         "first_degree": first, "text": txt,
                         "line": (f"{rel_lbl} — {cond}{age_txt}: {txt}")})
        else:
            recs.append({"relation": rel_lbl, "condition": cond, "test": None, "first_degree": rel in FIRST_DEGREE,
                         "text": "",
                         "line": (f"{rel_lbl} — {cond}{age_txt}: " +
                                  ("این مورد را در چکاپ بعدی با پزشکت مطرح کن."
                                   if fa else "Bring this up at your next checkup."))})
    order = {"colonoscopy": 0, "earlier mammography": 0, "genetic counseling": 0, "lipid screening": 1,
             "کولونوسکوپی": 0, "ماموگرافی زودتر": 0, "مشاوره ژنتیک": 0, "آزمایش چربی خون": 1}
    recs.sort(key=lambda r: (not r["first_degree"], order.get(r["test"], 2)))
    note = ("این‌ها یافته‌های غربالگری عمومی بر اساس سابقه‌ی خانوادگی‌اند؛ برنامه‌ی دقیق و سن شروع را پزشک تعیین می‌کند."
            if fa else "These are general screening prompts based on family history; the exact plan and start age are set by a doctor.")
    return {"ok": True, "members": members, "recommendations": recs,
            "note_fa": note, "message_fa": ""}
