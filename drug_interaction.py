# -*- coding: utf-8 -*-
"""
drug_interaction.py — جست‌وجوی دارو/گیاه دارویی + بررسی تداخل + هشدار حساسیت.
⚠️ اطلاعات عمومی آموزشی است؛ تصمیم نهایی فقط با پزشک/داروساز است.
"""
from __future__ import annotations

from typing import Any

from common_2077 import normalize

DRUGS: list[dict[str, Any]] = [
    {"id": "warfarin", "fa": ["وارفارین", "رفاران", "کومادین"], "en": ["warfarin", "coumadin"], "cat": "رقیق‌کننده‌ی خون"},
    {"id": "aspirin", "fa": ["آسپرین", "استیل سالیسیلیک اسید", "ASA", "بی‌کا"], "en": ["aspirin", "asa", "ecotrin"], "cat": "مسکن/ضدپلاکت"},
    {"id": "ibuprofen", "fa": ["ایبوپروفن", "ژلوفن", "بروفن", "ادویل"], "en": ["ibuprofen", "advil", "brufen"], "cat": "مسکن NSAID"},
    {"id": "diclofenac", "fa": ["دیکلوفناک", "دیکلوفناک", "ولتارن"], "en": ["diclofenac", "voltaren"], "cat": "مسکن NSAID"},
    {"id": "naproxen", "fa": ["ناپروکسن", "ناپروکسن سدیم"], "en": ["naproxen", "aleve"], "cat": "مسکن NSAID"},
    {"id": "acetaminophen", "fa": ["استامینوفن", "پاراستامول", "تیلنول", "اپاپ"], "en": ["acetaminophen", "paracetamol", "tylenol"], "cat": "تب‌بر/مسکن"},
    {"id": "amoxicillin", "fa": ["آموکسی‌سیلین", "اموکسی سیلین", "کو-آموکسی‌کلاو", "اوگمنتین"], "en": ["amoxicillin", "augmentin"], "cat": "آنتی‌بیوتیک"},
    {"id": "azithromycin", "fa": ["آزیترومایسین", "ازیترومایسین", "آزیتروسین"], "en": ["azithromycin", "zithromax"], "cat": "آنتی‌بیوتیک"},
    {"id": "ciprofloxacin", "fa": ["سیپروفلوکساسین", "سیپرو"], "en": ["ciprofloxacin", "cipro"], "cat": "آنتی‌بیوتیک"},
    {"id": "metronidazole", "fa": ["مترونیدازول", "فلاژیل"], "en": ["metronidazole", "flagyl"], "cat": "آنتی‌بیوتیک"},
    {"id": "metformin", "fa": ["متفورمین", "گلوکوفاژ"], "en": ["metformin", "glucophage"], "cat": "ضد دیابت"},
    {"id": "insulin", "fa": ["انسولین", "انسولین سریع", "انسولین NPH"], "en": ["insulin"], "cat": "ضد دیابت"},
    {"id": "glibenclamide", "fa": ["گلیبنکلامید", "داونیل"], "en": ["glibenclamide", "glyburide"], "cat": "ضد دیابت"},
    {"id": "atorvastatin", "fa": ["آتورواستاتین", "آتورواستاتین کلسیم", "لیپیتور"], "en": ["atorvastatin", "lipitor"], "cat": "کاهنده‌ی چربی خون"},
    {"id": "loratadine", "fa": ["لوراتادین", "کلاریتین"], "en": ["loratadine", "claritin"], "cat": "آنتی‌هیستامین"},
    {"id": "cetirizine", "fa": ["سیتریزین", "زرتک"], "en": ["cetirizine", "zyrtec"], "cat": "آنتی‌هیستامین"},
    {"id": "omeprazole", "fa": ["امپرازول", "اُمپرازول", "لوزک"], "en": ["omeprazole", "losec"], "cat": "کاهنده‌ی اسید معده (PPI)"},
    {"id": "pantoprazole", "fa": ["پانتوپرازول", "کنترولوک"], "en": ["pantoprazole", "controloc"], "cat": "کاهنده‌ی اسید معده (PPI)"},
    {"id": "sertraline", "fa": ["سرترالین", "زولوفت"], "en": ["sertraline", "zoloft"], "cat": "ضدافسردگی (SSRI)"},
    {"id": "fluoxetine", "fa": ["فلوکستین", "پروزاک"], "en": ["fluoxetine", "prozac"], "cat": "ضدافسردگی (SSRI)"},
    {"id": "propranolol", "fa": ["پروپرانولول", "ایندرال"], "en": ["propranolol", "inderal"], "cat": "بتابلاکر"},
    {"id": "amlodipine", "fa": ["آملودیپین", "نورواسک"], "en": ["amlodipine", "norvasc"], "cat": "ضد فشار خون (CCB)"},
    {"id": "captopril", "fa": ["کاپتوپریل", "کاپوتن"], "en": ["captopril", "capoten"], "cat": "ضد فشار خون (ACEI)"},
    {"id": "lisinopril", "fa": ["لیزینوپریل"], "en": ["lisinopril"], "cat": "ضد فشار خون (ACEI)"},
    {"id": "losartan", "fa": ["لوزارتان", "کوزار"], "en": ["losartan", "cozaar"], "cat": "ضد فشار خون (ARB)"},
    {"id": "hctz", "fa": ["هیدروکلروتیازید", "هایدروکلروتیازید"], "en": ["hydrochlorothiazide", "hctz"], "cat": "مدر تیازیدی"},
    {"id": "furosemide", "fa": ["فوروزماید", "فورسمید", "لازیکس"], "en": ["furosemide", "lasix"], "cat": "مدر لوپ"},
    {"id": "digoxin", "fa": ["دیگوکسین", "لناکسین"], "en": ["digoxin", "lanoxin"], "cat": "قلب"},
    {"id": "levothyroxine", "fa": ["لواتیروکسین", "لوتیروکسین", "ال‌تروکسین", "اوتریکس"], "en": ["levothyroxine", "synthroid", "euthyrox"], "cat": "هورمون تیروئید"},
    {"id": "prednisolone", "fa": ["پردنیزولون", "پردنیزون"], "en": ["prednisolone", "prednisone"], "cat": "کورتیکواستروئید"},
    {"id": "salbutamol", "fa": ["سالبوتامول", "ونتولین", "سالبوتامول اسپری"], "en": ["salbutamol", "albuterol", "ventolin"], "cat": "برونکودیلاتور (آسم)"},
    {"id": "nitroglycerin", "fa": ["نیترات", "نیتروگلیسیرین", "زبنیل"], "en": ["nitroglycerin"], "cat": "ضد آنژین"},
    {"id": "tramadol", "fa": ["ترامادول"], "en": ["tramadol"], "cat": "مسکن مخدر"},
    {"id": "codeine", "fa": ["کدئین", "کدئین شربت"], "en": ["codeine"], "cat": "مسکن/ضدسرفه"},
    {"id": "alprazolam", "fa": ["آلپرازولام", "زناکس"], "en": ["alprazolam", "xanax"], "cat": "ضد اضطراب (بنزودیازپین)"},
    {"id": "clonazepam", "fa": ["کلونازپام", "ریووترین"], "en": ["clonazepam", "rivotril"], "cat": "ضد تشنج/اضطراب"},
    # گیاهان دارویی
    {"id": "ginkgo", "fa": ["گیاه گینکو", "گینکو بیلوبا"], "en": ["ginkgo", "ginkgo biloba"], "cat": "گیاه دارویی"},
    {"id": "ginseng", "fa": ["جینسنگ"], "en": ["ginseng"], "cat": "گیاه دارویی"},
    {"id": "garlic", "fa": ["سیر", "قرص سیر", "عصاره‌ی سیر"], "en": ["garlic"], "cat": "گیاه دارویی"},
    {"id": "ginger", "fa": ["زنجبیل"], "en": ["ginger"], "cat": "گیاه دارویی"},
    {"id": "turmeric", "fa": ["زردچوبه", "کورکومین"], "en": ["turmeric", "curcumin"], "cat": "گیاه دارویی"},
    {"id": "greentea", "fa": ["چای سبز"], "en": ["green tea"], "cat": "گیاه دارویی"},
    {"id": "stjohnswort", "fa": ["گل راعی", "چای کوهی", "سن‌جان"], "en": ["st johns wort", "st. john's wort"], "cat": "گیاه دارویی"},
    {"id": "senna", "fa": ["سنا", " برگ سنا", "شربت سنا"], "en": ["senna"], "cat": "ملین گیاهی"},
    {"id": "licorice", "fa": ["ریشه‌ی شیرین‌بیان", "شیرین بیان"], "en": ["licorice", "liquorice"], "cat": "گیاه دارویی"},
    {"id": "chamomile", "fa": ["بابونه", "چای بابونه"], "en": ["chamomile"], "cat": "گیاه دارویی"},
]

