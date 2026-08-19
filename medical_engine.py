# -*- coding: utf-8 -*-
"""
medical_engine.py — offline medical engine: bilingual (en/fa) symptom lexicon,
red flag screening (checked before anything else) and the internal knowledge
base. It never fabricates medical information.
"""
from __future__ import annotations

import re
from typing import Any

from common_2077 import normalize

# ============================================================================
# 1) Symptom lexicon — id -> Persian + English keywords
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
    "sputum": "خلط", "thirst": "تشنگی زیاد", "weight_loss": "کاهش وزن", "weight_gain": "افزایش وزن", "tremor": "لرز",
    "blurred_vision": "تار شدن دید", "unilateral_weakness": "ضعف یک طرفه‌ی بدن",
    "speech_difficulty": "اختلال تکلم", "face_droop": "کج شدن صورت",
    "seizure": "تشنج", "loss_of_consciousness": "بیهوشی", "severe_bleeding": "خونریزی شدید",
    "confusion": "کاهش سطح هوشیاری/گیجی", "night_sweats": "عرق شبانه",
    "constipation": "یبوست", "joint_pain": "درد مفاصل", "back_pain": "کمردرد",
    "eye_redness": "قرمزی چشم", "tear_eyes": "اشک‌ریزش", "sweating": "عرق‌کردن",
    "left_arm_pain": "درد بازوی چپ", "sore_throat_dry": "خشکی گلو", "bloating": "نفخ",
    "rapid_breathing": "تنفس تند", "stiff_neck": "سفتی گردن", "photophobia": "حساسیت به نور",
    "apnea_observed": "قطع تنفس در خواب", "snoring": "خروپف", "daytime_sleepiness": "خواب‌آلودگی روزانه",
    "panic": "وحشت‌زدگی", "loss_of_interest": "بی‌علاقگی", "appetite_loss": "بی‌اشتهایی",
    "ear_pain": "درد گوش", "menstrual_cramps": "درد قاعدگی", "mouth_ulcer": "زخم/آفت دهان", "leg_swelling": "تورم پا", "calf_pain": "درد ساق پا"
}

SYMPTOM_NAMES_EN: dict[str, str] = {
    "fever": "fever", "cough": "cough", "sore_throat": "sore throat", "runny_nose": "runny nose",
    "sneezing": "sneezing", "body_ache": "body aches", "headache": "headache", "nausea": "nausea",
    "vomiting": "vomiting", "diarrhea": "diarrhea", "abdominal_pain": "abdominal pain",
    "dysuria": "painful urination", "urinary_frequency": "frequent urination", "skin_itch": "itchy skin",
    "rash": "rash/hives", "anxiety": "anxiety", "chest_pain": "chest pain",
    "shortness_of_breath": "shortness of breath", "dizziness": "dizziness", "fatigue": "fatigue",
    "palpitation": "palpitations", "heartburn": "heartburn", "flank_pain": "flank pain",
    "insomnia": "insomnia", "mood_low": "low mood", "wheezing": "wheezing",
    "sputum": "phlegm", "thirst": "excessive thirst", "weight_loss": "weight loss", "weight_gain": "weight gain", "tremor": "tremor/shaking",
    "blurred_vision": "blurred vision", "unilateral_weakness": "one-sided weakness",
    "speech_difficulty": "slurred speech", "face_droop": "facial droop",
    "seizure": "seizure", "loss_of_consciousness": "unconsciousness", "severe_bleeding": "severe bleeding",
    "confusion": "confusion", "night_sweats": "night sweats",
    "constipation": "constipation", "joint_pain": "joint pain", "back_pain": "back pain",
    "eye_redness": "red eyes", "tear_eyes": "watery eyes", "sweating": "sweating",
    "left_arm_pain": "left arm pain", "sore_throat_dry": "dry throat", "bloating": "bloating",
    "rapid_breathing": "rapid breathing", "stiff_neck": "stiff neck", "photophobia": "light sensitivity",
    "apnea_observed": "breathing pauses in sleep", "snoring": "snoring", "daytime_sleepiness": "daytime sleepiness",
    "panic": "panic", "loss_of_interest": "loss of interest", "appetite_loss": "loss of appetite",
    "ear_pain": "ear pain", "menstrual_cramps": "menstrual cramps", "mouth_ulcer": "mouth ulcer", "leg_swelling": "leg swelling", "calf_pain": "calf pain"
}


def sym_name(sid: str) -> str:
    from i18n import is_fa
    m = SYMPTOM_NAMES_FA if is_fa() else SYMPTOM_NAMES_EN
    return m.get(sid, sid)


