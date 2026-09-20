"""
renal_dosing.py — Cockcroft-Gault creatinine clearance calculator plus
kidney-function-aware medication warnings for common drugs.
Educational reference only; dosing decisions belong to a doctor/pharmacist.
"""
from __future__ import annotations

import re
from typing import Any

from common_2077 import normalize
from i18n import is_fa


def _num(v, default: float = 0.0) -> float:
    try:
        return float(str(v).replace(",", ".").strip())
    except (TypeError, ValueError):
        return default


def _female(sex: Any) -> bool:
    return str(sex).strip().lower() in ("f", "female", "زن", "w", "2")


def ibw_kg(sex, height_cm) -> float:
    h = _num(height_cm)
    if h <= 0:
        return 0.0
    inches_over_150 = (h - 150.0) / 2.54
    base = 45.5 if _female(sex) else 50.0
    return max(base, base + 2.3 * inches_over_150)


def cockcroft_gault(age, weight_kg, serum_creatinine_mg_dl, sex, height_cm=None) -> dict[str, Any]:
    fa = is_fa()
    age_i = _num(age)
    w = _num(weight_kg)
    scr = _num(serum_creatinine_mg_dl)
    if age_i <= 0 or w <= 0 or scr <= 0:
        return {"ok": False, "message_fa": "سن، وزن و کراتینین خون لازم است." if fa
                else "Age, weight and serum creatinine are required."}
    factor = 0.85 if _female(sex) else 1.0
    crcl = ((140.0 - age_i) * w * factor) / (72.0 * scr)
    out: dict[str, Any] = {"ok": True, "crcl": round(crcl, 1), "weight_used": w, "weight_mode": "actual"}
    ibw = 0.0
    if _num(height_cm) > 0:
        ibw = ibw_kg(sex, height_cm)
        out["ibw"] = round(ibw, 1)
        if w > 1.3 * ibw:
            adj = ibw + 0.4 * (w - ibw)
            crcl_adj = ((140.0 - age_i) * adj * factor) / (72.0 * scr)
            out["crcl_adjusted"] = round(crcl_adj, 1)
            out["weight_adjusted"] = round(adj, 1)
            out["weight_mode"] = "adjusted"
            out["crcl"] = round(crcl_adj, 1)
    if out["crcl"] >= 90:
        band, color = ("normal kidney function", "green") if not fa else ("عملکرد طبیعی کلیه", "green")
    elif out["crcl"] >= 60:
        band, color = ("mildly decreased (G2)", "yellow") if not fa else ("کاهش خفیف (G2)", "yellow")
    elif out["crcl"] >= 30:
        band, color = ("moderately decreased (G3)", "orange") if not fa else ("کاهش متوسط (G3)", "orange")
    elif out["crcl"] >= 15:
        band, color = ("severely decreased (G4)", "red") if not fa else ("کاهش شدید (G4)", "red")
    else:
        band, color = ("kidney failure range (G5)", "red") if not fa else ("محدوده‌ی نارسایی کلیه (G5)", "red")
    out["band"] = band
    out["level"] = color
    return out