INTERACTIONS: list[dict[str, Any]] = [
    {"a": "warfarin", "b": "aspirin", "sev": "major", "fa": "خطر خونریزی گوارشی به‌طور معنادار بالا می‌رود؛ فقط با نظر و پایش پزشک."},
    {"a": "warfarin", "b": "ibuprofen", "sev": "major", "fa": "NSAID ها اثر ضددخون‌چسبی را تشدید و خطر خونریزی را زیاد می‌کنند؛ پرهیز توصیه می‌شود."},
    {"a": "warfarin", "b": "diclofenac", "sev": "major", "fa": "خطر خونریزی و آسیب معده؛ جایگزین با نظر پزشک."},
    {"a": "warfarin", "b": "ginkgo", "sev": "moderate", "fa": "گینکو اثر رقیق‌کنندگی خون را تشدید می‌کند."},
    {"a": "warfarin", "b": "ginseng", "sev": "moderate", "fa": "جینسنگ ممکن است اثر وارفارین را کم کند (INR نامنظم)."},
    {"a": "warfarin", "b": "greentea", "sev": "minor", "fa": "مصرف زیاد چای سبز ممکن است اثر وارفارین را کاهش دهد."},
    {"a": "warfarin", "b": "turmeric", "sev": "moderate", "fa": "کورکومین اثر ضد انعقادی را تقویت می‌کند؛ خطر کبودی/خونریزی."},
    {"a": "warfarin", "b": "garlic", "sev": "moderate", "fa": "مکمل‌های سیر با وارفارین خطر خونریزی را بالا می‌برند."},
    {"a": "aspirin", "b": "ibuprofen", "sev": "moderate", "fa": "ایبوپروفن اثر محافظتی قلبی آسپرین را کم می‌کند و خطر معده را بالا می‌برد."},
    {"a": "sertraline", "b": "ibuprofen", "sev": "moderate", "fa": "SSRI + NSAID خطر خونریزی گوارشی را افزایش می‌دهد؛ در صورت لزوم با نظر پزشک و محافظ معده."},
    {"a": "fluoxetine", "b": "stjohnswort", "sev": "major", "fa": "خطر سندروم سروتونین؛ ترکیب تحت نظارت دقیق پزشک."},
    {"a": "sertraline", "b": "tramadol", "sev": "major", "fa": "خطر سندروم سروتونین و تشنج؛ فقط با تجویز و پایش."},
    {"a": "atorvastatin", "b": "grapefruit", "sev": "moderate", "fa": "گراپ‌فروت سطح استاتین را بالا می‌برد و خطر آسیب عضلانی را زیاد می‌کند."},
    {"a": "metronidazole", "b": "alcohol", "sev": "major", "fa": "الکل حین مصرف مترونیدازول واکنش شدید (دل‌درد، استفراغ، گرگرفتگی) می‌دهد؛ پرهیز."},
    {"a": "metformin", "b": "alcohol", "sev": "major", "fa": "الکل خطر اسیدوز لاکتیک و افت قند را با متفورمین زیاد می‌کند."},
    {"a": "digoxin", "b": "furosemide", "sev": "moderate", "fa": "مدرها با کاهش پتاسیم خطر سمیت دیگوکسین را بالا می‌برند؛ پایش الکترولیت لازم است."},
    {"a": "hctz", "b": "lisinopril", "sev": "minor", "fa": "ترکیب رایج و مؤثر است اما پایش فشار/پتاسیم/عملکرد کلیه لازم دارد."},
    {"a": "loratadine", "b": "azithromycin", "sev": "minor", "fa": "احتمال طولانی‌شدن QT در برخی افراد؛ در بیماری قلبی با پزشک مشورت شود."},
    {"a": "levothyroxine", "b": "calcium", "sev": "moderate", "fa": "مکمل کلسیم/آهن جذب لواتیروکسین را کم می‌کند؛ فاصله‌ی حداقل ۴ ساعت بگذارید."},
    {"a": "levothyroxine", "b": "omeprazole", "sev": "minor", "fa": "PPI ها ممکن است جذب هورمون تیروئید را کمی کم کنند؛ پایش TSH."},
    {"a": "prednisolone", "b": "ibuprofen", "sev": "moderate", "fa": "کورتون + NSAID خطر زخم و خونریزی معده را زیاد می‌کند."},
    {"a": "prednisolone", "b": "metformin", "sev": "moderate", "fa": "کورتون قند خون را بالا می‌برد؛ دوز دیابت ممکن است نیاز به تنظیم داشته باشد."},
    {"a": "senna", "b": "licorice", "sev": "minor", "fa": "مصرف مزمن، تعادل پتاسیم را مختل می‌کند."},
    {"a": "licorice", "b": "hctz", "sev": "moderate", "fa": "شیرین‌بیان با مدرها افت پتاسیم را تشدید می‌کند."},
    {"a": "codeine", "b": "alprazolam", "sev": "major", "fa": "سرکوب تنفس؛ ترکیب افیون و بنزودیازپین فقط تحت نظارت شدید پزشک."},
    {"a": "codeine", "b": "tramadol", "sev": "major", "fa": "خطر سرکوب تنفس و تشنج."},
    {"a": "glibenclamide", "b": "aspirin", "sev": "minor", "fa": "دوزهای بالای آسپرین اثر کاهنده‌ی قند را تشدید می‌کند؛ پایش قند."},
    {"a": "captopril", "b": "potassium", "sev": "moderate", "fa": "ACEI پتاسیم را بالا می‌برد؛ مکمل پتاسیم فقط با نظر پزشک."},
    {"a": "nitroglycerin", "b": "alprazolam", "sev": "minor", "fa": "افت فشار وضعیتی ممکن است تشدید شود."},
    {"a": "ciprofloxacin", "b": "calcium", "sev": "moderate", "fa": "لبنیات/مکمل کلسیم جذب سیپرو را کم می‌کنند؛ ۲ ساعت فاصله."},
    {"a": "insulin", "b": "prednisolone", "sev": "moderate", "fa": "کورتون نیاز انسولین را بالا می‌برد؛ پایش قند ضروری است."},
]

