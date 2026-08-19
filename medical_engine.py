# -*- coding: utf-8 -*-
"""
medical_engine.py — موتور پزشکی آفلاین: لغت‌نامه‌ی علائم، علائم خطر (Red Flag)
و پایه‌ی دانش داخلی بیماری‌ها. هیچ اطلاعات بدون منبع ساختگی تولید نمی‌شود.
"""
from __future__ import annotations

import re
from typing import Any

from common_2077 import normalize

# ============================================================================
# ۱) لغت‌نامه‌ی علائم — شناسه → کلیدواژه‌های فارسی
# ============================================================================

SYMPTOM_NAMES_FA: dict[str, str] = {
    "fever": "تب", "cough": "سرفه", "sore_throat": "گلودرد", "runny_nose": "آبریزش بینی",
    "sneezing": "عطسه", "body_ache": "بدن‌درد", "headache": "سردرد", "nausea": "حالت تهوع",
    "vomiting": "استفراغ", "diarrhea": "اسهال", "abdominal_pain": "درد شکم",
    "dysuria": "سوزش ادرار", "urinary_frequency": "تکرر ادرار", "skin_itch": "خارش پوست",
    "rash": "کهیر/لک پوستی", "anxiety": "اضطراب", "chest_pain": "درد قفسه سینه",
    "shortness_of_breath": "تنگی نفس", "dizziness": "سرگیجه", "fatigue": "خستگی",
    "palpitation": "تپش قلب", "heartburn": "سوزش سر دل", "flank_pain": "درد پهلو",
    "insomnia": "بی‌خوابی", "mood_low": "افت خلق/ناراحتی", "wheezing": "خس‌خس سینه",
    "sputum": "خلط", "thirst": "تشنگی زیاد", "weight_loss": "کاهش وزن",
    "blurred_vision": "تار شدن دید", "unilateral_weakness": "ضعف یک طرفه‌ی بدن",
    "speech_difficulty": "اختلال تکلم", "face_droop": "کج شدن صورت",
    "seizure": "تشنج", "loss_of_consciousness": "بیهوشی", "severe_bleeding": "خونریزی شدید",
    "confusion": "کاهش سطح هوشیاری/گیجی", "night_sweats": "عرق شبانه",
    "constipation": "یبوست", "joint_pain": "درد مفاصل", "back_pain": "کمردرد",
    "eye_redness": "قرمزی چشم", "tear_eyes": "اشک‌ریزش", "sweating": "عرق‌کردن",
    "left_arm_pain": "درد بازوی چپ", "sore_throat_dry": "خشکی گلو", "bloating": "نفخ",
    "food_intolerance": "عدم تحمل غذا", "rapid_breathing": "تنفس تند", "cyanosis": "کبودی لب‌ها",
    "stiff_neck": "گردن‌گرفتگی/سفتی گردن", "photophobia": "حساسیت به نور",
    "apnea_observed": "قطع تنفس در خواب", "snoring": "خروپف", "daytime_sleepiness": "خواب‌آلودگی روزانه",
    "panic": "وحشت‌زدگی", "loss_of_interest": "بی‌علاقگی", "appetite_loss": "بی‌اشتهایی",
}

