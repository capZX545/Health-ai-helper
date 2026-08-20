# -*- coding: utf-8 -*-
"""
drug_interaction.py — جست‌وجوی دارو/گیاه دارویی + بررسی تداخل + هشدار حساسیت. اطلاعات عمومی آموزشی است؛ تصمیم نهایی فقط با پزشک/داروساز است.
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
    {"id": "senna", "fa": ["سنا", "برگ سنا", "شربت سنا"], "en": ["senna"], "cat": "ملین گیاهی"},
    {"id": "licorice", "fa": ["ریشه‌ی شیرین‌بیان", "شیرین بیان"], "en": ["licorice", "liquorice"], "cat": "گیاه دارویی"},
    {"id": "chamomile", "fa": ["بابونه", "چای بابونه"], "en": ["chamomile"], "cat": "گیاه دارویی"},
    # ---- مسکن/تب‌بر ----
    {"id": "celecoxib", "fa": ["سلکوکسیب", "سلبرکس"], "en": ["celecoxib", "celebrex"], "cat": "مسکن NSAID (COX-2)"},
    {"id": "mefenamic", "fa": ["مفنامیک اسید", "پونستان"], "en": ["mefenamic acid", "ponstan"], "cat": "مسکن NSAID"},
    {"id": "indomethacin", "fa": ["ایندومتاسین", "ایندومتاسین"], "en": ["indomethacin", "indocid"], "cat": "مسکن NSAID"},
    {"id": "ketorolac", "fa": ["کتورولاک"], "en": ["ketorolac"], "cat": "مسکن NSAID"},
    # ---- آنتی‌بیوتیک/ضدعفونی ----
    {"id": "cephalexin", "fa": ["سفالکسین", "کفالکسین"], "en": ["cephalexin", "keflex"], "cat": "آنتی‌بیوتیک (سفالوسپورین)"},
    {"id": "cefixime", "fa": ["سفیکسیم", "سوپراکس"], "en": ["cefixime", "suprax"], "cat": "آنتی‌بیوتیک (سفالوسپورین)"},
    {"id": "clarithromycin", "fa": ["کلاریترومایسین", "کلاسیت"], "en": ["clarithromycin", "biaxin"], "cat": "آنتی‌بیوتیک (ماکرولید)"},
    {"id": "doxycycline", "fa": ["داوسیکلین", "دوکسی‌سایکلین", "ویبرامایسین"], "en": ["doxycycline", "vibramycin"], "cat": "آنتی‌بیوتیک (تتراسایکلین)"},
    {"id": "clindamycin", "fa": ["کلیندامایسین", "کلیناسین"], "en": ["clindamycin", "dalacin"], "cat": "آنتی‌بیوتیک"},
    {"id": "levofloxacin", "fa": ["لووفلوکساسین", "لووکس"], "en": ["levofloxacin", "levaquin"], "cat": "آنتی‌بیوتیک (فلوروکینولون)"},
    {"id": "nitrofurantoin", "fa": ["نیتروفورانتوئین", "فورادانتین"], "en": ["nitrofurantoin", "macrobid"], "cat": "آنتی‌بیوتیک ادراری"},
    {"id": "trimethoprim_sulfa", "fa": ["کو-تریموکسازول", "سینولار", "باکتیریم"], "en": ["co-trimoxazole", "trimethoprim sulfamethoxazole", "bactrim"], "cat": "آنتی‌بیوتیک"},
    {"id": "fluconazole", "fa": ["فلوکونازول", "دیفلوکان"], "en": ["fluconazole", "diflucan"], "cat": "ضدقارچ"},
    {"id": "clotrimazole", "fa": ["کلوتریمازول", "کانستن"], "en": ["clotrimazole", "canesten"], "cat": "ضدقارچ موضعی"},
    {"id": "acyclovir", "fa": ["آسیکلوویر", "زوویراکس"], "en": ["acyclovir", "zovirax"], "cat": "ضدویروس"},
    {"id": "oseltamivir", "fa": ["اسلتاموییر", "تامی‌فلو"], "en": ["oseltamivir", "tamiflu"], "cat": "ضدویروس (آنفلوآنزا)"},
    # ---- قلب و عروق ----
    {"id": "rosuvastatin", "fa": ["روزوواستاتین", "کرستور"], "en": ["rosuvastatin", "crestor"], "cat": "کاهنده‌ی چربی خون"},
    {"id": "simvastatin", "fa": ["سیمواستاتین", "زوکور"], "en": ["simvastatin", "zocor"], "cat": "کاهنده‌ی چربی خون"},
    {"id": "ezetimibe", "fa": ["ازتیمایب", "ازترول"], "en": ["ezetimibe", "ezetrol"], "cat": "کاهنده‌ی چربی خون"},
    {"id": "fenofibrate", "fa": ["فنوفیبرات", "لیپانتیل"], "en": ["fenofibrate", "lipanthyl"], "cat": "کاهنده‌ی تری‌گلیسیرید"},
    {"id": "bisoprolol", "fa": ["بیسوپرولول", "کونکور"], "en": ["bisoprolol", "concor"], "cat": "بتابلاکر"},
    {"id": "metoprolol", "fa": ["متوپرولول", "لوپرسور"], "en": ["metoprolol", "lopressor"], "cat": "بتابلاکر"},
    {"id": "carvedilol", "fa": ["کارودیلول", "کورگ"], "en": ["carvedilol", "coreg"], "cat": "بتابلاکر"},
    {"id": "atenolol", "fa": ["آتنولول", "تنورمین"], "en": ["atenolol", "tenormin"], "cat": "بتابلاکر"},
    {"id": "valsartan", "fa": ["والزارتان", "دیوان"], "en": ["valsartan", "diovan"], "cat": "ضد فشار خون (ARB)"},
    {"id": "telmisartan", "fa": ["تل می سارتان", "میکاردیس"], "en": ["telmisartan", "micardis"], "cat": "ضد فشار خون (ARB)"},
    {"id": "enalapril", "fa": ["انالاپریل", "رنیتک"], "en": ["enalapril", "renitec"], "cat": "ضد فشار خون (ACEI)"},
    {"id": "ramipril", "fa": ["رامی‌پریل", "تریتیس"], "en": ["ramipril", "tritace"], "cat": "ضد فشار خون (ACEI)"},
    {"id": "spironolactone", "fa": ["اسپیرونولاکتون", "آلداکتون"], "en": ["spironolactone", "aldactone"], "cat": "مدر نگهدارنده‌ی پتاسیم"},
    {"id": "rivaroxaban", "fa": ["ریواروکسابان", "زارلتو"], "en": ["rivaroxaban", "xarelto"], "cat": "ضد انعقاد (NOAC)"},
    {"id": "apixaban", "fa": ["آپیکسابان", "الیکویس"], "en": ["apixaban", "eliquis"], "cat": "ضد انعقاد (NOAC)"},
    {"id": "clopidogrel", "fa": ["کلوپیدوگرل", "پلاویکس"], "en": ["clopidogrel", "plavix"], "cat": "ضدپلاکت"},
    {"id": "ticagrelor", "fa": ["تیکاگرلور", "بریلینتا"], "en": ["ticagrelor", "brilinta"], "cat": "ضدپلاکت"},
    {"id": "amiodarone", "fa": ["آمیودارون", "کوردارون"], "en": ["amiodarone", "cordarone"], "cat": "ضد آریتمی"},
    {"id": "isosorbide", "fa": ["ایزوسورباید", "ایزوردیل"], "en": ["isosorbide", "isordil"], "cat": "ضد آنژین (نیترات)"},
    # ---- دیابت/تیروئید ----
    {"id": "gliclazide", "fa": ["گلیکلازید", "دیامیکرون"], "en": ["gliclazide", "diamicron"], "cat": "ضد دیابت (سولفونیل‌اوره)"},
    {"id": "sitagliptin", "fa": ["سیتاگلیپتین", "جانوویا"], "en": ["sitagliptin", "januvia"], "cat": "ضد دیابت"},
    {"id": "empagliflozin", "fa": ["امپاگلیفلوزین", "جاردیانس"], "en": ["empagliflozin", "jardiance"], "cat": "ضد دیابت (SGLT2)"},
    {"id": "insulin_glargine", "fa": ["انسولین گلارژین", "لانتوس"], "en": ["insulin glargine", "lantus"], "cat": "انسولین طولانی‌اثر"},
    {"id": "carbimazole", "fa": ["کاربیمازول", "نئومرکازول"], "en": ["carbimazole", "neo-mercazole"], "cat": "ضد پرکاری تیروئید"},
    # ---- گوارش ----
    {"id": "esomeprazole", "fa": ["ازومپرازول", "نکسیوم"], "en": ["esomeprazole", "nexium"], "cat": "کاهنده‌ی اسید معده (PPI)"},
    {"id": "famotidine", "fa": ["فاموتیدین"], "en": ["famotidine"], "cat": "کاهنده‌ی اسید معده (H2)"},
    {"id": "ondansetron", "fa": ["اندانسترون", "زوفران"], "en": ["ondansetron", "zofran"], "cat": "ضد تهوع"},
    {"id": "metoclopramide", "fa": ["متوکلوپرامید", "پرنورم"], "en": ["metoclopramide", "primperan"], "cat": "ضد تهوع/دستگاه گوارش"},
    {"id": "loperamide", "fa": ["لوپرامید", "ایمودیوم"], "en": ["loperamide", "imodium"], "cat": "ضد اسهال"},
    {"id": "lactulose", "fa": ["لاکتولوز", "دوفالاک"], "en": ["lactulose", "duphalac"], "cat": "ملین"},
    {"id": "bisacodyl", "fa": ["بیساکودییل", "دلوکوکس"], "en": ["bisacodyl", "dulcolax"], "cat": "ملین"},
    # ---- تنفسی/آلرژی ----
    {"id": "fexofenadine", "fa": ["فکسوفنادین", "الرتفکس"], "en": ["fexofenadine", "allegra"], "cat": "آنتی‌هیستامین"},
    {"id": "chlorpheniramine", "fa": ["کلرفنیرامین"], "en": ["chlorpheniramine"], "cat": "آنتی‌هیستامین خواب‌آور"},
    {"id": "hydroxyzine", "fa": ["هیدروکسی‌زین", "آتاراکس"], "en": ["hydroxyzine", "atarax"], "cat": "آنتی‌هیستامین/ضدخارش"},
    {"id": "pseudoephedrine", "fa": ["سودوافدرین"], "en": ["pseudoephedrine", "sudafed"], "cat": "بازکننده‌ی بینی"},
    {"id": "xylometazoline", "fa": ["زایلومتازولین", "اتریوین"], "en": ["xylometazoline", "otrivin"], "cat": "قطره‌ی بینی (کوتاه‌مدت)"},
    {"id": "ipratropium", "fa": ["ایپراتروپیوم", "اترونت"], "en": ["ipratropium", "atrovent"], "cat": "اسپری برونکودیلاتور"},
    {"id": "budesonide", "fa": ["بودزوناید", "پولمیکورت"], "en": ["budesonide", "pulmicort"], "cat": "کورتون استنشاقی"},
    {"id": "fluticasone", "fa": ["فلوتیکازون", "فلوونت/آوامیس"], "en": ["fluticasone", "flixotide", "avamys"], "cat": "کورتون استنشاقی/بینی"},
    {"id": "montelukast", "fa": ["مونته‌لوکاست", "سینگولیر"], "en": ["montelukast", "singulair"], "cat": "ضد آسم/آلرژی"},
    {"id": "theophylline", "fa": ["تئوفیلین"], "en": ["theophylline"], "cat": "برونکودیلاتور"},
    # ---- اعصاب/روان ----
    {"id": "escitalopram", "fa": ["اسسیتالوپرام", "سرالکس", "لکساپرو"], "en": ["escitalopram", "lexapro", "cipralex"], "cat": "ضدافسردگی (SSRI)"},
    {"id": "paroxetine", "fa": ["پاروکستین", "پاکسیل"], "en": ["paroxetine", "paxil"], "cat": "ضدافسردگی (SSRI)"},
    {"id": "sertraline2", "fa": ["سرترالین", "زولوفت"], "en": ["sertraline", "zoloft"], "cat": "ضدافسردگی (SSRI)"},
    {"id": "venlafaxine", "fa": ["ونلافاکسین", "افکسور"], "en": ["venlafaxine", "effexor"], "cat": "ضدافسردگی (SNRI)"},
    {"id": "duloxetine", "fa": ["دولوکستین", "سیمبالتا"], "en": ["duloxetine", "cymbalta"], "cat": "ضدافسردگی/درد (SNRI)"},
    {"id": "mirtazapine", "fa": ["میرتازاپین", "رمران"], "en": ["mirtazapine", "remeron"], "cat": "ضدافسردگی"},
    {"id": "amitriptyline", "fa": ["آمی‌تریپتیلین", "تریپتیزول"], "en": ["amitriptyline", "elavil"], "cat": "ضدافسردگی سه‌حلقه‌ای/درد"},
    {"id": "diazepam", "fa": ["دیازپام", "والیوم"], "en": ["diazepam", "valium"], "cat": "ضد اضطراب (بنزودیازپین)"},
    {"id": "zolpidem", "fa": ["زولپیدم", "استیلنوکس"], "en": ["zolpidem", "stilnox", "ambien"], "cat": "خواب‌آور"},
    {"id": "melatonin", "fa": ["ملاتونین"], "en": ["melatonin"], "cat": "مکمل خواب"},
    {"id": "quetiapine", "fa": ["کوتیاپین", "سرکوئل"], "en": ["quetiapine", "seroquel"], "cat": "ضد روان‌پریشی/ثبات‌دهنده‌ی خلق"},
    {"id": "lithium", "fa": ["لیتیوم", "لیتیوم کربنات"], "en": ["lithium", "lithium carbonate"], "cat": "ثبات‌دهنده‌ی خلق"},
    {"id": "valproate", "fa": ["والپروات سدیم", "دپاکین"], "en": ["valproate", "depakine", "divalproex"], "cat": "ضدتشنج/ثبات‌دهنده‌ی خلق"},
    {"id": "carbamazepine", "fa": ["کاربامازپین", "تگرتول"], "en": ["carbamazepine", "tegretol"], "cat": "ضدتشنج"},
    {"id": "lamotrigine", "fa": ["لاموتریژین", "لامکتال"], "en": ["lamotrigine", "lamictal"], "cat": "ضدتشنج"},
    {"id": "levetiracetam", "fa": ["لوورتیراستام", "کپرا"], "en": ["levetiracetam", "keppra"], "cat": "ضدتشنج"},
    {"id": "phenytoin", "fa": ["فنی‌توئین", "دیلانتین"], "en": ["phenytoin", "dilantin"], "cat": "ضدتشنج"},
    {"id": "levodopa", "fa": ["لوودوپا/کاربی‌دوپا", "سینمت"], "en": ["levodopa", "sinemet"], "cat": "ضد پارکینسون"},
    {"id": "sumatriptan", "fa": ["سوماتریپتان", "ایمیگران"], "en": ["sumatriptan", "imigran"], "cat": "ضد میگرن (تریپتان)"},
    # ---- ادراری/تناسلی/زنان ----
    {"id": "alfuzosin", "fa": ["آلفوزوسین", "اوزترین"], "en": ["alfuzosin", "uroxatral"], "cat": "ضد بزرگی پروستات"},
    {"id": "finasteride", "fa": ["فیناسترید", "پروسکار"], "en": ["finasteride", "proscar"], "cat": "ضد بزرگی پروستات"},
    {"id": "sildenafil", "fa": ["سیلدنافیل", "ویاگرا"], "en": ["sildenafil", "viagra"], "cat": "ضد اختلال نعوظ"},
    {"id": "tadalafil", "fa": ["تادالافیل", "سیالیس"], "en": ["tadalafil", "cialis"], "cat": "ضد اختلال نعوظ"},
    {"id": "ocp", "fa": ["قرص ضدبارداری", "قرص ترکیبی پیشگیری", "OCP"], "en": ["contraceptive pill", "oral contraceptive", "ocp", "birth control pill"], "cat": "قرص ضدبارداری"},
    # ---- استخوان/مکمل ----
    {"id": "alendronate", "fa": ["آلندرونات", "فوزاماکس"], "en": ["alendronate", "fosamax"], "cat": "درمان پوکی استخوان"},
    {"id": "calcium", "fa": ["کلسیم", "قرص کلسیم"], "en": ["calcium", "calcium carbonate"], "cat": "مکمل"},
    {"id": "vitamin_d", "fa": ["ویتامین D", "ویتامین دی"], "en": ["vitamin d", "cholecalciferol"], "cat": "مکمل"},
    {"id": "iron_supplement", "fa": ["قرص آهن", "فروس سولفات"], "en": ["iron supplement", "ferrous sulfate"], "cat": "مکمل آهن"},
    {"id": "potassium", "fa": ["پتاسیم", "قرص پتاسیم"], "en": ["potassium", "kcl", "potassium chloride"], "cat": "مکمل پتاسیم"},
    {"id": "folic_acid", "fa": ["فولیک اسید", "اسید فولیک"], "en": ["folic acid", "folate"], "cat": "مکمل"},
    # ---- نقرس/گوارش التهابی/ایمنی ----
    {"id": "allopurinol", "fa": ["آلوپورینول", "زایلوپریم"], "en": ["allopurinol", "zyloprim"], "cat": "پیشگیری از نقرس"},
    {"id": "colchicine", "fa": ["کولشیسین"], "en": ["colchicine"], "cat": "درمان حمله‌ی نقرس"},
    {"id": "febuxostat", "fa": ["فبوکسوستات", "ادوریک"], "en": ["febuxostat", "uloric"], "cat": "کاهنده‌ی اوریک اسید"},
    {"id": "methotrexate", "fa": ["متوترکسات"], "en": ["methotrexate"], "cat": "سرکوب‌کننده‌ی ایمنی (سرکوب‌کننده‌ی ایمنی)"},
    {"id": "azathioprine", "fa": ["آزاتیوپرین"], "en": ["azathioprine", "imuran"], "cat": "سرکوب‌کننده‌ی ایمنی"},
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
    {"a": "warfarin", "b": "clopidogrel", "sev": "major", "fa": "ترکیب ضد انعقاد + ضدپلاکت خطر خونریزی را چند برابر می‌کند؛ فقط با نظر پزشک و پایش."},
    {"a": "warfarin", "b": "rivaroxaban", "sev": "major", "fa": "دو ضدانعقاد با هم؛ خطر شدید خونریزی — فقط در شرایط ویژه‌ی بیمارستانی."},
    {"a": "warfarin", "b": "fluconazole", "sev": "major", "fa": "فلوکونازول سطح وارفارین را بالا می‌برد؛ خطر خونریزی؛ تنظیم مجدد دوز."},
    {"a": "warfarin", "b": "amiodarone", "sev": "major", "fa": "آمیودارون اثر وارفارین را قوی می‌کند؛ کاهش دوز و پایش INR الزامی."},
    {"a": "warfarin", "b": "trimethoprim_sulfa", "sev": "major", "fa": "کو-تریموکسازول اثر ضدانعقادی را تشدید می‌کند؛ پایش INR."},
    {"a": "aspirin", "b": "clopidogrel", "sev": "major", "fa": "دو ضدپلاکت با هم؛ خطر خونریزی گوارشی — فقط با تجویز و معمولاً با محافظ معده."},
    {"a": "aspirin", "b": "ticagrelor", "sev": "moderate", "fa": "خطر خونریزی؛ آسپرین دوز بالا با تیکاگرلور توصیه نمی‌شود."},
    {"a": "clopidogrel", "b": "omeprazole", "sev": "moderate", "fa": "امپرازول فعال‌سازی کلوپیدوگرل را کم می‌کند؛ پانتوپرازول ترجیح دارد."},
    {"a": "lisinopril", "b": "spironolactone", "sev": "major", "fa": "خطر افزایش شدید پتاسیم؛ پایش منظم پتاسیم و کلیه الزامی."},
    {"a": "enalapril", "b": "ibuprofen", "sev": "moderate", "fa": "NSAID اثر کاهنده‌ی فشار ACEI را کم و خطر کلیوی را زیاد می‌کند."},
    {"a": "digoxin", "b": "amiodarone", "sev": "major", "fa": "آمیودارون سطح دیگوکسین را بالا می‌برد؛ خطر سمیت؛ کاهش دوز و پایش سطح خون."},
    {"a": "atorvastatin", "b": "clarithromycin", "sev": "major", "fa": "کلاریترومایسین سطح استاتین را بالا می‌برد؛ خطر آسیب عضلانی؛ توقف موقت استاتین رایج است."},
    {"a": "simvastatin", "b": "amlodipine", "sev": "moderate", "fa": "آملودیپین سطح سیمواستاتین را بالا می‌برد؛ سقف دوز ۲۰ میلی‌گرم."},
    {"a": "atorvastatin", "b": "fluconazole", "sev": "major", "fa": "خطر میوپاتی (آسیب عضلانی)؛ پایش درد عضلانی."},
    {"a": "gliclazide", "b": "fluconazole", "sev": "major", "fa": "فلوکونازول قند را خیلی پایین می‌آورد (هیپوگلیسمی)؛ پایش قند."},
    {"a": "insulin", "b": "propranolol", "sev": "moderate", "fa": "بتابلاکر علائم هشدار افت قند (تپش/لرز) را پنهان می‌کند؛ پایش دقیق‌تر قند."},
    {"a": "sertraline", "b": "sumatriptan", "sev": "moderate", "fa": "خطر سندروم سروتونین؛ ترکیب رایج است اما با نظر پزشک."},
    {"a": "escitalopram", "b": "ibuprofen", "sev": "moderate", "fa": "SSRI + NSAID خطر خونریزی گوارشی؛ با محافظ معده."},
    {"a": "sertraline", "b": "warfarin", "sev": "moderate", "fa": "SSRI خطر خونریزی با وارفارین را زیاد می‌کند؛ پایش INR."},
    {"a": "lithium", "b": "ibuprofen", "sev": "major", "fa": "NSAID سطح لیتیوم را بالا می‌برد؛ خطر سمیت؛ پایش سطح خون."},
    {"a": "lithium", "b": "ramipril", "sev": "major", "fa": "ACEI سطح لیتیوم را بالا می‌برد؛ پایش منظم."},
    {"a": "lithium", "b": "hctz", "sev": "major", "fa": "تیازید دفع لیتیوم را کم می‌کند؛ خطر تجمع و سمیت."},
    {"a": "valproate", "b": "lamotrigine", "sev": "major", "fa": "والپروات سطح لاموتریژین را بالا می‌برد؛ خطر بثورات خطرناک؛ دوز کم و زیر نظر."},
    {"a": "carbamazepine", "b": "ocp", "sev": "moderate", "fa": "کاربامازپین اثر قرص ضدبارداری را کم می‌کند؛ روش کمکی لازم است."},
    {"a": "phenytoin", "b": "ocp", "sev": "moderate", "fa": "اثر ضدبارداری کم می‌شود؛ روش کمکی."},
    {"a": "theophylline", "b": "ciprofloxacin", "sev": "major", "fa": "سیپروفلوکساسین سطح تئوفیلین را بالا می‌برد؛ کاهش دوز."},
    {"a": "theophylline", "b": "clarithromycin", "sev": "major", "fa": "سطح تئوفیلین بالا می‌رود؛ پایش سطح خون."},
    {"a": "allopurinol", "b": "azathioprine", "sev": "major", "fa": "آلوپورینول سطح آزاتیوپرین را چند برابر می‌کند؛ خطر سرکوب مغز استخوان — فقط زیر نظر."},
    {"a": "allopurinol", "b": "warfarin", "sev": "moderate", "fa": "اثر وارفارین تقویت می‌شود؛ پایش INR."},
    {"a": "methotrexate", "b": "ibuprofen", "sev": "major", "fa": "NSAID دفع متوترکسات را کم می‌کند؛ خطر سمیت — با نظر متخصص."},
    {"a": "methotrexate", "b": "trimethoprim_sulfa", "sev": "major", "fa": "خطر شدید سرکوب مغز استخوان؛ ترکیب ممنوع جز با تجویز."},
    {"a": "sildenafil", "b": "nitroglycerin", "sev": "major", "fa": "منع مصرف مطلق: نیترات + سیلدنافیل افت خطرناک فشار؛ حداقل ۲۴-۴۸ ساعت فاصله."},
    {"a": "sildenafil", "b": "isosorbide", "sev": "major", "fa": "نیترات + مهار PDE5 = افت شدید فشار؛ ممنوع."},
    {"a": "tadalafil", "b": "nitroglycerin", "sev": "major", "fa": "منع مصرف؛ افت خطرناک فشار خون."},
    {"a": "sildenafil", "b": "tamsulosin", "sev": "moderate", "fa": "افت فشار وضعیتی؛ شروع با دوز کم."},
    {"a": "zolpidem", "b": "diazepam", "sev": "major", "fa": "سرکوب تنفس؛ فقط تحت نظر پزشک."},
    {"a": "codeine", "b": "zolpidem", "sev": "major", "fa": "افیون + خواب‌آور: سرکوب تنفس."},
    {"a": "pseudoephedrine", "b": "propranolol", "sev": "moderate", "fa": "خطر فشار و ضربان بالا؛ احتیاط."},
    {"a": "levothyroxine", "b": "iron_supplement", "sev": "moderate", "fa": "آهن جذب لوواتیروکسین را کم می‌کند؛ حداقل ۴ ساعت فاصله."},
    {"a": "doxycycline", "b": "calcium", "sev": "moderate", "fa": "کلسیم جذب داوسیکلین را کم می‌کند؛ ۲ ساعت فاصله."},
    {"a": "alendronate", "b": "calcium", "sev": "moderate", "fa": "آلندرونات صبح ناشتا؛ کلسیم چند ساعت بعد."},
    {"a": "spironolactone", "b": "potassium", "sev": "major", "fa": "خطر پتاسیم بالا و آریتمی؛ فقط با آزمایش و تجویز."},
    {"a": "clopidogrel", "b": "fluconazole", "sev": "moderate", "fa": "فلوکونازول اثر ضدپلاکتی کلوپیدوگرل را کم می‌کند."},
    {"a": "amiodarone", "b": "simvastatin", "sev": "major", "fa": "سطح سیمواستاتین بالا می‌رود؛ سقف دوز ۲۰ میلی‌گرم."},
]

from i18n import pick as _pick


def SEV_FA() -> dict:
    return {"major": _pick(("severe interaction", "تداخل شدید")),
            "moderate": _pick(("moderate interaction", "تداخل متوسط")),
            "minor": _pick(("minor interaction", "تداخل خفیف"))}


INTERACTIONS_EN: dict[tuple[str, str], str] = {
    ("warfarin", "aspirin"): "Significantly raises the risk of GI bleeding; only under a doctor with monitoring.",
    ("warfarin", "ibuprofen"): "NSAIDs amplify anticoagulation and raise bleeding risk; avoid.",
    ("warfarin", "diclofenac"): "Higher bleeding and stomach-injury risk; ask your doctor for an alternative.",
    ("warfarin", "ginkgo"): "Ginkgo adds its own blood-thinning effect.",
    ("warfarin", "ginseng"): "Ginseng may destabilize warfarin effect (erratic INR).",
    ("warfarin", "greentea"): "Heavy green tea intake may weaken warfarin.",
    ("warfarin", "turmeric"): "Curcumin strengthens the anticoagulant effect; more bruising/bleeding.",
    ("warfarin", "garlic"): "Garlic supplements raise bleeding risk with warfarin.",
    ("aspirin", "ibuprofen"): "Ibuprofen blunts aspirin heart protection and stresses the stomach.",
    ("sertraline", "ibuprofen"): "SSRI + NSAID raises GI bleeding risk; only with doctor guidance.",
    ("fluoxetine", "stjohnswort"): "Serotonin syndrome risk; combine only under close supervision.",
    ("sertraline", "tramadol"): "Serotonin syndrome and seizure risk; prescription and monitoring only.",
    ("atorvastatin", "grapefruit"): "Grapefruit raises statin levels and muscle-injury risk.",
    ("metronidazole", "alcohol"): "Alcohol during metronidazole causes a severe reaction; avoid completely.",
    ("metformin", "alcohol"): "Alcohol raises lactic acidosis and low-sugar risk with metformin.",
    ("digoxin", "furosemide"): "Diuretics lower potassium and raise digoxin toxicity; electrolyte monitoring needed.",
    ("hctz", "lisinopril"): "A common, effective combination, but BP/potassium/kidneys need monitoring.",
    ("loratadine", "azithromycin"): "Possible QT prolongation in some people; check with a doctor if heart disease.",
    ("levothyroxine", "calcium"): "Calcium/iron supplements reduce absorption; keep at least 4 hours apart.",
    ("levothyroxine", "omeprazole"): "PPIs may slightly reduce thyroid hormone absorption; monitor TSH.",
    ("prednisolone", "ibuprofen"): "Steroid + NSAID markedly raises ulcer and bleeding risk.",
    ("prednisolone", "metformin"): "Steroids raise blood sugar; diabetes doses may need adjusting.",
    ("senna", "licorice"): "Chronic use together disturbs potassium balance.",
    ("licorice", "hctz"): "Licorice worsens potassium loss with diuretics.",
    ("codeine", "alprazolam"): "Respiratory depression; opioid plus benzodiazepine only under close supervision.",
    ("codeine", "tramadol"): "Respiratory depression and seizure risk.",
    ("glibenclamide", "aspirin"): "High-dose aspirin strengthens the sugar-lowering effect; monitor glucose.",
    ("captopril", "potassium"): "ACE inhibitors raise potassium; supplements only on doctor advice.",
    ("nitroglycerin", "alprazolam"): "Postural low blood pressure may worsen.",
    ("ciprofloxacin", "calcium"): "Dairy/calcium reduces ciprofloxacin absorption; keep 2 hours apart.",
    ("insulin", "prednisolone"): "Steroids increase insulin needs; close glucose monitoring.",
}


def DISCLAIMER() -> str:
    return _pick(("This check is educational and not exhaustive; show your full medication list to a doctor or pharmacist.",
                  "این بررسی آموزشی است و کامل نیست؛ فهرست دارویی کامل خود را به پزشک/داروساز نشان بده."))


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
                "message_fa": __import__("i18n").tt("One of the drugs was not found in the internal list; try the exact name (e.g. 'warfarin'). ", "یکی از داروها در پایگاه داخلی پیدا نشد؛ نام را دقیق‌تر بنویس (مثلاً «وارفارین» یا «warfarin»). ")+ DISCLAIMER()}
    from i18n import is_fa
    sev = SEV_FA()
    disp = lambda d: d["fa"] if is_fa() else d["en"]
    ida, idb = da[0]["id"], db[0]["id"]
    matches = []
    for it in INTERACTIONS:
        if {it["a"], it["b"]} == {ida, idb}:
            detail_en = INTERACTIONS_EN.get((it["a"], it["b"])) or INTERACTIONS_EN.get((it["b"], it["a"])) or it["fa"]
            matches.append({"severity": it["sev"], "severity_fa": sev[it["sev"]],
                            "a_fa": disp(da[0]), "b_fa": disp(db[0]),
                            "detail_fa": it["fa"] if is_fa() else detail_en})
    if not matches:
        matches.append({"severity": "none",
                        "severity_fa": _pick(("no known interaction in this small internal list", "تداخل شناخته‌شده‌ای در پایگاه کوچک داخلی ثبت نشده")),
                        "a_fa": disp(da[0]), "b_fa": disp(db[0]),
                        "detail_fa": _pick(("absence here does not mean it is definitely safe.", "نبودِ تداخل در این پایگاه به معنای بی‌خطر بودن قطعی نیست."))})
    return {"ok": True, "a": da[0], "b": db[0], "interactions": matches, "disclaimer": DISCLAIMER()}


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
                    import i18n as _i18n
                    alerts.append(_i18n.tt(f"'{name['en']}' matches an allergy on your profile ({alias})!",
                                           f"«{name['fa']}» با حساسیت ثبت‌شده‌ی شما ({alias}) مطابقت دارد!"))
                    break
    return {"ok": True, "alerts": alerts}
