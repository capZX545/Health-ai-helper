"""
clinical_dialogue.py — step-by-step clinical dialogue: asks one useful question
at a time, records confirmed/denied symptoms, severity and duration, and avoids
repeating generic phrases like "I didn't understand".
"""
from __future__ import annotations

import random
from typing import Any

from medical_engine import detect_symptoms, sym_name

QUESTION_BANK: dict[str, dict[str, list[str]]] = {
    "fever": {"fa": ["تبت چقدر است و چند روز است ادامه دارد؟", "آیا تب با لرز همراه بوده؟"],
              "en": ["How high is the fever and how many days has it lasted?", "Has the fever come with chills?"]},
    "cough": {"fa": ["سرفه‌ات خشک است یا خلط‌دار؟", "سرفه چند روز است ادامه دارد؟"],
              "en": ["Is the cough dry or with phlegm?", "How many days have you been coughing?"]},
    "sore_throat": {"fa": ["گلودردت با دشواری بلع هم همراه است؟", "آیا روی لوزه‌ها لک سفید می‌بینی؟"],
                    "en": ["Is it painful to swallow too?", "Do you see white patches on your tonsils?"]},
    "headache": {"fa": ["سردردت یک طرفه است یا کل سر؟", "آیا نور یا صدا سردردت را بدتر می‌کند؟"],
                 "en": ["Is the headache on one side or all over?", "Does light or noise make it worse?"]},
    "abdominal_pain": {"fa": ["درد شکمت کجاست (بالا/پایین/راست/چپ) و آیا ناگهانی شروع شد؟", "آیا درد با غذا خوردن تغییر می‌کند؟"],
                       "en": ["Where is the pain (upper/lower/right/left) and did it start suddenly?", "Does eating change the pain?"]},
    "chest_pain": {"fa": ["درد به بازو، فک یا پشت کتف تیر می‌کشد؟", "درد با فعالیت بیشتر می‌شود؟"],
                   "en": ["Does the pain radiate to your arm, jaw or back?", "Does it get worse with activity?"]},
    "shortness_of_breath": {"fa": ["تنگی نفست در حالت استراحت هم هست یا فقط با فعالیت؟", "آیا خس‌خس سینه هم داری؟"],
                            "en": ["Are you breathless at rest or only on exertion?", "Any wheezing as well?"]},
    "diarrhea": {"fa": ["آیا در مدفوع خون یا مخوط دیده‌ای؟", "چند بار در روز اسهال داری؟"],
                 "en": ["Have you seen blood or mucus in the stool?", "How many bowel movements a day?"]},
    "vomiting": {"fa": ["استفراغ خونی یا رنگ قهوه‌ای داشته‌ای؟", "چند بار استفراغ کردی؟"],
                 "en": ["Was there blood or coffee-ground material in the vomit?", "How many times have you vomited?"]},
    "dysuria": {"fa": ["آیا ادرارت بوی بد یا رنگ تیره دارد؟", "آیا درد پهلو یا تب هم داری؟"],
                "en": ["Is the urine dark or foul-smelling?", "Any flank pain or fever as well?"]},
    "skin_itch": {"fa": ["خارش در چه ناحیه‌ای است و آیا بثورات پوستی هم داری؟", "آیا اخیراً دارو یا غذای جدیدی مصرف کرده‌ای؟"],
                  "en": ["Where is the itching, and is there a visible rash?", "Any new medication or food recently?"]},
    "rash": {"fa": ["لک‌ها کجای بدن است و آیا پخش شده؟", "آیا با خارش یا تب همراه است؟"],
             "en": ["Where is the rash and is it spreading?", "Is it itchy, or with fever?"]},
    "insomnia": {"fa": ["مشکل در به‌خواب‌رفتن داری یا بیدار شدن‌های مکرر؟", "چند هفته است این‌طور شده؟"],
                 "en": ["Trouble falling asleep or staying asleep?", "How many weeks has this been going on?"]},
    "anxiety": {"fa": ["این حالت با ضربان قلب تند یا تنگی نفس هم همراه می‌شود؟", "چه چیزی معمولاً نگرانی‌ات را تشدید می‌کند؟"],
                "en": ["Does it come with a racing heart or shortness of breath?", "What usually makes it worse?"]},
    "mood_low": {"fa": ["چند هفته است این حالت را داری؟", "آیا از کارهایی که قبلاً لذت می‌بردی الان هم لذت می‌بری؟"],
                 "en": ["How many weeks have you felt this way?", "Do you still enjoy things you used to enjoy?"]},
    "fatigue": {"fa": ["خستگی با کم‌خوابی همراه است یا حتی با خواب کافی هم هست؟", "آیا کاهش وزن یا تشنگی زیاد هم داری؟"],
                "en": ["Is the fatigue from poor sleep, or present even after full nights?", "Any weight loss or unusual thirst too?"]},
    "palpitation": {"fa": ["تپش در حالت استراحت هم اتفاق می‌افتد؟", "آیا همراهش سرگیجه یا درد سینه حس کرده‌ای؟"],
                    "en": ["Do palpitations happen at rest too?", "Any dizziness or chest pain with them?"]},
    "heartburn": {"fa": ["سوزش بعد از غذا یا خوابیدن بدتر می‌شود؟", "آیا ترش می‌کنی؟"],
                  "en": ["Worse after meals or lying down?", "Any sour reflux?"]},
    "urinary_frequency": {"fa": ["شب‌ها هم چند بار بیدار می‌شوی؟", "آیا تشنگی زیاد هم داری؟"],
                          "en": ["How many times a night do you wake to urinate?", "Are you unusually thirsty too?"]},
    "snoring": {"fa": ["آیا کسی گفته در خواب نفست قطع می‌شود؟", "روزها خواب‌آلوده‌ای؟"],
                "en": ["Has anyone said your breathing stops in your sleep?", "Are you sleepy during the day?"]},
    "flank_pain": {"fa": ["درد پهلو به سمت زیر شکم تیر می‌کشد؟", "آیا تب یا تهوع هم داری؟"],
                   "en": ["Does the pain radiate toward the lower abdomen?", "Any fever or nausea with it?"]},
    "joint_pain": {"fa": ["کدام مفاصل درد می‌کند و آیا صبح‌ها سفتی دارید؟"],
                   "en": ["Which joints hurt, and are they stiff in the morning?"]},
    "back_pain": {"fa": ["آیا درد به پا تیر می‌کشد یا بی‌حسی وجود دارد؟", "آیا تب یا کاهش وزن هم داری؟"],
                  "en": ["Does the pain shoot down a leg, or any numbness?", "Any fever or weight loss too?"]},
    "dizziness": {"fa": ["سرگیجه با چرخش محیط است یا حالت غش؟", "آیا با تغییر وضعیت سر بدتر می‌شود؟"],
                  "en": ["Is it a spinning feeling, or near-fainting?", "Worse with head position changes?"]},
    "nausea": {"fa": ["حالت تهوع با غذای خاص بدتر می‌شود؟", "آیا بارداری ممکن است؟ (برای خانم‌ها)"],
               "en": ["Do specific foods make it worse?", "Could pregnancy be possible?"]},
    "weight_loss": {"fa": ["کاهش وزن با اشتها همراه بوده یا بی‌اشتهایی؟", "چند کیلو در چه مدتی؟"],
                    "en": ["Was appetite normal or reduced?", "How many kilos over what time?"]},
    "thirst": {"fa": ["آیا تکرر ادرار هم داری؟", "آیا سابقه دیابت در خانواده هست؟"],
               "en": ["Are you urinating often too?", "Any family history of diabetes?"]},
    "blurred_vision": {"fa": ["تاری دید یک چشم است یا هر دو؟ دائمی یا مقطعی؟"],
                       "en": ["One eye or both? Constant or intermittent?"]},
}