SYMPTOM_KEYWORDS: dict[str, list[str]] = {
    "fever": ["تب", "تب دارم", "بدنم گرم", "حرارت دارم"],
    "cough": ["سرفه", "سرفه خشک", "سرفه خلط دار", "سرفه می کنم"],
    "sore_throat": ["گلودرد", "درد گلو", "گلویم درد", "گلو درد"],
    "runny_nose": ["آبریزش بینی", "دردام", "ابریزش بینی", "بینیم آب می اید", "سرما خورده ام"],
    "sneezing": ["عطسه", "عطسه می کنم"],
    "body_ache": ["بدن درد", "بدندرد", "درد بدن", "عضلاتم درد می کند", "درد عضله"],
    "headache": ["سردرد", "سر درد", "سرم درد می کند", "درد سر"],
    "nausea": ["حالت تهوع", "تهوع", "دل به هم می خورد", "حالت تهوع دارم", "دلم به هم می خورد"],
    "vomiting": ["استفراغ", "استفراغ کردم", "قی کردم", "قی می کنم"],
    "diarrhea": ["اسهال", "اسهال دارم", "رو گشاده", "مدفوع آبکی"],
    "abdominal_pain": ["درد شکم", "دل درد", "شکم درد", "درد شکمم", "معده ام درد", "درد معده", "درد پهلو پایین"],
    "dysuria": ["سوزش ادرار", "ادرار سوزش", "سوزش موقع ادرار"],
    "urinary_frequency": ["تکرر ادرار", "ادرار زیاد", "مدام دستشویی می روم", "تکرر"],
    "skin_itch": ["خارش", "خارش دارم", "دستم خارش", "خارش شدید"],
    "rash": ["لک", "لک قرمز", "کهیر", "جوش", "بثورات", "قرمزی پوست"],
    "anxiety": ["اضطراب", "مضطرب", "نگران هستم", "استرس دارم", "بی قرارم"],
    "chest_pain": ["درد قفسه سینه", "درد سینه", "قفسه سینه ام درد", "درد قفسه صدری", "فشار روی سینه", "سینه ام فشار می اید"],
    "shortness_of_breath": ["تنگی نفس", "نفس کم می اورد", "نفس نفس", "نفس تنگ", "سخت نفس می کشم", "کم اوردن نفس"],
    "dizziness": ["سرگیجه", "سرم گیج می رود", "حالت سرگیجه", "گیجی"],
    "fatigue": ["خستگی", "خسته ام", "بی حوصله و خسته", "ضعف و بی حالی", "بی حال"],
    "palpitation": ["تپش قلب", "قلبم تند می زند", "تپش", "ضربان قلب تند"],
    "heartburn": ["سوزش سر دل", "سوزش معده", "ترش کردم", "رفلاکس", "سوزش زیر سینه"],
    "flank_pain": ["درد پهلو", "درد کلیه", "پهلویم درد", "درد کمر پهلو"],
    "insomnia": ["بی خوابی", "خوابم نمی برد", "نمی توانم بخوابم", "بی خواب شده ام"],
    "mood_low": ["افسرده", "ناراحت هستم", "حال بد", "افت روحیه", "غمگین", "بی حوصله شده ام", "حوصله ندارم"],
    "wheezing": ["خس خس", "صدای سینه", "سینه ام صدا می دهد"],
    "sputum": ["خلط", "خلط دارم", "ادرار خلط"],
    "thirst": ["تشنگی", "تشنه ام", "مدام آب می خورم", "دهنم خشک"],
    "weight_loss": ["کاهش وزن", "لاغر شده ام", "وزن کم کرده ام", "وزنم کم شده"],
    "blurred_vision": ["تار شدن دید", "چشمانم تار", "تار می بینم", "دید تار"],
    "unilateral_weakness": ["ضعف یک طرف", "دست و پسم بی lực", "فلج", "یك طرف بدنم ضعف", "یک طرف بدنم بی حس", "دستم بی حس شده", "پایم بی حس"],
    "speech_difficulty": ["حرف زدن مشکل", "حرف نمی تواند بزند", "زبان بند می اید", "اختلال تکلم", "جمله هایم به هم می ریزد"],
    "face_droop": ["کج شدن صورت", "صورت کج", "دهان کج", "پلک افتاده یک طرف"],
    "seizure": ["تشنج", "تشنج کرد", "صرع", "حرکات غیر ارادی"],
    "loss_of_consciousness": ["بیهوش", "بیهوش شد", "کاما", "هوشیار نیست", "بیهوشی"],
    "severe_bleeding": ["خونریزی شدید", "خونریزی زیاد", "خون نمی ایستد", "خونریزی"],
    "confusion": ["گیج و منگ", "هوشیاری کم", "خواب آلود و بی قرار", "حالت کما", "منگ", "گیجی شدید"],
    "night_sweats": ["عرق شبانه", "شب ها عرق می کنم", "عرق کردن شب"],
    "constipation": ["یبوست", "مدفوع سفت", "دستشویی نمی روم"],
    "joint_pain": ["درد مفاصل", "مفاصلم درد", "درد زانو", "درد مفصل"],
    "back_pain": ["کمردرد", "کمر درد", "کمرم درد"],
    "eye_redness": ["قرمزی چشم", "چشم قرمز", "چشمانم قرمز"],
    "tear_eyes": ["اشک ریزش", "چشمم اشک می ریزد", "اشک"],
    "sweating": ["عرق سرد", "عرق کردم", "درد و عرق"],
    "left_arm_pain": ["درد بازوی چپ", "دست چپم درد", "درد شانه چپ", "درد بازو چپ"],
    "bloating": ["نفخ", "پف کردم", "شکمم باد"],
    "rapid_breathing": ["تنفس تند", "نفس تند", "تنفس سریع"],
    "cyanosis": ["کبودی لب", "لب ها کبود", "کبود شدن لب"],
    "stiff_neck": ["سفتی گردن", "گردن سفتی", "گردن نمی چرخد"],
    "photophobia": ["نور چشم می اذارد", "حساسیت به نور", "نور اذیت می کند"],
    "apnea_observed": ["قطع تنفس در خواب", "تنفس در خواب قطع", "اپنه"],
    "snoring": ["خروپف", "خر و پف", "خروپف شدید"],
    "daytime_sleepiness": ["خواب آلودگی روزانه", "روزها خواب الود", "مدام خوابم می برد"],
    "panic": ["وحشت", "پنیک", "حمله اضطراب", "دلم می خواهد جیغ بکشم"],
    "loss_of_interest": ["بی علاقگی", "هیچ چیز برایم جذاب نیست", "لذت نمی برم"],
    "appetite_loss": ["بی اشتهایی", "اشتها ندارم", "غذا نمی خورم"],
}

