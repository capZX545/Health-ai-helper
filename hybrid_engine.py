# -*- coding: utf-8 -*-
"""
The main brain: external AI + offline engine + auto-learning, wired together.
Flow:
  1) red flag check -> instant emergency answer, stop normal assessment
  2) try external AI (OpenRouter -> OpenAI -> DeepSeek -> local Ollama)
  3) on success: auto-learn (even if the offline brain is switched off)
  4) otherwise: offline brain answers, styled like the external AI it learned from
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
    """
    One instance per session (desktop or web).
    """

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
             image_note: str = "", image_hint: str | None = None, lang: str | None = None) -> dict[str, Any]:
        with _lock:
            return self._chat_inner(user_text, image_b64, image_mime, image_note, image_hint, lang)

    def _chat_inner(self, user_text: str, image_b64, image_mime, image_note, image_hint=None, lang=None) -> dict[str, Any]:
        user_text = (user_text or "")[:8000]
        # answer language: explicit choice > detected from the message > settings
        import i18n as _i18n
        if lang not in ("en", "fa"):
            letters = [c for c in (user_text or "") + (image_note or "") if c.isalpha()]
            fa_ratio = sum(1 for c in letters if "\u0600" <= c <= "\u06ff") / max(len(letters), 1)
            lang = "fa" if fa_ratio > 0.15 else _i18n.get_lang()
        _i18n.set_override(lang)
        try:
            return self._chat_body(user_text, image_b64, image_mime, image_note, image_hint)
        finally:
            _i18n.set_override(None)

    def _chat_body(self, user_text: str, image_b64, image_mime, image_note, image_hint=None) -> dict[str, Any]:
        from patient_profile import load_profile
        profile = load_profile()
        # with an image, red flags are checked against the text + image note
        red_flag_text = (user_text + " " + (image_note or "")).strip() if image_b64 else user_text
        analysis = analyze(red_flag_text, profile)

        # 1) red flags -> instant emergency answer, normal assessment stops →
        if analysis["red_flag"]:
            self._remember("user", user_text)
            reply = emergency_response(analysis["red_flag_reasons"])
            self._remember("assistant", reply)
            return {"ok": True, "text": reply, "source": "internal-emergency",
                    "red_flag": True, "reasons": analysis["red_flag_reasons"], "learned": False}

        # 1.5) intent routing: knowledge questions answered from local banks
        if not image_b64 and not analysis.get("red_flag"):
            try:
                from intent_router import classify
                from knowledge_answer import (answer_greeting, answer_drug_question,
                                              answer_disease_question, answer_advice_question)
                # priority: QA > lab > lifestyle > specific intent
                # (advice/lifestyle questions often contain disease words too)
                _ans = None
                from medical_qa import answer_from_qa
                from lab_answer import answer_lab_question, answer_lifestyle_question
                _ans = answer_from_qa(user_text)
                if not _ans:
                    _ans = answer_lab_question(user_text)
                if not _ans:
                    _ans = answer_lifestyle_question(user_text)
                if not _ans:
                    intent = classify(user_text)
                    if intent == "greeting":
                        _ans = answer_greeting(user_text)
                    elif intent == "advice_question":
                        _ans = answer_advice_question(user_text)
                    elif intent == "drug_question":
                        _ans = answer_drug_question(user_text)
                    elif intent == "disease_question":
                        _ans = answer_disease_question(user_text)
                if _ans:
                    self._remember("user", user_text)
                    self._remember("assistant", _ans)
                    return {"ok": True, "text": _ans, "source": "internal-knowledge",
                            "red_flag": False, "learned": False}
            except Exception:
                pass  # fall through to normal flow

        # 2) external AI if a key exists - images go here too
        s = get_settings()
        external = None
        if image_b64:
            import base64 as _b64mod
            from image_caption import analyze_image_with_ai, offline_analysis
            from image_type_detector import classify_image
            _raw = None
            try:
                _raw = _b64mod.b64decode(image_b64.split(",")[-1])
                _type_info = classify_image(_raw, image_hint)
            except Exception:
                _type_info = {"type": "other_photo", "label": "general photo", "confidence": 0.0,
                              "user_hint": False, "quality": [], "size": "?"}
            external = analyze_image_with_ai(image_b64, image_mime, image_note or user_text, self, _type_info)
            if not external.get("ok"):
                external = offline_analysis(_type_info, image_note or user_text, _raw if isinstance(_raw, bytes) else None)
                external["source"] = "internal-image"
            else:
                external["image_type"] = _type_info
                external["source"] = f"external:{external.get('provider', '?')}"
        else:
            ext_res = self._try_external(user_text, s)
            external = ext_res
        if external and external.get("ok"):
            text = external["text"]
            self._remember("user", user_text)
            self._remember("assistant", text)
            # 3) auto-learning - only from genuinely external replies, not our own text
            learned = False
            ext_source = str(external.get("source") or f"external:{external.get('provider', '?')}")
            is_truly_external = bool(external.get("provider")) and ext_source.startswith("external")
            if not is_truly_external:
                return {"ok": True, "text": text, "source": ext_source,
                        "red_flag": False, "learned": False, "image_type": external.get("image_type")}
            try:
                from auto_learning import learn_from_exchange
                _meta = {"image": bool(image_b64)}
                if image_b64 and isinstance(external.get("image_type"), dict):
                    _meta["image_type"] = external["image_type"].get("type", "?")
                entry = learn_from_exchange(user_text or image_note, text,
                                            provider=external.get("provider", ""), model=external.get("model", ""),
                                            red_flag=False, meta=_meta)
                learned = entry is not None
            except Exception:
                pass
            self.last_source = external.get("source") or f"external:{external.get('provider', '?')}"
            return {"ok": True, "text": text, "source": self.last_source, "red_flag": False,
                    "learned": learned, "image_type": external.get("image_type")}

        # 4) offline brain
        text, info = self.internal_answer(user_text, analysis)
        self._remember("user", user_text)
        self._remember("assistant", text)
        self.last_source = "internal"
        return {"ok": True, "text": text, "source": "internal", "red_flag": False,
                "learned": False, "image_type": (external or {}).get("image_type"),
                "external_error": external.get("error_fa") if external else None, "info": info}

    def _try_external(self, user_text: str, s: dict) -> dict[str, Any] | None:
        msgs = [{"role": "system", "content": self._system_prompt({}, self._rag(user_text))}]
        msgs.extend(self.memory[-8:])
        msgs.append({"role": "user", "content": user_text})
        # local model first?
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
        return last_err  # may be None when no key is configured

    def _rag(self, query: str) -> list[dict]:
        try:
            from semantic_rag import search
            return search(query, k=4)
        except Exception:
            return []

    # -------------------------------------------------------- offline brain
    def internal_answer(self, user_text: str, analysis: dict | None = None) -> tuple[str, dict]:
        from patient_profile import load_profile
        from behavior_imitation import apply_style
        from medical_nlg import compose_offline_answer
        from medical_engine import sym_name
        profile = load_profile()
        # move the dialogue forward
        proc = self.dialogue.process(user_text)
        analysis = analysis or analyze(user_text, profile)
        # ranking uses every symptom of the whole conversation, not just the last message
        # (a UTI mentioned last turn isn't lost when the next message only says 'mild fever')
        if not analysis.get("red_flag"):
            from bayesian_engine import rank_diseases
            dlg = self.dialogue
            combined = {"present": {sid: {"count": 1,
                                          "severity": proc["detected"]["present"].get(sid, {}).get("severity", "moderate"),
                                          "denied": False}
                                    for sid in dlg.mentioned},
                        "duration_days": proc["detected"].get("duration_days") or dlg.summary()["duration_days"],
                        "temp_c": proc["detected"].get("temp_c")}
            if combined["present"]:
                try:
                    analysis["candidates"] = rank_diseases(combined, profile)
                except Exception:
                    pass
            analysis["symptoms"] = [sym_name(s) for s in dlg.mentioned]
            analysis["denied"] = [sym_name(s) for s in dlg.denied]
        cand_ids = [c["id"] for c in analysis.get("candidates", [])]
        followup = self.dialogue.next_question(cand_ids)
        # 3+ symptoms and a clear top candidate -> skip further questions
        if followup and len(self.dialogue.mentioned) >= 3:
            top_pct = (analysis.get("candidates") or [{}])[0].get("percent", 0)
            if top_pct >= 25:
                followup = None
        # nothing recorded yet -> ask a concrete screening question
        if not followup and not self.dialogue.mentioned:
            from i18n import tt
            followup = tt("To get started: where is the discomfort (head, chest, belly, skin, urinary)? Any fever? How many days has it lasted?",
                          "برای شروع: ناراحتی کجاست (سر، سینه، شکم، پوست، ادرار)؟ تب داری؟ چند روز است ادامه دارد؟")
        # optional ML signal
        ml = None
        if get_settings().get("brain_enabled"):
            try:
                from ml_classifier import predict
                ml = predict(proc["detected"], profile, None)
            except Exception:
                ml = None
        rag_hits = self._rag(user_text)
        sections = compose_offline_answer(analysis, self.dialogue.summary(), profile, ml, rag_hits, followup)
        # brain disabled -> give limited guidance only
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

    # ------------------------------------------------------------- status
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