SYMPTOM_KEYWORDS: dict[str, list[str]] = {
    "fever": ["تب", "تب دارم", "بدنم گرم", "حرارت دارم", "fever", "temperature", "high temp"],
    "cough": ["سرفه", "سرفه خشک", "سرفه خلط دار", "cough", "coughing", "dry cough"],
    "sore_throat": ["گلودرد", "درد گلو", "گلویم درد", "گلود", "لوزه", "لوزه‌ها", "sore throat", "throat hurts", "throat pain", "swollen tonsils", "tonsils"],
    "sore_throat_dry": ["خشکی گلو", "گلویم خشک", "dry throat", "throat is dry"],
    "runny_nose": ["آبریزش بینی", "دردام", "بینیم آب می اید", "runny nose", "nose running", "nasal discharge"],
    "sneezing": ["عطسه", "sneezing", "sneeze", "sneezing a lot"],
    "body_ache": ["بدن درد", "بدندرد", "درد عضله", "body ache", "body aches", "muscle aches", "aches all over"],
    "headache": ["سردرد", "سر درد", "سرم درد می کند", "headache", "head hurts", "head pain", "migraine"],
    "nausea": ["حالت تهوع", "تهوع", "دلم به هم می خورد", "nausea", "nauseous", "feel sick", "queasy"],
    "vomiting": ["استفراغ", "قی کردم", "vomiting", "vomited", "throwing up", "threw up"],
    "diarrhea": ["اسهال", "رو گشاده", "مدفوع آبکی", "diarrhea", "loose stools", "watery stool"],
    "abdominal_pain": ["درد شکم", "دل درد", "شکم درد", "معده ام درد", "درد معده", "abdominal pain", "stomach ache", "stomach pain", "belly pain", "stomach hurts"],
    "dysuria": ["سوزش ادرار", "ادرار سوزش", "سوزش موقع ادرار", "burning urination", "painful urination", "burns when i pee", "dysuria",
                "burning when i urinate", "burns urinating", "burning pee", "stings when i pee", "pain urinating", "stings urinating"],
    "urinary_frequency": ["تکرر ادرار", "ادرار زیاد", "مدام دستشویی می روم", "frequent urination", "peeing a lot", "urinating often"],
    "skin_itch": ["خارش", "خارش دارم", "خارش شدید", "itching", "itchy", "itches a lot", "itch"],
    "rash": ["لک", "لک قرمز", "کهیر", "جوش", "بثورات", "قرمزی پوست", "تاول", "بثورات تاولی", "قرمزی", "قرمزی پخش شونده", "rash", "hives", "spots on skin", "red patch", "redness", "spreading redness", "skin redness", "blisters", "vesicles", "blister"],
    "anxiety": ["اضطراب", "مضطرب", "نگران هستم", "استرس دارم", "بی قرارم", "anxiety", "anxious", "stressed", "worried", "nervous"],
    "chest_pain": ["درد قفسه سینه", "درد سینه", "قفسه سینه ام درد", "درد قفسه صدری", "فشار روی سینه", "chest pain", "chest pressure", "chest tightness", "chest hurts"],
    "shortness_of_breath": ["تنگی نفس", "نفس کم می اورد", "نفس نفس", "سخت نفس می کشم", "shortness of breath", "hard to breathe", "cant breathe", "can not breathe", "difficulty breathing", "breathless", "out of breath"],
    "dizziness": ["سرگیجه", "سرم گیج می رود", "گیجی", "سرم می چرخد", "چرخش سر", "dizziness", "dizzy", "lightheaded", "vertigo", "room spins", "spinning"],
    "fatigue": ["خستگی", "خسته ام", "ضعف و بی حالی", "بی حال", "fatigue", "tired", "exhausted", "no energy"],
    "palpitation": ["تپش قلب", "قلبم تند می زند", "تپش", "palpitations", "racing heart", "heart pounding", "fast heartbeat"],
    "heartburn": ["سوزش سر دل", "سوزش معده", "ترش کردم", "رفلاکس", "heartburn", "acid reflux", "sour taste", "burning in chest"],
    "flank_pain": ["درد پهلو", "درد کلیه", "پهلویم درد", "flank pain", "kidney pain", "side pain", "pain in my side"],
    "insomnia": ["بی خوابی", "خوابم نمی برد", "نمی توانم بخوابم", "insomnia", "cant sleep", "can not sleep", "trouble sleeping", "not sleeping"],
    "mood_low": ["افسرده", "ناراحت هستم", "حال بد", "افت روحیه", "غمگین", "حوصله ندارم", "depressed", "low mood", "feeling down", "sad", "hopeless"],
    "wheezing": ["خس خس", "صدای سینه", "wheezing", "wheezing sound", "whistling chest"],
    "sputum": ["خلط", "خلط دارم", "phlegm", "sputum", "mucus cough"],
    "thirst": ["تشنگی", "تشنه ام", "مدام آب می خورم", "excessive thirst", "very thirsty", "always thirsty", "dry mouth"],
    "weight_loss": ["کاهش وزن", "لاغر شده ام", "وزنم کم شده", "weight loss", "losing weight", "lost weight"],
    "weight_gain": ["افزایش وزن", "چاق شده ام", "وزنم زیاد شده", "وزن اضافه کرده ام", "weight gain", "gaining weight", "gained weight"],
    "tremor": ["لرز دست", "دستم می لرزد", "بدنم می لرزد", "لرز دارند", "دستهایم می لرزد", "trembling", "shaking", "shaky", "tremor", "my hands are shaking"],
    "ear_pain": ["درد گوش", "گوشم درد", "درد داخل گوش", "ear pain", "earache", "ear hurts", "ear is painful"],
    "menstrual_cramps": ["درد قاعدگی", "درد پریود", "دلرد پریود", "کمردرد قاعدگی", "menstrual cramps", "period pain", "period cramps", "menstrual pain"],
    "mouth_ulcer": ["زخم دهان", "آفت دهان", "زخم داخل دهان", "mouth ulcer", "canker sore", "ulcer in mouth", "mouth sores", "cold sore"],
    "leg_swelling": ["تورم پا", "پایم ورم کرده", "تورم ساق پا", "تورم مچ پا", "پام ورم کرده", "leg swelling", "swollen leg", "swollen ankle", "swollen calf", "one leg is swollen", "calf is swollen", "leg is swollen", "پای چپم ورم", "پای راستم ورم"],
    "calf_pain": ["درد ساق پا", "ساق پام درد", "پام درد می کند", "calf pain", "pain in calf", "pain in one leg", "leg pain one side", "painful calf", "calf hurts", "leg is painful", "my leg hurts", "leg hurts"],
    "blurred_vision": ["تار شدن دید", "چشمانم تار", "تار می بینم", "blurred vision", "blurry vision", "vision is blurry"],
    "unilateral_weakness": ["ضعف یک طرف", "دست و پسم بی lực", "فلج", "یک طرف بدنم بی حس", "دستم بی حس شده", "پایم بی حس", "one sided weakness", "weakness on one side", "paralysis", "arm went numb", "leg went numb", "numb arm", "numb leg", "face is drooping"],
    "speech_difficulty": ["حرف زدن مشکل", "زبان بند می اید", "اختلال تکلم", "slurred speech", "cant speak", "can not speak", "trouble speaking", "speech problem", "words not coming out"],
    "face_droop": ["کج شدن صورت", "صورت کج", "صورتش کج", "دهان کج", "facial droop", "face drooping", "face is drooping", "mouth is drooping", "smile is uneven"],
    "seizure": ["تشنج", "صرع", "حرکات غیر ارادی", "seizure", "convulsion", "fitting", "convulsions"],
    "loss_of_consciousness": ["بیهوش", "کاما", "هوشیار نیست", "unconscious", "passed out", "fainted", "not responsive", "collapsed"],
    "severe_bleeding": ["خونریزی شدید", "خونریزی زیاد", "خون نمی ایستد", "severe bleeding", "bleeding heavily", "bleeding wont stop", "will not stop bleeding", "lots of blood"],
    "confusion": ["گیج و منگ", "کاهش هوشیاری", "منگ", "confused", "confusion", "not making sense", "very drowsy", "hard to wake"],
    "night_sweats": ["عرق شبانه", "شب ها عرق می کنم", "night sweats", "sweating at night"],
    "constipation": ["یبوست", "مدفوع سفت", "constipation", "constipated", "cant pass stool"],
    "joint_pain": ["درد مفاصل", "مفاصلم درد", "درد زانو", "joint pain", "joints hurt", "knee pain", "arthritis pain"],
    "back_pain": ["کمردرد", "کمر درد", "کمرم درد", "back pain", "back hurts", "lower back pain"],
    "eye_redness": ["قرمزی چشم", "چشم قرمز", "چشمم قرمز", "red eyes", "red eye", "eye redness", "bloodshot eyes", "my eye is red"],
    "tear_eyes": ["اشک ریزش", "چشمم اشک می ریزد", "watery eyes", "tearing eyes", "eyes watering"],
    "sweating": ["عرق سرد", "عرق کردم", "sweating", "cold sweat", "clammy", "sweating a lot"],
    "left_arm_pain": ["درد بازوی چپ", "دست چپم درد", "درد شانه چپ", "left arm pain", "pain in left arm", "left shoulder pain", "arm pain radiating"],
    "bloating": ["نفخ", "پف کردم", "شکمم باد", "bloating", "bloated", "gassy"],
    "rapid_breathing": ["تنفس تند", "نفس تند", "rapid breathing", "breathing fast", "fast breathing"],
    "stiff_neck": ["سفتی گردن", "گردن نمی چرخد", "stiff neck", "neck stiffness"],
    "photophobia": ["نور چشم می اذارد", "حساسیت به نور", "light hurts my eyes", "light sensitivity", "sensitive to light"],
    "apnea_observed": ["قطع تنفس در خواب", "اپنه", "breathing stops in sleep", "stops breathing at night", "sleep apnea"],
    "snoring": ["خروپف", "خر و پف", "خروپف شدید", "snoring", "snores loudly", "loud snoring"],
    "daytime_sleepiness": ["خواب آلودگی روزانه", "مدام خوابم می برد", "daytime sleepiness", "sleepy during the day", "falling asleep during the day"],
    "panic": ["وحشت", "پنیک", "حمله اضطراب", "panic", "panic attack"],
    "loss_of_interest": ["بی علاقگی", "هیچ چیز برایم جذاب نیست", "لذت نمی برم", "loss of interest", "no interest", "nothing is fun anymore", "anhedonia"],
    "appetite_loss": ["بی اشتهایی", "اشتها ندارم", "غذا نمی خورم", "loss of appetite", "no appetite", "not eating"],
}

NEGATION_FA = ["ندارم", "نداشتم", "نمی", "نبود", "خیر", "ندارد", "نکردم", "نکنم", "نیست", "خلاف"]
NEGATION_EN = ["no", "not", "dont", "don't", "never", "without", "denies", "deny", "negative", "havent", "hasn't", "haven't", "doesn't", "doesnt", "didnt", "didn't"]
SEVERE_WORDS = ["شدید", "خیلی زیاد", "غیرقابل تحمل", "وحشتناک", "کمرشکن", "severe", "excruciating", "unbearable", "worst", "intense", "terrible"]
MILD_WORDS = ["خفیف", "کم", "جزئی", "ناچیز", "کمی", "mild", "slight", "a little", "little bit"]

_LATIN_RE = re.compile(r"^[a-z'\s]+$")


def _is_denied(window: str) -> bool:
    for neg in NEGATION_FA:
        if neg in window:
            return True
    w = " " + window + " "
    for neg in NEGATION_EN:
        if re.search(rf"\s{re.escape(neg)}\s|{re.escape(neg)}\s", w):
            return True
    return False


# ============================================================================
# 2) Red flags — checked before any assessment
# ============================================================================

