# -*- coding: utf-8 -*-
import json, os, threading, time
from datetime import datetime, date, timedelta

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
REM_FILE = os.path.join(DATA_DIR, "med_reminders.json")
PROFILE_FILE = os.path.join(DATA_DIR, "patient_profile.json")

_WEEKDAY_FA = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه", "شنبه", "یکشنبه"]
_WEEKDAY_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _load() -> list:
    try:
        return json.load(open(REM_FILE, encoding="utf-8"))
    except Exception:
        return []


def _save(rem: list) -> None:
    json.dump(rem, open(REM_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def add(drug: str, times: list, days: str = "daily") -> dict:
    rem = _load()
    r = {"id": max([x["id"] for x in rem], default=0) + 1,
         "drug": drug, "times": [t.strip() for t in times if t.strip()],
         "days": days, "active": True,
         "created": datetime.now().isoformat()[:19]}
    rem.append(r)
    _save(rem)
    return {"ok": True, "id": r["id"], "total": len(rem)}


def remove(rid: int) -> dict:
    rem = [r for r in _load() if r["id"] != rid]
    _save(rem)
    return {"ok": True, "total": len(rem)}


def toggle(rid: int) -> dict:
    rem = _load()
    for r in rem:
        if r["id"] == rid:
            r["active"] = not r.get("active", True)
    _save(rem)
    return {"ok": True}


def list_all() -> list:
    return _load()


def _due_now(rem: dict, now: datetime) -> str | None:
    if not rem.get("active", True):
        return None
    if rem.get("days") == "daily":
        pass
    else:
        try:
            allowed = [int(x) for x in rem["days"].split(",") if x.strip().isdigit()]
            if allowed and now.weekday() not in allowed:
                return None
        except Exception:
            pass
    for t in rem.get("times", []):
        try:
            hh, mm = t.split(":")[:2]
            due = now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
            delta = (now - due).total_seconds()
            if 0 <= delta <= 300:
                return t
        except Exception:
            continue
    return None


def check_due(now: datetime | None = None) -> list[dict]:
    now = now or datetime.now()
    out = []
    for r in _load():
        t = _due_now(r, now)
        if t:
            out.append({"id": r["id"], "drug": r["drug"], "time": t})
    return out


class ReminderService:
    def __init__(self, callback=None, interval=60):
        self.callback = callback
        self.interval = interval
        self._stop = threading.Event()
        self._fired: dict[str, str] = {}
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _loop(self):
        while not self._stop.wait(self.interval):
            try:
                self._tick()
            except Exception:
                pass

    def _tick(self):
        now = datetime.now()
        day_key = now.strftime("%Y-%m-%d")
        for due in check_due(now):
            key = f"{due['id']}:{due['time']}:{day_key}"
            if key not in self._fired:
                self._fired[key] = key
                if len(self._fired) > 500:
                    self._fired = {k: v for k, v in self._fired.items() if day_key in k}
                if self.callback:
                    try:
                        self.callback(due)
                    except Exception:
                        pass


def notify_windows(title: str, message: str) -> bool:
    try:
        from ctypes import windll, sizeof, structure
        return False
    except Exception:
        return False


def toast(title: str, message: str) -> None:
    import platform
    system = platform.system()
    if system == "Windows":
        _toast_windows(title, message)
    elif system == "Darwin":
        os.system(f'osascript -e \'display notification "{message}" with title "{title}"\'')
    else:
        try:
            os.system(f'notify-send "{title}" "{message}" 2>/dev/null &')
        except Exception:
            pass


def _toast_windows(title: str, message: str) -> None:
    try:
        import subprocess
        ps = (
            "$ErrorActionPreference='SilentlyContinue';"
            "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null;"
            "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null;"
            f"$xml = New-Object Windows.Data.Xml.Dom.XmlDocument;"
            f"$xml.LoadXml('<toast><visual><binding template=\"ToastGeneric\"><text>{title}</text><text>{message}</text></binding></visual></toast>');"
            "$toast = New-Object Windows.UI.Notifications.ToastNotification $xml;"
            "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('NexusMed 2077').Show($toast);"
        )
        subprocess.Popen(["powershell", "-WindowStyle", "Hidden", "-Command", ps],
                         creationflags=0x08000000 if hasattr(subprocess, "CREATE_NO_WINDOW") else 0)
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)
        except Exception:
            pass
