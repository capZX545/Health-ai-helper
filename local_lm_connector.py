import json, os, threading, time, urllib.request

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
CFG_FILE = os.path.join(DATA_DIR, "lm_studio_config.json")

_DEFAULTS = {"enabled": False, "auto": True, "base_url": "http://localhost:1234", "model": ""}
_lock = threading.RLock()
_detect = {"ts": 0.0, "found": False, "base_url": "", "models": []}
_watch_started = False
PROBE_TIMEOUT = 0.8
CACHE_TTL = 45.0
FOUND_TTL = 300.0


def _cfg() -> dict:
    try:
        d = json.load(open(CFG_FILE, encoding="utf-8"))
        if isinstance(d, dict):
            merged = dict(_DEFAULTS)
            merged.update(d)
            return merged
    except Exception:
        pass
    return dict(_DEFAULTS)


def _save(cfg: dict) -> None:
    try:
        json.dump(cfg, open(CFG_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:
        pass


def _candidates() -> list[str]:
    cfg = _cfg()
    seen: list[str] = []
    for u in (os.environ.get("LMSTUDIO_URL", ""), cfg.get("base_url", ""),
              "http://localhost:1234", "http://127.0.0.1:1234",
              "http://localhost:1235", "http://127.0.0.1:1235"):
        u = str(u or "").strip().rstrip("/")
        if u and u not in seen:
            seen.append(u)
    return seen


def _probe(base: str) -> list[str]:
    try:
        req = urllib.request.Request(base + "/v1/models", method="GET")
        with urllib.request.urlopen(req, timeout=PROBE_TIMEOUT) as r:
            d = json.loads(r.read())
        return [m.get("id", "") for m in d.get("data", []) if m.get("id")]
    except Exception:
        return []


def autodiscover(force: bool = False) -> dict:
    with _lock:
        if not force and (time.time() - _detect["ts"]) < CACHE_TTL:
            return dict(_detect)
    cfg = _cfg()
    for base in _candidates():
        models = _probe(base)
        if models:
            with _lock:
                _detect.update({"ts": time.time(), "found": True,
                                "base_url": base, "models": models})
            if cfg.get("base_url", "") != base or not cfg.get("model") or cfg.get("model") not in models:
                new_cfg = dict(cfg)
                new_cfg["base_url"] = base
                if not new_cfg.get("model") or new_cfg["model"] not in models:
                    new_cfg["model"] = models[0]
                _save(new_cfg)
            return dict(_detect)
    with _lock:
        _detect.update({"ts": time.time(), "found": False, "base_url": "", "models": []})
    return dict(_detect)


def detect_status(force: bool = False) -> dict:
    return autodiscover(force=force)


def start_watch(interval: float = 45.0) -> None:
    global _watch_started
    with _lock:
        if _watch_started:
            return
        _watch_started = True

    def loop():
        while True:
            try:
                autodiscover(force=False)
            except Exception:
                pass
            time.sleep(interval)

    threading.Thread(target=loop, daemon=True).start()


def is_enabled() -> bool:
    return bool(_cfg().get("enabled", False))


def set_enabled(on: bool) -> None:
    cfg = _cfg()
    cfg["enabled"] = bool(on)
    cfg["auto"] = bool(on)
    _save(cfg)


def set_auto(on: bool) -> None:
    cfg = _cfg()
    cfg["auto"] = bool(on)
    _save(cfg)


def is_active() -> bool:
    cfg = _cfg()
    if cfg.get("enabled"):
        return True
    if not cfg.get("auto", True):
        return False
    with _lock:
        fresh = (time.time() - _detect["ts"]) < FOUND_TTL
        return bool(_detect["found"] and fresh)


def set_config(base_url: str, model: str) -> None:
    cfg = _cfg()
    cfg["base_url"] = base_url.rstrip("/")
    cfg["model"] = model
    _save(cfg)


def get_config() -> dict:
    return _cfg()


def _target() -> tuple[str, str]:
    cfg = _cfg()
    with _lock:
        base = _detect["base_url"] if _detect["found"] else ""
        models = list(_detect["models"]) if _detect["found"] else []
    if not base:
        base = cfg.get("base_url", "http://localhost:1234")
    model = cfg.get("model", "")
    if models:
        if not model or model not in models:
            model = models[0]
    if not model:
        model = "local-model"
    return base, model


def _post(url: str, payload: dict, timeout: int = 60) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def list_models() -> list[str]:
    base, _ = _target()
    try:
        req = urllib.request.Request(base + "/v1/models", method="GET")
        with urllib.request.urlopen(req, timeout=5) as r:
            d = json.loads(r.read())
        return [m.get("id", "") for m in d.get("data", [])]
    except Exception:
        return []


def test_connection() -> dict:
    base, _ = _target()
    try:
        req = urllib.request.Request(base + "/v1/models", method="GET")
        with urllib.request.urlopen(req, timeout=5) as r:
            json.loads(r.read())
        models = list_models()
        return {"ok": True, "models": models,
                "message_fa": f"اتصال برقرار است — {len(models)} مدل موجود",
                "message_en": f"Connected — {len(models)} model(s) available"}
    except Exception:
        return {"ok": False, "models": [],
                "message_fa": "اتصال برقرار نشد. LM Studio را باز کن و Local Server را روشن کن (پورت 1234).",
                "message_en": "Cannot connect. Open LM Studio and start the Local Server (port 1234)."}


def chat(messages: list[dict], temperature: float = 0.4, max_tokens: int = 800) -> dict:
    base, model = _target()
    try:
        r = _post(base + "/v1/chat/completions", {
            "model": model, "messages": messages,
            "temperature": temperature, "max_tokens": max_tokens,
        })
        text = r["choices"][0]["message"]["content"]
        return {"ok": True, "text": text, "model": model}
    except Exception as e:
        return {"ok": False, "error": str(e)[:120],
                "error_fa": "خطا در اتصال به LM Studio: " + str(e)[:80]}


def chat_stream(messages: list, temperature: float = 0.4, max_tokens: int = 800,
                timeout: int = 120):
    base, model = _target()
    payload = json.dumps({
        "model": model, "messages": messages,
        "temperature": temperature, "max_tokens": max_tokens, "stream": True,
    }).encode()
    req = urllib.request.Request(base + "/v1/chat/completions", data=payload, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        for raw in r:
            line = raw.decode("utf-8", "ignore").strip()
            if not line.startswith("data:"):
                continue
            data_str = line[5:].strip()
            if data_str == "[DONE]":
                break
            try:
                obj = json.loads(data_str)
            except Exception:
                continue
            try:
                delta = obj["choices"][0].get("delta", {}).get("content")
            except Exception:
                delta = None
            if delta:
                yield delta
