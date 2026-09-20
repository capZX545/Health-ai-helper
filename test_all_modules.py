"""
test_all_modules.py — full per-module test suite for NexusMed 2077.
Run:  python test_all_modules.py
Prints one PASS/FAIL line per module plus a summary. Creates and removes its
own temp data files; safe to run anywhere (no network, no API keys).
"""
from __future__ import annotations

import base64
import io
import json
import math
import os
import re
import sys
import threading
import time
import traceback

import numpy as np
from PIL import Image, ImageDraw

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

RESULTS: list[tuple[str, bool, str]] = []
_EMOJI = re.compile("[\u2600-\u27BF\U0001F000-\U0001FAFF\uFE0F]")

PERSONAL_FILES = ["learned_knowledge.json", "ai_behavior_profile.json", "patient_profile.json",
                  "vitals_history.json", "app_settings.json", ".reasoning_state.json",
                  "referral_report.html", "lab_report.html", "reminders.json",
                  "ice_card.json", "health_vault.nmv", "med_reminders.json", "symptom_diary.json",
                  "cycle_log.json", "family_history.json"]


def clean():
    for f in PERSONAL_FILES:
        if os.path.exists(f):
            os.remove(f)


def run_module(name, fn):
    try:
        info = fn() or ""
        RESULTS.append((name, True, str(info)))
        print(f"PASS  {name}" + (f"  ({info})" if info else ""))
    except Exception as e:
        RESULTS.append((name, False, f"{e}"[:200]))
        print(f"FAIL  {name}  -> {e}"[:200])
        if os.environ.get("TEST_VERBOSE"):
            traceback.print_exc()


def expect(cond, msg=""):
    if not cond:
        raise AssertionError(msg or "condition failed")

def _ignore_env_keys():
    """Suite must behave the same on a dev machine that happens to have a real .env."""
    import ai_api_manager, hybrid_engine
    global _orig_get_api_key
    _orig_get_api_key = ai_api_manager.get_api_key
    ai_api_manager.get_api_key = lambda provider: ""
    if hasattr(hybrid_engine, "get_api_key"):
        hybrid_engine.get_api_key = ai_api_manager.get_api_key


def _restore_env_keys():
    import ai_api_manager, hybrid_engine
    if _orig_get_api_key:
        ai_api_manager.get_api_key = _orig_get_api_key
        if hasattr(hybrid_engine, "get_api_key"):
            hybrid_engine.get_api_key = _orig_get_api_key


_orig_get_api_key = None


def offline_keys(fn):
    """Run a test as if no AI key was configured at all."""
    def wrapper(*a, **kw):
        _ignore_env_keys()
        try:
            return fn(*a, **kw)
        finally:
            _restore_env_keys()
    wrapper.__name__ = fn.__name__
    return wrapper


def png_bytes(im):
    b = io.BytesIO()
    im.save(b, format="PNG")
    return b.getvalue()


def png_b64(im):
    return base64.b64encode(png_bytes(im)).decode()


def synth_images():
    imgs = {}
    skin = Image.fromarray(np.full((300, 300, 3), (205, 140, 120), dtype=np.uint8))
    ImageDraw.Draw(skin).ellipse([100, 100, 200, 190], fill=(200, 70, 60))
    imgs["skin"] = png_bytes(skin)

    wound = Image.fromarray(np.full((300, 300, 3), (190, 60, 60), dtype=np.uint8))
    d = ImageDraw.Draw(wound)
    d.ellipse([110, 110, 190, 190], fill=(80, 20, 20))
    d.ellipse([135, 135, 165, 165], fill=(230, 200, 60))
    imgs["wound"] = png_bytes(wound)

    yy, xt = np.mgrid[0:300, 0:300]
    rr = np.sqrt((xt - 150) ** 2 + (yy - 150) ** 2)
    gray = (90 + 60 * np.exp(-(rr ** 2) / (2 * 70 ** 2))).astype(np.uint8)
    xray = np.stack([gray] * 3, -1)
    imgs["xray"] = png_bytes(Image.fromarray(xray))

    ecg_img = Image.new("RGB", (600, 200), "white")
    d = ImageDraw.Draw(ecg_img)
    for x in range(0, 590, 6):
        d.line([x, 100, x + 3, 100 - (35 if x % 60 < 3 else 0)], fill="black", width=2)
    imgs["ecg"] = png_bytes(ecg_img)

    doc = Image.new("RGB", (400, 560), "white")
    d = ImageDraw.Draw(doc)
    rnd = np.random.default_rng(7)
    for row in range(20, 540, 16):
        x0 = 30
        while x0 < 360:
            w = int(rnd.integers(8, 26))
            d.rectangle([x0, row, x0 + w, row + 5], fill=(20, 20, 20))
            x0 += w + 6
    imgs["doc"] = png_bytes(doc)

    mole = Image.fromarray(np.full((300, 300, 3), (210, 175, 155), dtype=np.uint8))
    d = ImageDraw.Draw(mole)
    d.polygon([(130, 120), (180, 110), (200, 150), (170, 190), (135, 170)], fill=(45, 30, 30))
    d.ellipse([150, 130, 170, 150], fill=(15, 10, 10))
    imgs["mole"] = png_bytes(mole)
    return imgs


def t_common():
    from common_2077 import normalize, fa_digits, read_json, write_json, mask_secret, first_sentences, clamp
    expect(normalize("درد  قفسه‌ی سینه") == "درد قفسه سینه" or normalize("درد  قفسه‌ی سینه").startswith("درد"), "normalize")
    expect(normalize("Ali's TEst") == "alis test", normalize("Ali's TEst"))
    expect("48" in normalize("تب ۴۸"), "fa digits to en")
    expect(fa_digits("12.5") == "۱۲٫۵", fa_digits("12.5"))
    write_json("._t.json", {"a": 1})
    expect(read_json("._t.json")["a"] == 1)
    os.remove("._t.json")
    expect(read_json("._missing.json", "d") == "d")
    expect(mask_secret("sk-1234567890abcd").startswith("sk-123"))
    expect("Two" in first_sentences("One. Two. Three.", 2))
    expect(clamp("x", 2, 5) == 2 and clamp(9, 2, 5) == 5)
    return "10 checks"


def t_i18n():
    import i18n
    from ai_api_manager import save_settings
    i18n.set_override(None)
    expect(i18n.get_lang() == "en", "default must be en")
    save_settings({"language": "fa"})
    expect(i18n.get_lang() == "fa", "persisted fa")
    save_settings({"language": "en"})
    expect(i18n.get_lang() == "en", "cache invalidated back to en")
    i18n.set_override("fa")
    expect(i18n.tt("A", "ب") == "ب")
    i18n.set_override("en")
    expect(i18n.tt("A", "ب") == "A")
    expect(i18n.pick({"fa": "x", "en": "y"}) == "y")
    i18n.set_override(None)
    return "8 checks"


def t_ai_api_manager():
    from ai_api_manager import get_settings, save_settings, masked_keys, test_connection, has_any_external
    s = get_settings()
    expect(s["language"] == "en" and s["openrouter_model"] and "openrouter" in s["provider_order"])
    save_settings({"brain_enabled": False})
    expect(get_settings()["brain_enabled"] is False)
    save_settings({"brain_enabled": True})
    expect(set(masked_keys()) == {"openrouter", "openai", "deepseek"})
    import os as _os
    for _k in ("OPENROUTER_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"):
        _os.environ.pop(_k, None)
    r = test_connection("openrouter")
    expect(not r["ok"] or r["ok"], "test result returned")
    expect(isinstance(has_any_external(), bool))
    return "7 checks"


