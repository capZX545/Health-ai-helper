"""
DrugBank-style drug records: ATC class, route, half-life, metabolism,
contraindications, pregnancy warnings. Other modules (interactions, prescription
scan) read from here.
"""
from __future__ import annotations

from typing import Any

ATC_CATEGORIES = {
    "A": ("گوارش و سوخت‌وساز", "Alimentary tract and metabolism"),
    "B": ("خون و اعضای خون‌ساز", "Blood and blood forming organs"),
    "C": ("قلب و عروق", "Cardiovascular system"),
    "D": ("پوست", "Dermatologicals"),
    "G": ("دستگاه تناسلی و ادرار", "Genito-urinary system and sex hormones"),
    "H": ("هورمون‌های سیستمیک", "Systemic hormonal preparations"),
    "J": ("ضدعفونی عمومی", "Antiinfectives for systemic use"),
    "L": ("ضدنئوپلاسم و ایمنی", "Antineoplastic and immunomodulating agents"),
    "M": ("عضله و اسکلت", "Musculo-skeletal system"),
    "N": ("سیستم عصبی", "Nervous system"),
    "P": ("ضد انگل", "Antiparasitic products"),
    "R": ("دستگاه تنفسی", "Respiratory system"),
    "S": ("اندام‌های حسی", "Sensory organs"),
    "V": ("متفرقه", "Various"),
}

