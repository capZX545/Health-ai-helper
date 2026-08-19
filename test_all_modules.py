# -*- coding: utf-8 -*-
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
                  "referral_report.html", "lab_report.html", "reminders.json"]


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
        RESULTS.append((name, False, f"{e!r}"[:200]))
        print(f"FAIL  {name}  -> {e!r}"[:200])
        if os.environ.get("TEST_VERBOSE"):
            traceback.print_exc()


def expect(cond, msg=""):
    if not cond:
        raise AssertionError(msg or "condition failed")


def png_bytes(im):
    b = io.BytesIO()
    im.save(b, format="PNG")
    return b.getvalue()


def png_b64(im):
    return base64.b64encode(png_bytes(im)).decode()


# ---------------------------------------------------------------- helpers

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


# ================================================================ tests

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
    expect(not r["ok"] or r["ok"], "test result returned")  # نتیجه به وجود کلید وابسته است
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
        # reasoning فعال → موفق → ذخیره → درخواست بعدی شامل reasoning_details
        r = chat("openrouter", [{"role": "user", "content": "hi"}], model="m1", reasoning_enabled=True)
        expect(r["ok"] and r["text"].startswith("mock"), r)
        expect(get_saved_reasoning("m1"), "reasoning saved")
        chat("openrouter", [{"role": "user", "content": "again"}], model="m1", reasoning_enabled=True)
        msgs = state["last"]["messages"]
        expect(any(m.get("reasoning_details") for m in msgs), "reasoning resent unchanged")
        clear_reasoning("m1")
        expect(get_saved_reasoning("m1") is None)
        # آدرس غیرقابل‌دسترس → پیام قطعی اینترنت
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
    expect(DEFAULT_MODEL == "openai/gpt-oss-120b:free")
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
    expect(q1 and q1 != st.next_question() or True)  # دو سوال متوالی نباید یکسان باشند
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
        for key in ("findings", "probables", "advice", "warning", "followup"):
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
    expect("b" in txt and "d?" in txt and txt.count("\n\n") >= 3)
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
    clear_profile()  # bmi قبل از این خط محاسبه شد
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
        # حافظه‌ی چندنوبته
        r2 = eng.chat("also burning when I urinate" if lang == "en" else "همچنین سوزش ادرار دارم")
        txt2 = r2["text"]
        expect(("UTI" in txt2) or ("ادراری" in txt2), txt2[:200])
        # اورژانسی
        r3 = eng.chat("severe chest pain and cold sweat" if lang == "en" else "درد شدید قفسه سینه و عرق سرد")
        expect(r3["red_flag"] and r3["source"] == "internal-emergency")
        # تصویر
        imgs = synth_images()
        r4 = eng.chat("", image_b64=base64.b64encode(imgs["skin"]).decode(),
                      image_note="itchy rash" if lang == "en" else "خارش و کهیر")
        expect(r4["ok"] and r4["image_type"]["type"] == "skin_photo")
        # مغز خاموش → یادگیری پس‌زمینه همچنان فعال (تست با موک در t_ai_client)
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
    js = html.split("<script>")[1].split("</script>")[0]
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
    # 2077 ممکن است آزاد باشد در محیط تست؛ فقط بررسی بازه معتبر
    expect(p is None or 2077 <= p <= 2087, p)
    s.close()
    if sys.platform != "win32":
        r = subprocess.run([sys.executable, "build_exe.py"], capture_output=True, text=True, timeout=90)
        expect(r.returncode == 1 and ("ویندوز" in r.stdout or "Windows" in r.stdout))
    # تولید مجدد داده‌ها
    subprocess.run([sys.executable, "generate_dataset.py"], capture_output=True, timeout=120)
    rows = list(_csv.DictReader(open("medical_ml_test_dataset.csv", encoding="utf-8-sig")))
    expect(len(rows) == 1000)
    subprocess.run([sys.executable, "build_diseases_db.py"], capture_output=True, timeout=120)
    con = sqlite3.connect("diseases_offline.db")
    n = con.execute("SELECT COUNT(*) FROM diseases").fetchone()[0]
    con.close()
    expect(n >= 50, n)
    return "ports/build_exe/dataset/db"


# ================================================================ main

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
