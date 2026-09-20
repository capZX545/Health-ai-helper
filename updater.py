"""
updater.py — checks GitHub for a newer NexusMed release, downloads the
Windows setup and launches it. Works fully offline-safe: without internet
every call fails silently and the app keeps running.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from typing import Any

from common_2077 import APP_VERSION
from i18n import is_fa

REPO = "capZX545/Health-ai-helper"
API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
TIMEOUT = 8


def _ver_tuple(v: str) -> tuple:
    nums = []
    for part in re.findall(r"\d+", str(v or "")):
        try:
            nums.append(int(part))
        except ValueError:
            nums.append(0)
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums[:3])


def _get(url: str, headers: dict[str, str] | None = None, timeout: int = TIMEOUT) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "NexusMed2077-Updater", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def check_latest(timeout: int = TIMEOUT) -> dict[str, Any]:
    fa = is_fa()
    try:
        raw = _get(API_URL, headers={"Accept": "application/vnd.github+json"}, timeout=timeout)
        rel = json.loads(raw.decode("utf-8"))
    except Exception:
        return {"ok": False, "offline": True, "newer": False,
                "message_fa": "اتصال به گیت‌هاب ممکن نشد (آفلاین؟)." if fa
                else "Could not reach GitHub (offline?)."}
    tag = str(rel.get("tag_name") or "").lstrip("v")
    asset_url = ""
    asset_size = 0
    for a in rel.get("assets") or []:
        name = str(a.get("name") or "")
        if name.lower().endswith(".exe") and "setup" in name.lower():
            asset_url = str(a.get("browser_download_url") or "")
            asset_size = int(a.get("size") or 0)
            break
    newer = _ver_tuple(tag) > _ver_tuple(APP_VERSION)
    return {
        "ok": True, "offline": False, "newer": newer,
        "current": APP_VERSION, "latest": tag,
        "release_url": rel.get("html_url") or "",
        "download_url": asset_url,
        "download_size": asset_size,
        "published_at": rel.get("published_at") or "",
        "message_fa": "",
    }


def download_and_run(url: str) -> dict[str, Any]:
    fa = is_fa()
    if not url:
        return {"ok": False, "message_fa": "لینک دانلود پیدا نشد." if fa else "Download link not found."}
    try:
        blob = _get(url, timeout=300)
    except Exception as e:
        return {"ok": False, "message_fa": f"دانلود ناموفق: {e}" if fa else f"Download failed: {e}"}
    path = os.path.join(tempfile.gettempdir(), "NexusMed_Setup_new.exe")
    try:
        with open(path, "wb") as f:
            f.write(blob)
    except Exception as e:
        return {"ok": False, "message_fa": f"{e}"}
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)
        else:
            subprocess.Popen([path])
    except Exception as e:
        return {"ok": True, "path": path, "launched": False,
                "message_fa": (f"دانلود شد: {path} (اجرا خودکار ممکن نشد: {e})" if fa
                               else f"Downloaded: {path} (auto-run failed: {e})")}
    return {"ok": True, "path": path, "launched": True,
            "message_fa": ("نصاب جدید دانلود و اجرا شد — برنامه را ببند و نصب را تمام کن."
                           if fa else "New installer downloaded and launched - close the app and finish the install.")}
