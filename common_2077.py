# -*- coding: utf-8 -*-
"""
Shared helpers for NexusMed 2077.
Zero external dependencies, stdlib only.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import threading
from datetime import datetime, timezone

APP_NAME = "NexusMed 2077"
APP_VERSION = "6.0.0"
DATA_DIR = _BASE = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__))

MEDICAL_DISCLAIMER_FA = (
    "این نرم‌افزار یک دستیار اطلاعاتی است، جایگزین پزشک نیست و تشخیص قطعی نمی‌دهد. "
    "در موارد اورژانسی فوراً با اورژانس تماس بگیرید (ایران: ۱۱۵ — اروپا: ۱۱۲)."
)
MEDICAL_DISCLAIMER_EN = (
    "This software is an informational assistant. It is not a substitute for a doctor "
    "and it does not give definitive diagnoses. In an emergency, call for help "
    "immediately (Iran: 115 - Europe: 112)."
)


def MEDICAL_DISCLAIMER() -> str:
    from i18n import tt
    return tt(MEDICAL_DISCLAIMER_EN, MEDICAL_DISCLAIMER_FA)

EMERGENCY_NUMBERS = {
    "ایران": {"اورژانس پزشکی": "115", "اورژانس اجتماعی": "123", "مشاوره تلفنی سلامت": "1480"},
    "اروپا/فنلاند": {"اورژانس": "112", "خط بحران (MIELI)": "113"},
}

_ENGINES_LOCK = threading.RLock()

# ---------------------------------------------------------------- date/time

def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def fa_digits(text) -> str:
    """
    Latin digits to Persian digits for display.
    """
    s = str(text)
    return s.translate(str.maketrans("0123456789.", "۰۱۲۳۴۵۶۷۸۹٫"))

# ---------------------------------------------------------- farsi normalization

_AR_TO_FA = str.maketrans({"ي": "ی", "ك": "ک", "ۀ": "ه", "ة": "ه", "أ": "ا", "إ": "ا", "آ": "ا", "\u200c": ""})
_FA_DIGIT_TO_EN = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

def normalize(text: str) -> str:
    """
    Normalize Persian text so compare/search works.
    """
    if not text:
        return ""
    t = str(text).translate(_AR_TO_FA)
    t = t.translate(_FA_DIGIT_TO_EN)
    t = t.replace("\u064b", "").replace("\u064c", "").replace("\u064d", "").replace("\u064e", "").replace("\u064f", "")
    t = re.sub(r"[\u200e\u200f\u202a-\u202e]", "", t)
    t = re.sub(r"[«»\"'ٌٍَُِّْ]", "", t)
    t = t.lower()
    t = re.sub(r"[^\w\sآ-ی]", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()

# ------------------------------------------------------------------ JSON IO

def read_json(path: str, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def write_json(path: str, data) -> bool:
    try:
        dirn = os.path.dirname(os.path.abspath(path))
        if dirn:
            os.makedirs(dirn, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=dirn or ".", suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
        return True
    except Exception:
        return False

# -------------------------------------------------------------------- .env

def load_env(path: str | None = None) -> dict:
    """
    Tiny .env loader without external deps.
    If .env is missing but .env.example exists, it copies it automatically.
    """
    path = path or os.path.join(_BASE, ".env")
    if not os.path.exists(path):
        example = os.path.join(_BASE, ".env.example")
        if os.path.exists(example):
            try:
                import shutil
                shutil.copy2(example, path)
                print("[setup] .env created from .env.example")
            except Exception:
                pass
    env = {}
    if not os.path.exists(path):
        return env
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return env

def env_get(key: str, default: str = "") -> str:
    v = os.environ.get(key)
    if v:
        return v
    return load_env().get(key, default)

def env_set(key: str, value: str, path: str | None = None) -> bool:
    """
    Write/update one key in .env without touching the other secrets.
    """
    path = path or os.path.join(_BASE, ".env")
    lines = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                lines = f.read().splitlines()
        except Exception:
            lines = []
    found = False
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s and not s.startswith("#") and s.split("=", 1)[0].strip() == key:
            lines[i] = f"{key}={value}"
            found = True
            break
    if not found:
        lines.append(f"{key}={value}")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        os.environ[key] = value
        return True
    except Exception:
        return False

def mask_secret(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 10:
        return key[:3] + "••••"
    return key[:6] + "••••••••"+ key[-4:]

# ----------------------------------------------------------------- text

def first_sentences(text: str, n: int = 2, max_chars: int = 320) -> str:
    parts = re.split(r"(?<=[.!؟?])\s+", (text or "").strip())
    out = " ".join(parts[:n]).strip()
    return out[:max_chars]

def is_question(line: str) -> bool:
    return "?" in (line or "") or "؟" in (line or "")

def clamp(v, lo, hi):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return lo
    return max(lo, min(hi, v))

def safe_percent(p: float) -> int:
    return int(round(clamp(p, 0.0, 100.0)))
