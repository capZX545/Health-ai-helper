# -*- coding: utf-8 -*-
"""
hybrid_engine.py — مغز اصلی: ترکیب AI خارجی + مغز داخلی آفلاین + یادگیری خودکار.
جریان:
  ۱) بررسی Red Flag → پاسخ اورژانسی فوری و توقف تشخیص معمول
  ۲) تلاش برای AI خارجی (OpenRouter → OpenAI → DeepSeek → Ollama محلی)
  ۳) در صورت موفقیت: یادگیری خودکار (حتی اگر مغز داخلی خاموش باشد)
  ۴) در صورت عدم دسترسی: پاسخ مغز داخلی با سبک آموخته‌شده از AI خارجی
"""
from __future__ import annotations

import threading
from typing import Any

from ai_api_manager import get_api_key, get_settings
from common_2077 import MEDICAL_DISCLAIMER, now_iso
from medical_engine import analyze, emergency_response

_lock = threading.RLock()

SAFETY_RULES_FA = """قوانین الزامی تو:
1. هرگز تشخیص قطعی نده؛ همیشه بگو «احتمالی».
2. اول از همه علائم خطر (درد قفسه سینه، تنگی نفس شدید، خونریزی شدید، بیهوشی، تشنج، ضعف/فلج ناگهانی، اختلال تکلم، کجی صورت، کاهش هوشیاری، تب بسیار شدید، درد شدید ناگهانی) را بررسی کن؛ اگر بود، فوراً به تماس با اورژانس (ایران ۱۱۵ / اروپا 112) توصیه کن و تشخیص معمول را متوقف کن.
3. دارو را فقط به‌صورت عمومی و با تأکید بر تجویز پزشک مطرح کن.
4. اطلاعات پزشکی جعلی/بدون منبع معتبر نساز؛ اگر مطمئن نیستی، صادقانه بگو و سوال پیگیری بپرس.
5. فارسی روان و همدلانه جواب بده؛ مرحله‌به‌مرحله؛ بدون اغراق.
6. در پایان یک یا دو سوال پیگیری برای دقیق‌ترشدن ارزیابی بپرس.
7. یادآوری کن که خروجی تو جایگزین پزشک نیست.
سبک پاسخ: بخش‌بندی با عنوان‌های کوتاه (علائم، احتمالات، مراقبت، سوال بعدی) و بولت‌پوینت‌های کوتاه."""


def _profile_line(profile: dict) -> str:
    if not profile:
        return "پروفایل بیمار: ثبت نشده."
    bits = []
    for k, fa in (("name", "نام"), ("age", "سن"), ("gender", "جنسیت"), ("weight_kg", "وزن"), ("height_cm", "قد")):
        if profile.get(k):
            bits.append(f"{fa}: {profile[k]}")
    if profile.get("conditions"):
        bits.append("بیماری زمینه‌ای: "+ str(profile["conditions"]))
    if profile.get("allergies"):
        bits.append("حساسیت: "+ str(profile["allergies"]))
    return "پروفایل بیمار — "+ ("، ".join(bits) if bits else "ثبت نشده") + "."