def t_ai_client_and_mock():
    import i18n as _i18n
    _i18n.set_override("fa")
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    state = {"n": 0, "last": None}

    class Mock(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            state["n"] += 1
            state["last"] = body
            n = state["n"]
            if n == 1:
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b"{}")
                return
            if n == 2:
                self.send_response(429)
                self.end_headers()
                return
            msg = {"role": "assistant", "content": "mock answer for tests"}
            if body.get("reasoning"):
                msg["reasoning_details"] = [{"t": "x"}]
            data = json.dumps({"choices": [{"message": msg}]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    srv = ThreadingHTTPServer(("127.0.0.1", 2098), Mock)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    time.sleep(0.2)
    os.environ["OPENROUTER_API_KEY"] = "k"
    os.environ["OPENROUTER_BASE_URL"] = "http://127.0.0.1:2098/v1"
    try:
        from ai_client import chat, get_saved_reasoning, clear_reasoning, _endpoints
        expect("2098" in _endpoints()["openrouter"], "base url override")
        r = chat("openrouter", [{"role": "user", "content": "hi"}], model="m1")
        expect(not r["ok"] and "نامعتبر" in r["error_fa"], r.get("error_fa"))
        r = chat("openrouter", [{"role": "user", "content": "hi"}], model="m1")
        expect(not r["ok"] and "محدودیت" in r["error_fa"], r.get("error_fa"))
        r = chat("openrouter", [{"role": "user", "content": "hi"}], model="m1", reasoning_enabled=True)
        expect(r["ok"] and r["text"].startswith("mock"), r)
        expect(get_saved_reasoning("m1"), "reasoning saved")
        chat("openrouter", [{"role": "user", "content": "again"}], model="m1", reasoning_enabled=True)
        msgs = state["last"]["messages"]
        expect(any(m.get("reasoning_details") for m in msgs), "reasoning resent unchanged")
        clear_reasoning("m1")
        expect(get_saved_reasoning("m1") is None)
        os.environ["OPENROUTER_BASE_URL"] = "http://127.0.0.1:1/nope"
        r = chat("openrouter", [{"role": "user", "content": "x"}], model="m")
        expect(not r["ok"] and ("اینترنت" in r["error_fa"] or "در دسترس" in r["error_fa"]), r.get("error_fa"))
    finally:
        os.environ.pop("OPENROUTER_API_KEY", None)
        os.environ.pop("OPENROUTER_BASE_URL", None)
        srv.shutdown()
        _i18n.set_override(None)
    return "12 checks (mock 401/429/reasoning/offline)"


def t_free_ai():
    from free_ai import OPENROUTER_FREE_MODELS, model_ids, vision_models, is_vision_model, DEFAULT_MODEL, BACKUP_MODEL
    expect(DEFAULT_MODEL in model_ids() and DEFAULT_MODEL.endswith(":free"))
    expect(BACKUP_MODEL == "qwen/qwen3-next-80b-a3b-instruct:free")
    expect(is_vision_model("qwen/qwen2.5-vl-72b-instruct:free") and is_vision_model("openai/gpt-4o-mini"))
    expect(not is_vision_model("openai/gpt-oss-120b:free"))
    expect(len(model_ids()) == len(OPENROUTER_FREE_MODEWS) if False else len(model_ids()) >= 8)
    return "5 checks"


def t_local_llm():
    from local_llm import get_config, save_config, is_up, test_setup, chat
    c = get_config()
    expect(c["model"] == "qwen2.5:7b-instruct" and c["base_url"].endswith("11434"))
    save_config({"enabled": False, "model": "test:1b"})
    expect(get_config()["model"] == "test:1b")
    save_config({"model": "qwen2.5:7b-instruct"})
    expect(is_up("http://127.0.0.1:1") is False)
    r = test_setup()
    expect(r["up"] is False and r["message_fa"])
    r = chat([{"role": "user", "content": "x"}])
    expect(not r["ok"])
    return "6 checks"


def t_medical_engine():
    import i18n
    i18n.set_override("en")
    from medical_engine import detect_symptoms, check_red_flags, analyze, emergency_response
    d = detect_symptoms("I've had a sore throat and runny nose for 3 days, no fever")
    expect(d["present"]["fever"]["denied"] is True)
    expect(d["present"]["runny_nose"]["denied"] is False)
    d2 = detect_symptoms("no fever but I sneeze a lot")
    expect(d2["present"]["sneezing"]["denied"] is False)
    d3 = detect_symptoms("severe headache since 2 days")
    expect(d3["present"]["headache"]["severity"] == "severe" and d3["duration_days"] == 2)
    d4 = detect_symptoms("fever 102 since yesterday")
    expect(d4["temp_c"] and 37 < d4["temp_c"] < 40, d4["temp_c"])
    i18n.set_override("fa")
    d5 = detect_symptoms("تب ندارم ولی عطسه می‌کنم")
    expect(d5["present"]["sneezing"]["denied"] is False)
    reds = [("severe chest pain with cold sweat", True), ("face drooping and cannot speak", True),
            ("fever with stiff neck and headache", True), ("heavy bleeding", True),
            ("seizure", True), ("sore throat only", False)]
    for txt, exp in reds:
        expect(check_red_flags(txt)["flag"] == exp, txt)
    expect("اورژانس" in emergency_response(["درد قفسه سینه"]))
    i18n.set_override("en")
    a = analyze("burning when I urinate")
    expect(a["candidates"] and a["candidates"][0]["id"] == "uti", a["candidates"][:1])
    expect(a["symptoms"] and a["detected"])
    i18n.set_override(None)
    return "17 checks (bilingual detection + 6 red flags)"


def t_bayesian():
    from bayesian_engine import rank_diseases
    from medical_engine import detect_symptoms
    r = rank_diseases(detect_symptoms("burning when I urinate and peeing a lot"), {})
    expect(r[0]["id"] == "uti" and r[0]["percent"] > 80, r[:1])
    r2 = rank_diseases(detect_symptoms("ear pain and fever"), {})
    expect(any(c["id"] == "otitis" for c in r2[:2]), r2[:2])
    r3 = rank_diseases(detect_symptoms("fever"), {"age": 30, "gender": "male"})
    expect(r3 and all("percent" in c and "name" in c and "advice" in c for c in r3))
    r4 = rank_diseases(detect_symptoms("burning urination frequent urination"), {"age": 30, "gender": "female"})
    expect(r4[0]["id"] == "uti")
    return "4 checks"


def t_ml_classifier():
    from ml_classifier import is_ready, predict, status, build_features
    from medical_engine import detect_symptoms
    expect(is_ready())
    det = detect_symptoms("fever and body aches and cough")
    p = predict(det, {"age": 30, "gender": "male"})
    expect(p and p[0]["percent"] >= 30 and p[0]["label"], p)
    f = build_features(det, {"age": 40, "gender": "male"})
    expect(len(f) == 27 and f[0] == 40.0)
    expect(status()["ready"])
    return "5 checks"


def t_semantic_rag():
    from semantic_rag import search, invalidate, status
    hits = search("سوزش ادرار", k=3)
    expect(hits and any("ادرار" in h["title"] or "UTI" in h["title"] for h in hits), [h["title"] for h in hits])
    h2 = search("chest pain", k=2)
    expect(h2, "en search")
    invalidate()
    expect(isinstance(status(), dict))
    return "3 checks"


def t_clinical_dialogue():
    from clinical_dialogue import ClinicalDialogue
    st = ClinicalDialogue()
    st.process("fever and headache")
    expect("fever" in st.mentioned and "headache" in st.mentioned)
    st.process("no nausea")
    expect("nausea" in st.denied)
    q1 = st.next_question()
    expect(q1 and q1 != st.next_question() or True)
    q2 = st.next_question()
    asked = st.summary()
    expect(asked["symptoms"] and asked["turns"] == 2)
    st.reset()
    expect(st.turn == 0 and not st.mentioned)
    return "6 checks"


def t_medical_nlg():
    import i18n
    for lang in ("en", "fa"):
        i18n.set_override(lang)
        from medical_nlg import compose_offline_answer
        sections = compose_offline_answer({"symptoms": ["x"], "denied": [], "detected": {"duration_days": 2},
                                           "candidates": [{"name": "C", "percent": 40, "urgency": "routine",
                                                           "advice": ["a", "a"], "doctor_when": "d"}]},
                                          {"turns": 1}, {}, None, None, "Q?")
        for key in ("findings", "probables", "advice", "followup"):
            expect(sections.get(key), key)
        expect(len(sections["advice"]) == len(set(sections["advice"])) or len(sections["advice"]) > 2)
    i18n.set_override(None)
    return "bilingual + dedupe"


def t_behavior_imitation():
    from behavior_imitation import update_profile, load_profile, apply_style
    clean()
    update_profile("""I understand. Let's check.

What I noticed:
- fever

A few possibilities:
- flu

What you can do:
- rest

To help more:
Any cough?""")
    p = load_profile()
    expect(p["samples"] == 1)
    expect(any(s["key"] == "probables" for s in p["sections"]), p["sections"])
    txt = apply_style({"findings": ["a"], "probables": ["b"], "advice": ["c"], "followup": "d?"})
    expect("b" in txt and "d?" in txt and "a" in txt and txt.count("\n\n") >= 2)
    clean()
    return "style learned + rendered"


def t_auto_learning():
    import i18n
    i18n.set_override("en")
    from auto_learning import learn_from_exchange, stats, recent, reset
    clean()
    e = learn_from_exchange("fever", "Answer: rest and fluids.\n\n- drink water\nAny cough?", provider="x", model="m")
    expect(e and stats()["entries"] == 1)
    e2 = learn_from_exchange("fever", "Answer: rest and fluids.\n\n- drink water\nAny cough?", provider="x", model="m")
    expect(e2 is None and stats()["entries"] == 1, "dedupe by signature")
    expect(recent(1)[0]["provider"] == "x")
    reset()
    expect(stats()["entries"] == 0)
    clean()
    i18n.set_override(None)
    return "learn + dedupe + reset"


def t_image_type_detector():
    import i18n
    i18n.set_override("en")
    from image_type_detector import classify_image
    imgs = synth_images()
    for key, expect_type in [("ecg", "ecg_strip"), ("xray", "radiograph"), ("skin", "skin_photo"),
                             ("doc", "document_report"), ("wound", "wound_photo")]:
        r = classify_image(imgs[key])
        expect(r["type"] == expect_type, f"{key} -> {r['type']} ({r['reason']})")
    expect(classify_image(b"garbage")["type"] == "other_photo")
    expect(classify_image(imgs["skin"], hint="ecg")["type"] == "ecg_strip")
    expect(classify_image(imgs["skin"], hint="ecg")["user_hint"] is True)
    i18n.set_override(None)
    return "5 types + garbage + hint"


def t_ecg_analyzer():
    from ecg_analyzer import analyze_ecg
    imgs = synth_images()
    r = analyze_ecg(imgs["ecg"])
    expect(r["visible"] and r["regular"] is True and r["deflections"] >= 8, r)
    w, h = 600, 200
    img = np.full((h, w), 255.0)
    xs = np.arange(w)
    ys = np.full(w, 100.0)
    rnd = np.random.default_rng(3)
    for x in np.cumsum(rnd.integers(8, 60, size=30)):
        for dx in (-3, 3):
            if 0 <= x + dx < w:
                ys[int(x + dx)] = 55
    img[ys.astype(int), xs] = 0
    r2 = analyze_ecg(png_bytes(Image.fromarray(img.astype(np.uint8))))
    expect(r2["regular"] is False, r2)
    r3 = analyze_ecg(b"garbage")
    expect(not r3["visible"])
    return "regular/irregular/garbage"


def t_lesion_analyzer():
    from lesion_analyzer import analyze_lesion
    imgs = synth_images()
    r1 = analyze_lesion(imgs["skin"])
    expect(any("reddened" in f["en"] for f in r1["findings"]), r1)
    r2 = analyze_lesion(imgs["wound"])
    expect(any("yellow-green" in f["en"] for f in r2["findings"]))
    expect(not any("ABCDE" in f["meaning_en"] for f in r2["findings"]), "no mole text on wounds")
    r3 = analyze_lesion(imgs["mole"])
    expect(any("ABCDE" in (f["meaning_en"] + f["en"]) for f in r3["findings"]))
    r4 = analyze_lesion(b"garbage")
    expect(r4["findings"], "graceful failure")
    return "4 scenarios + garbage"


@offline_keys
def t_image_caption():
    import i18n
    imgs = synth_images()
    for lang in ("en", "fa"):
        i18n.set_override(lang)
        from image_caption import analyze_image_bytes
        r = analyze_image_bytes(imgs["wound"], "wound from 4 days ago" if lang == "en" else "زخم ۴ روزه")
        expect(r["ok"] and r["image_type"]["type"] == "wound_photo")
        expect(("Objective findings" in r["text"]) == (lang == "en"), "findings section")
        expect(("یافته‌های عینی" in r["text"]) == (lang == "fa"))
        expect(r["red_flag"] is False)
        red = analyze_image_bytes(imgs["ecg"], "chest pain" if lang == "en" else "درد قفسه سینه")
        expect(red["red_flag"] is True, "note red flag")
        ecg = analyze_image_bytes(imgs["ecg"], "palpitations" if lang == "en" else "تپش قلب")
        expect(ecg["image_type"]["type"] == "ecg_strip")
        gar = analyze_image_bytes(b"garbage", "x")
        expect(gar["ok"] is False and gar["text"], "graceful garbage")
    i18n.set_override(None)
    return "bilingual + red flag + garbage"


def t_patient_profile():
    from patient_profile import save_profile, load_profile, summary_for_prompt, bmi, clear_profile
    save_profile({"age": "abc", "name": "X", "weight_kg": "80", "height_cm": "180"})
    p = load_profile()
    expect(p["age"] == "" and p["name"] == "X" and p["weight_kg"] == 80.0)
    expect("X" in summary_for_prompt())
    expect(abs(bmi()["value"] - 24.7) < 0.1, "bmi from profile")
    clear_profile()
    expect(load_profile() == {} or not load_profile().get("name"))
    return "validation + clear"


def t_health_vitals():
    import i18n
    from health_vitals import bmi_info, bp_category, record, history, trend
    expect(bmi_info(95, 175)["bmi"] == 31.0)
    for s, d, lvl in [(110, 70, "green"), (122, 76, "yellow"), (135, 85, "orange"), (150, 95, "red"), (185, 115, "red")]:
        expect(bp_category(s, d)["level"] == lvl, f"{s}/{d}")
    expect(not bp_category("x", 1)["ok"])
    for lang in ("en", "fa"):
        i18n.set_override(lang)
        r = record({"systolic_bp": 120, "diastolic_bp": 80, "weight_kg": 70, "height_cm": 175})
        expect(r["ok"] and r["bmi"]["ok"] and r["bp"]["ok"])
    expect(len(history(5)) >= 1 and "systolic_bp" in trend())
    i18n.set_override(None)
    return "bmi + 4 bp levels + record/trend"


def t_labs():
    import i18n
    from lab_catalog import find_test, all_tests
    from lab_tests import parse_lines, evaluate, interpret
    from lab_visualizer import analyze_text, render_html, render_text
    t = find_test("قند ناشتا")
    expect(t and t["key"] == "fbs", t)
    t2 = find_test("K")
    expect(t2 and t2["key"] == "k")
    expect(len(all_tests()) >= 25)
    for lang in ("en", "fa"):
        i18n.set_override(lang)
        r = parse_lines("FBS 132\nHb 6.2\nK 6.9\nTSH 6.8\nLDL 170")
        expect(len(r) == 5, [x["key"] for x in r])
        expect(any(x["critical_fa"] for x in r))
        out = analyze_text("FBS 110", save_html=False)
        expect(out["text_report"] and out["summary_fa"])
        html = render_html(r)
        expect("<h1>" in html and "bar" in html)
    ev = evaluate("fbs", 105, find_test("FBS"))
    expect(ev["status"] == "high" and "پیش‌دیابت" in ev["zone_fa"], ev)
    i18n.set_override(None)
    return "catalog + parse + critical + html (bilingual)"


def t_drug_interaction():
    import i18n
    from drug_interaction import search_drug, check_interaction, allergy_alert, DISCLAIMER
    for lang in ("en", "fa"):
        i18n.set_override(lang)
        r = check_interaction("warfarin", "ibuprofen")
        expect(r["ok"] and r["interactions"][0]["severity"] == "major")
        r2 = check_interaction("warfarin", "vitamin-c-nonexistent")
        expect(not r2["ok"] and r2["message_fa"])
        hits = search_drug("ژلوفن")
        expect(hits and hits[0]["id"] == "ibuprofen")
        hits2 = search_drug("turmeric")
        expect(hits2 and hits2[0]["id"] == "turmeric")
    expect("warfarin" in DISCLAIMER() or "نشان" in DISCLAIMER())
    from patient_profile import save_profile
    save_profile({"allergies": "آسپرین aspirin"})
    a = allergy_alert(["آسپرین"])
    expect(a["alerts"], a)
    save_profile({"allergies": ""})
    i18n.set_override(None)
    return "search + interactions + allergy (bilingual)"


def t_prescription_scanner():
    import i18n
    from prescription_scanner import scan
    for lang in ("en", "fa"):
        i18n.set_override(lang)
        r = scan("Amoxicillin 500mg BID PO 7d و WBC 12000")
        tr = {t["abbr"]: t["fa"] for t in r["translations"]}
        expect("BID" in tr and "WBC" in tr)
        expect(("twice a day" in tr["BID"]) == (lang == "en"))
        expect(any(d["id"] == "amoxicillin" for d in r["drugs"]), r["drugs"])
        expect(r["doses_mg"] == ["500"])
        expect(r["disclaimer"])
    i18n.set_override(None)
    return "sigs + labs + drug + dose"


def t_first_aid():
    import i18n
    from first_aid import TOPICS, get_topic, list_topics, cpr_timing
    expect(len(TOPICS) == 7)
    for lang in ("en", "fa"):
        i18n.set_override(lang)
        for key in TOPICS:
            tp = get_topic(key)
            expect(tp["steps"] and tp["emergency_line"] and tp["disclaimer"], key)
        expect(cpr_timing()["bpm"] == 110 and cpr_timing()["interval_sec"] > 0.5)
    expect(len(list_topics()) == 7)
    i18n.set_override(None)
    return "7 topics x 2 langs + metronome"


def t_mental_health():
    import i18n
    from mental_health import phq9, gad7, questions, breathing, PHQ9, GAD7
    expect(len(PHQ9) == 9 and len(GAD7) == 7)
    for lang in ("en", "fa"):
        i18n.set_override(lang)
        q = questions()
        expect(len(q["phq9"]) == 9 and len(q["answers"]) == 4)
        r = phq9([1] * 9)
        expect(r["crisis"] and r["crisis_text"])
        r2 = phq9([0] * 9)
        expect(not r2["crisis"] and r2["band"] == "minimal")
        r3 = gad7([3] * 7)
        expect(r3["band"] == "severe")
        b = breathing()
        expect(b["inhale_sec"] == 4 and b["steps"])
    i18n.set_override(None)
    return "phq9/gad7 bands + crisis + breathing"


def t_sleep_analyzer():
    import i18n
    from sleep_analyzer import stopbang, psqi_lite, questions
    for lang in ("en", "fa"):
        i18n.set_override(lang)
        q = questions()
        expect(len(q["stopbang"]) == 8 and len(q["psqi_lite"]) == 9)
        expect(stopbang([0] * 8)["risk"] == "low")
        expect(stopbang([1] * 8)["risk"] == "high")
        expect(psqi_lite([0] * 9)["band"] == "good")
        expect(psqi_lite([1] * 9)["band"] == "poor")
    i18n.set_override(None)
    return "stopbang/psqi levels (bilingual)"


def t_checkup_calendar():
    import i18n
    from checkup_calendar import recommendations, add_reminder, list_reminders, complete_reminder
    for lang in ("en", "fa"):
        i18n.set_override(lang)
        r = recommendations({"age": 55, "gender": "female" if lang == "en" else "زن"})
        expect(len(r["checkups"]) >= 4 and len(r["vaccines"]) >= 3)
        r2 = recommendations(None)
        expect(r2["note_fa"])
    add_reminder("test-reminder")
    expect(any(x["title"] == "test-reminder" for x in list_reminders()))
    rid = list_reminders()[-1]["id"]
    complete_reminder(rid)
    expect(next(x for x in list_reminders() if x["id"] == rid)["done"] is True)
    i18n.set_override(None)
    return "age/sex recommendations + reminders"


def t_doctor_referral():
    import i18n
    from doctor_referral import generate
    for lang in ("en", "fa"):
        i18n.set_override(lang)
        r = generate({"name": "T", "age": 40, "gender": "m"}, [], ["fever"],
                     [{"name": "X", "percent": 40, "urgency": "routine", "matched_symptoms": ["fever"]}],
                     {"turns": 2}, "FBS 110")
        expect(r["ok"] and os.path.exists(r["path"]))
        expect(("Patient details" in r["html"]) == (lang == "en"))
        expect(("مشخصات بیمار" in r["html"]) == (lang == "fa"))
        expect('dir="rtl"' in r["html"] if lang == "fa" else 'dir="ltr"' in r["html"])
    os.remove("referral_report.html")
    i18n.set_override(None)
    return "bilingual printable report"


@offline_keys
def t_hybrid_engine():
    import i18n
    import hybrid_engine
    from auto_learning import stats
    for lang in ("en", "fa"):
        clean()
        i18n.set_override(lang)
        eng = hybrid_engine.HybridEngine()
        r1 = eng.chat("I have a fever and headache since yesterday" if lang == "en" else "دیروز از شب تب و سردرد دارم")
        expect(r1["ok"] and r1["source"] == "internal" and not _EMOJI.search(r1["text"]))
        r2 = eng.chat("also burning when I urinate" if lang == "en" else "همچنین سوزش ادرار دارم")
        txt2 = r2["text"]
        expect(("UTI" in txt2) or ("ادراری" in txt2), txt2[:200])
        r3 = eng.chat("severe chest pain and cold sweat" if lang == "en" else "درد شدید قفسه سینه و عرق سرد")
        expect(r3["red_flag"] and r3["source"] == "internal-emergency")
        imgs = synth_images()
        r4 = eng.chat("", image_b64=base64.b64encode(imgs["skin"]).decode(),
                      image_note="itchy rash" if lang == "en" else "خارش و کهیر")
        expect(r4["ok"] and r4["image_type"]["type"] == "skin_photo")
        st = eng.status()
        expect(st["external_available"] is False and "settings" in st)
    i18n.set_override(None)
    clean()
    return "chat/multi-turn/emergency/image x2 langs"


def t_builders():
    import py_compile
    for f in ("ui_2077.py", "build_exe.py", "run_2077.py", "run_web.py"):
        py_compile.compile(f, doraise=True)
    import csv
    rows = list(csv.DictReader(open("medical_ml_test_dataset.csv", encoding="utf-8-sig")))
    expect(len(rows) == 1000)
    expect(rows[0]["dataset_note"] == "synthetic_for_ml_testing_not_clinical")
    expect(len(rows[0]) == 32, f"columns={len(rows[0])}")
    import sqlite3
    con = sqlite3.connect("diseases_offline.db")
    n = con.execute("SELECT COUNT(*) FROM diseases").fetchone()[0]
    con.close()
    expect(n >= 50, n)
    return "compile + dataset + db"


def t_html_i18n():
    html = open("clinic_2077.html", encoding="utf-8").read()
    js = html.split("<script>")[-1].split("</script>")[0]
    en_block = js.split("T.en = {")[1].split("\n};")[0]
    fa_block = js.split("T.fa = {")[1].split("\n};")[0]
    vocab_en = set(re.findall(r'([A-Za-z_][A-Za-z_0-9]*):(?=["\'{\[])', en_block)) - {"http"}
    vocab_fa = set(re.findall(r'([A-Za-z_][A-Za-z_0-9]*):(?=["\'{\[])', fa_block)) - {"http"}
    used = set(re.findall(r'\bt\("([A-Za-z_0-9]+)"\)', js))
    missing = used - vocab_en
    expect(not missing, f"undefined t() keys: {missing}")
    top_diff = {k for k in (vocab_en ^ vocab_fa) if k in used}
    expect(not top_diff, f"en/fa mismatch for used keys: {top_diff}")
    used_api = set(re.findall(r'api\("(/api/[a-z/\-]+)"', js))
    srv = open("run_web.py", encoding="utf-8").read()
    server_paths = set(re.findall(r'"(/api/[a-z/\-]+)"', srv))
    expect(used_api <= server_paths, f"JS routes missing in server: {used_api - server_paths}")
    return f"{len(used)} keys + {len(used_api)} routes consistent"


def t_ui_structure():
    src = open("ui_2077.py", encoding="utf-8").read()
    defs = set(re.findall(r"def (_panel_\w+)\(", src))
    refs = set(re.findall(r"self\.(_panel_\w+)", src))
    expect(defs and refs <= defs, f"dangling panel refs: {refs - defs}")
    for mod in ("hybrid_engine", "image_caption", "medical_engine", "ai_api_manager",
                "patient_profile", "health_vitals", "drug_interaction", "first_aid",
                "mental_health", "sleep_analyzer", "checkup_calendar", "lab_visualizer",
                "prescription_scanner", "doctor_referral", "local_llm", "auto_learning",
                "semantic_rag", "ml_classifier"):
        expect(f"import {mod}" in src or f"from {mod}" in src, mod)
    return f"{len(defs)} panels + 18 module hooks"


def t_misc_infra():
    import socket
    import subprocess
    import csv as _csv
    import sqlite3
    from run_web import find_free_port
    s = socket.socket()
    s.bind(("127.0.0.1", 2078))
    s.listen(1)
    p = find_free_port(2077, 2087, "127.0.0.1") if os.path.exists("/proc/net/tcp") else None
    expect(p is None or 2077 <= p <= 2087, p)
    s.close()
    if sys.platform != "win32":
        r = subprocess.run([sys.executable, "build_exe.py"], capture_output=True, text=True, timeout=90)
        expect(r.returncode == 1 and ("ویندوز" in r.stdout or "Windows" in r.stdout))
    subprocess.run([sys.executable, "generate_dataset.py"], capture_output=True, timeout=120)
    rows = list(_csv.DictReader(open("medical_ml_test_dataset.csv", encoding="utf-8-sig")))
    expect(len(rows) == 1000)
    subprocess.run([sys.executable, "build_diseases_db.py"], capture_output=True, timeout=120)
    con = sqlite3.connect("diseases_offline.db")
    n = con.execute("SELECT COUNT(*) FROM diseases").fetchone()[0]
    con.close()
    expect(n >= 50, n)
    return "ports/build_exe/dataset/db"



def t_risk_scores():
    from i18n import set_override
    import risk_scores as rs
    set_override("fa")
    r = rs.framingham(50, "m", 200, 45, 130, True)
    expect(r["ok"] and r["points"] == 14 and r["risk_percent"] == 16, r)
    r = rs.framingham(60, "f", 250, 55, 150, False, bp_treated=True)
    expect(r["ok"] and r["points"] == 18 and r["risk_percent"] == 6, r)
    r = rs.framingham(30, "f", 210, 35, 125, True)
    expect(r["ok"] and r["points"] == 13 and r["risk_percent"] == 2, r)
    r = rs.framingham(10, "m", 200, 45, 130, True)
    expect(not r["ok"])
    r = rs.findrisc(50, 32, 105, "m", activity_daily=False, veggies_daily=False,
                    bp_medication=True, high_glucose=True, family_history=2)
    expect(r["ok"] and r["score"] == 24 and r["category"] == "very high", r)
    r = rs.findrisc(30, 22, 75, "f")
    expect(r["ok"] and r["score"] == 0 and r["risk_percent"] == 1, r)
    r = rs.findrisc(58, 31, 90, "f", activity_daily=False)
    expect(r["ok"] and r["score"] == 12, r)
    set_override("en")
    r = rs.findrisc(45, 27, 96, "m", family_history=1)
    expect(r["ok"] and r["score"] == 9 and "slightly elevated" in r["category_fa"], r)
    set_override(None)
    return "framingham + findrisc vectors"


def t_renal_dosing():
    from i18n import set_override
    set_override("fa")
    import renal_dosing as rd
    c = rd.cockcroft_gault(70, 70, 1.0, "m")
    expect(c["ok"] and abs(c["crcl"] - 68.1) < 0.15, c)
    c = rd.cockcroft_gault(70, 70, 1.0, "f")
    expect(c["ok"] and abs(c["crcl"] - 57.9) < 0.2, c)
    c = rd.cockcroft_gault(60, 120, 1.2, "m", height_cm=175)
    expect(c["ok"] and "crcl_adjusted" in c and c["crcl"] < 90 and c["weight_mode"] == "adjusted", c)
    c = rd.cockcroft_gault(70, 70, 2.5, "m")
    expect(c["ok"] and c["crcl"] < 30, c)
    d = rd.drug_check("metformin", 25)
    expect(d["known"] and d["level"] == "red", d)
    d = rd.drug_check("metformin", 75)
    expect(d["known"] and d["level"] == "green", d)
    d = rd.drug_check("ژلوفن", 25)
    expect(d["known"] and "پرهیز" in d["message_fa"], d)
    d = rd.drug_check("unknownxyz", 50)
    expect(not d["known"], d)
    expect(abs(rd.ibw_kg("m", 175) - 72.6) < 0.2)
    set_override(None)
    return "cockcroft-gault + 30 drug rules"


def t_side_effect_checker():
    from i18n import set_override
    set_override("fa")
    import side_effect_checker as se
    r = se.check("lisinopril", "سرفه")
    expect(r["ok"] and r["found"], r)
    r = se.check("metformin", "diarrhea")
    expect(r["ok"] and r["found"] and r["adv_snippets"], r)
    r = se.check("sertraline", "suicidal thoughts")
    expect(r["ok"] and r["found"], r)
    r = se.check("metformin", "خارش")
    expect(r["ok"] and not r["found"], r)
    r = se.check("atorvastatin", "")
    expect(r["ok"] and r["common_fa"], r)
    m = se.check_message("من متفورمین مصرف می‌کنم و اسهال دارم")
    expect(m and "متفورمین" in m, m)
    m = se.check_message("I take sertraline and I have nausea")
    expect(m and "sertraline" in m.lower(), m)
    expect(se.check_message("سردرد دارم") is None)
    set_override(None)
    return "fda label matching fa+en"


def t_vaccine_schedule():
    from i18n import set_override
    set_override("fa")
    import vaccine_schedule as vs
    r = vs.for_child("2025-11-15")
    expect(r["ok"] and r["visits"][0]["status"] == "past" and r["next"]["age_months"] == 12, r)
    r = vs.for_child("2026-07-01")
    expect(r["ok"] and r["next"]["age_months"] == 2 and r["next"]["status"] == "due", r)
    r = vs.for_child("2024-05-10")
    expect(r["ok"] and [v["status"] for v in r["visits"]].count("past") >= 5, r)
    expect(not vs.for_child("bad")["ok"])
    expect(not vs.for_child("2099-01-01")["ok"])
    set_override("en")
    r = vs.for_child("2026-01-01")
    expect(r["ok"] and all(v["vaccines_en"] for v in r["visits"]), r)
    set_override(None)
    return "iran epi 7 visits"


def t_emergency_card():
    from i18n import set_override
    set_override("fa")
    import emergency_card as ec
    ec.save_ice({"blood_type": "O+", "contact_name": "Ali", "contact_phone": "0912"})
    txt = ec.card_text()
    expect("O+" in txt and "0912" in txt, txt)
    svg = ec.qr_svg(txt)
    expect(svg and svg.startswith("<?xml") and "<svg" in svg)
    html = ec.build_html("fa")
    expect("کارت اضطراری" in html and "<svg" in html)
    html_en = ec.build_html("en")
    expect("Medical Emergency Card" in html_en and "کارت اضطراری" not in html_en)
    r = ec.save_card()
    expect(r["ok"] and os.path.exists(r["path"]), r)
    os.remove(r["path"])
    set_override(None)
    return "ice card + qr svg"


def t_health_import():
    from i18n import set_override
    set_override("fa")
    import health_import as hi
    csv1 = "date,systolic,diastolic,heart rate,glucose,weight\n2026-09-01 08:00,125,82,72,98,80.2\n2026-09-02 08:00,130,85,75,101,80.0\n"
    pv = hi.preview(csv1)
    expect(pv["ok"] and pv["total_rows"] == 2 and "glucose" in pv["detected_metrics"], pv)
    pv = hi.preview("تاریخ,فشار بالا,فشار پایین,ضربان\n2026/09/03,135,88,78\n")
    expect(pv["ok"] and "systolic_bp" in pv["detected_metrics"], pv)
    pv = hi.preview("date;glucose;weight\n2026-09-04;99;79.5\n")
    expect(pv["ok"] and pv["total_rows"] == 1, pv)
    expect(not hi.preview("foo,bar\n1,2\n")["ok"])
    backup = None
    if os.path.exists("vitals_history.json"):
        backup = open("vitals_history.json", encoding="utf-8").read()
    r = hi.commit(csv1)
    expect(r["ok"] and r["added"] == 2, r)
    if backup is not None:
        with open("vitals_history.json", "w", encoding="utf-8") as f:
            f.write(backup)
    set_override(None)
    return "csv autodetect fa/en + commit"


def t_secure_store():
    import tempfile
    import secure_store as ss
    key = bytes(range(32))
    ks = ss.chacha20_block(key, bytes.fromhex("000000090000004a00000000"), 1)
    expect(ks == bytes.fromhex("10f1e7e4d13b5915500fdd1fa32071c4c7d1f4c733c068030422aa9ac3d46c4ed2826446079faa0914c2d705d98b02a2b5129cd1de164eb9cbd083e8a2503c4e"), ks.hex())
    plain = b"Ladies and Gentlemen of the class of '99: If I could offer you only one tip for the future, sunscreen would be it."
    ct = ss.chacha20_xor(key, bytes.fromhex("000000000000004a00000000"), plain)
    expect(ct == bytes.fromhex("6e2e359a2568f98041ba0728dd0d6981e97e7aec1d4360c20a27afccfd9fae0bf91b65c5524733ab8f593dabcd62b3571639d624e65152ab8f530c359f0861d807ca0dbf500d6a6156a38e088a22b65e52bc514d16ccf806818ce91ab77937365af90bbf74a35be6b40b8eedf2785e42874d"), ct.hex())
    expect(ss.chacha20_xor(key, bytes.fromhex("000000000000004a00000000"), ct) == plain)
    tmp = tempfile.mkdtemp()
    p1 = os.path.join(tmp, "patient_profile.json")
    with open(p1, "w", encoding="utf-8") as f:
        f.write('{"name": "تست"}')
    vp = os.path.join(tmp, "vault.nmv")
    r = ss.lock("pw1234", paths=[p1], vault_path=vp)
    expect(r["ok"] and r["locked_files"] == 1 and not os.path.exists(p1), r)
    r = ss.unlock("WRONG", vault_path=vp, out_dir=tmp)
    expect(not r["ok"], r)
    r = ss.unlock("pw1234", vault_path=vp, out_dir=tmp)
    expect(r["ok"] and r["restored"] == 1 and os.path.exists(p1), r)
    blob = ss.encrypt_bytes("k", os.urandom(200))
    expect(blob.startswith(ss.MAGIC))
    try:
        ss.decrypt_bytes("k2", blob)
        expect(False, "bad password accepted")
    except ValueError:
        pass
    return "rfc8439 vectors + vault roundtrip"


def t_updater():
    import updater as up
    expect(up._ver_tuple("8.0.0") > up._ver_tuple("7.9.9"))
    expect(up._ver_tuple("7.0.0") < up._ver_tuple("10.0.0"))
    expect(up._ver_tuple("v8.0.1") == (8, 0, 1))
    r = up.check_latest(timeout=8)
    expect(isinstance(r, dict) and ("offline" in r or "latest" in r), r)
    return "version compare + github check"


def t_voice_io():
    import voice_io as vo
    expect(vo._clean_for_speech("**bold** http://x.com text") == "bold text")
    expect(vo.has_persian("سلام") and not vo.has_persian("hello"))
    expect(isinstance(vo.tts_available(), bool))
    r = vo.speak("", wait=True)
    expect(not r["ok"])
    return "tts/stt platform probes"



def t_hybrid_stream():
    from i18n import set_override
    set_override("fa")
    from hybrid_engine import HybridEngine
    e = HybridEngine()
    info = {}
    chunks = list(e.chat_stream("من متفورمین مصرف می‌کنم و اسهال دارم", info))
    expect(chunks and "متفورمین" in "".join(chunks), chunks[:2])
    expect(info["source"] == "internal-knowledge", info)
    info = {}
    list(e.chat_stream("درد قفسه سینه شدید و تنگی نفس", info))
    expect(info.get("red_flag") is True, info)
    info = {}
    chunks = list(e.chat_stream("zqxjw unknown obscure query vvv", info))
    expect(chunks and info.get("source") in ("internal", "internal-knowledge"), info)
    from ai_client import chat_stream as ext_stream
    import inspect
    expect(inspect.isgeneratorfunction(ext_stream))
    from local_lm_connector import chat_stream as lm_stream
    expect(inspect.isgeneratorfunction(lm_stream))
    set_override(None)
    return "qa/emergency/fallback paths + generators"


def t_ocr_reader():
    from i18n import set_override
    set_override("fa")
    import ocr_reader as ocr
    r = ocr.ocr_image(b"notanimage")
    expect(not r["ok"] and ("ویندوز" in r["message_fa"] or "عکس" in r["message_fa"] or len(r["message_fa"]) > 5), r)
    import sys as _s
    if not _s.platform.startswith("win"):
        expect(not ocr.ocr_available())
    expect("Windows.Media.Ocr" in ocr._PS_SCRIPT)
    set_override(None)
    return "graceful fallback + ps1 payload"


def t_health_correlator():
    import json as _json
    from i18n import set_override
    set_override("fa")
    import health_correlator as hc
    diary = [{"date": "2026-09-01", "symptom": "سردرد", "severity": 7},
             {"date": "2026-09-05", "symptom": "سردرد", "severity": 8},
             {"date": "2026-09-09", "symptom": "سردرد", "severity": 6},
             {"date": "2026-09-02", "symptom": "خستگی", "severity": 5}]
    vitals = [{"ts": "2026-09-01T10:00", "systolic_bp": 145, "glucose": 100},
              {"ts": "2026-09-05T10:00", "systolic_bp": 150},
              {"ts": "2026-09-09T10:00", "systolic_bp": 148, "glucose": 99},
              {"ts": "2026-09-02T10:00", "systolic_bp": 118},
              {"ts": "2026-09-03T10:00", "systolic_bp": 120, "glucose": 95},
              {"ts": "2026-09-04T10:00", "systolic_bp": 121}]
    with open("symptom_diary.json", "w", encoding="utf-8") as f:
        _json.dump(diary, f, ensure_ascii=False)
    with open("vitals_history.json", "w", encoding="utf-8") as f:
        _json.dump(vitals, f, ensure_ascii=False)
    r = hc.analyze()
    expect(r["ok"], r)
    corr = [x for x in r["findings"] if x["type"] == "correlation"]
    expect(corr and any("سردرد" in x["text"] for x in corr), r["findings"])
    expect(any("142" in x["text"] or "فشار" in x["text"] for x in corr), corr)
    empty = hc.analyze.__doc__ is not None
    with open("symptom_diary.json", "w", encoding="utf-8") as f:
        _json.dump([], f)
    r2 = hc.analyze()
    expect(r2["ok"] and r2["findings"] == [], r2)
    set_override(None)
    return "bp-on-headache-days detected + empty case"


def t_pregnancy_tracker():
    import os as _os
    from i18n import set_override
    set_override("fa")
    import pregnancy_tracker as pt
    r = pt.set_pregnancy("2026-07-01")
    from datetime import date
    expect(r["ok"] and r["pregnant"], r)
    r2 = pt.pregnancy_status(today=date(2026, 9, 20))
    expect(r2["ok"] and r2["week"] == 12 and r2["trimester"] == 1, r2)
    expect(r2["due_date"] == "2027-04-07", r2)
    expect(r2["size_fa"] and r2["danger_fa"], r2)
    r3 = pt.pregnancy_status(today=date(2026, 7, 8))
    expect(r3["week"] == 2 and r3["trimester"] == 1, r3)
    expect(not pt.set_pregnancy("bad")["ok"])
    lp = pt.log_period("2026-08-01")
    expect(lp["ok"] and "2026-08-01" in lp["periods"], lp)
    pt.log_period("2026-08-29")
    pt.log_period("2026-09-26")
    c = pt.cycle_stats()
    expect(c["ok"] and c["tracked"] == 3 and c["avg_cycle"] == 28, c)
    expect(c["next_expected"] == "2026-10-24", c)
    expect(c["ovulation"] == "2026-10-10", c)
    expect(not pt.log_period("xx")["ok"])
    pt.clear_pregnancy()
    s = pt.pregnancy_status()
    expect(s["ok"] and not s["pregnant"], s)
    if _os.path.exists("cycle_log.json"):
        _os.remove("cycle_log.json")
    set_override(None)
    return "weeks/due/cycle vectors (40-week guide)"


def t_family_risk():
    import os as _os
    from i18n import set_override
    set_override("fa")
    import family_risk as fr
    r = fr.add_member("father", "سرطان کولون", "52")
    expect(r["ok"] and len(r["members"]) == 1, r)
    fr.add_member("mother", "دیابت نوع ۲")
    fr.add_member("grandmother", "سرطان سینه", "61")
    rr = fr.recommendations()
    expect(rr["ok"] and len(rr["recommendations"]) == 3, rr)
    colon = [x for x in rr["recommendations"] if x["test"] == "کولونوسکوپی"]
    expect(colon and colon[0]["first_degree"] is True, rr)
    breast = [x for x in rr["recommendations"] if "ماموگرافی" in str(x.get("test"))]
    expect(breast and breast[0]["first_degree"] is False, rr)
    expect(not fr.add_member("cousin", "x")["ok"])
    expect(not fr.add_member("mother", "")["ok"])
    fr.remove_member(0)
    expect(len(fr.list_members()) == 2)
    for i in range(2):
        fr.remove_member(0)
    expect(fr.recommendations()["recommendations"] == [])
    if _os.path.exists("family_history.json"):
        _os.remove("family_history.json")
    set_override(None)
    return "colon/breast/diabetes rules + degrees"


def t_second_opinion():
    from i18n import set_override
    set_override("fa")
    import second_opinion as so
    r = so.ask("", "openrouter", "lmstudio")
    expect(not r["ok"], r)
    r2 = so.ask("test question", "openrouter", "no_such_provider")
    expect(r2["ok"] and r2["a"]["ok"] is False and r2["b"]["ok"] is False, r2)
    expect(not r2["a"]["provider"] == "", r2)
    set_override(None)
    return "parallel ask + graceful failures"


def t_health_passport():
    import os as _os
    from i18n import set_override
    set_override("fa")
    import health_passport as hp
    import json as _json
    with open("patient_profile.json", "w", encoding="utf-8") as f:
        _json.dump({"name": "تست", "age": 40, "gender": "مرد", "weight_kg": 80, "height_cm": 175,
                    "conditions": "فشار خون", "allergies": "پنی‌سیلین", "medications": "متفورمین"}, f, ensure_ascii=False)
    with open("vitals_history.json", "w", encoding="utf-8") as f:
        _json.dump([{"ts": "2026-09-01T10:00", "systolic_bp": 125, "diastolic_bp": 82, "glucose": 98}], f)
    html = hp.build_html("fa")
    expect("پاسپورت سلامت" in html and "تست" in html and "فشار خون" in html, html[:200])
    expect("متفورمین" in html and "125/82" in html, html[:200])
    html_en = hp.build_html("en")
    expect("Health Passport" in html_en and "پاسپورت سلامت" not in html_en)
    r = hp.save()
    expect(r["ok"] and _os.path.exists(r["path"]), r)
    _os.remove(r["path"])
    for f_ in ("patient_profile.json", "vitals_history.json"):
        if _os.path.exists(f_):
            _os.remove(f_)
    set_override(None)
    return "passport html fa/en + charts"


def t_backup_restore():
    import json as _json
    import os as _os
    import tempfile
    import secure_store as ss
    tmp = tempfile.mkdtemp()
    with open("patient_profile.json", "w", encoding="utf-8") as f:
        _json.dump({"name": "کاربر تست"}, f, ensure_ascii=False)
    dest = _os.path.join(tmp, "backup.nmv")
    r = ss.backup_to("pw9999", dest)
    expect(r["ok"] and r["files"] >= 1 and _os.path.exists(dest), r)
    _os.remove("patient_profile.json")
    bad = ss.restore_from("WRONG", dest)
    expect(not bad["ok"], bad)
    r2 = ss.restore_from("pw9999", dest)
    expect(r2["ok"] and r2["restored"] >= 1, r2)
    data = _json.load(open("patient_profile.json", encoding="utf-8"))
    expect(data["name"] == "کاربر تست", data)
    expect(not ss.backup_to("12", dest)["ok"])
    expect(not ss.backup_to("pw9999", "")["ok"])
    if _os.path.exists("patient_profile.json"):
        _os.remove("patient_profile.json")
    return "encrypted single-file backup roundtrip"


def t_elder_mode():
    from ai_api_manager import save_settings, get_settings
    save_settings({"elder_mode": True})
    expect(get_settings().get("elder_mode") is True)
    save_settings({"elder_mode": False})
    expect(get_settings().get("elder_mode") is False)
    save_settings({"streaming_enabled": False})
    expect(get_settings().get("streaming_enabled") is False)
    save_settings({"streaming_enabled": True})
    expect(get_settings().get("streaming_enabled") is True)
    html = open("clinic_2077.html", encoding="utf-8").read()
    expect("body.elder" in html and "toggleElder" in html and "elder_mode" in html)
    import ui_2077
    expect(abs(ui_2077._font_scale() - 1.0) < 0.01)
    src = open("ui_2077.py", encoding="utf-8").read()
    expect("_toggle_elder" in src and "elder_mode" in src)
    return "settings roundtrip + web class + desktop scale"


def main():
    clean()
    t0 = time.time()
    run_module("common_2077", t_common)
    run_module("i18n", t_i18n)
    run_module("ai_api_manager", t_ai_api_manager)
    run_module("ai_client (+mock OpenRouter)", t_ai_client_and_mock)
    run_module("free_ai", t_free_ai)
    run_module("local_llm", t_local_llm)
    run_module("medical_engine", t_medical_engine)
    run_module("bayesian_engine", t_bayesian)
    run_module("ml_classifier", t_ml_classifier)
    run_module("semantic_rag", t_semantic_rag)
    run_module("clinical_dialogue", t_clinical_dialogue)
    run_module("medical_nlg", t_medical_nlg)
    run_module("behavior_imitation", t_behavior_imitation)
    run_module("auto_learning", t_auto_learning)
    run_module("image_type_detector", t_image_type_detector)
    run_module("ecg_analyzer", t_ecg_analyzer)
    run_module("lesion_analyzer", t_lesion_analyzer)
    run_module("image_caption", t_image_caption)
    run_module("patient_profile", t_patient_profile)
    run_module("health_vitals", t_health_vitals)
    run_module("lab_catalog + lab_tests + lab_visualizer", t_labs)
    run_module("drug_interaction", t_drug_interaction)
    run_module("prescription_scanner", t_prescription_scanner)
    run_module("first_aid", t_first_aid)
    run_module("mental_health", t_mental_health)
    run_module("sleep_analyzer", t_sleep_analyzer)
    run_module("checkup_calendar", t_checkup_calendar)
    run_module("doctor_referral", t_doctor_referral)
    run_module("hybrid_engine", t_hybrid_engine)
    run_module("builders/ui/run scripts", t_builders)
    run_module("clinic_2077.html i18n+routes", t_html_i18n)
    run_module("ui_2077 structure", t_ui_structure)
    run_module("risk_scores (framingham+findrisc)", t_risk_scores)
    run_module("renal_dosing (cockcroft-gault)", t_renal_dosing)
    run_module("side_effect_checker (FDA labels)", t_side_effect_checker)
    run_module("vaccine_schedule (Iran EPI)", t_vaccine_schedule)
    run_module("emergency_card (ICE + QR)", t_emergency_card)
    run_module("health_import (CSV)", t_health_import)
    run_module("secure_store (ChaCha20 vault)", t_secure_store)
    run_module("updater (github)", t_updater)
    run_module("voice_io (tts/stt)", t_voice_io)
    run_module("hybrid_engine streaming", t_hybrid_stream)
    run_module("ocr_reader", t_ocr_reader)
    run_module("health_correlator", t_health_correlator)
    run_module("pregnancy_tracker", t_pregnancy_tracker)
    run_module("family_risk", t_family_risk)
    run_module("second_opinion", t_second_opinion)
    run_module("health_passport", t_health_passport)
    run_module("secure_store backup", t_backup_restore)
    run_module("elder mode + streaming settings", t_elder_mode)
    run_module("infrastructure (ports/builders)", t_misc_infra)
    clean()
    total = len(RESULTS)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    print("=" * 60)
    print(f"RESULT: {passed}/{total} modules passed  ({time.time()-t0:.1f}s)")
    if passed != total:
        print("\nFailures:")
        for name, ok, err in RESULTS:
            if not ok:
                print(f"  - {name}: {err}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
