"""
i18n.py — language layer. English is the default language; Persian is fully
supported. The active language is stored in app_settings.json ("language")
and every user-facing module picks its strings through this module, so the
switch applies immediately without restarting anything.
"""
from __future__ import annotations

import threading

_lock = threading.RLock()
_override: str | None = None


_lang_cache: dict = {"stamp": None, "gen": -1, "value": "en"}


def get_lang() -> str:
    """Active language code: "en" (default) or "fa"; cached per settings file."""
    if _override in ("en", "fa"):
        return _override
    try:
        import os
        from ai_api_manager import SETTINGS_PATH, _SETTINGS_GEN
        stamp = (os.path.getmtime(SETTINGS_PATH), _SETTINGS_GEN)
        if _lang_cache["stamp"] == stamp:
            return _lang_cache["value"]
        from ai_api_manager import get_settings
        value = "fa" if get_settings().get("language") == "fa" else "en"
        _lang_cache.update({"stamp": stamp, "value": value})
        return value
    except Exception:
        return "en"


def set_lang(lang: str) -> str:
    """Persist the language choice."""
    global _override
    _override = None
    try:
        from ai_api_manager import save_settings
        save_settings({"language": "fa" if str(lang).startswith("fa") else "en"})
    except Exception:
        pass
    return get_lang()


def is_fa() -> bool:
    return get_lang() == "fa"


def tt(en: str, fa: str) -> str:
    """Pick a string for the active language."""
    return fa if is_fa() else en


def _get_setting_lang() -> str:
    try:
        from ai_api_manager import get_settings
        return "fa" if get_settings().get("language") == "fa" else "en"
    except Exception:
        return "en"


def set_override(lang: str | None) -> None:
    """Force a language for the current thread of work (used by tests)."""
    global _override
    _override = lang if lang in ("en", "fa") else None


def pick(pair: dict | tuple | list) -> any:
    """Pick from {"en": x, "fa": y} or (en, fa) structures."""
    if isinstance(pair, dict):
        return pair.get(get_lang()) or pair.get("en")
    if isinstance(pair, (tuple, list)) and len(pair) >= 2:
        return pair[1] if is_fa() else pair[0]
    return pair