RED_FLAGS: list[dict[str, Any]] = [
    {"id": "chest_pain", "any": ["درد قفسه سینه", "درد قفسه صدری", "درد سینه", "قفسه سینه ام درد", "فشار روی سینه", "سینه ام فشار",
                                 "chest pain", "chest pressure", "chest tightness", "pain in my chest", "tightness in chest"],
     "en": "chest pain", "fa": "درد قفسه سینه"},
    {"id": "severe_sob", "any": ["تنگی نفس شدید", "نفس نمی توانم", "نفس نفس", "سخت نفس",
                                 "cant breathe", "can not breathe", "cannot breathe", "struggling to breathe", "hard to breathe", "severe shortness of breath"],
     "en": "severe shortness of breath", "fa": "تنگی نفس"},
    {"id": "severe_bleeding", "any": ["خونریزی شدید", "خونریزی زیاد", "خون نمی ایستد",
                                      "severe bleeding", "bleeding heavily", "bleeding wont stop", "will not stop bleeding"],
     "en": "severe bleeding", "fa": "خونریزی شدید"},
    {"id": "unconscious", "any": ["بیهوش", "هوشیار نیست", "هوشیاری ندارد", "کما",
                                  "unconscious", "passed out", "not responsive", "collapsed", "unresponsive"],
     "en": "unconsciousness", "fa": "بیهوشی"},
    {"id": "seizure", "any": ["تشنج", "seizure", "convulsion", "convulsions", "fitting"], "en": "seizure", "fa": "تشنج"},
    {"id": "sudden_weakness", "any": ["ضعف ناگهانی", "فلج", "بی حس شد", "بی حس شده", "ضعف یک طرف", "یک طرف بدنم ضعف", "دستم بی حس", "پایم بی حس",
                                      "sudden weakness", "weakness on one side", "paralysis", "one side is weak", "arm went numb", "leg went numb", "numbness one side", "face is drooping"],
     "en": "sudden weakness or paralysis", "fa": "ضعف یا فلج ناگهانی"},
    {"id": "speech", "any": ["حرف زدن مشکل", "اختلال تکلم", "زبان بند", "حرف نمی تواند", "نمی تواند حرف", "نمی توانم حرف",
                             "slurred speech", "cant speak", "can not speak", "trouble speaking", "speech is slurred", "words not coming out"],
     "en": "speech difficulty", "fa": "اختلال تکلم"},
    {"id": "face_droop", "any": ["کج شدن صورت", "صورت کج", "صورتش کج", "دهان کج",
                                 "facial droop", "face drooping", "face is drooping", "mouth is drooping", "smile is uneven", "one side of face"],
     "en": "facial droop", "fa": "کج شدن صورت"},
    {"id": "consciousness", "any": ["گیج و منگ", "کاهش هوشیاری", "خواب آلود و بی قرار", "منگ شده",
                                    "confused", "confusion", "not making sense", "very drowsy", "hard to wake", "altered consciousness"],
     "en": "decreased consciousness", "fa": "کاهش سطح هوشیاری"},
    {"id": "high_fever", "any": ["تب 40", "تب 41", "تب بالای 40", "تب خیلی بالا", "تب شدید",
                                 "fever 40", "fever 41", "fever of 104", "fever of 105", "very high fever"],
     "en": "very high fever", "fa": "تب بسیار شدید"},
    {"id": "sudden_severe_pain", "any": ["درد شدید ناگهانی", "ناگهانی درد شدید", "درد غیرقابل تحمل", "درد وحشتناک",
                                         "sudden severe pain", "worst headache of my life", "worst headache ever", "unbearable pain", "sudden excruciating"],
     "en": "sudden severe pain", "fa": "درد شدید ناگهانی"},
]

_NUM = r"(\d{1,3}(?:[.,]\d)?)"
DURATION_RE = re.compile(_NUM + r"\s*(روز|هفته|شب|ماه|سال|ساعت|days?|weeks?|months?|years?|hours?)", re.IGNORECASE)
TEMP_RE = re.compile(r"(?:تب|حرارت|fever|temperature|temp)\s*" + _NUM)
FEVER_RE = re.compile(r"(?:تب|fever|temp)\s*(\d{2}(?:[.,]\d)?)")

# ============================================================================
# 3) Internal knowledge base — p = rough P(symptom | condition) for Bayes.
#    Output is always presented as "possible", never as a diagnosis.
# ============================================================================