NEGATION_WORDS = ["ندارم", "نداشتم", "نمی", "نبود", "خیر", "ندارد", "نکردم", "نکنم", "نیست", "خلاف"]
SEVERE_WORDS = ["شدید", "خیلی زیاد", "غیرقابل تحمل", "وحشتناک", "بسیار شدید", "کمرشکن", "دیگره", "متحمل"]
MILD_WORDS = ["خفیف", "کم", "جزئی", "ناچیز", "کمی"]

# ============================================================================
# ۲) علائم خطر — بخش ۱۳ پرامپت
# ============================================================================

RED_FLAGS: list[dict[str, Any]] = [
    {"id": "chest_pain", "any": ["درد قفسه سینه", "درد قفسه صدری", "درد سینه", "قفسه سینه ام درد", "قفسه سینه درد", "فشار روی سینه", "سینه ام فشار"], "label": "درد قفسه سینه"},
    {"id": "severe_sob", "any": ["تنگی نفس شدید", "نفس نمی توانم", "نفس نمی تواند", "نفس نفس", "سخت نفس"], "label": "تنگی نفس"},
    {"id": "severe_bleeding", "any": ["خونریزی شدید", "خونریزی زیاد", "خون نمی ایستد"], "label": "خونریزی شدید"},
    {"id": "unconscious", "any": ["بیهوش", "هوشیار نیست", "هوشیاری ندارد", "کما"], "label": "بیهوشی"},
    {"id": "seizure", "any": ["تشنج"], "label": "تشنج"},
    {"id": "sudden_weakness", "any": ["ضعف ناگهانی", "فلج", "بی حس شد", "بی حس شده", "ضعف یک طرف", "یک طرف بدنم ضعف", "دستم بی حس", "پایم بی حس"], "label": "ضعف یا فلج ناگهانی"},
    {"id": "speech", "any": ["حرف زدن مشکل", "اختلال تکلم", "زبان بند", "حرف نمی تواند", "نمی تواند حرف", "نمی توانم حرف", "سخن گفتن مشکل"], "label": "اختلال تکلم"},
    {"id": "face_droop", "any": ["کج شدن صورت", "صورت کج", "صورتش کج", "دهان کج", "صورت کج شد"], "label": "کج شدن صورت"},
    {"id": "consciousness", "any": ["گیج و منگ", "کاهش هوشیاری", "خواب آلود و بی قرار", "حالت کما", "منگ شده"], "label": "کاهش سطح هوشیاری"},
    {"id": "high_fever", "any": ["تب 40", "تب 41", "تب بالای 40", "تب خیلی بالا", "تب شدید"], "label": "تب بسیار شدید"},
    {"id": "sudden_severe_pain", "any": ["درد شدید ناگهانی", "ناگهانی درد شدید", "درد غیرقابل تحمل", "درد وحشتناک"], "label": "درد شدید ناگهانی"},
]

_NUM = r"(\d{1,3}(?:[.,]\d)?)"
DURATION_RE = re.compile(_NUM + r"\s*(روز|هفته|شب|ماه|سال|ساعت)", re.IGNORECASE)
TEMP_RE = re.compile(r"(?:تب|حرارت)\s*"+ _NUM)
FEVER_RE = re.compile(r"تب\s*(\d{2}(?:[.,]\d)?)")

# ============================================================================
# ۳) پایه‌ی دانش داخلی — احتمالات بالینی رایج (فقط اطلاعات عمومی شناخته‌شده)
#    p = برآورد P(علامت | بیماری) برای موتور بیز؛ همه‌ی خروجی‌ها «احتمالی» ارائه می‌شوند.
# ============================================================================

