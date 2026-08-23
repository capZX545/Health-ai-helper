# -*- coding: utf-8 -*-
"""
Local web version of NexusMed 2077.
Default address: http://localhost:2077 - if taken, ports 2078..2087 are tried.
Run:  python run_web.py  [--host 127.0.0.1] [--port 2077] [--no-browser]
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
MAX_BODY = 15 * 1024 * 1024  # 15 MB max (images)

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

    def log_message(self, fmt, *args):  # keep logs small
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
            if path == "/api/who/profile":
                from who_connector import get_country_profile
                country = "IRN"
                return self._json(get_country_profile(country))
            if path == "/api/learning/status":
                from auto_learning import stats, recent
                from behavior_imitation import load_profile
                st = get_engine().status()
                return self._json({"ok": True,
                    "entries": stats()["entries"],
                    "recent": recent(3),
                    "style_samples": load_profile().get("samples", 0),
                    "brain_on": st.get("settings", {}).get("brain_enabled", True),
                    "learning_active": True})
            if path == "/api/settings/full":
                # same code lives in do_POST but the UI needs GET
                from ai_api_manager import get_settings, masked_keys, has_any_external
                from local_llm import get_config as llm_config
                from auto_learning import stats as learn_stats
                from semantic_rag import status as rag_status
                from ml_classifier import status as ml_status
                from medical_engine import DISEASES, SYMPTOM_KEYWORDS
                from drug_interaction import DRUGS, INTERACTIONS
                s = get_settings()
                lc = llm_config()
                all_settings = {
                    "language": {"value": s["language"], "type": "choice", "options": ["en", "fa"]},
                    "brain_enabled": {"value": s["brain_enabled"], "type": "bool"},
                    "openrouter_model": {"value": s["openrouter_model"], "type": "text"},
                    "reasoning_enabled": {"value": s["reasoning_enabled"], "type": "bool"},
                    "local_llm_enabled": {"value": lc.get("enabled", False), "type": "bool"},
                    "local_llm_model": {"value": lc.get("model", ""), "type": "text"},
                }
                from medical_catalog import stats as cat_stats
                cs = cat_stats()
                stats_block = {
                    "diseases": len(DISEASES), "symptoms": len(SYMPTOM_KEYWORDS),
                    "drugs": len(DRUGS), "interactions": len(INTERACTIONS),
                    "learning_entries": learn_stats()["entries"],
                    "rag_docs": rag_status().get("indexed_docs", 0),
                    "ml_ready": ml_status().get("ready", False),
                    "catalog_conditions": cs["conditions"],
                    "catalog_drugs": cs["drugs"],
                    "external_available": has_any_external(),
                    "masked_keys": masked_keys(),
                }
                return self._json({"ok": True, "settings": all_settings, "stats": stats_block})
            if path == "/api/conversations":
                from common_2077 import read_json
                import os as _os
                hist = read_json(_os.path.join(DATA_DIR, "conversation_history.json"), default=[]) or []
                return self._json({"ok": True, "conversations": hist[:20]})
            if path == "/api/learning":
                from auto_learning import recent, stats
                return self._json({"ok": True, **stats(), "recent": recent(5)})
            if self._api_knowledge(path):
                return
            return self._json({"ok": False, "message_fa": "مسیر یافت نشد"}, 404)
        except Exception as e:
            return self._json({"ok": False, "message_fa": "خطای سرور: "+ str(e)[:120]}, 500)

    def _api_knowledge(self, path: str) -> bool:
        """
        Read-only knowledge routes (GET). Returns False when the path doesn't match.
        """
        from urllib.parse import parse_qs
        from knowledge_browser import fa_disease_name
        qs = parse_qs(urlparse(self.path).query)
        q = (qs.get("q", [""])[0] or "").strip()
        if path == "/api/knowledge/symptoms":
            from knowledge_browser import get_all_symptoms, search_symptoms
            syms = search_symptoms(q) if q else get_all_symptoms()
            self._json({"ok": True, "total": len(syms), "symptoms": syms})
            return True
        if path == "/api/knowledge/diseases":
            from knowledge_browser import get_all_diseases, search_diseases
            dis = search_diseases(q) if q else get_all_diseases()
            self._json({"ok": True, "total": len(dis), "diseases": dis})
            return True
        if path == "/api/knowledge/drugs":
            from knowledge_browser import get_all_drugs, search_drugs, get_drug_count, get_interaction_count
            drugs = search_drugs(q) if q else get_all_drugs()
            self._json({"ok": True, "total": get_drug_count(), "interactions": get_interaction_count(), "drugs": drugs})
            return True
        if path == "/api/knowledge/drugs_fda":
            from knowledge_browser import search_fda_drugs, get_fda_drug_count
            limit = int((qs.get("limit", ["40"])[0] or 40))
            results = search_fda_drugs(q, limit) if q else []
            self._json({"ok": True, "total": get_fda_drug_count(), "q": q, "drugs": results})
            return True
        if path == "/api/knowledge/diseases-all":
            from knowledge_browser import (search_doid, search_wiki_diseases,
                                           get_all_diseases, get_fda_drug_count)
            from medical_catalog import stats as cat_stats
            from knowledge_browser import get_catalog_diseases
            limit = int((qs.get("limit", ["30"])[0] or 30))
            rows = []
            nq = __import__("common_2077").normalize(q)
            # 1) engine diseases
            for d in get_all_diseases():
                if q and (nq in __import__("common_2077").normalize(d.get("name", "")) or nq in __import__("common_2077").normalize(d.get("fa", ""))):
                    rows.append({"src": "engine", "name": d.get("name", ""), "fa": d.get("fa", ""),
                                 "code": "", "sym": [s.get("name") for s in (d.get("symptoms") or [])][:8]})
                if len(rows) >= limit:
                    break
            # 2) ICD catalog (with the fa -> en bridge)
            if q and len(rows) < limit:
                for c in (get_catalog_diseases(q, 10).get("results") or []):
                    rows.append({"src": "icd10", "name": c.get("name", ""), "fa": c.get("fa", "") or fa_disease_name(icd=c.get("icd10", "")),
                                 "code": c.get("icd10", ""), "sym": []})
                    if len(rows) >= limit:
                        break
            # 3) DOID
            if q and len(rows) < limit:
                for d in search_doid(q, 10):
                    rows.append({"src": "doid", "name": d.get("name", ""), "fa": fa_disease_name(en=d.get("name", "")),
                                 "code": "DOID:" + d.get("doid", ""), "def": d.get("def", ""), "sym": []})
                    if len(rows) >= limit:
                        break
            # 4) wikidata (with symptoms/treatments)
            if q and len(rows) < limit:
                for e in search_wiki_diseases(q, 10):
                    rows.append({"src": "wiki", "name": e.get("en", ""), "fa": e.get("fa", ""),
                                 "code": e.get("icd", "") or e.get("qid", ""), "sym": e.get("sym", [])[:10],
                                 "drug": e.get("drug", [])[:10]})
                    if len(rows) >= limit:
                        break
            from knowledge_browser import hpo_count, _load_doid, _load_wiki
            self._json({"ok": True, "q": q, "results": rows,
                        "counts": {"engine": len(get_all_diseases()), "icd10": cat_stats().get("conditions", 0),
                                   "doid": len(_load_doid()), "wiki": len(_load_wiki()),
                                   "hpo": hpo_count()}})
            return True
        if path == "/api/knowledge/hpo":
            from knowledge_browser import search_hpo, hpo_count
            limit = int((qs.get("limit", ["40"])[0] or 40))
            self._json({"ok": True, "total": hpo_count(),
                        "terms": (search_hpo(q, limit) if q else [])[:limit]})
            return True
        if path == "/api/knowledge/drug-label":
            from knowledge_browser import get_drug_label, fa_drug_name
            g = (qs.get("g", [""])[0] or q or "").strip()
            lb = get_drug_label(g) if g else None
            self._json({"ok": bool(lb), "fa": fa_drug_name(g or ""), "label": lb})
            return True
        if path == "/api/knowledge/catalog":
            from knowledge_browser import get_catalog_diseases
            self._json(get_catalog_diseases(q, 30))
            return True
        return False

    # ------------------------------------------------------- live connectors
    def _http_json(self, url: str, timeout: int = 15):
        import requests
        r = requests.get(url, timeout=timeout,
                         headers={"User-Agent": "NexusMed2077/2.0 (github.com/capZX545)"})
        r.raise_for_status()
        return r.json()

    def _live_pubmed(self, q: str) -> dict:
        if not q:
            return {"ok": False, "message_fa": "عبارتی برای جستجو بده."}
        try:
            import urllib.parse as up
            es = self._http_json(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax=8&term="
                + up.quote(q), 20)
            ids = es.get("esearchresult", {}).get("idlist", [])
            if not ids:
                return {"ok": True, "total": 0, "articles": []}
            su = self._http_json(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id="
                + ",".join(ids), 20)
            arts = []
            for pid in ids:
                it = su.get("result", {}).get(pid, {})
                arts.append({
                    "pmid": pid,
                    "title": it.get("title", ""),
                    "journal": it.get("source", ""),
                    "date": it.get("pubdate", ""),
                    "authors": (it.get("authors") or [{}])[0].get("name", ""),
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pid}/",
                })
            return {"ok": True, "total": es.get("esearchresult", {}).get("count", "0"), "articles": arts}
        except Exception as e:
            return {"ok": False, "message_fa": "خطا در اتصال به PubMed: " + str(e)[:100]}

    def _live_trials(self, q: str) -> dict:
        if not q:
            return {"ok": False, "message_fa": "عبارتی برای جستجو بده."}
        try:
            import urllib.parse as up
            d = self._http_json(
                "https://clinicaltrials.gov/api/v2/studies?query.term=" + up.quote(q)
                + "&pageSize=8&countTotal=true", 20)
            out = []
            for s in d.get("studies", []):
                p = s.get("protocolSection", {})
                out.append({
                    "nct": p.get("identificationModule", {}).get("nctId", ""),
                    "title": p.get("identificationModule", {}).get("briefTitle", ""),
                    "status": p.get("statusModule", {}).get("overallStatus", ""),
                    "phase": (p.get("designModule", {}).get("phases") or [""])[0],
                    "conditions": ", ".join((p.get("conditionsModule", {}).get("conditions") or [])[:3]),
                    "url": "https://clinicaltrials.gov/study/" + p.get("identificationModule", {}).get("nctId", ""),
                })
            return {"ok": True, "total": d.get("totalCount", len(out)), "trials": out}
        except Exception as e:
            return {"ok": False, "message_fa": "خطا در اتصال به ClinicalTrials.gov: " + str(e)[:100]}

    def _live_rxnorm(self, name: str) -> dict:
        if not name:
            return {"ok": False, "message_fa": "نام دارو را بده."}
        try:
            import urllib.parse as up
            q = up.quote(name)
            rid = self._http_json(f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={q}", 15)
            rxcui = (rid.get("idGroup", {}).get("rxnormId") or [""])[0]
            concepts = []
            if rxcui:
                d = self._http_json(f"https://rxnav.nlm.nih.gov/REST/drugs.json?name={q}", 15)
                for g in d.get("drugGroup", {}).get("conceptGroup", []):
                    for c in (g.get("conceptProperties") or [])[:4]:
                        concepts.append({"tty": c.get("tty", ""), "name": c.get("name", ""),
                                         "rxcui": c.get("rxcui", "")})
            return {"ok": bool(rxcui), "rxcui": rxcui, "concepts": concepts[:10],
                    "message_fa": "" if rxcui else "در RxNorm پیدا نشد — نام انگلیسی دقیق‌تر امتحان کن."}
        except Exception as e:
            return {"ok": False, "message_fa": "خطا در اتصال به RxNav: " + str(e)[:100]}

    def _live_fda_events(self, drug: str) -> dict:
        if not drug:
            return {"ok": False, "message_fa": "نام دارو را بده."}
        try:
            import urllib.parse as up
            base = "https://api.fda.gov/drug/event.json?limit=1"
            rx = up.quote(f'patient.drug.medicinalproduct:"{drug}"')
            cnt = self._http_json(
                f"https://api.fda.gov/drug/event.json?search={rx}&count=patient.reaction.reactionmeddrapt.exact&limit=12", 20)
            reactions = [(b.get("term", ""), b.get("count", 0)) for b in cnt.get("results", [])]
            n_reports = sum(c for _, c in reactions)
            return {"ok": True, "drug": drug, "total_reports_min": n_reports,
                    "reactions": reactions}
        except Exception as e:
            return {"ok": False, "message_fa": "خطا در اتصال به openFDA/FAERS: " + str(e)[:100]}

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
                from i18n import tt
                for provider, field in (("openrouter", "openrouter_key"), ("openai", "openai_key"), ("deepseek", "deepseek_key")):
                    v = data.get(field)
                    if v is not None and str(v).strip():
                        sv = str(v).strip()
                        if len(sv) < 10 or any(ch.isspace() for ch in sv):
                            return self._json({"ok": False, "changed": changed,
                                               "message_fa": tt("That does not look like a valid API key.", "این مقدار شبیه کلید API معتبر نیست.")}, 400)
                        if set_api_key(provider, sv):
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
            if path == "/api/pubmed":
                return self._json(self._live_pubmed(str(data.get("q") or "").strip()))
            if path == "/api/trials":
                return self._json(self._live_trials(str(data.get("q") or "").strip()))
            if path == "/api/rxnorm":
                return self._json(self._live_rxnorm(str(data.get("drug") or data.get("q") or "").strip()))
            if path == "/api/fda-events":
                return self._json(self._live_fda_events(str(data.get("drug") or "").strip()))
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
                # triage level from the urgency of the top candidates
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
            if path == "/api/doctor_mode":
                # doctor mode: special prompt + external AI or the offline brain
                text = str(data.get("text") or "").strip()
                if not text:
                    from i18n import tt
                    return self._json({"ok": False, "message_fa": tt("Describe a patient scenario first.", "یک سناریوی بیمار بنویسید.")}, 400)
                from ai_api_manager import get_api_key, get_settings
                from common_2077 import now_iso
                from patient_profile import load_profile
                s = get_settings()
                # build the 'a doctor answers' prompt «
                dlg = get_engine().dialogue.summary()
                prof = load_profile()
                scenario_prompt = f"""You are now in DOCTOR MODE. The user describes a patient scenario and you respond as an experienced physician explaining the differential diagnosis to a colleague. Be clinical, structured and specific. Use medical terminology but explain each term briefly in Farsi.