DISEASES: list[dict[str, Any]] = [
    {"id": "common_cold", "fa": "سرماخوردگی", "en": "Common cold", "prior": 0.16, "urgency": "routine",
     "symptoms": {"cough": 0.8, "sore_throat": 0.6, "runny_nose": 0.9, "sneezing": 0.75, "fever": 0.3, "headache": 0.35, "body_ache": 0.35, "sputum": 0.3},
     "advice": ["استراحت و خواب کافی", "مایعات گرم فراوان", "غرغره‌ی آب نمک ولرم برای گلودرد"],
     "advice_en": ["Rest and get enough sleep", "Plenty of warm fluids", "Saltwater gargle for the sore throat"],
     "doctor_when": "اگر تب بیش از ۳ روز ادامه یافت یا گلودرد شدید با تب بالا بدون سرفه",
     "doctor_when_en": "If fever lasts more than 3 days, or severe sore throat with high fever and no cough"},
    {"id": "influenza", "fa": "آنفلوآنزا", "en": "Influenza", "prior": 0.09, "urgency": "routine",
     "symptoms": {"fever": 0.9, "body_ache": 0.85, "headache": 0.7, "cough": 0.7, "fatigue": 0.9, "sore_throat": 0.4},
     "advice": ["استراحت کامل در خانه", "مایعات فراوان", "استامینوفن برای تب و بدن‌درد در صورت نیاز"],
     "advice_en": ["Full rest at home", "Drink plenty of fluids", "Paracetamol as needed for fever and aches"],
     "doctor_when": "تنگی نفس، درد قفسه سینه یا تب بالای ۳ روز؛ یا گروه پرخطر (بارداری، سالمند، بیماری زمینه‌ای)",
     "doctor_when_en": "Shortness of breath, chest pain, or fever beyond 3 days; or high-risk group (pregnant, elderly, chronic illness)"},
    {"id": "allergic_rhinitis", "fa": "آلرژی فصلی", "en": "Allergic rhinitis", "prior": 0.08, "urgency": "routine",
     "symptoms": {"sneezing": 0.85, "runny_nose": 0.8, "tear_eyes": 0.5, "eye_redness": 0.4, "skin_itch": 0.3, "cough": 0.25},
     "advice": ["اجتناب از مواجهه با محرک (گرد و غبار، گرده)", "شست‌وشوی بینی با سالین", "آنتی‌هیستامین بدون نسخه در صورت صلاحدید داروخانه"],
     "advice_en": ["Avoid triggers (dust, pollen)", "Saline nasal rinse", "Over-the-counter antihistamine if the pharmacist agrees"],
     "doctor_when": "علائم بیشتر از ۲ هفته ادامه یافت یا تنگی نفس اضافه شد",
     "doctor_when_en": "Symptoms beyond 2 weeks, or new shortness of breath"},
    {"id": "covid_like", "fa": "عفونت تنفسی ویروسی (شبیه کووید)", "en": "COVID-like viral illness", "prior": 0.05, "urgency": "routine",
     "symptoms": {"fever": 0.7, "cough": 0.8, "fatigue": 0.8, "sore_throat": 0.5, "shortness_of_breath": 0.25, "body_ache": 0.6},
     "advice": ["استراحت و ایزوله‌شدن در خانه", "تست تشخیصی در صورت دسترسی", "پایش تنفس؛ در صورت بدترشدن تنگی نفس اورژانس"],
     "advice_en": ["Rest and stay home", "Test if available", "Watch your breathing; worsening breathlessness means emergency"],
     "doctor_when": "تنگی نفس، اشباع اکسیژن پایین، درد قفسه سینه",
     "doctor_when_en": "Shortness of breath, low oxygen saturation, or chest pain"},
    {"id": "migraine", "fa": "میگرن احتمالی", "en": "Migraine (possible)", "prior": 0.06, "urgency": "routine",
     "symptoms": {"headache": 1.0, "nausea": 0.6, "photophobia": 0.6, "vomiting": 0.3, "dizziness": 0.3, "blurred_vision": 0.25},
     "advice": ["استراحت در اتاق تاریک و ساکت", "خواب کافی و پرهیز از محرک‌ها", "ثبت دفترچه‌ی سردرد برای یافتن محرک‌ها"],
     "advice_en": ["Rest in a dark, quiet room", "Regular sleep; avoid known triggers", "Keep a headache diary"],
     "doctor_when": "سردرد ناگهانی و شدیدترین عمر، تب با سفتی گردن، یا ضعف بدن → فوری",
     "doctor_when_en": "Sudden worst-ever headache, fever with stiff neck, or weakness - urgent"},
    {"id": "tension_headache", "fa": "سردرد تنشی", "en": "Tension headache", "prior": 0.07, "urgency": "routine",
     "symptoms": {"headache": 1.0, "fatigue": 0.5, "insomnia": 0.4, "back_pain": 0.3, "anxiety": 0.4},
     "advice": ["تنظیم خواب و استراحت چشم", "کشش و حرکات شانه و گردن", "کمکردن استرس و صفحه‌نمایش"],
     "advice_en": ["Fix your sleep; rest your eyes", "Neck and shoulder stretches", "Reduce stress and screen time"],
     "doctor_when": "تغییر الگوی سردرد یا همراهی با علائم عصبی",
     "doctor_when_en": "A change in headache pattern, or any neurological signs"},
    {"id": "gastroenteritis", "fa": "گاستروانتریت (اسهال عفونی)", "en": "Gastroenteritis", "prior": 0.08, "urgency": "routine",
     "symptoms": {"diarrhea": 0.9, "nausea": 0.7, "vomiting": 0.6, "abdominal_pain": 0.7, "fever": 0.4, "appetite_loss": 0.5},
     "advice": ["ORS/مایعات و آب فراوان برای جبران آب", "غذای سبک و کم‌چرب (برنج، سوپ)", "پرهیز از لبنیات و غذاهای چرب تا بهبود نسبی"],
     "advice_en": ["ORS/fluids to replace losses", "Light, low-fat food (rice, soup)", "Skip dairy and fatty food until you improve"],
     "doctor_when": "خون در مدفوع، اسهال بیش از ۳ روز، علائم کم‌آبی شدید، تب بالا",
     "doctor_when_en": "Blood in stool, diarrhea over 3 days, signs of dehydration, or high fever"},
    {"id": "food_poisoning", "fa": "احتمال مسمومیت غذایی", "en": "Food poisoning (possible)", "prior": 0.05, "urgency": "routine",
     "symptoms": {"vomiting": 0.8, "nausea": 0.8, "diarrhea": 0.7, "abdominal_pain": 0.7, "fever": 0.3},
     "advice": ["مایعات کوچک و مکرر", "استراحت", "پرهیز از غذای مشکوک مصرف‌شده"],
     "advice_en": ["Small, frequent sips of fluid", "Rest", "Avoid the suspected food"],
     "doctor_when": "استفراغ مداوم بیش از ۲۴ ساعت، خون در مدفوع، تب بالا، علائم کم‌آبی",
     "doctor_when_en": "Vomiting past 24 hours, blood in stool, high fever, or dehydration"},
    {"id": "gerd", "fa": "رفلاکس معده به مری (احتمالی)", "en": "GERD (possible)", "prior": 0.06, "urgency": "routine",
     "symptoms": {"heartburn": 0.9, "chest_pain": 0.3, "nausea": 0.3, "sore_throat_dry": 0.25, "bloating": 0.4, "cough": 0.2},
     "advice": ["پرهیز از غذای تند/چرب/قهوه و نوشیدنی گازدار", "شام سبک ۳ ساعت قبل خواب", "کاهش وزن در صورت اضافه‌وزن"],
     "advice_en": ["Cut spicy/fatty food, coffee and sodas", "Light dinner 3 hours before bed", "Lose weight if above range"],
     "doctor_when": "درد قفسه سینه مطرح است → اول اورژانس؛ بلع دشوار یا کاهش وزن",
     "doctor_when_en": "Any chest pain is an emergency first; also difficulty swallowing or weight loss"},
    {"id": "peptic_ulcer", "fa": "زخم معده (احتمالی)", "en": "Peptic ulcer (possible)", "prior": 0.03, "urgency": "routine",
     "symptoms": {"abdominal_pain": 0.9, "heartburn": 0.5, "nausea": 0.4, "bloating": 0.4, "vomiting": 0.2},
     "advice": ["پرهیز از مسکن‌های NSAID مثل ایبوپروفن بدون نظر پزشک", "غذای منظم و پرهیز از سیگار و الکل"],
     "advice_en": ["No NSAID painkillers like ibuprofen without a doctor", "Regular meals; no smoking or alcohol"],
     "doctor_when": "استفراغ خونی یا مدفوع سیاه → فوری؛ درد شدید ناگهانی شکم → اورژانس",
     "doctor_when_en": "Vomiting blood or black stools - urgent; sudden severe abdominal pain - emergency"},
    {"id": "uti", "fa": "عفونت ادراری (احتمالی)", "en": "UTI (possible)", "prior": 0.06, "urgency": "routine",
     "symptoms": {"dysuria": 0.9, "urinary_frequency": 0.8, "abdominal_pain": 0.4, "flank_pain": 0.25, "fever": 0.25},
     "advice": ["نوشیدن آب کافی", "مراجعه برای آزمایش ادرار و در صورت نیاز آنتی‌بیوتیک با تجویز پزشک"],
     "advice_en": ["Drink enough water", "See a clinician for a urine test; antibiotics only by prescription"],
     "doctor_when": "تب و لرز با درد پهلو (درگیری کلیه)، بارداری، یا خون در ادرار",
     "doctor_when_en": "Fever and chills with flank pain (kidney involvement), pregnancy, or blood in urine"},
    {"id": "kidney_stone", "fa": "سنگ کلیه (احتمالی)", "en": "Kidney stone (possible)", "prior": 0.03, "urgency": "urgent",
     "symptoms": {"flank_pain": 0.9, "abdominal_pain": 0.4, "nausea": 0.5, "vomiting": 0.4, "dysuria": 0.3},
     "advice": ["درد شدید کولیکی → مراجعه فوری", "آب فراوان بعد از نظر پزشک"],
     "advice_en": ["Severe colicky pain - seek care now", "Plenty of water once a doctor approves"],
     "doctor_when": "درد کولیکی شدید، تب، یا استفراغ مداوم → اورژانس",
     "doctor_when_en": "Severe colicky pain, fever, or constant vomiting - emergency"},
    {"id": "strep_throat", "fa": "گلودرد استرپتوکوکی (احتمالی)", "en": "Strep throat (possible)", "prior": 0.03, "urgency": "routine",
     "symptoms": {"sore_throat": 1.0, "fever": 0.7, "headache": 0.3, "appetite_loss": 0.3, "cough": 0.1},
     "advice": ["غرغره‌ی آب نمک", "مایعات گرم", "معاینه و در صورت نیاز تست سریع استرپ"],
     "advice_en": ["Saltwater gargle", "Warm fluids", "An exam and a rapid strep test if suggested"],
     "doctor_when": "تب بالا با گلودرد شدید بدون سرفه، تورم گردن یا مشکل تنفس",
     "doctor_when_en": "High fever with severe sore throat and no cough, neck swelling, or trouble breathing"},
    {"id": "sinusitis", "fa": "سینوزیت (احتمالی)", "en": "Sinusitis (possible)", "prior": 0.04, "urgency": "routine",
     "symptoms": {"headache": 0.8, "runny_nose": 0.6, "fever": 0.3, "cough": 0.4, "fatigue": 0.4},
     "advice": ["شست‌وشوی بینی با سالین", "بخور آب گرم", "استراحت"],
     "advice_en": ["Saline nasal rinse", "Steam inhalation", "Rest"],
     "doctor_when": "علائم بیش از ۱۰ روز، تب بالا، تورم دور چشم → فوری",
     "doctor_when_en": "Symptoms past 10 days, high fever, or swelling around the eye - urgent"},
    {"id": "hypertension_likely", "fa": "فشار خون بالا (احتمالی)", "en": "Possible high blood pressure", "prior": 0.04, "urgency": "routine",
     "symptoms": {"headache": 0.5, "dizziness": 0.4, "palpitation": 0.3, "fatigue": 0.3, "blurred_vision": 0.2},
     "advice": ["اندازه‌گیری فشار خون در آرامش، چند بار", "کمکردن نمک، ترک سیگار، فعالیت هوازی منظم"],
     "advice_en": ["Measure your blood pressure calmly, more than once", "Less salt, no smoking, regular aerobic activity"],
     "doctor_when": "فشار ≥ ۱۸۰/۱۲۰ یا درد قفسه سینه/تنگی نفس/ضعف → اورژانس فوری",
     "doctor_when_en": "BP at or above 180/120, or chest pain/breathlessness/weakness - emergency"},
    {"id": "hyperglycemia_likely", "fa": "قند خون بالا (احتمالی)", "en": "Possible high blood sugar", "prior": 0.03, "urgency": "routine",
     "symptoms": {"thirst": 0.8, "urinary_frequency": 0.7, "fatigue": 0.6, "blurred_vision": 0.4, "weight_loss": 0.4},
     "advice": ["انجام قند خون ناشتا (FBS) و در صورت امکان HbA1c", "پرهیز از نوشیدنی‌های شیرین تا مشخص‌شدن قند"],
     "advice_en": ["Get a fasting blood sugar (FBS) and HbA1c if possible", "No sugary drinks until sugar is known"],
     "doctor_when": "تهوع و استفراغ با تنفس تند و بوی استون دهان (کتواسیدوز) → اورژانس فوری",
     "doctor_when_en": "Nausea and vomiting with fast breathing and fruity breath (ketoacidosis) - emergency"},
    {"id": "asthma", "fa": "آسم (احتمالی)", "en": "Asthma (possible)", "prior": 0.03, "urgency": "urgent",
     "symptoms": {"wheezing": 0.9, "shortness_of_breath": 0.8, "cough": 0.6, "chest_pain": 0.2},
     "advice": ["در حمله: نشستن راحت و اسپری اضطراری در صورت دارا بودن", "پرهیز از محرک‌ها (دود، حساسیت‌زا)"],
     "advice_en": ["During an attack: sit upright, use your rescue inhaler if you have one", "Avoid triggers (smoke, allergens)"],
     "doctor_when": "حمله‌ی شدید، لب‌های کبود، یا بی‌اثری اسپری → اورژانس فوری",
     "doctor_when_en": "Severe attack, blue lips, or inhaler not helping - emergency"},
    {"id": "bronchitis", "fa": "برونشیت حاد (احتمالی)", "en": "Acute bronchitis (possible)", "prior": 0.03, "urgency": "routine",
     "symptoms": {"cough": 0.95, "sputum": 0.7, "fever": 0.3, "fatigue": 0.5, "wheezing": 0.3, "chest_pain": 0.2},
     "advice": ["مایعات گرم و استراحت", "پرهیز از دود سیگار"],
     "advice_en": ["Warm fluids and rest", "Avoid smoke"],
     "doctor_when": "تب بالا، تنگی نفس، یا سرفه بیش از ۳ هفته",
     "doctor_when_en": "High fever, breathlessness, or a cough beyond 3 weeks"},
    {"id": "pneumonia", "fa": "پنومونی (احتمالی — نیاز به بررسی پزشک)", "en": "Pneumonia (possible - needs a clinician)", "prior": 0.02, "urgency": "urgent",
     "symptoms": {"fever": 0.8, "cough": 0.8, "sputum": 0.6, "shortness_of_breath": 0.6, "chest_pain": 0.4, "fatigue": 0.6, "rapid_breathing": 0.4},
     "advice": ["این حالت نیاز به معاینه و احتمالاً عکس قفسه سینه دارد؛ مراجعه در اولین فرصت"],
     "advice_en": ["This pattern needs an exam and possibly a chest X-ray; see a clinician soon"],
     "doctor_when": "تنگی نفس شدید، تب بالا با گیجی، لب کبود → اورژانس",
     "doctor_when_en": "Severe breathlessness, high fever with confusion, blue lips - emergency"},
    {"id": "anxiety_stress", "fa": "اضطراب/استرس", "en": "Anxiety/stress", "prior": 0.09, "urgency": "routine",
     "symptoms": {"anxiety": 0.9, "palpitation": 0.5, "insomnia": 0.6, "fatigue": 0.5, "panic": 0.4, "headache": 0.3, "dizziness": 0.3},
     "advice": ["تمرین تنفس عمیق (۴ ثانیه دم، ۴ نگه‌داشتن، ۶ بازدم)", "کاهش کافئین، خواب منظم", "در صورت تداوم، مشاوره‌ی روان‌شناس"],
     "advice_en": ["Slow breathing (in 4s, hold 4s, out 6s)", "Less caffeine, regular sleep", "Consider a counselor if it persists"],
     "doctor_when": "افکار آسیب به خود → فوری با خط بحران یا اورژانس تماس بگیرید (ایران: ۱۴۸۰/۱۲۳)",
     "doctor_when_en": "Any thoughts of self-harm - contact a crisis line or emergency services now"},
    {"id": "depression_likely", "fa": "افسردگی (احتمالی)", "en": "Depression (possible)", "prior": 0.04, "urgency": "routine",
     "symptoms": {"mood_low": 0.9, "loss_of_interest": 0.8, "insomnia": 0.6, "fatigue": 0.7, "appetite_loss": 0.5},
     "advice": ["صحبت با فرد مورد اعتماد", "فعالیت بدنی سبک روزانه", "پرکردن پرسش‌نامه‌ی PHQ-9 در بخش سلامت روان این برنامه"],
     "advice_en": ["Talk to someone you trust", "Light daily activity", "Fill the PHQ-9 in the mental health section"],
     "doctor_when": "هرگونه فکر به آسیب رساندن به خود → فوری با خط بحران تماس بگیرید",
     "doctor_when_en": "Any thought of harming yourself - call a crisis line immediately"},
    {"id": "iron_def_anemia", "fa": "کم‌خونی کم‌آهن (احتمالی)", "en": "Iron-deficiency anemia (possible)", "prior": 0.04, "urgency": "routine",
     "symptoms": {"fatigue": 0.9, "dizziness": 0.5, "palpitation": 0.3, "shortness_of_breath": 0.3, "headache": 0.3},
     "advice": ["انجام CBC و آهن/فریتین", "غذاهای غنی از آهن (گوشت قرمز، حبوبات، سبزیجات تیره) با منبع ویتامین C"],
     "advice_en": ["Get a CBC and iron/ferritin", "Iron-rich foods (red meat, legumes, dark greens) with vitamin C"],
     "doctor_when": "تنگی نفس یا درد قفسه سینه، خونریزی پیشین، بارداری",
     "doctor_when_en": "Breathlessness or chest pain, prior blood loss, or pregnancy"},
    {"id": "hypothyroid_likely", "fa": "کم‌کاری تیروئید (احتمالی)", "en": "Hypothyroidism (possible)", "prior": 0.03, "urgency": "routine",
     "symptoms": {"fatigue": 0.8, "constipation": 0.5, "mood_low": 0.4, "weight_gain": 0.6},
     "advice": ["آزمایش TSH و T4 آزاد", "مراجعه به پزشک در صورت غیرطبیعی بودن"],
     "advice_en": ["Test TSH and free T4", "See a doctor if abnormal"],
     "doctor_when": "کاهش هوشیاری یا ضربان قلب خیلی کند → اورژانس",
     "doctor_when_en": "Falling consciousness or a very slow pulse - emergency"},
    {"id": "urticaria", "fa": "کهیر/آلرژی پوستی (احتمالی)", "en": "Urticaria (possible)", "prior": 0.03, "urgency": "routine",
     "symptoms": {"skin_itch": 0.9, "rash": 0.8},
     "advice": ["آنتی‌هیستامین در صورت صلاحدید داروخانه", "اجتناب از محرک (غذا/داروی جدید)", "سرد کردن موضعی"],
     "advice_en": ["Antihistamine if the pharmacist agrees", "Avoid the new trigger (food/drug)", "Cool compress on the area"],
     "doctor_when": "تورم لب/زبان/گلو یا تنگی نفس → آنافیلاکسی است، فوری اورژانس",
     "doctor_when_en": "Swelling of lips/tongue/throat or trouble breathing - that is anaphylaxis, call emergency now"},
    {"id": "eczema_likely", "fa": "اگزما/درماتیت (احتمالی)", "en": "Eczema (possible)", "prior": 0.03, "urgency": "routine",
     "symptoms": {"skin_itch": 0.9, "rash": 0.7},
     "advice": ["مرطوب‌کننده‌ی بدون عطر", "حمام کوتاه ولرم", "پرهیز از خاراندن"],
     "advice_en": ["Fragrance-free moisturizer", "Short, lukewarm showers", "Do not scratch"],
     "doctor_when": "علامت عفونت (ترشح، درد، تب) یا بی‌پاسخی به مراقبت عمومی",
     "doctor_when_en": "Signs of infection (discharge, pain, fever) or no response to basic care"},
    {"id": "sleep_apnea_likely", "fa": "آپنه‌ی خواب (احتمالی)", "en": "Sleep apnea (possible)", "prior": 0.03, "urgency": "routine",
     "symptoms": {"snoring": 0.9, "apnea_observed": 0.8, "daytime_sleepiness": 0.8, "headache": 0.4, "fatigue": 0.6},
     "advice": ["پرکردن STOP-BANG در بخش تحلیل خواب برنامه", "کاهش وزن در صورت اضافه‌وزن، خوابیدن به پهلو"],
     "advice_en": ["Fill the STOP-BANG in the sleep section", "Weight loss if above range; sleep on your side"],
     "doctor_when": "خواب‌آلودگی شدید پشت فرمان یا حین کار → ارزیابی پزشک خواب",
     "doctor_when_en": "Severe sleepiness while driving or at work - see a sleep doctor"},
    {"id": "insomnia_stress", "fa": "بی‌خوابی مرتبط با استرس", "en": "Stress-related insomnia", "prior": 0.05, "urgency": "routine",
     "symptoms": {"insomnia": 1.0, "anxiety": 0.6, "fatigue": 0.6, "mood_low": 0.3},
     "advice": ["به‌خوابیدن و بیدارشدن در ساعت ثابت", "پرهیز از صفحه‌نمایش ۱ ساعت قبل خواب و کافئین بعدازظهر", "تکنیک آرام‌سازی عضلات"],
     "advice_en": ["Fixed sleep and wake times", "No screens 1 hour before bed; no afternoon caffeine", "Muscle relaxation techniques"],
     "doctor_when": "بی‌خوابی بیش از ۱ ماه یا همراه با افکار نگران‌کننده‌ی شدید",
     "doctor_when_en": "Insomnia beyond a month, or distressing thoughts"},
    {"id": "dyspepsia", "fa": "سوءهاضمه/نفخ", "en": "Functional dyspepsia", "prior": 0.04, "urgency": "routine",
     "symptoms": {"bloating": 0.8, "abdominal_pain": 0.6, "nausea": 0.4, "heartburn": 0.4, "appetite_loss": 0.3},
     "advice": ["وعده‌های کوچک و دفعات بیشتر", "کاهش چربی، کافئین و نوشابه", "پیاده‌روی بعد از غذا"],
     "advice_en": ["Smaller, more frequent meals", "Less fat, caffeine and soda", "Walk after eating"],
     "doctor_when": "کاهش وزن بی‌دلیل، استفراغ خونی، اختلال بلع، سن بالای ۵۰ با علامت جدید",
     "doctor_when_en": "Unexplained weight loss, vomiting blood, trouble swallowing, or new symptoms over 50"},
    {"id": "appendicitis", "fa": "آپاندیسیت (احتمالی — اورژانسی)", "en": "Appendicitis (possible - urgent)", "prior": 0.02, "urgency": "emergency",
     "symptoms": {"abdominal_pain": 0.9, "nausea": 0.6, "vomiting": 0.4, "fever": 0.5, "appetite_loss": 0.7},
     "advice": ["هیچ‌چیز نخور و نیاشام", "مسکن/ملین خودسرانه نکن (علائم را پنهان می‌کند)", "همین امروز اورژانس/مطب"],
     "advice_en": ["Do not eat or drink", "No painkillers or laxatives on your own (they mask signs)", "Emergency department or clinic today"],
     "doctor_when": "درد شکم که به گوشه‌ی راست‌پایین می‌رود + تهوع/بی‌اشتهایی → فوری",
     "doctor_when_en": "Belly pain moving to the lower right side with nausea/loss of appetite - urgent"},
    {"id": "meningitis", "fa": "مننژیت (احتمالی — اورژانسی)", "en": "Meningitis (possible - urgent)", "prior": 0.008, "urgency": "emergency",
     "symptoms": {"fever": 0.8, "headache": 0.8, "stiff_neck": 0.8, "photophobia": 0.5, "vomiting": 0.4, "confusion": 0.4, "rash": 0.2},
     "advice": ["تب + سردرد + سفتی گردن = همین حالا اورژانس", "به هیچ عنوان در خانه منتظر نمان"],
     "advice_en": ["Fever + headache + stiff neck = emergency right now", "Do not wait at home"],
     "doctor_when": "ترکیب تب و سردرد و گردن سفت → اورژانس فوری (۱۱۵/۱۱۲)",
     "doctor_when_en": "Fever with headache and stiff neck - call emergency now (115/112)"},
    {"id": "angina_likely", "fa": "آنژین صدری (احتمالی)", "en": "Angina (possible)", "prior": 0.02, "urgency": "emergency",
     "symptoms": {"chest_pain": 1.0, "shortness_of_breath": 0.5, "sweating": 0.4, "left_arm_pain": 0.3},
     "advice": ["هر درد قفسه سینه تا خلاف آن ثابت شود اورژانس است", "فعالیت را متوقف کن و کمک بخواه"],
     "advice_en": ["Any chest pain is an emergency until proven otherwise", "Stop exertion and get help"],
     "doctor_when": "درد سینه با فعالیت که با استراحت خوب می‌شود → ارزیابی قلبی فوری",
     "doctor_when_en": "Chest tightness on exertion relieved by rest - urgent cardiac assessment"},
    {"id": "dvt_likely", "fa": "لخته‌ی وریدی پا/DVT (احتمالی)", "en": "Leg DVT (possible)", "prior": 0.01, "urgency": "urgent",
     "symptoms": {"leg_swelling": 0.9, "calf_pain": 0.8, "skin_itch": 0.1},
     "advice": ["پا را مالش نده", "همان روز پزشک/اورژانس (سونوگرافی داپلر)", "اگر تنگی نفس هم اضافه شد → اورژانس فوری (آمبولی)"],
     "advice_en": ["Do not massage the leg", "Same-day clinician/emergency (duplex ultrasound)", "New breathlessness means emergency (clot to the lungs)"],
     "doctor_when": "تورم و درد یک پا، به‌ویژه بعد از سفر طولانی/بی‌حرکتی/جراحی → همان روز",
     "doctor_when_en": "One swollen painful leg, especially after long travel/immobility/surgery - same day"},
    {"id": "otitis", "fa": "عفونت گوش (احتمالی)", "en": "Ear infection (possible)", "prior": 0.03, "urgency": "routine",
     "symptoms": {"ear_pain": 1.0, "fever": 0.5, "sore_throat": 0.3},
     "advice": ["مسکن ساده در صورت نیاز", "معاینه‌ی گوش توسط پزشک", "در کودکان زیر ۲ سال ارزیازه پزشک لازم است"],
     "advice_en": ["Simple pain relief if needed", "An ear exam by a clinician", "Under age 2, always see a doctor"],
     "doctor_when": "درد شدید، ترشح از گوش، تب بالا یا تورم پشت گوش → فوری",
     "doctor_when_en": "Severe pain, discharge from the ear, high fever, or swelling behind the ear - urgent"},
    {"id": "dysmenorrhea", "fa": "دیسمنوره (درد قاعدگی)", "en": "Menstrual cramps", "prior": 0.05, "urgency": "routine",
     "symptoms": {"menstrual_cramps": 1.0, "abdominal_pain": 0.6, "nausea": 0.3, "back_pain": 0.4},
     "advice": ["کمپرس گرم روی شکم", "فعالیت بدنی سبک", "مسکن ساده طبق دستور داروخانه/پزشک"],
     "advice_en": ["Warm compress on the lower belly", "Light activity", "Simple pain relief as advised by pharmacist/doctor"],
     "doctor_when": "درد غیرقابل کنترل، خونریزی خیلی زیاد یا تب",
     "doctor_when_en": "Uncontrollable pain, very heavy bleeding, or fever"},
    {"id": "chickenpox", "fa": "آبله‌مرغان (احتمالی)", "en": "Chickenpox (possible)", "prior": 0.02, "urgency": "routine",
     "symptoms": {"fever": 0.7, "rash": 0.9, "skin_itch": 0.7, "appetite_loss": 0.3},
     "advice": ["جداسازی تا خشک‌شدن تاول‌ها", "خارش: آنتی‌هیستامین/لوسیون با نظر داروخانه", "ناخن‌ها کوتاه"],
     "advice_en": ["Isolate until the blisters crust over", "Itch: antihistamine/lotion per pharmacist", "Keep nails short"],
     "doctor_when": "تب بالا، علائم عفونت پوست، سردرد شدید، بزرگسال/باردار → پزشک",
     "doctor_when_en": "High fever, skin infection signs, severe headache, adult/pregnant - see a doctor"},
    {"id": "scabies", "fa": "گال (احتمالی)", "en": "Scabies (possible)", "prior": 0.02, "urgency": "routine",
     "symptoms": {"skin_itch": 1.0, "rash": 0.5},
     "advice": ["خارش شدید شبانه و درگیری چند نفر از خانواده ← احتمال گال", "درمان موضعی تجویزی برای همه‌ی اعضا هم‌زمان", "شست‌وشوی البسه با آب داغ"],
     "advice_en": ["Severe night itch plus affected family members points to scabies", "Prescribed topical treatment for everyone at once", "Hot-wash clothes and bedding"],
     "doctor_when": "زخم/عفونت ثانویه یا بی‌پاسخ به درمان",
     "doctor_when_en": "Secondary infection or no response to treatment"},
    {"id": "oral_aphthous", "fa": "آفت دهان (احتمالی)", "en": "Mouth ulcer / aphthous (possible)", "prior": 0.03, "urgency": "routine",
     "symptoms": {"mouth_ulcer": 1.0, "fever": 0.1},
     "advice": ["دهان‌شویه‌ی ملایم و غذای غیرادکنه", "خمیر بی‌حسی بدون نسخه در صورت صلاحدید داروخانه", "بزرگ‌تر از ۱ سانتی‌متر یا بیش از ۲ هفته → پزشک"],
     "advice_en": ["Mild mouthwash, avoid spicy food", "Over-the-counter numbing gel if the pharmacist agrees", "Bigger than 1 cm or beyond 2 weeks - see a doctor"],
     "doctor_when": "زخم بزرگ/مقاوم، تب، یا درگیری مفاصل/چشم",
     "doctor_when_en": "Large or persistent ulcer, fever, or joint/eye involvement"},
    {"id": "allergic_conjunctivitis", "fa": "آلرژی چشمی (احتمالی)", "en": "Allergic conjunctivitis (possible)", "prior": 0.03, "urgency": "routine",
     "symptoms": {"eye_redness": 0.9, "tear_eyes": 0.8, "skin_itch": 0.4, "sneezing": 0.4},
     "advice": ["شست‌وشوی چشم با آب تمیز/قطره اشک مصنوعی", "پرهیز از مالش و مواجهه با محرک", "آنتی‌هیستامین در صورت صلاحدید داروخانه"],
     "advice_en": ["Rinse eyes with clean water/artificial tears", "No rubbing; avoid the trigger", "Antihistamine if the pharmacist agrees"],
     "doctor_when": "درد شدید چشم، تغییر دید، نورآزاری شدید یا ترشح چرکی",
     "doctor_when_en": "Severe eye pain, vision change, strong light sensitivity, or pus"},
    {"id": "bppv_vertigo", "fa": "سرگیجه‌ی خوش‌خیم/BPPV (احتمالی)", "en": "Benign vertigo / BPPV (possible)", "prior": 0.03, "urgency": "routine",
     "symptoms": {"dizziness": 1.0, "nausea": 0.5, "vomiting": 0.3},
     "advice": ["حرکات آرام سر؛ در حمله بنشین", "تغییر وضعیت ناگهانی سر را کم کن", "مانور تصحیحی فقط با فیزیوتراپیست/پزشک"],
     "advice_en": ["Slow head movements; sit during an attack", "Avoid sudden head position changes", "Repositioning maneuvers only with a trained clinician"],
     "doctor_when": "سرگیجه با ضعف/اختلال تکلم/دوبینی یا شنوایی → فوری",
     "doctor_when_en": "Vertigo with weakness/slurred speech/double vision or hearing loss - urgent"},
    {"id": "gallbladder_likely", "fa": "صفرا/کیسه‌ی صفرا (احتمالی)", "en": "Gallbladder problem (possible)", "prior": 0.02, "urgency": "urgent",
     "symptoms": {"abdominal_pain": 0.8, "nausea": 0.5, "vomiting": 0.3, "fever": 0.2, "bloating": 0.4},
     "advice": ["غذای کم‌چرب تا معاینه", "درد شدید بعد از غذای چرب + تهوع ← احتمال کولیک صفراوی؛ ارزیابی پزشک", "سونوگرافی در صورت تجویز"],
     "advice_en": ["Low-fat food until examined", "Severe pain after fatty meals plus nausea points to biliary colic; see a doctor", "Ultrasound if ordered"],
     "doctor_when": "درد شدید مستمر + تب/زردی → اورژانس",
     "doctor_when_en": "Constant severe pain with fever/jaundice - emergency"},
    {"id": "cellulitis", "fa": "سلولیت (عفونت بافت نرم — احتمالی)", "en": "Cellulitis (skin infection, possible)", "prior": 0.02, "urgency": "urgent",
     "symptoms": {"rash": 0.9, "fever": 0.7, "skin_itch": 0.2},
     "advice": ["قرمزی را با ماژیک دور خط بزن تا پخش‌شدنش معلوم شود", "همان روز پزشک/اورژانس", "ناحیه را بالا نگه دار"],
     "advice_en": ["Draw a line around the redness with a pen to track spreading", "Same-day clinician/emergency", "Keep the limb raised"],
     "doctor_when": "قرمزی پخش‌شونده با تب یا درد → فوری؛ عفونت پوستی درمان‌نشده خطرناک است",
     "doctor_when_en": "Spreading redness with fever or pain - urgent; untreated skin infection is dangerous"},
    {"id": "hypoglycemia", "fa": "افت قند خون (احتمالی — اورژانسی)", "en": "Low blood sugar (possible - urgent)", "prior": 0.02, "urgency": "emergency",
     "symptoms": {"sweating": 0.9, "tremor": 0.9, "palpitation": 0.5, "dizziness": 0.5, "confusion": 0.3, "nausea": 0.3},
     "advice": ["اگر بیمار هوشیار است: ۱۵ گرم قند سریع (آب‌قند/عربی) و بعد ۱۵ دقیقه صبر", "اندازه‌گیری قند اگر دستگاه هست", "تکرار تا بهبود؛ سپس میان‌وعده‌ی نشاسته‌دار"],
     "advice_en": ["If fully conscious: 15 g fast sugar (glucose tabs/sweet drink), wait 15 minutes", "Check sugar if a meter is available", "Repeat until better, then a starchy snack"],
     "doctor_when": "بی‌هوشی، تشنج یا عدم بهبود بعد از دو نوبت قند → اورژانس فوری",
     "doctor_when_en": "Unconsciousness, seizure, or no recovery after two sugar rounds - call emergency now"},
    {"id": "shingles", "fa": "زونا (احتمالی)", "en": "Shingles / herpes zoster (possible)", "prior": 0.02, "urgency": "routine",
     "symptoms": {"rash": 0.9, "skin_itch": 0.5, "fever": 0.3, "body_ache": 0.3},
     "advice": ["تاول‌های کمربندشکل/یک‌طرفه + درد سوزشی ← مطرح برای زونا", "شروع دارو در ۷۲ ساعت اول مؤثرترین است → مراجعه‌ی سریع", "تماس با بارداران/کودکان واکسین‌نشده را قطع کن"],
     "advice_en": ["One-sided belt-like blisters with burning pain point to shingles", "Medication works best within 72 hours - seek care promptly", "Avoid contact with pregnant/unvaccinated people"],
     "doctor_when": "زونا روی صورت/چشم، تب بالا، یا درد شدید → همان روز پزشک",
     "doctor_when_en": "Shingles on the face/eye, high fever, or severe pain - same-day doctor"},
    {"id": "tonsillitis_viral", "fa": "لوزه‌ی ورم‌کرده/تونسیلیت (احتمالی)", "en": "Tonsillitis (possible)", "prior": 0.03, "urgency": "routine",
     "symptoms": {"sore_throat": 1.0, "fever": 0.6, "headache": 0.3, "appetite_loss": 0.3},
     "advice": ["مایعات سرد/ولرم و استراحت", "غرغره‌ی آب نمک", "اگر لوزه‌ها چرکی + تب بالا + غدد گردن ورم‌کرده → معاینه برای تست استرپ"],
     "advice_en": ["Cool or warm fluids and rest", "Saltwater gargle", "Pus on tonsils + high fever + swollen neck glands - get examined for strep"],
     "doctor_when": "درد شدید یک‌طرفه، مشکل بلع/تنفس، یا تب بالا → پزشک",
     "doctor_when_en": "Severe one-sided pain, trouble swallowing/breathing, or high fever - see a doctor"},
]


