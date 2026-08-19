# -*- coding: utf-8 -*-
"""
clinical_dialogue.py — مکالمه‌ی بالینی قدم‌به‌قدم: پرسش هوشمند، ثبت رد/قبول علامت،
شدت و مدت، و پرهیز از تکرار جملات کلی مثل «متوجه نشدم».
"""
from __future__ import annotations

import random
from typing import Any

from medical_engine import SYMPTOM_KEYWORDS, SYMPTOM_NAMES_FA, detect_symptoms

QUESTION_BANK: dict[str, list[str]] = {
    "fever": ["تبت چقدر است و چند روز است ادامه دارد؟", "آیا تب با لرز همراه بوده؟"],
    "cough": ["سرفه‌ات خشک است یا خلط‌دار؟", "سرفه چند روز است ادامه دارد؟"],
    "sore_throat": ["گلودردت با دشواری بلع هم همراه است؟", "آیا روی لوزه‌ها لک سفید می‌بینی؟"],
    "headache": ["سردردت یک طرفه است یا کل سر؟", "آیا نور یا صدا سردردت را بدتر می‌کند؟"],
    "abdominal_pain": ["درد شکمت کجاست (بالا/پایین/راست/چپ) و آیا ناگهانی شروع شد؟", "آیا درد با غذا خوردن تغییر می‌کند؟"],
    "chest_pain": ["درد به بازو، فک یا پشت کتف تیر می‌کشد؟", "درد با فعالیت بیشتر می‌شود؟"],
    "shortness_of_breath": ["تنگی نفست در حالت استراحت هم هست یا فقط با فعالیت؟", "آیا خس‌خس سینه هم داری؟"],
    "diarrhea": ["آیا در مدفوع خون یا مخوط دیده‌ای؟", " چند بار در روز اسهال داری؟"],
    "vomiting": ["استفراغ خونی یا رنگ قهوه‌ای داشته‌ای؟", "چند بار استفراغ کردی؟"],
    "dysuria": ["آیا ادرارت بوی بد یا رنگ تیره دارد؟", "آیا درد پهلو یا تب هم داری؟"],
    "skin_itch": ["خارش در چه ناحیه‌ای است و آیا بثورات پوستی هم داری؟", "آیا اخیراً دارو یا غذای جدیدی مصرف کرده‌ای؟"],
    "rash": ["لک‌ها کجای بدن است و آیا پخش شده؟", "آیا با خارش یا تب همراه است؟"],
    "insomnia": ["مشکل در به‌خواب‌رفتن داری یا بیدار شدن‌های مکرر؟", "چند هفته است این‌طور شده؟"],
    "anxiety": ["این حالت با ضربان قلب تند یا تنگی نفس هم همراه می‌شود؟", "چه چیزی معمولاً نگرانی‌ات را تشدید می‌کند؟"],
    "mood_low": ["چند هفته است این حالت را داری؟", "آیا از کارهایی که قبلاً لذت می‌بردی الان هم لذت می‌بری؟"],
    "fatigue": ["خستگی با کم‌خوابی همراه است یا حتی با خواب کافی هم هست؟", "آیا کاهش وزن یا تشنگی زیاد هم داری؟"],
    "palpitation": ["تپش در حالت استراحت هم اتفاق می‌افتد؟", "آیا همراهش سرگیجه یا درد سینه حس کرده‌ای؟"],
    "heartburn": ["سوزش بعد از غذا یا خوابیدن بدتر می‌شود؟", "آیا ترش می‌کنی؟"],
    "urinary_frequency": ["شبها هم چند بار بیدار می‌شوی؟", "آیا تشنگی زیاد هم داری؟"],
    "snoring": ["آیا کسی گفته در خواب نفست قطع می‌شود؟", "روزها خواب‌آلوده‌ای؟"],
    "flank_pain": ["درد پهلو به سمت زیر شکم تیر می‌کشد؟", "آیا تب یا تهوع هم داری؟"],
    "joint_pain": ["کدام مفاصل درد می‌کند و آیا صبح‌ها سفتی دارید؟"],
    "back_pain": ["آیا درد به پا تیر می‌کشد یا بی‌حسی وجود دارد؟", "آیا تب یا کاهش وزن هم داری؟"],
    "dizziness": ["سرگیجه با چرخش محیط است یا حالت غش؟", "آیا با تغییر وضعیت سر بدتر می‌شود؟"],
    "nausea": ["حالت تهوع با غذای خاص بدتر می‌شود؟", "آیا بارداری ممکن است؟ (برای خانم‌ها)"],
    "weight_loss": ["کاهش وزن با اشتها همراه بوده یا بی‌اشتهایی؟", "چند کیلو در چه مدتی؟"],
    "thirst": ["آیا تکرر ادرار هم داری؟", "آیا سابقه دیابت در خانواده هست؟"],
    "blurred_vision": ["تاری دید یک چشم است یا هر دو؟ دائمی یا مقطعی؟"],
}