ACKS_FA = ["متوجه شدم.", "دقیق توضیح دادی، ممنون.", "خب، این نکته مهمی است.", "درکت می‌کنم.", "باشه، ادامه بده."]
ACKS_EN = ["Got it.", "Thanks, that's helpful detail.", "Okay, that matters.", "I understand.", "Alright, go on."]
ACK_POOL: list[str] = []

MAX_QUESTIONS_PER_SYMPTOM = 1


class ClinicalDialogue:
    """Dialogue state for one session."""

    def __init__(self):
        self.history: list[dict[str, Any]] = []
        self.asked: dict[str, int] = {}
        self.mentioned: set[str] = set()
        self.denied: set[str] = set()
        self.turn = 0

    def _ack(self) -> str:
        from i18n import is_fa
        global ACK_POOL
        if not ACK_POOL:
            ACK_POOL = (ACKS_FA if is_fa() else ACKS_EN) * 3
            random.shuffle(ACK_POOL)
        return ACK_POOL.pop() if ACK_POOL else ("متوجه شدم." if is_fa() else "Got it.")

    def process(self, user_text: str) -> dict[str, Any]:
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
                self.denied.discard(sid)
        self.history.append({
            "turn": self.turn, "text": user_text[:500], "new_mentions": new_mentions,
            "new_denials": new_denials, "duration_days": det.get("duration_days"),
            "temp_c": det.get("temp_c"),
        })
        return {"detected": det, "new_mentions": new_mentions, "new_denials": new_denials}

    def next_question(self, candidate_ids: list[str] | None = None) -> str | None:
        """Pick the next most useful question: an unconfirmed symptom of the top
        candidates, or an under-asked mentioned symptom."""
        from i18n import is_fa
        lang = "fa" if is_fa() else "en"
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
                return random.choice(QUESTION_BANK[sid][lang])
        for sid in QUESTION_BANK:
            if sid in self.mentioned and self.asked.get(sid, 0) < MAX_QUESTIONS_PER_SYMPTOM:
                self.asked[sid] = self.asked.get(sid, 0) + 1
                return random.choice(QUESTION_BANK[sid][lang])
        return None

    def summary(self) -> dict[str, Any]:
        return {
            "turns": self.turn,
            "symptoms": sorted(sym_name(s) for s in self.mentioned),
            "denied": sorted(sym_name(s) for s in self.denied),
            "symptoms_fa": sorted(sym_name(s) for s in self.mentioned),
            "denied_fa": sorted(sym_name(s) for s in self.denied),
            "duration_days": next((h["duration_days"] for h in reversed(self.history) if h["duration_days"]), None),
            "last_temp": next((h["temp_c"] for h in reversed(self.history) if h["temp_c"]), None),
        }

    def reset(self):
        self.__init__()


def answer_ack(user_text: str, state: ClinicalDialogue) -> str:
    """Short acknowledgment for yes/no/short answers to the previous question."""
    from i18n import is_fa
    proc = state.process(user_text)
    parts = []
    if proc["new_mentions"]:
        m = "، ".join(sym_name(s) for s in proc["new_mentions"]) if is_fa() else ", ".join(sym_name(s) for s in proc["new_mentions"])
        parts.append(state._ack() + ((" «" + m + "» را ثبت کردم.") if is_fa() else (f" Noted: {m}.")))
    if proc["new_denials"]:
        m = "، ".join(sym_name(s) for s in proc["new_denials"]) if is_fa() else ", ".join(sym_name(s) for s in proc["new_denials"])
        parts.append(("خب، «" + m + "» را رد می‌کنیم.") if is_fa() else f"Okay, we'll cross off {m}.")
    if not parts:
        parts.append(state._ack())
    return " ".join(parts)