DISEASES: list[dict[str, Any]] = [
    {"id": "common_cold", "fa": "سرماخوردگی", "en": "Common cold", "prior": 0.16, "urgency": "routine",
     "symptoms": {"cough": 0.8, "sore_throat": 0.6, "runny_nose": 0.85, "sneezing": 0.7, "fever": 0.3, "headache": 0.35, "body_ache": 0.35, "sputum": 0.3},
     "advice": ["استراحت و خواب کافی", "مایعات گرم فراوان", "غرغره‌ی آب نمک ولرم برای گلودرد", "تب‌بر ساده مثل استامینوفن طبق دستور داروخانه/پزشک"],
     "doctor_when": "اگر تب بیش از ۳ روز ادامه یافت یا گلودرد شدید با تب بالا بدون سرفه"},
    {"id": "influenza", "fa": "آنفلوآنزا", "en": "Influenza", "prior": 0.09, "urgency": "routine",
     "symptoms": {"fever": 0.9, "body_ache": 0.85, "headache": 0.7, "cough": 0.7, "fatigue": 0.9, "sore_throat": 0.4, "chills": 0.6, "night_sweats": 0.3},
     "advice": ["استراحت کامل در خانه", "مایعات فراوان", "استامینوفن برای تب و بدن‌درد در صورت نیاز", "پرهیز از حضور در جمع تا بهبودی"],
     "doctor_when": "اگر تنگی نفس، درد قفسه سینه یا تب بالای ۳ روز داشتید؛ یا گروه پرخطر (بارداری، سالمند، بیماری زمینه‌ای)"},
    {"id": "allergic_rhinitis", "fa": "آلرژی فصلی", "en": "Allergic rhinitis", "prior": 0.08, "urgency": "routine",
     "symptoms": {"sneezing": 0.9, "runny_nose": 0.85, "tear_eyes": 0.5, "eye_redness": 0.4, "skin_itch": 0.3, "cough": 0.25},
     "advice": ["اجتناب از مواجهه با محرک (گرد و غبار، گرده)", "شست‌وشوی بینی با سالین", "آنتی‌هیستامین بدون نسخه در صورت صلاحدید داروخانه"],
     "doctor_when": "اگر علائم بیشتر از ۲ هفته ادامه یافت یا تنگی نفس اضافه شد"},
    {"id": "covid_like", "fa": "عفونت تنفسی ویروسی (شبیه کووید)", "en": "COVID-like viral illness", "prior": 0.05, "urgency": "routine",
     "symptoms": {"fever": 0.7, "cough": 0.8, "fatigue": 0.8, "sore_throat": 0.5, "shortness_of_breath": 0.25, "loss_of_smell": 0.4, "body_ache": 0.6},
     "advice": ["استراحت و ایزوله‌شدن در خانه", "تست تشخیصی در صورت دسترسی", "پایش تنفس؛ در صورت بدترشدن تنگی نفس اورژانس"],
     "doctor_when": "تنگی نفس، اشباع اکسیژن پایین، درد قفسه سینه"},
    {"id": "migraine", "fa": "میگرن احتمالی", "en": "Migraine (possible)", "prior": 0.06, "urgency": "routine",
     "symptoms": {"headache": 1.0, "nausea": 0.6, "photophobia": 0.6, "vomiting": 0.3, "dizziness": 0.3, "blurred_vision": 0.25},
     "advice": ["استراحت در اتاق تاریک و ساکت", "خواب کافی و پرهیز از محرک‌ها (بی‌خوابی، گرسنگی، استرس)", "ثبت دفترچه‌ی سردرد برای یافتن محرک‌ها"],
     "doctor_when": "سردرد ناگهانی و شدیدترین عمر، سردرد با تب و سفتی گردن، یا سردرد با ضعف بدن → فوری"},
    {"id": "tension_headache", "fa": "سردرد تنشی", "en": "Tension headache", "prior": 0.07, "urgency": "routine",
     "symptoms": {"headache": 1.0, "stress": 0.6, "fatigue": 0.5, "insomnia": 0.4, "back_pain": 0.3},
     "advice": ["تنظیم خواب و استراحت چشم", "کشش و حرکات شانه و گردن", "کمکردن استرس و صفحه‌نمایش"],
     "doctor_when": "تغییر الگوی سردرد یا همراهی با علائم عصبی"},
    {"id": "gastroenteritis", "fa": "گاستروانتریت (اسهال عفونی)", "en": "Gastroenteritis", "prior": 0.08, "urgency": "routine",
     "symptoms": {"diarrhea": 0.9, "nausea": 0.7, "vomiting": 0.6, "abdominal_pain": 0.7, "fever": 0.4, "appetite_loss": 0.5},
     "advice": ["ORS/مایعات و آب فراوان برای جبران آب", "غذای سبک و کم‌چرب (برنج، سوپ)", "پرهیز از لبنیات و غذاهای چرب تا بهبود نسبی"],
     "doctor_when": "خون در مدفوع، اسهال بیش از ۳ روز، علائم کم‌آبی شدید (بی‌ادراری، خشکی دهان)، تب بالا"},
    {"id": "food_poisoning", "fa": "احتمال مسمومیت غذایی", "en": "Food poisoning (possible)", "prior": 0.05, "urgency": "routine",
     "symptoms": {"vomiting": 0.8, "nausea": 0.8, "diarrhea": 0.7, "abdominal_pain": 0.7, "fever": 0.3},
     "advice": ["مایعات کوچک و مکرر", "استراحت", "پرهیز از غذای مشکوک مصرف‌شده"],
     "doctor_when": "استفراغ مداوم بیش از ۲۴ ساعت، خون در مدفوع، تب بالا، علائم کم‌آبی"},
    {"id": "gerd", "fa": "رفلاکس معده به مری (احتمالی)", "en": "GERD (possible)", "prior": 0.06, "urgency": "routine",
     "symptoms": {"heartburn": 0.9, "chest_pain": 0.3, "nausea": 0.3, "sore_throat_dry": 0.25, "bloating": 0.4, "cough": 0.2},
     "advice": ["پرهیز از غذای تند/چرب/قهوه و نوشیدنی گازدار", "خوابیدن با سر بالا و شام سبک ۳ ساعت قبل خواب", "کاهش وزن در صورت اضافه‌وزن"],
     "doctor_when": "درد قفسه سینه مطرح است → اول اورژانس؛ بلع دشوار یا کاهش وزن"},
    {"id": "peptic_ulcer", "fa": "زخم معده (احتمالی)", "en": "Peptic ulcer (possible)", "prior": 0.03, "urgency": "routine",
     "symptoms": {"abdominal_pain": 0.9, "heartburn": 0.5, "nausea": 0.4, "bloating": 0.4, "vomiting": 0.2},
     "advice": ["پرهیز از مسکن‌های NSAID مثل ایبوپروفن بدون نظر پزشک", "غذای منظم و پرهیز از سیگار و الکل"],
     "doctor_when": "استفراغ خونی یا مدفوع سیاه → فوری؛ درد شدید ناگهانی شکم → اورژانس"},
    {"id": "uti", "fa": "عفونت ادراری (احتمالی)", "en": "UTI (possible)", "prior": 0.06, "urgency": "routine",
     "symptoms": {"dysuria": 0.9, "urinary_frequency": 0.8, "abdominal_pain": 0.4, "flank_pain": 0.25, "fever": 0.25, "hematuria": 0.2},
     "advice": ["نوشیدن آب کافی", "مراجعه برای آزمایش ادرار و در صورت نیاز آنتی‌بیوتیک با تجویز پزشک"],
     "doctor_when": "تب و لرز با درد پهلو (درگیری کلیه)، بارداری، یا خون در ادرار"},
    {"id": "kidney_stone", "fa": "سنگ کلیه (احتمالی)", "en": "Kidney stone (possible)", "prior": 0.03, "urgency": "urgent",
     "symptoms": {"flank_pain": 0.9, "abdominal_pain": 0.4, "nausea": 0.5, "vomiting": 0.4, "dysuria": 0.3, "hematuria": 0.4},
     "advice": ["درد شدید کولیکی → مراجعه فوری", "آب فراوان بعد از نظر پزشک"],
     "doctor_when": "درد کولیکی شدید، تب، یا استفراغ مداوم → اورژانس"},
    {"id": "strep_throat", "fa": "گلودرد استرپتوکوکی (احتمالی)", "en": "Strep throat (possible)", "prior": 0.03, "urgency": "routine",
     "symptoms": {"sore_throat": 1.0, "fever": 0.7, "headache": 0.3, "appetite_loss": 0.3, "cough": 0.1},
     "advice": ["غرغره‌ی آب نمک", "مایعات گرم", "معاینه و در صورت نیاز تست سریع استرپ"],
     "doctor_when": "تب بالا با گلودرد شدید بدون سرفه، تورم گردن یا مشکل تنفس"},
    {"id": "sinusitis", "fa": "سینوزیت (احتمالی)", "en": "Sinusitis (possible)", "prior": 0.04, "urgency": "routine",
     "symptoms": {"headache": 0.8, "runny_nose": 0.6, "fever": 0.3, "cough": 0.4, "facial_pain": 0.7, "fatigue": 0.4},
     "advice": ["شست‌وشوی بینی با سالین", "بخور آب گرم", "استراحت"],
     "doctor_when": "علائم بیش از ۱۰ روز، تب بالا، تورم دور چشم → فوری"},
    {"id": "hypertension_likely", "fa": "فشار خون بالا (احتمالی)", "en": "Possible high BP", "prior": 0.04, "urgency": "routine",
     "symptoms": {"headache": 0.5, "dizziness": 0.4, "palpitation": 0.3, "fatigue": 0.3, "blurred_vision": 0.2},
     "advice": ["اندازه‌گیری فشار خون در آرامش، چند بار", "کمکردن نمک، ترک سیگار، فعالیت هوازی منظم"],
     "doctor_when": "فشار ≥ ۱۸۰/۱۲۰ یا درد قفسه سینه/تنگی نفس/ضعف → اورژانس فوری"},
    {"id": "hyperglycemia_likely", "fa": "قند خون بالا (احتمالی)", "en": "Possible hyperglycemia", "prior": 0.03, "urgency": "routine",
     "symptoms": {"thirst": 0.8, "urinary_frequency": 0.7, "fatigue": 0.6, "blurred_vision": 0.4, "weight_loss": 0.4},
     "advice": ["انجام قند خون ناشتا (FBS) و در صورت امکان HbA1c", "پرهیز از نوشیدنی‌های شیرین تا مشخص‌شدن قند"],
     "doctor_when": "تهوع و استفراغ با تنفس تند و بوی استون دهان (احتمال کتواسیدوز) → اورژانس فوری"},
    {"id": "asthma", "fa": "آسم (احتمالی)", "en": "Asthma (possible)", "prior": 0.03, "urgency": "urgent",
     "symptoms": {"wheezing": 0.9, "shortness_of_breath": 0.8, "cough": 0.6, "chest_pain": 0.2},
     "advice": ["در حمله: نشستن راحت و استفاده از اسپری اضطراری در صورت دارا بودن", "پرهیز از محرک‌ها (دود، حساسیت‌زا)"],
     "doctor_when": "حمله‌ی شدید، لب‌های کبود، یا بی‌اثری اسپری → اورژانس فوری"},
    {"id": "bronchitis", "fa": "برونشیت حاد (احتمالی)", "en": "Acute bronchitis (possible)", "prior": 0.03, "urgency": "routine",
     "symptoms": {"cough": 0.95, "sputum": 0.7, "fever": 0.3, "fatigue": 0.5, "wheezing": 0.3, "chest_pain": 0.2},
     "advice": ["مایعات گرم و استراحت", "پرهیز از دود سیگار"],
     "doctor_when": "تب بالا، تنگی نفس، یا سرفه بیش از ۳ هفته"},
    {"id": "pneumonia", "fa": "پنومونی (احتمالی — نیاز به بررسی پزشک)", "en": "Pneumonia (possible)", "prior": 0.02, "urgency": "urgent",
     "symptoms": {"fever": 0.8, "cough": 0.8, "sputum": 0.6, "shortness_of_breath": 0.6, "chest_pain": 0.4, "fatigue": 0.6, "rapid_breathing": 0.4},
     "advice": ["این حالت نیاز به معاینه و احتمالاً عکس قفسه سینه دارد؛ مراجعه در اولین فرصت"],
     "doctor_when": "تنگی نفس شدید، تب بالا با گیجی، لب کبود → اورژانس"},
    {"id": "anxiety_stress", "fa": "اضطراب/استرس", "en": "Anxiety/stress", "prior": 0.09, "urgency": "routine",
     "symptoms": {"anxiety": 0.9, "palpitation": 0.5, "insomnia": 0.6, "fatigue": 0.5, "panic": 0.4, "headache": 0.3, "dizziness": 0.3},
     "advice": ["تمرین تنفس عمیق (۴ ثانیه دم، ۴ نگه‌داشتن، ۶ بازدم)", "کاهش کافئین، خواب منظم", "در صورت تداوم، مشاوره‌ی روان‌شناس"],
     "doctor_when": "افکار آسیب به خود → فوری با خط بحران یا اورژانس تماس بگیرید (ایران: ۱۴۸۰/۱۲۳)"},
    {"id": "depression_likely", "fa": "افسردگی (احتمالی)", "en": "Depression (possible)", "prior": 0.04, "urgency": "routine",
     "symptoms": {"mood_low": 0.9, "loss_of_interest": 0.8, "insomnia": 0.6, "fatigue": 0.7, "appetite_loss": 0.5},
     "advice": ["صحبت با فرد مورد اعتماد", "فعالیت بدنی سبک روزانه", "پرکردن پرسش‌نامه‌ی PHQ-9 در بخش سلامت روان این برنامه"],
     "doctor_when": "هرگونه فکر به آسیب رساندن به خود → فوری با خط بحران تماس بگیرید (ایران: ۱۴۸۰ — اروپا: 112)"},
    {"id": "iron_def_anemia", "fa": "کم‌خونی کم‌آهن (احتمالی)", "en": "Iron-deficiency anemia (possible)", "prior": 0.04, "urgency": "routine",
     "symptoms": {"fatigue": 0.9, "dizziness": 0.5, "palpitation": 0.3, "pallor": 0.5, "shortness_of_breath": 0.3, "headache": 0.3},
     "advice": ["انجام CBC و آهن/فریتین", "غذاهای غنی از آهن (گوشت قرمز، حبوبات، سبزیجات تیره) با منبع ویتامین C"],
     "doctor_when": "تنگی نفس یا درد قفسه سینه، خونریزی پیشین، بارداری"},
    {"id": "hypothyroid_likely", "fa": "کم‌کاری تیروئید (احتمالی)", "en": "Hypothyroidism (possible)", "prior": 0.03, "urgency": "routine",
     "symptoms": {"fatigue": 0.8, "weight_gain": 0.6, "constipation": 0.5, "cold_intolerance": 0.6, "mood_low": 0.4, "dry_skin": 0.4},
     "advice": ["آزمایش TSH و T4 آزاد", "مراجعه به پزشک در صورت غیرطبیعی بودن"],
     "doctor_when": "کاهش هوشیاری یا ضربان قلب خیلی کند → اورژانس"},
    {"id": "urticaria", "fa": "کهیر/آلرژی پوستی (احتمالی)", "en": "Urticaria (possible)", "prior": 0.03, "urgency": "routine",
     "symptoms": {"skin_itch": 0.9, "rash": 0.8, "swelling": 0.3},
     "advice": ["آنتی‌هیستامین در صورت صلاحدید داروخانه", "اجتناب از محرک (غذا/داروی جدید)", "سرد کردن موضعی"],
     "doctor_when": "تورم لب/زبان/گلو یا تنگی نفس → آنافیلاکسی است، فوری اورژانس"},
    {"id": "eczcema_likely", "fa": "اگزما/درماتیت (احتمالی)", "en": "Eczema (possible)", "prior": 0.03, "urgency": "routine",
     "symptoms": {"skin_itch": 0.9, "rash": 0.7, "dry_skin": 0.7},
     "advice": ["مرطوب‌کننده‌ی بدون عطر", "حمام کوتاه ولرم", "پرهیز از خاراندن"],
     "doctor_when": "علامت عفونت (ترشح، درد، تب) یا بی‌پاسخی به مراقبت عمومی"},
    {"id": "sleep_apnea_likely", "fa": "آپنه‌ی خواب (احتمالی)", "en": "Sleep apnea (possible)", "prior": 0.03, "urgency": "routine",
     "symptoms": {"snoring": 0.9, "apnea_observed": 0.8, "daytime_sleepiness": 0.8, "headache": 0.4, "fatigue": 0.6},
     "advice": ["پرکردن STOP-BANG در بخش تحلیل خواب برنامه", "کاهش وزن در صورت اضافه‌وزن، خوابیدن به پهلو"],
     "doctor_when": "خواب‌آلودگی شدید پشت فرمان یا حین کار → ارزیابی پزشک خواب"},
    {"id": "insomnia_stress", "fa": "بی‌خوابی مرتبط با استرس", "en": "Stress-related insomnia", "prior": 0.05, "urgency": "routine",
     "symptoms": {"insomnia": 1.0, "anxiety": 0.6, "fatigue": 0.6, "mood_low": 0.3},
     "advice": ["به‌خوابیدن و بیدارشدن در ساعت ثابت", "پرهیز از صفحه‌نمایش ۱ ساعت قبل خواب و کافئین بعدازظهر", "تکنیک آرام‌سازی عضلات"],
     "doctor_when": "بی‌خوابی بیش از ۱ ماه یا همراه با افکار نگران‌کننده‌ی شدید"},
    {"id": "dyspepsia", "fa": "سوءهاضمه/نفخ", "en": "Functional dyspepsia", "prior": 0.04, "urgency": "routine",
     "symptoms": {"bloating": 0.8, "abdominal_pain": 0.6, "nausea": 0.4, "heartburn": 0.4, "appetite_loss": 0.3},
     "advice": ["وعده‌های کوچک و دفعات بیشتر", "کاهش چربی، کافئین و نوشابه", "پیاده‌روی بعد از غذا"],
     "doctor_when": "کاهش وزن بی‌دلیل، استفراغ خونی، اختلال بلع، سن بالای ۵۰ با علامت جدید"},
]