DRUG_DATABASE: dict[str, dict[str, Any]] = {
    "metformin": {
        "atc": "A10BA02", "class_fa": "ضد دیابت - بی‌گوانید", "half_life": "6h",
        "metabolism": "بدون متابولیسم کبدی، دفع کلیوی",
        "routes": ["خوراکی"], "pregnancy": "B (ایمن در بارداری با تجویز)",
        "contra_fa": "نارسایی کلیه (GFR<30)، اسیدوز متابولیک",
        "notes_fa": "خط اول دیابت نوع ۲؛ خطر کم هایپوگلیسمی؛ با غذا مصرف شود",
    },
    "insulin": {
        "atc": "A10AB01", "class_fa": "انسولین", "half_life": "variable",
        "metabolism": "آنزیمی (گلوکاگون)",
        "routes": ["زیرجلدی", "وریدی"], "pregnancy": "A (ضروری در دیابت نوع 1)",
        "contra_fa": "هایپوگلیسمی",
        "notes_fa": "نوع‌های مختلف: سریع (آسپارت)، رگولار (NPH)، طولانی (گلارژین/دگلودک)",
    },
    "warfarin": {
        "atc": "B01AA03", "class_fa": "ضدانعقاد - کومارین", "half_life": "36-42h",
        "metabolism": "کبدی CYP2C9",
        "routes": ["خوراکی"], "pregnancy": "X (منع مصرف در بارداری)",
        "contra_fa": "خونریزی فعال، زخم معده فعال، جراحی اخیر، IKR نامکنترل",
        "notes_fa": "پایش INR منظم حیاتی است؛ تداخل با ویتامین K و داروهای فراوان",
    },
    "atorvastatin": {
        "atc": "C10AA05", "class_fa": "کاهنده‌ی کلسترول - استاتین", "half_life": "14h",
        "metabolism": "کبدی CYP3A4",
        "routes": ["خوراکی"], "pregnancy": "X (منع مصرف)",
        "contra_fa": "بیماری کبدی فعال، بارداری، شیردهی",
        "notes_fa": "شب مصرف شود؛ درد عضلانی غیرعادی را گزارش کنید (CPK)",
    },
    "amoxicillin": {
        "atc": "J01CA04", "class_fa": "آنتی‌بیوتیک - آمینوپنی‌سیلین", "half_life": "1h",
        "metabolism": "کبدی جزئی، دفع کلیوی",
        "routes": ["خوراکی"], "pregnancy": "B (ایمن)",
        "contra_fa": "حساسیت به پنی‌سیلین",
        "notes_fa": "دوره‌ی کامل را تمام کنید؛ اسهال آنتی‌بیوتیکی شایع است",
    },
    "azithromycin": {
        "atc": "J01FA10", "class_fa": "آنتی‌بیوتیک - ماکرولید", "half_life": "68h",
        "metabolism": "بدون متابولیسم، دفع صفراوی",
        "routes": ["خوراکی", "وریدی"], "pregnancy": "B",
        "contra_fa": "حساسیت به ماکرولید، QT طولانی",
        "notes_fa": "۵ روز دوره (به دلیل نیمه‌عمر طولانی)؛ فاصله از آنتی‌اسید",
    },
    "ciprofloxacin": {
        "atc": "J01MA02", "class_fa": "آنتی‌بیوتیک - فلوروکینولون", "half_life": "4h",
        "metabolism": "کبدی جزئی، دفع کلیوی",
        "routes": ["خوراکی", "ورودی"], "pregnancy": "C (احتیاط)",
        "contra_fa": "حساسیت به کینولون، میاستنی گراویس",
        "notes_fa": "با لبنیات/کلسیم/آهن فاصله ۲ ساعت؛ خطر پارگی تاندون",
    },
    "sertraline": {
        "atc": "N06AB06", "class_fa": "ضدافسردگی - SSRI", "half_life": "26h",
        "metabolism": "کبدی گسترده",
        "routes": ["خوراکی"], "pregnancy": "C (ارزیابی ریسک/فایده)",
        "contra_fa": "هم‌زمانی با MAOI، سندروم سروتونین",
        "notes_fa": "اثر کامل ۴-۶ هفته زمان می‌برد؛ قطع تدریجی الزامی است",
    },
    "lithium": {
        "atc": "N05AN01", "class_fa": "ثبات‌دهنده‌ی خلق", "half_life": "24h",
        "metabolism": "بدون متابولیسم، دفع کلیوی",
        "routes": ["خوراکی"], "pregnancy": "D (خطر نقص جنین)",
        "contra_fa": "نارسایی کلیه، کم‌کاری تیروئید untreated، دیورتیک هم‌زمان",
        "notes_fa": "پایش سطح خون (0.6-1.2 mmol/L) حیاتی؛ سمیت با NSAID/دیورتیک",
    },
    "levothyroxine": {
        "atc": "H03AA01", "class_fa": "هورمون تیروئید", "half_life": "7d",
        "metabolism": "دکلرونیزاسیون",
        "routes": ["خوراکی"], "pregnancy": "A (ادامه در بارداری)",
        "contra_fa": "تیروتوکسیکوز کنترل‌نشده، سکته‌ی قلبی اخیر",
        "notes_fa": "صبح ناشتا ۳۰-۶۰ دقیقه قبل صبحانه؛ با کلسیم/آهن ۴ ساعت فاصله",
    },
    "salbutamol": {
        "atc": "R03AC02", "class_fa": "برونکودیلاتور - آگونیست بتا۲ کوتاه", "half_life": "4h",
        "metabolism": "کبدی",
        "routes": ["استنشاق", "خوراکی"], "pregnancy": "C (ایمن در استنشاق)",
        "contra_fa": "تاکی‌آریتمی کنترل‌نشده",
        "notes_fa": "اسپری نجات (rescue)؛ بیش از ۲ بار/هفته = کنترل ناکافی آسم",
    },
    "prednisolone": {
        "atc": "H02AB06", "class_fa": "کورتیکواستروئید سیستمیک", "half_life": "3h (بیولوژیک ۱۸-۳۶h)",
        "metabolism": "کبدی",
        "routes": ["خوراکی", "وریدی", "موضعی"], "pregnancy": "C",
        "contra_fa": "عفونت سیستمیک کنترل‌نشده، زخم معده فعال",
        "notes_fa": "قطع تدریجی الزامی (خطر نارسایی فوق کلیوی)؛ پایش قند/فشار",
    },
    "allopurinol": {
        "atc": "M04AA01", "class_fa": "کاهنده‌ی اوریک اسید", "half_life": "1-3h",
        "metabolism": "کبدی به اکسسی‌پورینول",
        "routes": ["خوراکی"], "pregnancy": "C",
        "contra_fa": "حمله‌ی حاد نقرس (شروع نکنید)، حساسیت",
        "notes_fa": "پیشگیری از حمله، نه درمان حمله؛ شروع با دوز کم + کلشیسین پوشش",
    },
    "digoxin": {
        "atc": "C01AA05", "class_fa": "گلیکوزید قلبی", "half_life": "36-48h",
        "metabolism": "کبدی جزئی، دفع کلیوی",
        "routes": ["خوراکی", "وریدی"], "pregnancy": "C",
        "contra_fa": "بلوک قلبی، تاکی‌آریتمی بطنی، هیپوکالمی",
        "notes_fa": "پایش سطح خون (0.5-2 ng/mL) و پتاسیم؛ سمیت با دیورتیک/آمیودارون",
    },
    "methotrexate": {
        "atc": "L01BA01", "class_fa": "ضدنئوپلاسم/ایمن‌Suppressor", "half_life": "3-10h",
        "metabolism": "کبدی جزئی، دفع کلیوی",
        "routes": ["خوراکی", "زیرجلدی", "وریدی"], "pregnancy": "X (منع مطلق)",
        "contra_fa": "بارداری، نارسایی کبد/کلیه، سرکوب مغز استخوان",
        "notes_fa": "همیشه با فولیک اسید؛ هفتگی (نه روزانه) در RA؛ پایش CBC/LFT",
    },
    "tamsulosin": {
        "atc": "G04CA02", "class_fa": "آلفا-۱ بلاکر (پروستات)", "half_life": "10h",
        "metabolism": "کبدی CYP3A4",
        "routes": ["خوراکی"], "pregnancy": "B (برای مردان)",
        "contra_fa": "افت فشار شدید، حساسیت به سولفا",
        "notes_fa": "۳۰ دقیقه بعد از همان وعده‌ی غذا هر روز؛ افت فشار وضعیتی شایع",
    },
    "sildenafil": {
        "atc": "G04BE03", "class_fa": "مهارکننده‌ی PDE5", "half_life": "4h",
        "metabolism": "کبدی CYP3A4",
        "routes": ["خوراکی"], "pregnancy": "N/A (مردان)",
        "contra_fa": "نیترات هر نوع، افت فشار شدید، بیماری شبکیه نادر",
        "notes_fa": "منع مصرف مطلق با نیترات (نیتروگلیسیرین/ایزوسورباید)",
    },
    "amiodarone": {
        "atc": "C01BD01", "class_fa": "ضد آریتمی کلاس III", "half_life": "40-55 روز",
        "metabolism": "کبدی",
        "routes": ["خوراکی", "وریدی"], "pregnancy": "D",
        "contra_fa": "برادیکاردی شدید، بلوک قلبی، تیروتوکسیکوز، آلرژی ید",
        "notes_fa": "نیمه‌عمر بسیار طولانی؛ پایش تیروئید/ریه/کبد/چشم؛ رنگ پوست",
    },
    "clopidogrel": {
        "atc": "B01AC04", "class_fa": "ضدپلاکت - تینوپیریدین", "half_life": "6h (متابولیت فعال)",
        "metabolism": "کبدی CYP2C19 (پروداروگ)",
        "routes": ["خوراکی"], "pregnancy": "B",
        "contra_fa": "خونریزی فعال، زخم معده، نارسایی کبدی شدید",
        "notes_fa": "با آسپرین در سندرم حاد کرونری؛ اثر ۵ روز شروع؛ قطع ۵ روز قبل جراحی",
    },
    "sumatriptan": {
        "atc": "N02CC01", "class_fa": "آگونیست سروتونین 5-HT1 (تریپتان)", "half_life": "2h",
        "metabolism": "کبدی MAO",
        "routes": ["خوراکی", "زیرجلدی", "بینی"], "pregnancy": "C",
        "contra_fa": "بیماری کرونری، سکته‌ی اخیر، HTN کنترل‌نشده، MAOI",
        "notes_fa": "در شروع حمله؛ حداکثر ۲ دوز در ۲۴ ساعت؛ سندرم سروتونین با SSRI",
    },
    "metoclopramide": {
        "atc": "A03FA01", "class_fa": "ضد تهوع - پروکینتیک", "half_life": "5h",
        "metabolism": "کبدی",
        "routes": ["خوراکی", "وریدی", "موضعی"], "pregnancy": "B",
        "contra_fa": "انسداد روده، پارکینسون، تشنج، خونریزی گوارشی",
        "notes_fa": "بی‌شک ستون عصبی: خطر دیستونی/تاردیو دیسکینزیا در مصرف طولانی",
    },
    "furosemide": {
        "atc": "C03CA01", "class_fa": "مدر لوپ", "half_life": "2h",
        "metabolism": "کبدی جزئی، دفع کلیوی",
        "routes": ["خوراکی", "وریدی"], "pregnancy": "C",
        "contra_fa": "بی‌آبی شدید، آنوری، کم‌شنوایی",
        "notes_fa": "پایش پتاسیم/سدیم/کرئاتینین؛ هایپوکالمی خطر دیگوکسین",
    },
    "morphine": {
        "atc": "N02AA01", "class_fa": "افیون قوی", "half_life": "2-4h",
        "metabolism": "کبدی (گلوکورونیداسیون)",
        "routes": ["خوراکی", "وریدی", "موضعی"], "pregnancy": "C",
        "contra_fa": "افسردگی تنفسی، انسداد روده، ترومبوسیتوپنی",
        "notes_fa": "دوز بر اساس پاسخ بالینی؛ نالوکسان آنتاگونیست؛ یبوست پیشگیرانه",
    },
    "vancomycin": {
        "atc": "J01XA01", "class_fa": "گلیکوپپتید (MRSA)", "half_life": "6h",
        "metabolism": "دفع کلیوی (بدون متابولیسم)",
        "routes": ["ورودی"], "pregnancy": "C",
        "contra_fa": "حساسیت، نارسایی کلیه بدون تنظیم دوز",
        "notes_fa": "پایش سطح خون (trough 15-20 mcg/mL)؛ نفروتوکسیسیتی/اتوتوکسیسیتی",
    },
    "folic_acid": {
        "atc": "B03BB01", "class_fa": "ویتامین B9", "half_life": "N/A",
        "metabolism": "کبدی",
        "routes": ["خوراکی"], "pregnancy": "A (توصیه در بارداری)",
        "contra_fa": "هیچ (ایمن)",
        "notes_fa": "۴۰۰ میکروگرم روزانه در بارداری (پیشگیری از نقص لوله‌ی عصبی)",
    },
    "alendronate": {
        "atc": "M05BA04", "class_fa": "بیس‌فسفونات", "half_life": "10 سال (در استخوان)",
        "metabolism": "بدون متابولیسم",
        "routes": ["خوراکی"], "pregnancy": "D",
        "contra_fa": "نارسایی مری، هیپوکلسمی، نارسایی کلیه",
        "notes_fa": "صبح ناشتا با آب فراوان؛ ۳۰ دقیقه ناشتا بمانید؛ کلسیم هم‌زمان نhilfe",
    },
}


def get_drug_info(drug_id: str) -> dict[str, Any] | None:
    """
    Full drug record from the DrugBank-style database.
    """
    return DRUG_DATABASE.get(drug_id)


def search_by_atc(letter: str) -> list[dict]:
    """
    All drugs under one ATC group.
    """
    return [{"id": k, **v} for k, v in DRUG_DATABASE.items() if v["atc"].startswith(letter)]


def search_by_class(query: str) -> list[dict]:
    """
    Search by drug class.
    """
    from common_2077 import normalize
    nq = normalize(query)
    return [{"id": k, **v} for k, v in DRUG_DATABASE.items() if nq in normalize(v["class_fa"])]


def pregnancy_category(drug_id: str) -> str:
    info = DRUG_DATABASE.get(drug_id)
    if not info:
        return "N/A"
    return info.get("pregnancy", "N/A")


def list_all() -> list[str]:
    return list(DRUG_DATABASE.keys())
