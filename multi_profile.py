# -*- coding: utf-8 -*-
import json, os

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILES_DIR = os.path.join(DATA_DIR, "profiles")
ACTIVE_FILE = os.path.join(DATA_DIR, "active_profile.json")

_PERSONAL = ["patient_profile.json", "vitals_history.json", "symptom_diary.json",
             "med_reminders.json", "learned_knowledge.json", "ai_behavior_profile.json"]


def _ensure_dir():
    os.makedirs(PROFILES_DIR, exist_ok=True)


def list_profiles() -> list[dict]:
    _ensure_dir()
    out = []
    for f in sorted(os.listdir(PROFILES_DIR)):
        if f.endswith(".json"):
            try:
                meta = json.load(open(os.path.join(PROFILES_DIR, f), encoding="utf-8"))
                out.append({"id": f[:-5], "name": meta.get("name", f[:-5]),
                            "age": meta.get("age", ""), "gender": meta.get("gender", "")})
            except Exception:
                out.append({"id": f[:-5], "name": f[:-5], "age": "", "gender": ""})
    return out


def create_profile(name: str, age: str = "", gender: str = "") -> dict:
    _ensure_dir()
    pid = name.strip().replace(" ", "_").lower() or "profile"
    base = pid
    n = 1
    while os.path.exists(os.path.join(PROFILES_DIR, pid + ".json")):
        n += 1
        pid = f"{base}_{n}"
    meta = {"name": name.strip(), "age": age, "gender": gender, "created": __import__("datetime").datetime.now().isoformat()[:19]}
    json.dump(meta, open(os.path.join(PROFILES_DIR, pid + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return {"ok": True, "id": pid, "name": name.strip()}


def _active_id() -> str:
    try:
        return json.load(open(ACTIVE_FILE, encoding="utf-8")).get("active", "default")
    except Exception:
        return "default"


def _set_active(pid: str) -> None:
    json.dump({"active": pid}, open(ACTIVE_FILE, "w", encoding="utf-8"))


def get_active() -> dict:
    _ensure_dir()
    pid = _active_id()
    for p in list_profiles():
        if p["id"] == pid:
            return p
    return {"id": "default", "name": "Default", "age": "", "gender": ""}


def switch_profile(pid: str) -> dict:
    _ensure_dir()
    profiles = {p["id"] for p in list_profiles()}
    if pid not in profiles:
        return {"ok": False, "message_fa": "پروفایل پیدا نشد", "message_en": "Profile not found"}
    old = _active_id()
    if old == pid:
        return {"ok": True, "id": pid, "switched": False}
    _archive(old)
    _restore(pid)
    _set_active(pid)
    return {"ok": True, "id": pid, "switched": True}


def _archive(pid: str) -> None:
    _ensure_dir()
    d = os.path.join(PROFILES_DIR, pid)
    os.makedirs(d, exist_ok=True)
    for f in _PERSONAL:
        src = os.path.join(DATA_DIR, f)
        if os.path.exists(src):
            os.replace(src, os.path.join(d, f))


def _restore(pid: str) -> None:
    d = os.path.join(PROFILES_DIR, pid)
    if not os.path.isdir(d):
        return
    for f in _PERSONAL:
        src = os.path.join(d, f)
        if os.path.exists(src):
            os.replace(src, os.path.join(DATA_DIR, f))


def delete_profile(pid: str) -> dict:
    _ensure_dir()
    if _active_id() == pid:
        return {"ok": False, "message_fa": "پروفایل فعال را نمی‌توان حذف کرد",
                "message_en": "Cannot delete the active profile"}
    import shutil
    meta = os.path.join(PROFILES_DIR, pid + ".json")
    data = os.path.join(PROFILES_DIR, pid)
    for p in (meta, data):
        if os.path.exists(p):
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    return {"ok": True}