SEV_FA = {"major": "🔴 تداخل شدید", "moderate": "🟠 تداخل متوسط", "minor": "🟡 تداخل خفیف"}

DISCLAIMER = "⚠️ این بررسی آموزشی است و کامل نیست؛ فهرست دارویی کامل خود را به پزشک/داروساز نشان بده."


def _norm_all(drug: dict) -> list[str]:
    words = []
    for w in drug["fa"] + drug["en"]:
        words.append(normalize(w))
    return [w for w in words if w]


def search_drug(q: str) -> list[dict[str, Any]]:
    nq = normalize(q)
    if not nq:
        return []
    out = []
    for d in DRUGS:
        names = _norm_all(d)
        score = 0
        for n in names:
            if n == nq:
                score = max(score, 100)
            elif nq in n or n in nq:
                score = max(score, 70)
        if score:
            out.append({"id": d["id"], "fa": d["fa"][0], "en": d["en"][0], "cat": d["cat"], "score": score})
    out.sort(key=lambda x: x["score"], reverse=True)
    return out[:8]


def find_drug(q: str) -> dict | None:
    r = search_drug(q)
    return r[0] if r else None


def check_interaction(a: str, b: str) -> dict[str, Any]:
    da, db = search_drug(a), search_drug(b)
    if not da or not db:
        return {"ok": False,
                "message_fa": "یکی از داروها در پایگاه داخلی پیدا نشد؛ نام را دقیق‌تر بنویس (مثلاً «وارفارین» یا «warfarin»). " + DISCLAIMER}
    ida, idb = da[0]["id"], db[0]["id"]
    matches = []
    for it in INTERACTIONS:
        if {it["a"], it["b"]} == {ida, idb}:
            matches.append({"severity": it["sev"], "severity_fa": SEV_FA[it["sev"]],
                            "a_fa": da[0]["fa"], "b_fa": db[0]["fa"], "detail_fa": it["fa"]})
    if not matches:
        matches.append({"severity": "none", "severity_fa": "🟢 تداخل شناخته‌شده‌ای در پایگاه کوچک داخلی ثبت نشده",
                        "a_fa": da[0]["fa"], "b_fa": db[0]["fa"],
                        "detail_fa": "نبودِ تداخل در این پایگاه به معنای بی‌خطر بودن قطعی نیست."})
    return {"ok": True, "a": da[0], "b": db[0], "interactions": matches, "disclaimer": DISCLAIMER}


def allergy_alert(drug_names: list[str]) -> dict[str, Any]:
    """مقایسه با حساسیت‌های پروفایل بیمار."""
    from patient_profile import load_profile
    prof = load_profile()
    al = normalize(prof.get("allergies") or "")
    if not al or not drug_names:
        return {"ok": True, "alerts": []}
    alerts = []
    for q in drug_names:
        d = search_drug(q)
        if not d:
            continue
        for name in d[0:1]:
            for alias in [name["fa"], name["en"]]:
                if normalize(alias) and normalize(alias) in al:
                    alerts.append(f"🔴 «{name['fa']}» با حساسیت ثبت‌شده‌ی شما ({alias}) مطابقت دارد!")
                    break
    return {"ok": True, "alerts": alerts}