# ============================================================================
# ۴) تشخیص علائم از متن فارسی
# ============================================================================

def detect_symptoms(text: str) -> dict[str, Any]:
    """خروجی: {present: {sid: {count, severity, denied}}, duration_days, temp_c}
    نفی/تأیید داخل «بند» (clause) یک جمله بررسی می‌شود تا «تب ندارم» به علائم قبلی سرایت نکند."""
    t = normalize(text)
    clauses = re.split(r"[،؛,.!؟?!\n]", t)
    present: dict[str, dict] = {}
    for sid, kws in SYMPTOM_KEYWORDS.items():
        for kw in kws:
            nk = normalize(kw)
            if not nk:
                continue
            hit = None
            for cl in clauses:
                idx = cl.find(nk)
                if idx < 0:
                    continue
                window = cl[max(0, idx - 14): idx + len(nk) + 14]
                hit = {
                    "denied": any(neg in window for neg in NEGATION_WORDS) and ("نمی" not in nk),
                    "severe": any(sw in window for sw in SEVERE_WORDS),
                    "mild": any(mw in window for mw in MILD_WORDS),
                }
                break
            if hit is None:
                continue
            entry = present.setdefault(sid, {"count": 0, "severity": "moderate", "denied": False})
            entry["count"] += 1
            if hit["denied"]:
                entry["denied"] = True
            if hit["severe"]:
                entry["severity"] = "severe"
            elif hit["mild"] and entry["severity"] != "severe":
                entry["severity"] = "mild"
            break
    duration_days = None
    for m in DURATION_RE.finditer(t):
        num = float(m.group(1).replace(",", "."))
        unit = m.group(2)
        mult = {"روز": 1, "شب": 1, "هفته": 7, "ماه": 30, "سال": 365, "ساعت": 0.5, "ساعت": 1 / 24}.get(unit, 1)
        duration_days = round(num * mult, 1)
        break
    temp_c = None
    for m in FEVER_RE.finditer(t):
        v = float(m.group(1).replace(",", "."))
        if 34 <= v <= 45:
            temp_c = v
        elif 95 <= v <= 113:
            temp_c = round((v - 32) / 1.8, 1)
    return {"present": present, "duration_days": duration_days, "temp_c": temp_c}