# ============================================================================
# 4) Symptom detection from free text (en/fa)
# ============================================================================

def detect_symptoms(text: str) -> dict[str, Any]:
    """Returns {present: {sid: {count, severity, denied}}, duration_days, temp_c}.
    Negation is checked inside the same clause so 'no fever' does not leak
    onto earlier symptoms."""
    clauses = [normalize(c) for c in re.split(r"[،؛,.!؟?!\n]", text or "")]
    clauses = [c for c in clauses if c]
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
                    "denied": _is_denied(window) and ("نمی" not in nk) and ("not" not in nk) and ("cant" not in nk) and ("can not" not in nk),
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
    t = " ".join(clauses)
    duration_days = None
    for m in DURATION_RE.finditer(t):
        num = float(m.group(1).replace(",", "."))
        unit = m.group(2).lower()
        mult = {"روز": 1, "شب": 1, "هفته": 7, "ماه": 30, "سال": 365, "ساعت": 1 / 24,
                "day": 1, "days": 1, "week": 7, "weeks": 7, "month": 30, "months": 30,
                "year": 365, "years": 365, "hour": 1 / 24, "hours": 1 / 24}.get(unit, 1)
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
    """Screen for the red flag list before anything else."""
    from i18n import is_fa
    t = normalize(text)
    reasons: list[str] = []
    hits: list[str] = []
    for rf in RED_FLAGS:
        if any(normalize(k) in t for k in rf["any"]):
            reasons.append(rf["fa"] if is_fa() else rf["en"])
            hits.append(rf["id"])
    # combined pattern: pain/pressure ... chest, even split by another word
    if "chest_pain" not in hits and ("قفسه سینه" in t or "chest" in t) and any(
            w in t for w in ("درد", "فشار", "سوزش", "pain", "pressure", "tight", "burning", "burn")):
        reasons.append("درد قفسه سینه" if is_fa() else "chest pain")
        hits.append("chest_pain")
    # numeric fever >= 40
    if detected and detected.get("temp_c") and detected["temp_c"] >= 40:
        reasons.append("تب بسیار شدید (۴۰ درجه یا بالاتر)" if is_fa() else "very high fever (40 C or above)")
        hits.append("high_fever")
    # FAST cluster: at least 2 of weakness/speech/face
    s = set(hits)
    fast = {"sudden_weakness", "speech", "face_droop"} & s
    if len(fast) >= 2:
        reasons.append("علائم مطرح برای سکته‌ی مغزی" if is_fa() else "signs suggesting a stroke")
        hits.append("stroke_cluster")
    # chest pain + sweat/left arm
    if "chest_pain" in s and any(k in t for k in ("عرق", "بازوی چپ", "دست چپ", "فک", "تهوع", "sweat", "left arm", "jaw", "nausea", "clammy")):
        reasons.append("علائم مطرح برای حمله‌ی قلبی" if is_fa() else "signs suggesting a heart attack")
        hits.append("heart_attack")
    # خوشه‌ی مننژیت: سفتی گردن + تب یا سردرد
    if detected:
        pres = {s for s, i in detected.get("present", {}).items() if not i.get("denied")}
        if "stiff_neck" in pres and ({"fever", "headache", "photophobia", "confusion"} & pres):
            reasons.append("سفتی گردن با تب/سردرد — مطرح برای مننژیت" if is_fa() else "neck stiffness with fever/headache - possible meningitis")
            hits.append("meningitis_cluster")
    # severity of key symptoms
    if detected:
        for sid, info in detected["present"].items():
            if sid in ("chest_pain", "shortness_of_breath", "abdominal_pain") and info["severity"] == "severe" and not info.get("denied"):
                label = sym_name(sid)
                entry = (f"{label} شدید" if is_fa() else f"severe {label}")
                if entry not in reasons:
                    reasons.append(entry)
    return {"flag": bool(reasons), "reasons": reasons, "hits": sorted(set(hits))}