ACKS = ["متوجه شدم.", "دقیق توضیح دادی، ممنون.", "خب، این نکته مهمی است.", "درکت می‌کنم.", "باشه، ادامه بده."]
ACK_POOL: list[str] = []

MAX_QUESTIONS_PER_SYMPTOM = 1


class ClinicalDialogue:
    """حالت گفتگوی بالینی برای یک جلسه."""

    def __init__(self):
        self.history: list[dict[str, Any]] = []
        self.asked: dict[str, int] = {}
        self.mentioned: set[str] = set()
        self.denied: set[str] = set()
        self.turn = 0

    def _ack(self) -> str:
        global ACK_POOL
        if not ACK_POOL:
            ACK_POOL = ACKS * 3
            random.shuffle(ACK_POOL)
        return ACK_POOL.pop() if ACK_POOL else "متوجه شدم."

    def process(self, user_text: str) -> dict[str, Any]:
        """به‌روزرسانی وضعیت با پیام جدید کاربر."""
        self.turn += 1
        det = detect_symptoms(user_text)
        new_mentions, new_denials = [], []
        for sid, info in det["present"].items():
            if info.get("denied"):
                if sid not in self.denied and sid not in self.mentioned:
                    new_denials.append(sid)
                self.denied.add(sid)
                self.mentioned.discard(sid)
            else:
                if sid not in self.mentioned:
                    new_mentions.append(sid)
                self.mentioned.add(sid)
            self.denied.discard(sid) if not info.get("denied") else None
        self.history.append({
            "turn": self.turn, "text": user_text[:500], "new_mentions": new_mentions,
            "new_denials": new_denials, "duration_days": det.get("duration_days"),
            "temp_c": det.get("temp_c"),
        })
        return {"detected": det, "new_mentions": new_mentions, "new_denials": new_denials}

    def next_question(self, candidate_ids: list[str] | None = None) -> str | None:
        """انتخاب بعدی‌ترین پرسش مفید: علامت تاییدنشده‌ی کاندیدها یا علامت جدید ذکرنشده."""
        from medical_engine import DISEASES
        prio: list[str] = []
        if candidate_ids:
            byid = {d["id"]: d for d in DISEASES}
            for cid in candidate_ids[:3]:
                d = byid.get(cid)
                if d:
                    prio.extend([s for s in d["symptoms"] if s in QUESTION_BANK])
        for sid in prio:
            if sid not in self.mentioned and sid not in self.denied and self.asked.get(sid, 0) < MAX_QUESTIONS_PER_SYMPTOM:
                self.asked[sid] = self.asked.get(sid, 0) + 1
                return random.choice(QUESTION_BANK[sid])
        for sid in QUESTION_BANK:
            if sid in self.mentioned and self.asked.get(sid, 0) < MAX_QUESTIONS_PER_SYMPTOM:
                self.asked[sid] = self.asked.get(sid, 0) + 1
                return random.choice(QUESTION_BANK[sid])
        return None

    def summary(self) -> dict[str, Any]:
        return {
            "turns": self.turn,
            "symptoms_fa": sorted(SYMPTOM_NAMES_FA.get(s, s) for s in self.mentioned),
            "denied_fa": sorted(SYMPTOM_NAMES_FA.get(s, s) for s in self.denied),
            "duration_days": next((h["duration_days"] for h in reversed(self.history) if h["duration_days"]), None),
            "last_temp": next((h["temp_c"] for h in reversed(self.history) if h["temp_c"]), None),
        }

    def reset(self):
        self.__init__()


def answer_ack(user_text: str, state: ClinicalDialogue) -> str:
    """پاسخ کوتاه برای جواب‌های بله/خیر/توضیح کاربر به پرسش قبلی."""
    proc = state.process(user_text)
    parts = []
    if proc["new_mentions"]:
        parts.append(state._ack() + " «" + "، ".join(SYMPTOM_NAMES_FA.get(s, s) for s in proc["new_mentions"]) + "» را ثبت کردم.")
    if proc["new_denials"]:
        parts.append("خب، «" + "، ".join(SYMPTOM_NAMES_FA.get(s, s) for s in proc["new_denials"]) + "» را رد می‌کنیم.")
    if not parts:
        parts.append(state._ack())
    return " ".join(parts)
