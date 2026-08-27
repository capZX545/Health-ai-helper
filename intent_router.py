"""
intent_router.py — classifies what the user wants before answering.

Routes each message to the right brain:
  greeting | drug_question | disease_question | advice_question |
  symptom_report | smalltalk/other
"""
from __future__ import annotations

import re
from typing import Any

from common_2077 import normalize

_GREET = [
    r"^(سلام|درود|هی|های|hello|hi|hey)\b",
    r"(چطوری|خوبی|حالت چطوره|how are you)",
    r"^(ممنون|مرسی|تشکر|thanks|thank you)$",
]
_DRUG_Q = [
    r"(دارو|قرص|کپسول|شیاف|آمپول|دوز|عوارض|تداخل)",
    r"(drug|pill|tablet|dosage|side effect|interaction)",
    r"(ایبوپروفن|استامینوفن|آسپرین|پنی‌سیلین|آموکسی|متفرمین|وارفارین|سرترالین|امپرازول|ibuprofen|paracetamol|aspirin|metformin|warfarin)",
]
_DISEASE_Q = [
    r"(بیماری|عوارض|نشانه‌های|علائم).*(چیه|چیست|بگو|توضیح|what|explain)",
    r"(دیابت|فشار خون|سرطان|آسم|کرونا|پارکینسون|آلزایمر|اگزما|پسوریازیس|میگرن|آرتروز|هپاتیت|مالاریا|سل|واریس|diabetes|cancer|asthma|migraine)",
    r"(چیه|چیست|چی هست).*$",
]
_ADVICE_Q = [
    r"(چیکار|چه کنم|چکار|توصیه|درمان|بهترین راه|راه حل|what should|how to|treatment|remedy)",
    r"(خسته|خستگی|بی‌حال|tired|fatigue)",
    r"(ویتامین|چقدر بخورم|دوز|vitamin|dose|dosage)",
]
_SYMP = [
    r"(درد|سردرد|دل‌درد|دل درد|تب|سرفه|خارش|تورم|سرگیجه|تهوع|استفراغ|اسهال|یبوست|تنگی|سوزش|خستگی|بی‌خوابی|ضعف|کرختی|بی‌حسی|pain|fever|cough|itch|swell|dizzy|nausea)",
    r"(دارم|هستم|شدم|احساس|گرفتم)",
]


def _hit(text: str, patterns: list[str]) -> bool:
    low = text.lower().strip()
    for p in patterns:
        if re.search(p, low, re.I):
            return True
    return False


def classify(message: str) -> str:
    """Return one of: greeting, drug_question, disease_question,
    advice_question, symptom_report, other."""
    m = (message or "").strip()
    if not m:
        return "other"
    n = normalize(m)
    if _hit(m, _GREET):
        return "greeting"
    if _hit(m, _DRUG_Q):
        return "drug_question"
    if _hit(m, _DISEASE_Q):
        return "disease_question"
    if _hit(m, _ADVICE_Q):
        return "advice_question"
    if _hit(m, _SYMP):
        return "symptom_report"
    return "other"