EMERGENCY_RESPONSE_EN = """**EMERGENCY WARNING - routine assessment stopped**

The following red flag signs were detected in your message: {reasons}

**Right now:**
1. Call emergency services - Iran: 115 | Europe/Finland: 112
2. Keep the person safe and still (sitting, or lying on the side if consciousness is dropping)
3. If stroke is suspected: note the exact time symptoms started; give no food, water or medication by mouth
4. If chest pain: stop all activity, sit and stay calm; medication only as directed by the dispatcher
5. If unconscious and not breathing: start CPR (the CPR tool in this app keeps a 110 bpm pace)

This assistant does not continue routine assessment at this point; emergency care comes first.
{disclaimer}"""

EMERGENCY_RESPONSE_FA = """**هشدار اورژانسی — تشخیص معمول متوقف شد**

در متن شما این نشانگان خطر شناسایی شد: {reasons}

**همین حالا:**
1. با اورژانس تماس بگیرید — ایران: ۱۱۵ | اروپا/فنلاند: ۱۱۲
2. فرد را در موقعیت امن نگه دارید (نشسته یا خوابیده به پهلو در صورت کاهش هوشیاری)
3. در مشکوک به سکته: زمان شروع علائم را یادداشت کنید؛ به فرد غذای آب یا دارو ندهید
4. در درد قفسه سینه: فعالیت متوقف، نشستن و آرامش؛ دارو فقط با راهنمایی اورژانس
5. در بیهوشی بدون تنفس: CPR را شروع کنید (ابزار CPR این برنامه ضرباهنگ ۱۱۰ در دقیقه دارد)

این برنامه در این مرحله تشخیص معمول انجام نمی‌دهد؛ اولویت با رسیدگی اورژانسی است.
{disclaimer}"""


def emergency_response(reasons: list[str], disclaimer: str = "") -> str:
    from common_2077 import MEDICAL_DISCLAIMER
    from i18n import is_fa
    tmpl = EMERGENCY_RESPONSE_FA if is_fa() else EMERGENCY_RESPONSE_EN
    return tmpl.format(
        reasons="، ".join(reasons) if is_fa() else ", ".join(reasons),
        disclaimer="\n\n" + (disclaimer or MEDICAL_DISCLAIMER()),
    )


def analyze(text: str, profile: dict | None = None) -> dict[str, Any]:
    """Overall analysis: red flags first, then symptoms, then Bayes ranking."""
    detected = detect_symptoms(text)
    red = check_red_flags(text, detected)
    result = {
        "red_flag": red["flag"],
        "red_flag_reasons": red["reasons"],
        "detected": detected,
        "symptoms": [sym_name(s) for s, i in detected["present"].items() if not i.get("denied")],
        "denied": [sym_name(s) for s, i in detected["present"].items() if i.get("denied")],
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