class HybridEngine:
    """یک نمونه برای هر جلسه (دسکتاپ یا وب)."""

    def __init__(self):
        from clinical_dialogue import ClinicalDialogue
        self.dialogue = ClinicalDialogue()
        self.memory: list[dict[str, str]] = []
        self.last_source = "internal"

    # ------------------------------------------------------------- system prompt
    def _system_prompt(self, profile: dict, rag_hits: list[dict]) -> str:
        from patient_profile import load_profile
        prof = profile or load_profile()
        dlg = self.dialogue.summary()
        rag_ctx = "\n".join(f"- ({h['source']}) {h['text'][:180]}" for h in (rag_hits or [])[:4]) or "موردی یافت نشد."
        return f"""تو «نکسوس» هستی؛ دستیار هوشمند پزشکی فارسی NexusMed 2077. مثل یک پزشک باتجربه و دلسوز صحبت کن.

{_profile_line(prof)}
وضعیت گفتگوی بالینی تا اینجا: علائم ذکرشده: {dlg['symptoms_fa']}; ردشده: {dlg['denied_fa']}; نوبت گفتگو: {dlg['turns']}.
دانش داخلی مرتبط (RAG):
{rag_ctx}

{SAFETY_RULES_FA}"""

    # ------------------------------------------------------------------ chat
    def chat(self, user_text: str, image_b64: str | None = None, image_mime: str = "image/jpeg",
             image_note: str = "") -> dict[str, Any]:
        with _lock:
            return self._chat_inner(user_text, image_b64, image_mime, image_note)

    def _chat_inner(self, user_text: str, image_b64, image_mime, image_note) -> dict[str, Any]:
        from patient_profile import load_profile
        profile = load_profile()
        analysis = analyze(user_text, profile)

        # ۱) علائم خطر → پاسخ اورژانسی فوری؛ تشخیص معمول متوقف
        if analysis["red_flag"]:
            self._remember("user", user_text)
            reply = emergency_response(analysis["red_flag_reasons"])
            self._remember("assistant", reply)
            return {"ok": True, "text": reply, "source": "internal-emergency",
                    "red_flag": True, "reasons": analysis["red_flag_reasons"], "learned": False}

        # ۲) AI خارجی (در صورت وجود کلید) — تصویر هم اینجا ارسال می‌شود
        s = get_settings()
        external = None
        if image_b64:
            from image_caption import analyze_image_with_ai
            external = analyze_image_with_ai(image_b64, image_mime, image_note or user_text, self)
        else:
            ext_res = self._try_external(user_text, s)
            external = ext_res
        if external and external.get("ok"):
            text = external["text"]
            self._remember("user", user_text)
            self._remember("assistant", text)
            # ۳) یادگیری خودکار — حتی اگر مغز داخلی خاموش باشد
            learned = False
            try:
                from auto_learning import learn_from_exchange
                entry = learn_from_exchange(user_text or image_note, text,
                                            provider=external.get("provider", ""), model=external.get("model", ""),
                                            red_flag=False, meta={"image": bool(image_b64)})
                learned = entry is not None
            except Exception:
                pass
            self.last_source = f"external:{external.get('provider', '?')}"
            return {"ok": True, "text": text, "source": self.last_source, "red_flag": False, "learned": learned}

        # ۴) مغز داخلی آفلاین
        text, info = self.internal_answer(user_text, analysis)
        self._remember("user", user_text)
        self._remember("assistant", text)
        self.last_source = "internal"
        return {"ok": True, "text": text, "source": "internal", "red_flag": False,
                "learned": False, "external_error": external.get("error_fa") if external else None, "info": info}

    def _try_external(self, user_text: str, s: dict) -> dict[str, Any] | None:
        msgs = [{"role": "system", "content": self._system_prompt({}, self._rag(user_text))}]
        msgs.extend(self.memory[-8:])
        msgs.append({"role": "user", "content": user_text})
        # اولویت محلی؟
        if s.get("local_first"):
            from local_llm import chat as local_chat, get_config
            if get_config().get("enabled"):
                r = local_chat(msgs)
                if r.get("ok"):
                    return r
        order = [p for p in s["provider_order"] if p != "local" and get_api_key(p)]
        last_err = None
        for p in order:
            from ai_client import chat as ext_chat
            kw = {"reasoning_enabled": bool(s.get("reasoning_enabled")) and p == "openrouter"}
            r = ext_chat(p, msgs, model=(s.get("openrouter_model") if p == "openrouter"else None), **kw)
            if r.get("ok"):
                return r
            last_err = r
        if s.get("local_first") is False:
            from local_llm import chat as local_chat, get_config
            if get_config().get("enabled"):
                r = local_chat(msgs)
                if r.get("ok"):
                    return r
        return last_err  # ممکن است None باشد (هیچ کلیدی تنظیم نشده)

    def _rag(self, query: str) -> list[dict]:
        try:
            from semantic_rag import search
            return search(query, k=4)
        except Exception:
            return []

    # -------------------------------------------------------- مغز داخلی
    def internal_answer(self, user_text: str, analysis: dict | None = None) -> tuple[str, dict]:
        from patient_profile import load_profile
        from behavior_imitation import apply_style
        from medical_nlg import compose_offline_answer
        profile = load_profile()
        analysis = analysis or analyze(user_text, profile)
        # گفتگو را جلو ببر
        proc = self.dialogue.process(user_text)
        cand_ids = [c["id"] for c in analysis.get("candidates", [])]
        followup = self.dialogue.next_question(cand_ids)
        # سیگنال ML (اختیاری)
        ml = None
        if get_settings().get("brain_enabled"):
            try:
                from ml_classifier import predict
                ml = predict(proc["detected"], profile, None)
            except Exception:
                ml = None
        rag_hits = self._rag(user_text)
        sections = compose_offline_answer(analysis, self.dialogue.summary(), profile, ml, rag_hits, followup)
        # اگر مغز داخلی خاموش است فقط راهنمایی محدود بده
        if not get_settings().get("brain_enabled"):
            from i18n import tt
            text = (tt("The internal brain is switched off in settings - essentials only:\n\n", "مغز داخلی در تنظیمات خاموش است — فقط موارد الزامی:\n\n")
                    + str(sections["warning"]) + "\n\n"+ str(sections["followup"])
                    + "\n\n"+ tt("(Background learning from external AI replies stays active.)", "(یادگیری پس‌زمینه از پاسخ‌های AI خارجی همچنان فعال است.)"))
            return text, {"candidates": []}
        text = apply_style(sections)
        disc = MEDICAL_DISCLAIMER()
        if disc not in text:
            text += "\n\n"+ disc
        return text, {"candidates": analysis.get("candidates", [])}

    def _remember(self, role: str, content: str):
        self.memory.append({"role": role, "content": content[:4000]})
        if len(self.memory) > 24:
            self.memory = self.memory[-24:]

    # ------------------------------------------------------------- وضعیت
    def status(self) -> dict[str, Any]:
        from ai_api_manager import has_any_external, masked_keys
        from local_llm import get_config
        try:
            from auto_learning import stats as learn_stats
            ls = learn_stats()
        except Exception:
            ls = {"entries": 0}
        return {
            "time": now_iso(),
            "external_available": has_any_external(),
            "masked_keys": masked_keys(),
            "local": get_config(),
            "learning": ls,
            "last_source": self.last_source,
            "settings": get_settings(),
        }
