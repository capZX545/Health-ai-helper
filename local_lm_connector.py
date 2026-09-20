import json, os, urllib.request

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
CFG_FILE = os.path.join(DATA_DIR, "local_lm_config.json")


def _cfg() -> dict:
    try:
        return json.load(open(CFG_FILE, encoding="utf-8"))
    except Exception:
        return {"enabled": False, "base_url": "http://localhost:1234", "model": ""}


def _save(cfg: dict) -> None:
    json.dump(cfg, open(CFG_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def is_enabled() -> bool:
    return _cfg().get("enabled", False)


def set_enabled(on: bool) -> None:
    cfg = _cfg()
    cfg["enabled"] = on
    _save(cfg)


def set_config(base_url: str, model: str) -> None:
    cfg = _cfg()
    cfg["base_url"] = base_url.rstrip("/")
    cfg["model"] = model
    _save(cfg)


def get_config() -> dict:
    return _cfg()


def _post(url: str, payload: dict, timeout: int = 60) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def list_models() -> list[str]:
    cfg = _cfg()
    base = cfg.get("base_url", "http://localhost:1234")
    try:
        req = urllib.request.Request(base + "/v1/models", method="GET")
        with urllib.request.urlopen(req, timeout=5) as r:
            d = json.loads(r.read())
        return [m.get("id", "") for m in d.get("data", [])]
    except Exception:
        return []


def test_connection() -> dict:
    cfg = _cfg()
    base = cfg.get("base_url", "http://localhost:1234")
    try:
        req = urllib.request.Request(base + "/v1/models", method="GET")
        with urllib.request.urlopen(req, timeout=5) as r:
            json.loads(r.read())
        models = list_models()
        return {"ok": True, "models": models,
                "message_fa": f"اتصال برقرار است — {len(models)} مدل موجود",
                "message_en": f"Connected — {len(models)} model(s) available"}
    except Exception as e:
        return {"ok": False, "models": [],
                "message_fa": "اتصال برقرار نشد. LM Studio را باز کن و Local Server را روشن کن (پورت 1234).",
                "message_en": "Cannot connect. Open LM Studio and start the Local Server (port 1234)."}


def chat(messages: list[dict], temperature: float = 0.4, max_tokens: int = 800) -> dict:
    cfg = _cfg()
    base = cfg.get("base_url", "http://localhost:1234")
    model = cfg.get("model", "")
    if not model:
        models = list_models()
        model = models[0] if models else "local-model"
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
    cfg = _cfg()
    base = cfg.get("base_url", "http://localhost:1234")
    model = cfg.get("model", "")
    if not model:
        models = list_models()
        model = models[0] if models else "local-model"
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