def check_red_flags(text: str, detected: dict | None = None) -> dict[str, Any]:
    """بررسی ۱۳ علامت خطر — قبل از هر تشخیص."""
    t = normalize(text)
    reasons: list[str] = []
    hits: list[str] = []
    for rf in RED_FLAGS:
        if any(normalize(k) in t for k in rf["any"]):
            reasons.append(rf["label"])
            hits.append(rf["id"])
    # الگوی ترکیبی: «درد/فشار/سوزش ... قفسه سینه» حتی با فاصله (مثل: درد شدید قفسه سینه)
    if "chest_pain" not in hits and "قفسه سینه" in t and any(w in t for w in ("درد", "فشار", "سوزش", "گیر ")):
        if "درد قفسه سینه" not in reasons:
            reasons.append("درد قفسه سینه")
        hits.append("chest_pain")
    # تب عددی ≥ 40
    if detected and detected.get("temp_c") and detected["temp_c"] >= 40:
        reasons.append("تب بسیار شدید (۴۰ درجه یا بالاتر)")
        hits.append("high_fever")
    # خوشه‌ی سکته (FAST): دست‌کم ۲ علامت از ضعف/تکلم/صورت
    s = set(hits)
    fast = {"sudden_weakness", "speech", "face_droop"} & s
    if len(fast) >= 2:
        if "علائم مطرح برای سکته‌ی مغزی" not in reasons:
            reasons.append("علائم مطرح برای سکته‌ی مغزی")
        hits.append("stroke_cluster")
    # درد قفسه سینه + عرقدگی/دست چپ
    if "chest_pain" in s and any(k in t for k in ["عرق", "بازوی چپ", "دست چپ", "فک", "تهوع"]):
        if "علائم مطرح برای حمله‌ی قلبی" not in reasons:
            reasons.append("علائم مطرح برای حمله‌ی قلبی")
        hits.append("heart_attack")
    # شدت علائم موجود
    if detected:
        for sid, info in detected["present"].items():
            if sid in ("chest_pain", "shortness_of_breath", "abdominal_pain") and info["severity"] == "severe" and not info.get("denied"):
                label = SYMPTOM_NAMES_FA.get(sid, sid)
                if f"{label} شدید" not in reasons:
                    reasons.append(f"{label} شدید")
    return {"flag": bool(reasons), "reasons": reasons, "hits": sorted(set(hits))}


