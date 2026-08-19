# -*- coding: utf-8 -*-
"""
run_web.py — نسخه‌ی وب محلی NexusMed 2077.
آدرس پیش‌فرض: http://localhost:2077 — اگر اشغال بود، پورت‌های ۲۰۷۸ تا ۲۰۸۷ امتحان می‌شوند.
اجرا:  python run_web.py  [--host 127.0.0.1] [--port 2077] [--no-browser]
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from common_2077 import APP_NAME, APP_VERSION, DATA_DIR

HTML_FILE = os.path.join(DATA_DIR, "clinic_2077.html")
MAX_BODY = 15 * 1024 * 1024  # حداکثر ۱۵ مگابایت (برای تصاویر)

_engine = None
_engine_lock = threading.Lock()


def get_engine():
    global _engine
    with _engine_lock:
        if _engine is None:
            from hybrid_engine import HybridEngine
            _engine = HybridEngine()
        return _engine


def find_free_port(start: int = 2077, end: int = 2087, host: str = "127.0.0.1") -> int | None:
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host, port))
                return port
            except OSError:
                continue
    return None


class Handler(BaseHTTPRequestHandler):
    server_version = f"NexusMed2077/{APP_VERSION}"

    # ------------------------------------------------------------- helpers
    def _json(self, obj, code: int = 200):
        try:
            body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        except Exception:
            body = json.dumps({"ok": False, "message_fa": "خطای داخلی سرور"}).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _html(self, text: str, code: int = 200):
        body = text.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0 or n > MAX_BODY:
            return {}
        raw = self.rfile.read(n)
        try:
            data = json.loads(raw.decode("utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def log_message(self, fmt, *args):  # لاگ کم‌حجم
        sys.stderr.write("•")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # --------------------------------------------------------------- GET
    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path in ("/", "/index.html", "/clinic_2077.html"):
                with open(HTML_FILE, "r", encoding="utf-8") as f:
                    return self._html(f.read())
            if path == "/api/status":
                return self._json(self._status())
            if path == "/api/models":
                from free_ai import OPENROUTER_FREE_MODELS
                return self._json({"ok": True, "models": OPENROUTER_FREE_MODELS})
            if path == "/api/profile":
                from patient_profile import load_profile
                return self._json({"ok": True, "profile": load_profile()})
            if path == "/api/vitals/history":
                from health_vitals import history, trend
                return self._json({"ok": True, "history": history(30), "trend": trend()})
            if path == "/api/firstaid":
                from first_aid import list_topics
                return self._json({"ok": True, "topics": list_topics()})
            if path.startswith("/api/firstaid/"):
                from first_aid import cpr_timing, get_topic
                key = path.rsplit("/", 1)[-1]
                if key == "cpr-timing":
                    return self._json({"ok": True, **cpr_timing()})
                t = get_topic(key)
                return self._json({"ok": bool(t), "topic": t})
            if path == "/api/mental/breathing":
                from mental_health import breathing
                return self._json({"ok": True, **breathing()})
            if path == "/api/mental/questions":
                from mental_health import questions as mh_questions
                q = mh_questions()
                return self._json({"ok": True, "phq9": q["phq9"], "gad7": q["gad7"], "answers": q["answers"]})
            if path == "/api/sleep/questions":
                from sleep_analyzer import questions
                return self._json({"ok": True, **questions()})
            if path == "/api/checkup":
                from checkup_calendar import list_reminders, recommendations
                return self._json({"ok": True, **recommendations(), "reminders": list_reminders()})
            if path == "/api/localllm":
                from local_llm import get_config
                return self._json({"ok": True, "config": get_config()})
            if path == "/api/learning":
                from auto_learning import recent, stats
                return self._json({"ok": True, **stats(), "recent": recent(5)})
            return self._json({"ok": False, "message_fa": "مسیر یافت نشد"}, 404)
        except Exception as e:
            return self._json({"ok": False, "message_fa": "خطای سرور: "+ str(e)[:120]}, 500)

    def _status(self) -> dict:
        eng = get_engine()
        st = eng.status()
        from ai_api_manager import env_summary
        st["app"] = {"name": APP_NAME, "version": APP_VERSION}
        st["env"] = env_summary()
        try:
            from semantic_rag import status as rag_status
            st["rag"] = rag_status()
        except Exception:
            st["rag"] = {}
        return {"ok": True, **st}

    # -------------------------------------------------------------- POST
    def do_POST(self):
        path = urlparse(self.path).path
        data = self._body()
        try:
            if path == "/api/chat":
                text = str(data.get("text") or "").strip()
                from i18n import tt
                if not text and not data.get("image_b64"):
                    return self._json({"ok": False, "message_fa": tt("The message is empty.", "پیام خالی است.")}, 400)
                if data.get("image_b64"):
                    import base64 as _b64chk
                    try:
                        _b64chk.b64decode(str(data["image_b64"]).split(",")[-1])
                    except Exception:
                        return self._json({"ok": False, "message_fa": tt("The attached image could not be decoded. Send it as PNG or JPG.",
                                                                         "تصویر ضمیمه قابل رمزگشایی نبود. آن را به‌صورت PNG یا JPG بفرست.")}, 400)
                res = get_engine().chat(text, image_b64=data.get("image_b64"),
                                        image_mime=data.get("image_mime", "image/jpeg"),
                                        image_note=str(data.get("image_note") or ""),
                                        image_hint=data.get("image_hint"))
                return self._json(res)
            if path == "/api/settings":
                from ai_api_manager import get_settings, save_settings
                if data:
                    s = save_settings(data)
                else:
                    s = get_settings()
                return self._json({"ok": True, "settings": s})
            if path == "/api/settings/keys":
                from ai_api_manager import masked_keys, set_api_key
                changed = []
                for provider, field in (("openrouter", "openrouter_key"), ("openai", "openai_key"), ("deepseek", "deepseek_key")):
                    v = data.get(field)
                    if v is not None and str(v).strip():
                        if set_api_key(provider, str(v).strip()):
                            changed.append(provider)
                return self._json({"ok": True, "changed": changed, "masked": masked_keys(),
                                   "message_fa": "کلیدها ذخیره شد (فایل .env) — بدون نیاز به ری‌استارت." if changed else "کلید جدیدی وارد نشد."})
            if path == "/api/settings/test":
                from ai_api_manager import test_connection
                provider = str(data.get("provider") or "openrouter")
                return self._json(test_connection(provider))
            if path == "/api/profile":
                from patient_profile import load_profile, save_profile
                return self._json({"ok": True, "profile": save_profile(data)})
            if path == "/api/vitals":
                from health_vitals import record
                return self._json(record(data))
            if path == "/api/labs":
                from lab_visualizer import analyze_text
                return self._json(analyze_text(str(data.get("text") or ""), save_html=bool(data.get("save"))))
            if path == "/api/drugs":
                from drug_interaction import allergy_alert, check_interaction, search_drug
                mode = data.get("mode", "search")
                if mode == "interact":
                    res = check_interaction(str(data.get("a") or ""), str(data.get("b") or ""))
                else:
                    res = {"ok": True, "results": search_drug(str(data.get("q") or ""))}
                    if data.get("names"):
                        res["allergy"] = allergy_alert([str(x) for x in data["names"]])
                return self._json(res)
            if path == "/api/mental":
                from mental_health import gad7, phq9
                answers = data.get("answers") or []
                res = phq9(answers) if data.get("type") == "phq9"else gad7(answers)
                return self._json(res)
            if path == "/api/sleep":
                from sleep_analyzer import psqi_lite, stopbang
                answers = data.get("answers") or []
                res = stopbang(answers) if data.get("type") == "stopbang"else psqi_lite(answers)
                return self._json(res)
            if path == "/api/checkup/reminders":
                from checkup_calendar import add_reminder
                return self._json(add_reminder(str(data.get("title") or "یادآور چکاپ"), str(data.get("when") or "")))
            if path == "/api/prescription":
                from prescription_scanner import scan
                return self._json(scan(str(data.get("text") or "")))
            if path == "/api/referral":
                from doctor_referral import generate
                from health_vitals import history
                from patient_profile import load_profile
                eng = get_engine()
                dlg = eng.dialogue.summary()
                cands = []
                try:
                    from medical_engine import analyze
                    cands = analyze(str(data.get("text") or dlg.get("symptoms_fa", "")), load_profile()).get("candidates", [])
                except Exception:
                    pass
                res = generate(load_profile(), history(8), dlg.get("symptoms_fa"), cands, dlg, str(data.get("labs_text") or ""))
                return self._json(res)
            if path == "/api/localllm":
                from local_llm import save_config
                return self._json({"ok": True, "config": save_config(data)})
            if path == "/api/localllm/test":
                from local_llm import test_setup
                return self._json(test_setup())
            if path == "/api/image":
                from image_caption import analyze_image_bytes
                from i18n import tt
                import base64
                b64 = str(data.get("image_b64") or "")
                note = str(data.get("note") or "")
                if not b64:
                    return self._json({"ok": False, "message_fa": tt("No image was sent.", "تصویری ارسال نشد.")}, 400)
                img_bytes = base64.b64decode(b64.split(",")[-1])
                return self._json(analyze_image_bytes(img_bytes, note, hint=data.get("hint")))
            if path == "/api/assess":
                from medical_engine import analyze, detect_symptoms, emergency_response
                from patient_profile import load_profile
                from ml_classifier import predict as ml_predict
                text = str(data.get("text") or "").strip()
                if not text:
                    from i18n import tt
                    return self._json({"ok": False, "message_fa": tt("Enter your symptoms first.", "اول علائمت را بنویس.")}, 400)
                profile = load_profile()
                a = analyze(text, profile)
                if a["red_flag"]:
                    return self._json({"ok": True, "red_flag": True,
                                       "reasons": a["red_flag_reasons"],
                                       "text": emergency_response(a["red_flag_reasons"])})
                ml = None
                try:
                    ml = ml_predict(a["detected"], profile, None)
                except Exception:
                    ml = None
                rag = []
                try:
                    from semantic_rag import search
                    rag = [h.get("title") for h in search(text, k=3) if h.get("title")]
                except Exception:
                    pass
                # سطح تریاژ بر اساس فوریت برترین کاندیدها
                urgencies = [c.get("urgency") for c in a["candidates"][:3]]
                from i18n import is_fa
                if "emergency" in urgencies:
                    level = "emergency"
                elif "urgent" in urgencies:
                    level = "urgent"
                else:
                    level = "routine"
                where = {
                    "emergency": ("Go to the emergency department NOW or call 115/112." , "همین حالا به اورژانس برو یا با ۱۱۵/۱۱۲ تماس بگیر."),
                    "urgent": ("See a clinician today or at the first opportunity.", "امروز یا در اولین فرصت به پزشک مراجعه کن."),
                    "routine": ("A routine visit is enough; monitor your symptoms.", "مراجعه‌ی سرپایی کافی است؛ علائم را زیر نظر بگیر."),
                }[level]
                triage = {"level": level, "where": where[1] if is_fa() else where[0]}
                return self._json({"ok": True, "red_flag": False,
                                   "symptoms": a["symptoms"], "denied": a["denied"],
                                   "duration_days": a["detected"].get("duration_days"),
                                   "temp_c": a["detected"].get("temp_c"),
                                   "candidates": a["candidates"], "ml": ml, "rag": rag,
                                   "triage": triage})
            if path == "/api/learning/reset":
                from auto_learning import reset
                return self._json({"ok": reset()})
            if path == "/api/dialogue/reset":
                get_engine().dialogue.reset()
                return self._json({"ok": True})
            return self._json({"ok": False, "message_fa": "مسیر یافت نشد"}, 404)
        except Exception as e:
            return self._json({"ok": False, "message_fa": "خطای سرور: "+ str(e)[:150]}, 500)


def main() -> int:
    ap = argparse.ArgumentParser(description="NexusMed 2077 — وب محلی")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=2077)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()

    port = args.port
    if port == 2077:
        port = find_free_port(2077, 2087, args.host) or 2078
    httpd = ThreadingHTTPServer((args.host, port), Handler)

    def _warmup():
        # پیش‌بارگیری مدل ML و ایندکس RAG تا اولین چت کاربر سریع باشد
        try:
            from ml_classifier import is_ready
            is_ready()
        except Exception:
            pass
        try:
            from semantic_rag import search
            search("fever", k=1)
        except Exception:
            pass

    threading.Thread(target=_warmup, daemon=True).start()
    url = f"http://{'localhost' if args.host in ('127.0.0.1', '0.0.0.0') else args.host}:{port}"
    print("=" * 56)
    print(f"{APP_NAME} v{APP_VERSION} - bilingual medical assistant (en/fa)")
    print(f"Web UI: {url}")
    print("Not a doctor replacement. Emergency: Iran 115 / Europe 112")
    print("=" * 56)
    if not args.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nخروج.")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