Patient scenario: {text}

Previous conversation context: symptoms={dlg.get("symptoms",[])}; turns={dlg.get("turns",0)}
Patient profile: {prof}

Structure your answer as:
1. Summary of the case (خلاصه‌ی کیس)
2. Differential diagnosis with probabilities (تشخیص افتراقی با احتمال)
3. Key distinguishing features between top differentials (نکات افتراقی)
4. Recommended workup (آزمایش‌ها و بررسی‌های پیشنهادی)
5. Immediate management considerations (درمان اولیه)
6. Red flags to watch for (علائم خطر)

Answer in Farsi. Be specific about medications (name them) but always note prescription requirement."""
                # try the external AI
                ext_res = None
                for p in [x for x in s["provider_order"] if x != "local" and get_api_key(x)]:
                    from ai_client import chat as ext_chat
                    mdl = s.get("openrouter_model") if p == "openrouter" else None
                    kw = {"reasoning_enabled": bool(s.get("reasoning_enabled")) and p == "openrouter"}
                    r = ext_chat(p, [{"role": "system", "content": "You are an experienced physician."},
                                     {"role": "user", "content": scenario_prompt}], model=mdl, max_tokens=2000, **kw)
                    if r.get("ok"):
                        ext_res = r
                        break
                if ext_res:
                    # auto-learning
                    try:
                        from auto_learning import learn_from_exchange
                        learn_from_exchange(f"[doctor-mode] {text[:200]}", ext_res["text"],
                                            provider=ext_res.get("provider", ""), model=ext_res.get("model", ""),
                                            meta={"mode": "doctor"})
                    except Exception:
                        pass
                    return self._json({"ok": True, "text": ext_res["text"], "source": f"doctor:{ext_res.get('provider','?')}", "learned": True})
                # fallback: offline brain
                from medical_engine import analyze
                a = analyze(text, load_profile())
                if a["red_flag"]:
                    from medical_engine import emergency_response
                    return self._json({"ok": True, "text": emergency_response(a["red_flag_reasons"]), "source": "doctor:internal-emergency", "red_flag": True})
                parts = []
                parts.append(" خلاصه‌ی کیس:")
                parts.append(f"  علائم: {'، '.join(a['symptoms']) if a['symptoms'] else '—'}")
                if a.get("duration_days"):
                    parts.append(f"  مدت: {a['detected']['duration_days']} روز")
                parts.append("")
                parts.append(" تشخیص افتراقی (مغز داخلی — برای تحلیل عمیق‌تر کلید OpenRouter را فعال کنید):")
                if a["candidates"]:
                    for c in a["candidates"][:5]:
                        parts.append(f"  • {c['name']} (~{c['percent']}%) [{c['urgency']}]")
                        if c.get("matched_symptoms"):
                            parts.append(f"    منطبق: {'، '.join(c['matched_symptoms'])}")
                        if c.get("doctor_when"):
                            parts.append(f"     {c['doctor_when']}")
                else:
                    parts.append("  اطلاعات کافی نیست — جزئیات بیشتری بنویسید.")
                parts.append("")
                parts.append(" بررسی‌های پیشنهادی:")
                parts.append("  • معاینه‌ی فیزیکی هدفمند بر اساس علائم")
                parts.append("  • آزمایش‌های عمومی: CBC, FBS, Cr, ALT/AST")
                parts.append("  • در صورت لزوم: تصویربرداری هدفمند")
                return self._json({"ok": True, "text": "\n".join(parts), "source": "doctor:internal", "learned": False})
            if path == "/api/who/profile":
                from who_connector import get_country_profile
                country = "IRN"
                return self._json(get_country_profile(country))
            if path == "/api/learning/status":
                from auto_learning import stats, recent
                from behavior_imitation import load_profile
                from semantic_rag import status as rag_status
                from i18n import is_fa
                fa = is_fa()
                labels = {
                    "entries": ("Learned entries", "موارد آموخته‌شده"),
                    "brain_on": ("Internal brain", "مغز داخلی"),
                    "style_samples": ("Style profile samples", "نمونه‌های سبک"),
                    "rag_docs": ("RAG indexed docs", "اسناد نمایه‌شده"),
                }
                st = get_engine().status()
                return self._json({"ok": True,
                    "entries": stats()["entries"],
                    "recent": recent(3),
                    "style_samples": load_profile().get("samples", 0),
                    "brain_on": st.get("settings", {}).get("brain_enabled", True),
                    "learning_active": True,
                    "note_fa": "یادگیری پس‌زمینه از هر پاسخ AI خارجی همیشه فعال است، حتی وقتی مغز داخلی خاموش است." if fa else
                               "Background learning from every external AI reply is always active, even when the internal brain is off."})
            if path == "/api/fda/search":
                from openfda_connector import search_adverse_events, search_drug_label, learn_from_fda
                drug = str(data.get("drug") or "").strip()
                mode = data.get("mode", "events")
                if not drug:
                    from i18n import tt
                    return self._json({"ok": False, "message_fa": tt("Enter a drug name.", "نام دارو را وارد کنید.")}, 400)
                if mode == "label":
                    res = search_drug_label(drug)
                elif mode == "learn":
                    res = learn_from_fda(drug)
                else:
                    res = search_adverse_events(drug)
                return self._json(res)
            if path == "/api/who/profile":
                from who_connector import get_country_profile, learn_who_data
                country = str(data.get("country") or "IRN").strip().upper()
                if data.get("learn"):
                    res = learn_who_data(country)
                else:
                    res = get_country_profile(country)
                return self._json(res)
            if path == "/api/trials/search":
                from clinical_trials_connector import search_trials
                res = search_trials(
                    condition=str(data.get("condition") or ""),
                    intervention=str(data.get("intervention") or ""),
                    status=str(data.get("status") or "RECRUITING"),
                    limit=min(int(data.get("limit") or 5), 10),
                )
                return self._json(res)
            if path == "/api/drugbank/info":
                from drugbank_connector import get_drug_info, search_by_atc, search_by_class, ATC_CATEGORIES, list_all
                drug_id = str(data.get("id") or "").strip()
                atc = str(data.get("atc") or "").strip()
                cls = str(data.get("class") or "").strip()
                if drug_id:
                    info = get_drug_info(drug_id)
                    return self._json({"ok": bool(info), "drug": info})
                if atc:
                    drugs = search_by_atc(atc)
                    return self._json({"ok": True, "drugs": drugs, "category": ATC_CATEGORIES.get(atc, "")})
                if cls:
                    drugs = search_by_class(cls)
                    return self._json({"ok": True, "drugs": drugs})
                return self._json({"ok": True, "all": list_all()})
            if path == "/api/settings/save_all":
                from ai_api_manager import save_settings, set_api_key
                from local_llm import save_config
                changed = []
                # API keys
                for provider, field in (("openrouter","openrouter_key"),("openai","openai_key"),("deepseek","deepseek_key")):
                    v = data.get(field)
                    if v and str(v).strip() and len(str(v).strip()) >= 10:
                        set_api_key(provider, str(v).strip())
                        changed.append(provider)
                # general settings
                updates = {}
                for key in ("language","brain_enabled","openrouter_model","reasoning_enabled"):
                    if key in data:
                        updates[key] = data[key]
                if updates:
                    save_settings(updates)
                    changed.extend(updates.keys())
                # Ollama
                llm_updates = {}
                for key in ("enabled","model","base_url"):
                    if key in data:
                        llm_updates[key] = data[key]
                if llm_updates:
                    save_config(llm_updates)
                    changed.append("local_llm")
                from i18n import tt
                return self._json({"ok": True, "changed": changed,
                    "message_fa": tt("All settings saved", "همه‌ی تنظیمات ذخیره شد")})
            if path == "/api/settings/full":
                from ai_api_manager import get_settings, save_settings, masked_keys, has_any_external, test_connection
                from local_llm import get_config as llm_config
                from i18n import is_fa
                from auto_learning import stats as learn_stats
                from semantic_rag import status as rag_status
                from ml_classifier import status as ml_status
                from medical_engine import DISEASES, SYMPTOM_KEYWORDS
                from drug_interaction import DRUGS, INTERACTIONS
                from common_2077 import DATA_DIR
                import os as _os
                fa = is_fa()
                L = lambda en, f: f if fa else en
                s = get_settings()
                st = get_engine().status()
                all_settings = {
                    "language": {"value": s["language"], "type": "choice", "options": ["en", "fa"], "label": L("Language", "زبان")},
                    "brain_enabled": {"value": s["brain_enabled"], "type": "bool", "label": L("Offline brain (diagnosis engine)", "مغز داخلی (موتور تشخیص)")},
                    "openrouter_model": {"value": s["openrouter_model"], "type": "text", "label": L("AI Model", "مدل هوش مصنوعی")},
                    "reasoning_enabled": {"value": s["reasoning_enabled"], "type": "bool", "label": L("Reasoning (uses more tokens)", "استدلال (توکن بیشتر)")},
                    "local_llm_enabled": {"value": llm_config().get("enabled", False), "type": "bool", "label": L("Local AI (Ollama)", "هوش محلی (Ollama)")},
                    "local_llm_model": {"value": llm_config().get("model", ""), "type": "text", "label": L("Local model", "مدل محلی")},
                }
                stats_block = {
                    "diseases": len(DISEASES),
                    "symptoms": len(SYMPTOM_KEYWORDS),
                    "drugs": len(DRUGS),
                    "interactions": len(INTERACTIONS),
                    "learning_entries": learn_stats()["entries"],
                    "rag_docs": rag_status().get("indexed_docs", 0),
                    "ml_ready": ml_status().get("ready", False),
                    "catalog_conditions": _DATA.get("conditions", 0),
                    "external_available": has_any_external(),
                    "masked_keys": masked_keys(),
                    "env_exists": _os.path.exists(_os.path.join(DATA_DIR, ".env")),
                }
                from medical_catalog import stats as cat_stats
                stats_block["catalog_conditions"] = cat_stats()["conditions"]
                stats_block["catalog_drugs"] = cat_stats()["drugs"]
                return self._json({"ok": True, "settings": all_settings, "stats": stats_block})
            if self._api_knowledge(path):
                return

            if path == "/api/catalog/search":
                from medical_catalog import search_conditions, search_drugs, stats, get_chapter_fa
                q = str(data.get("q") or "").strip()
                mode = data.get("mode", "all")
                if not q:
                    st = stats()
                    return self._json({"ok": True, "total_conditions": st["conditions"], "total_drugs": st["drugs"]})
                results = {}
                if mode in ("all", "conditions"):
                    conds = search_conditions(q, 20)
                    results["conditions"] = [{"name": c["name"], "icd10": c["icd10"],
                                              "chapter_fa": get_chapter_fa(c["icd10"])} for c in conds]
                if mode in ("all", "drugs"):
                    results["drugs"] = search_drugs(q, 20)
                return self._json({"ok": True, "query": q, **results})
            if path == "/api/learning/reset":
                from auto_learning import reset
                return self._json({"ok": reset()})
            if path == "/api/who/profile":
                from who_connector import get_country_profile
                country = "IRN"
                return self._json(get_country_profile(country))
            if path == "/api/learning/status":
                from auto_learning import stats, recent
                from behavior_imitation import load_profile
                st = get_engine().status()
                return self._json({"ok": True,
                    "entries": stats()["entries"],
                    "recent": recent(3),
                    "style_samples": load_profile().get("samples", 0),
                    "brain_on": st.get("settings", {}).get("brain_enabled", True),
                    "learning_active": True})
            if path == "/api/settings/full":
# same code lives in do_POST but the UI needs GET
                from ai_api_manager import get_settings, masked_keys, has_any_external
                from local_llm import get_config as llm_config
                from auto_learning import stats as learn_stats
                from semantic_rag import status as rag_status
                from ml_classifier import status as ml_status
                from medical_engine import DISEASES, SYMPTOM_KEYWORDS
                from drug_interaction import DRUGS, INTERACTIONS
                s = get_settings()
                lc = llm_config()
                all_settings = {
                    "language": {"value": s["language"], "type": "choice", "options": ["en", "fa"]},
                    "brain_enabled": {"value": s["brain_enabled"], "type": "bool"},
                    "openrouter_model": {"value": s["openrouter_model"], "type": "text"},
                    "reasoning_enabled": {"value": s["reasoning_enabled"], "type": "bool"},
                    "local_llm_enabled": {"value": lc.get("enabled", False), "type": "bool"},
                    "local_llm_model": {"value": lc.get("model", ""), "type": "text"},
                }
                from medical_catalog import stats as cat_stats
                cs = cat_stats()
                stats_block = {
                    "diseases": len(DISEASES), "symptoms": len(SYMPTOM_KEYWORDS),
                    "drugs": len(DRUGS), "interactions": len(INTERACTIONS),
                    "learning_entries": learn_stats()["entries"],
                    "rag_docs": rag_status().get("indexed_docs", 0),
                    "ml_ready": ml_status().get("ready", False),
                    "catalog_conditions": cs["conditions"],
                    "catalog_drugs": cs["drugs"],
                    "external_available": has_any_external(),
                    "masked_keys": masked_keys(),
                }
                return self._json({"ok": True, "settings": all_settings, "stats": stats_block})
            if path == "/api/conversations":
                from common_2077 import read_json, write_json, DATA_DIR
                import os as _os
                hist_path = _os.path.join(DATA_DIR, "conversation_history.json")
                hist = read_json(hist_path, default=[]) or []
                if self.command == "POST":
                    # save the current conversation before starting a new one
                    eng = get_engine()
                    dlg = eng.dialogue.summary()
                    if dlg.get("turns", 0) > 0 and (eng.memory or []):
                        conv = {
                            "ts": __import__("common_2077", fromlist=["now_iso"]).now_iso(),
                            "turns": dlg["turns"],
                            "symptoms": dlg.get("symptoms", []),
                            "messages": [{"role": m["role"], "content": m["content"][:500]} for m in eng.memory[-20:]],
                        }
                        hist.insert(0, conv)
                        hist = hist[:50]  # last 50 conversations
                        write_json(hist_path, hist)
                    # conversation reset
                    eng.dialogue.reset()
                    eng.memory = []
                    from auto_learning import stats as learn_stats
                    return self._json({"ok": True, "saved": True, "total_saved": len(hist), "learning": learn_stats()})
                return self._json({"ok": True, "conversations": hist[:20]})
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
        # warm up the ML model and RAG index so the first chat feels fast
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