EMERGENCY_RESPONSE_TEMPLATE = """**هشدار اورژانی — تشخیص معمول متوقف شد**

در متن شما این نشانگان خطر شناسایی شد: {reasons}

**همین حالا:**
1. با اورژانس تماس بگیرید — ایران: ۱۱۵ | اروپا/فنلاند: ۱۱۲
2. فرد را در موقعیت امن نگه دارید (نشسته یا خوابیده به پهلو در صورت کاهش هوشیاری)
3. در مشکوک به سکته: زمان شروع علائم را یادداشت کنید؛ به فرد غذای آب یا دارو ندهید
4. در درد قفسه سینه: فعالیت متوقف، نشستن و آرامش؛ دارو فقط با راهنمایی اورژانس
5. در بیهوشی بدون تنفس: CPR را شروع کنید (دکمه‌ی CPR برنامه: ضرباهنگ ۱۱۰ در دقیقه)
 این برنامه در این مرحله تشخیص معمول انجام نمی‌دهد؛ اولویت با رسیدگی اورژانسی است.
{disclaimer}"""


def emergency_response(reasons: list[str], disclaimer: str = "") -> str:
    from common_2077 import MEDICAL_DISCLAIMER
    return EMERGENCY_RESPONSE_TEMPLATE.format(
        reasons="، ".join(reasons) if reasons else "علائم خطر",
        disclaimer="\n\n"+ (disclaimer or MEDICAL_DISCLAIMER),
    )


def analyze(text: str, profile: dict | None = None) -> dict[str, Any]:
    """تحلیل کلی: red flag → علائم → رتبه‌بندی بیزین."""
    detected = detect_symptoms(text)
    red = check_red_flags(text, detected)
    result = {
        "red_flag": red["flag"],
        "red_flag_reasons": red["reasons"],
        "detected": detected,
        "symptoms_fa": [SYMPTOM_NAMES_FA.get(s, s) for s, i in detected["present"].items() if not i.get("denied")],
        "denied_fa": [SYMPTOM_NAMES_FA.get(s, s) for s, i in detected["present"].items() if i.get("denied")],
        "candidates": [],
        "profile": profile or {},
    }
    if not red["flag"]:
        try:
            from bayesian_engine import rank_diseases
            result["candidates"] = rank_diseases(detected, profile or {})
        except Exception:
            result["candidates"] = []
    return result