_DRUGS: list[dict[str, Any]] = [
    {"id": "metformin", "en": ["metformin", "glucophage"], "fa": ["متفورمین", "گلوکوفاژ"], "threshold": 60,
     "mid": ("reduce the dose (often to a maximum of 1000 mg/day) and monitor kidney function every 3-6 months",
             "دوز را کم کن (اغلب حداکثر ۱۰۰۰ میلی‌گرم در روز) و عملکرد کلیه را هر ۳ تا ۶ ماه چک کن"),
     "low": ("contraindicated below 30; risk of lactic acidosis - the doctor must switch the drug",
             "زیر ۳۰ منع مصرف دارد؛ خطر اسیدوز لاکتیک — پزشک باید دارو را عوض کند")},
    {"id": "ibuprofen", "en": ["ibuprofen", "advil", "brufen"], "fa": ["ایبوپروفن", "ژلوفن", "بروفن", "ادویل"], "threshold": 60,
     "mid": ("use the lowest dose for the shortest time and stay well hydrated; watch for swelling and less urine",
             "کمترین دوز برای کوتاه‌ترین زمان و مایعات کافی؛ تورم و کاهش ادرار را زیر نظر بگیر"),
     "low": ("avoid below 30 - high risk of acute kidney injury; ask the doctor for a safer painkiller",
             "زیر ۳۰ پرهیز شود — خطر بالا‌ی آسیب حاد کلیه؛ از پزشک مسکن ایمن‌تر بگیر")},
    {"id": "diclofenac", "en": ["diclofenac", "voltaren"], "fa": ["دیکلوفناک", "ولتارن"], "threshold": 60,
     "mid": ("short-term use only, lowest dose", "فقط کوتاه‌مدت و با کمترین دوز"),
     "low": ("avoid below 30 - kidney and cardiovascular risk", "زیر ۳۰ پرهیز شود — خطر کلیوی و قلبی-عروقی")},
    {"id": "naproxen", "en": ["naproxen"], "fa": ["ناپروکسن"], "threshold": 60,
     "mid": ("lowest dose, short-term", "کمترین دوز، کوتاه‌مدت"),
     "low": ("avoid below 30", "زیر ۳۰ پرهیز شود")},
    {"id": "aspirin_high", "en": ["aspirin"], "fa": ["آسپرین", "استیل سالیسیلیک اسید"], "threshold": 60,
     "mid": ("low-dose (81-100 mg) is usually fine; higher pain/anti-inflammatory doses need medical advice",
             "دوز کم (۸۱ تا ۱۰۰ میلی‌گرم) معمولاً مشکلی ندارد؛ دوزهای بالاتر مسکن نیاز به نظر پزشک دارد"),
     "low": ("high-dose aspirin is avoided below 30 (bleeding and accumulation risk)",
             "آسپرین با دوز بالا زیر ۳۰ مصرف نمی‌شود (خطر خونریزی و انباشت)")},
    {"id": "amoxicillin", "en": ["amoxicillin", "augmentin"], "fa": ["آموکسی‌سیلین", "کوآموکسی‌کلاو", "اوگمنتین"], "threshold": 30,
     "mid": ("no change needed above 30", "بالای ۳۰ تغییری لازم نیست"),
     "low": ("extend the interval (usually every 12 hours instead of 8) - doctor decides",
             "فاصله‌ی بین دوزها بیشتر شود (معمولاً هر ۱۲ ساعت به‌جای ۸) — پزشک تصمیم می‌گیرد")},
    {"id": "ciprofloxacin", "en": ["ciprofloxacin", "cipro"], "fa": ["سیپروفلوکساسین", "سیپرو"], "threshold": 30,
     "mid": ("standard dosing usually works above 30", "بالای ۳۰ معمولاً دوز استاندارد است"),
     "low": ("dose is reduced or interval extended below 30", "زیر ۳۰ دوز کم یا فاصله بیشتر می‌شود")},
    {"id": "nitrofurantoin", "en": ["nitrofurantoin", "macrobid"], "fa": ["نیتروفورانتوئین"], "threshold": 30,
     "mid": ("acceptable for short courses above 30", "بالای ۳۰ برای دوره‌ی کوتاه قابل قبول است"),
     "low": ("avoided below 30 - not effective and toxic to nerves", "زیر ۳۰ استفاده نمی‌شود — بی‌اثر و سمی برای اعصاب")},
    {"id": "lisinopril", "en": ["lisinopril"], "fa": ["لیزینوپریل"], "threshold": 60,
     "mid": ("start low, re-check creatinine and potassium 1-2 weeks after any change",
             "با دوز کم شروع کن؛ ۱ تا ۲ هفته بعد از هر تغییر کراتینین و پتاسیم را چک کن"),
     "low": ("used with great caution and close monitoring below 30", "زیر ۳۰ با احتیاط زیاد و پایش مکرر استفاده می‌شود")},
    {"id": "enalapril", "en": ["enalapril"], "fa": ["انالاپریل"], "threshold": 60,
     "mid": ("start low, monitor potassium and creatinine", "دوز کم شروع کن؛ پتاسیم و کراتینین را پایش کن"),
     "low": ("caution with close monitoring", "با احتیاط و پایش دقیق")},
    {"id": "losartan", "en": ["losartan"], "fa": ["لوزارتان"], "threshold": 60,
     "mid": ("monitor potassium and creatinine after changes", "بعد از تغییرات پتاسیم و کراتینین را چک کن"),
     "low": ("caution; doctor adjusts the dose", "احتیاط؛ پزشک دوز را تنظیم می‌کند")},
    {"id": "valsartan", "en": ["valsartan"], "fa": ["والسارتان"], "threshold": 60,
     "mid": ("monitor potassium and creatinine", "پتاسیم و کراتینین را پایش کن"),
     "low": ("caution; dose adjusted by doctor", "احتیاط؛ دوز را پزشک تنظیم می‌کند")},
    {"id": "furosemide", "en": ["furosemide", "lasix"], "fa": ["فوروزماید", "فوروسماید", "لازیکس"], "threshold": 30,
     "mid": ("works, but higher doses may be needed and dehydration must be avoided",
             "اثر دارد ولی ممکن است دوز بالاتر لازم باشد و کم‌آبی باید پیشگیری شود"),
     "low": ("markedly less effective below 30; the doctor may switch to other diuretics",
             "زیر ۳۰ اثرش به‌شدت کم می‌شود؛ ممکن است پزشک به مدر دیگر سوئیچ کند")},
    {"id": "hydrochlorothiazide", "en": ["hydrochlorothiazide", "hctz"], "fa": ["هیدروکلروتیازید"], "threshold": 30,
     "mid": ("usually still effective above 30", "بالای ۳۰ معمولاً همچنان مؤثر است"),
     "low": ("largely ineffective below 30", "زیر ۳۰ عملاً بی‌اثر است")},
    {"id": "spironolactone", "en": ["spironolactone"], "fa": ["اسپیرونولاکتون"], "threshold": 30,
     "mid": ("potassium must be monitored regularly", "پتاسیم باید منظم چک شود"),
     "low": ("avoided below 30 - dangerous potassium rise", "زیر ۳۰ استفاده نمی‌شود — بالا رفتن خطرناک پتاسیم")},
    {"id": "digoxin", "en": ["digoxin"], "fa": ["دیگوکسین"], "threshold": 60,
     "mid": ("dose is often lowered; level monitoring helps", "دوز اغلب کم می‌شود؛ اندازه‌گیری سطح خون کمک می‌کند"),
     "low": ("significantly reduced doses; blood levels must be followed", "دوز به‌طور چشمگیری کم می‌شود؛ سطح خون باید پیگیری شود")},
    {"id": "gabapentin", "en": ["gabapentin"], "fa": ["گاباپنتین"], "threshold": 60,
     "mid": ("dose is adjusted to kidney function", "دوز متناسب با عملکرد کلیه تنظیم می‌شود"),
     "low": ("dose is strongly reduced below 30 (accumulation, drowsiness)", "زیر ۳۰ دوز به‌شدت کم می‌شود (انباشت و خواب‌آلودگی)")},
    {"id": "allopurinol", "en": ["allopurinol"], "fa": ["آلوپورینول"], "threshold": 60,
     "mid": ("start with a lower dose", "با دوز کمتر شروع شود"),
     "low": ("dose is clearly reduced below 60 in practice; risk of rash", "عملاً زیر ۶۰ دوز مشخصاً کم می‌شود؛ خطر بثورات پوستی")},
    {"id": "warfarin", "en": ["warfarin", "coumadin"], "fa": ["وارفارین", "کومادین"], "threshold": 60,
     "mid": ("more frequent INR checks are advised", "چک مکررتر INR توصیه می‌شود"),
     "low": ("sensitivity increases; INR must be followed closely", "حساسیت بیشتر می‌شود؛ INR باید دقیق پیگیری شود")},
    {"id": "enoxaparin", "en": ["enoxaparin", "clexane"], "fa": ["انوکساپارین", "کلکسان"], "threshold": 30,
     "mid": ("standard dosing above 30", "بالای ۳۰ دوز استاندارد"),
     "low": ("switched to once-daily dosing below 30", "زیر ۳۰ به دوز یک‌بار در روز تغییر می‌کند")},
    {"id": "morphine", "en": ["morphine"], "fa": ["مورفین"], "threshold": 60,
     "mid": ("long-acting forms need care", "فرم‌های طولانی‌اثر نیازمند احتیاط‌اند"),
     "low": ("active metabolites accumulate - dose reduced or avoided", "متابولیت‌های فعال انباشته می‌شوند — دوز کم یا مصرف نمی‌شود")},
    {"id": "tramadol", "en": ["tramadol"], "fa": ["ترامادول"], "threshold": 30,
     "mid": ("usual dosing above 30", "بالای ۳۰ دوز معمول"),
     "low": ("maximum 200 mg/day in two doses, spaced 12 hours apart", "حداکثر ۲۰۰ میلی‌گرم در روز، دو نوبت با فاصله ۱۲ ساعت")},
    {"id": "metoclopramide", "en": ["metoclopramide"], "fa": ["متوکلوپرامید", "پرایمپران"], "threshold": 60,
     "mid": ("dose often halved", "دوز اغلب نصف می‌شود"),
     "low": ("dose clearly reduced - risk of tremor and restlessness", "دوز مشخصاً کم می‌شود — خطر لرز و بی‌قراری")},
    {"id": "glibenclamide", "en": ["glibenclamide", "glyburide", "daonil"], "fa": ["گلیبنکلامید", "داونیل"], "threshold": 60,
     "mid": ("hypoglycemia risk rises; safer alternatives exist", "خطر افت قند بالا می‌رود؛ جایگزین ایمن‌تر وجود دارد"),
     "low": ("avoided below 30 - long, dangerous hypoglycemia", "زیر ۳۰ مصرف نمی‌شود — افت قند طولانی و خطرناک")},
    {"id": "insulin", "en": ["insulin"], "fa": ["انسولین"], "threshold": 60,
     "mid": ("insulin lasts longer; glucose must be monitored more closely", "انسولین طولانی‌تر اثر می‌کند؛ قند دقیق‌تر پایش شود"),
     "low": ("needs are lower and less predictable; close glucose monitoring", "نیاز کمتر و کمتر قابل پیش‌بینی است؛ پایش دقیق قند")},
    {"id": "atorvastatin", "en": ["atorvastatin", "lipitor"], "fa": ["آتورواستاتین", "لیپیتور"], "threshold": 30,
     "mid": ("no adjustment usually needed", "معمولاً نیازی به تغییر دوز نیست"),
     "low": ("usable with caution; report muscle pain immediately", "با احتیاط قابل مصرف است؛ درد عضله را فوراً گزارش کن")},
    {"id": "sertraline", "en": ["sertraline", "zoloft"], "fa": ["سرترالین", "زولوفت"], "threshold": 30,
     "mid": ("no adjustment usually needed", "معمولاً نیازی به تغییر دوز نیست"),
     "low": ("lower starting dose considered below 30", "زیر ۳۰ دوز شروع کمتر در نظر گرفته می‌شود")},
    {"id": "apixaban", "en": ["apixaban", "eliquis"], "fa": ["آپیکسابان", "الیکویس"], "threshold": 60,
     "mid": ("standard dosing above 60 (with age/weight rules)", "بالای ۶۰ دوز استاندارد (با قواعد سن/وزن)"),
     "low": ("dose criteria change below 30 - doctor must confirm", "زیر ۳۰ معیارهای دوز تغییر می‌کند — پزشک باید تأیید کند")},
    {"id": "dabigatran", "en": ["dabigatran", "pradaxa"], "fa": ["دابیگاتران", "پراداکسا"], "threshold": 30,
     "mid": ("standard dosing above 30", "بالای ۳۰ دوز استاندارد"),
     "low": ("contraindicated below 30", "زیر ۳۰ منع مصرف دارد")},
    {"id": "vancomycin", "en": ["vancomycin"], "fa": ["وانکومایسین"], "threshold": 60,
     "mid": ("dosing guided by blood levels", "دوز با سطح خون تنظیم می‌شود"),
     "low": ("levels are essential; dosing is fully kidney-guided", "اندازه‌گیری سطح ضروری است؛ دوز کاملاً کلیوی تنظیم می‌شود")},
]


def find_drug(query: str) -> dict[str, Any] | None:
    q = normalize(query)
    if not q:
        return None
    for d in _DRUGS:
        for alias in d["en"] + d["fa"]:
            if normalize(alias) in q or q in normalize(alias):
                return d
    return None


def drug_check(drug_name: str, crcl: float) -> dict[str, Any]:
    fa = is_fa()
    d = find_drug(drug_name or "")
    if d is None:
        return {"ok": True, "known": False,
                "message_fa": ("این دارو در جدول تنظیم دوز کلیوی نیست — از پزشک یا داروساز بپرس."
                               if fa else "This drug is not in the renal dosing table - ask your doctor or pharmacist.")}
    crcl = _num(crcl)
    known_names = d["fa"][0] if fa else d["en"][0].title()
    if crcl >= d["threshold"]:
        msg = d["mid"][1] if fa else d["mid"][0]
        level = "yellow" if crcl < 60 else "green"
    else:
        msg = d["low"][1] if fa else d["low"][0]
        level = "red"
    return {"ok": True, "known": True, "drug": known_names, "threshold": d["threshold"], "level": level,
            "message_fa": msg}
