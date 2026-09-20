"""
secure_store.py — a zero-dependency data vault for personal health files.
Pure-python ChaCha20 (RFC 8439) keystream + HMAC-SHA256 authentication +
PBKDF2-HMAC-SHA256 key derivation, all from the standard library.
Lock moves the personal JSON files into one encrypted vault file;
unlock restores them. If the password is lost the data cannot be recovered.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import struct
from typing import Any

from common_2077 import DATA_DIR
from i18n import is_fa

VAULT_PATH = os.path.join(DATA_DIR, "health_vault.nmv")
MAGIC = b"NMVAULT1"
PBKDF2_ROUNDS = 200_000
SALT_LEN = 16
NONCE_LEN = 12
KEY_LEN = 32

PROTECTED_FILES = [
    "patient_profile.json",
    "vitals_history.json",
    "med_reminders.json",
    "symptom_diary.json",
    "ice_card.json",
    "conversation_history.json",
    "cycle_log.json",
    "family_history.json",
    "learned_knowledge.json",
    "ai_behavior_profile.json",
    "app_settings.json",
]


def _rotl(v: int, c: int) -> int:
    return ((v << c) & 0xFFFFFFFF) | (v >> (32 - c))


def _quarter(s: list[int], a: int, b: int, c: int, d: int) -> None:
    s[a] = (s[a] + s[b]) & 0xFFFFFFFF
    s[d] ^= s[a]
    s[d] = _rotl(s[d], 16)
    s[c] = (s[c] + s[d]) & 0xFFFFFFFF
    s[b] ^= s[c]
    s[b] = _rotl(s[b], 12)
    s[a] = (s[a] + s[b]) & 0xFFFFFFFF
    s[d] ^= s[a]
    s[d] = _rotl(s[d], 8)
    s[c] = (s[c] + s[d]) & 0xFFFFFFFF
    s[b] ^= s[c]
    s[b] = _rotl(s[b], 7)


def chacha20_block(key: bytes, nonce: bytes, counter: int) -> bytes:
    constants = [0x61707865, 0x3320646E, 0x79622D32, 0x6B206574]
    k = list(struct.unpack("<8I", key[:32]))
    n = list(struct.unpack("<3I", nonce[:12]))
    state = constants + k + [counter & 0xFFFFFFFF] + n
    working = list(state)
    for _ in range(10):
        _quarter(working, 0, 4, 8, 12)
        _quarter(working, 1, 5, 9, 13)
        _quarter(working, 2, 6, 10, 14)
        _quarter(working, 3, 7, 11, 15)
        _quarter(working, 0, 5, 10, 15)
        _quarter(working, 1, 6, 11, 12)
        _quarter(working, 2, 7, 8, 13)
        _quarter(working, 3, 4, 9, 14)
    out = [(working[i] + state[i]) & 0xFFFFFFFF for i in range(16)]
    return struct.pack("<16I", *out)


def chacha20_xor(key: bytes, nonce: bytes, data: bytes) -> bytes:
    out = bytearray()
    for i in range(0, len(data), 64):
        block = chacha20_block(key, nonce, i // 64 + 1)
        chunk = data[i:i + 64]
        out.extend(bytes(a ^ b for a, b in zip(chunk, block)))
    return bytes(out)


def derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS, dklen=KEY_LEN)


def encrypt_bytes(password: str, data: bytes) -> bytes:
    salt = os.urandom(SALT_LEN)
    nonce = os.urandom(NONCE_LEN)
    key = derive_key(password, salt)
    ct = chacha20_xor(key, nonce, data)
    tag = hmac.new(key, salt + nonce + ct, hashlib.sha256).digest()
    return MAGIC + salt + nonce + tag + ct


def decrypt_bytes(password: str, blob: bytes) -> bytes:
    if len(blob) < len(MAGIC) + SALT_LEN + NONCE_LEN + 32:
        raise ValueError("vault file is too short")
    if blob[:len(MAGIC)] != MAGIC:
        raise ValueError("not a NexusMed vault file")
    off = len(MAGIC)
    salt = blob[off:off + SALT_LEN]
    off += SALT_LEN
    nonce = blob[off:off + NONCE_LEN]
    off += NONCE_LEN
    tag = blob[off:off + 32]
    off += 32
    ct = blob[off:]
    key = derive_key(password, salt)
    good = hmac.compare_digest(hmac.new(key, salt + nonce + ct, hashlib.sha256).digest(), tag)
    if not good:
        raise ValueError("wrong password or corrupted vault")
    return chacha20_xor(key, nonce, ct)


def status() -> dict[str, Any]:
    fa = is_fa()
    locked = os.path.exists(VAULT_PATH)
    if locked:
        try:
            size = os.path.getsize(VAULT_PATH)
        except Exception:
            size = 0
        return {"ok": True, "locked": True, "size": size,
                "message_fa": "داده‌های سلامت قفل هستند." if fa else "Health data is locked."}
    return {"ok": True, "locked": False,
            "message_fa": "داده‌های سلامت باز (رمزنگاری نشده)." if fa else "Health data is unlocked (not encrypted)."}


def lock(password: str, paths: list[str] | None = None, vault_path: str | None = None) -> dict[str, Any]:
    fa = is_fa()
    vp = vault_path or VAULT_PATH
    if os.path.exists(vp):
        return {"ok": False, "message_fa": "قبلاً قفل شده؛ اول باز کن." if fa else "Already locked; unlock first."}
    if not password or len(password) < 4:
        return {"ok": False, "message_fa": "رمز حداقل ۴ نویسه باشد." if fa else "Password must be at least 4 characters."}
    files: dict[str, str] = {}
    used: list[str] = []
    for name in (paths or [os.path.join(DATA_DIR, f) for f in PROTECTED_FILES]):
        if os.path.exists(name) and os.path.getsize(name) > 0:
            with open(name, "rb") as f:
                raw = f.read()
            if raw.strip():
                files[os.path.basename(name)] = base64.b64encode(raw).decode("ascii")
                used.append(name)
    if not files:
        return {"ok": False, "message_fa": "فایلی برای قفل کردن پیدا نشد." if fa else "No files found to lock."}
    blob = encrypt_bytes(password, json.dumps({"files": files}, ensure_ascii=False).encode("utf-8"))
    check = decrypt_bytes(password, blob)
    if json.loads(check.decode("utf-8")).get("files") != files:
        return {"ok": False, "message_fa": "خطای داخلی رمزنگاری؛ عملیات لغو شد." if fa
                else "Internal encryption error; operation aborted."}
    with open(vp, "wb") as f:
        f.write(blob)
    for name in used:
        try:
            os.remove(name)
        except Exception:
            pass
    return {"ok": True, "locked_files": len(files),
            "message_fa": (f"{len(files)} فایل با رمزنگاری ChaCha20 قفل شد. رمزت را گم نکن — بدون آن بازگشتی وجود ندارد."
                           if fa else f"{len(files)} files locked with ChaCha20 encryption. Do not lose the password - there is no recovery.")}


def unlock(password: str, vault_path: str | None = None, out_dir: str | None = None) -> dict[str, Any]:
    fa = is_fa()
    vp = vault_path or VAULT_PATH
    if not os.path.exists(vp):
        return {"ok": False, "message_fa": "خزانه‌ی قفل‌شده‌ای وجود ندارد." if fa else "No locked vault exists."}
    try:
        with open(vp, "rb") as f:
            blob = f.read()
        data = json.loads(decrypt_bytes(password, blob).decode("utf-8"))
    except ValueError as e:
        msg = "wrong password or corrupted vault" if "wrong password" in str(e) else str(e)
        return {"ok": False, "message_fa": ("رمز اشتباه است." if fa else "Wrong password.") if "wrong" in msg else msg}
    except Exception as e:
        return {"ok": False, "message_fa": f"{e}"}
    files = data.get("files") or {}
    if not files:
        return {"ok": False, "message_fa": "خزانه خالی است." if fa else "Vault is empty."}
    base = out_dir or DATA_DIR
    restored = 0
    try:
        for name, b64 in files.items():
            name = os.path.basename(str(name))
            with open(os.path.join(base, name), "wb") as f:
                f.write(base64.b64decode(b64))
            restored += 1
        os.remove(vp)
    except Exception as e:
        return {"ok": False, "restored": restored, "message_fa": f"{e}"}
    return {"ok": True, "restored": restored,
            "message_fa": (f"{restored} فایل بازگردانی شد و رمزنگاری برداشته شد."
                           if fa else f"{restored} files restored and encryption removed.")}


def backup_to(password: str, dest_path: str) -> dict[str, Any]:
    fa = is_fa()
    if not password or len(password) < 4:
        return {"ok": False, "message_fa": "رمز حداقل ۴ نویسه باشد." if fa else "Password must be at least 4 characters."}
    if not dest_path:
        return {"ok": False, "message_fa": "مسیر فایل پشتیبان را بده." if fa else "Give the backup file path."}
    files: dict[str, str] = {}
    for name in [os.path.join(DATA_DIR, f) for f in PROTECTED_FILES]:
        if os.path.exists(name) and os.path.getsize(name) > 0:
            with open(name, "rb") as f:
                raw = f.read()
            if raw.strip():
                files[os.path.basename(name)] = base64.b64encode(raw).decode("ascii")
    if not files:
        return {"ok": False, "message_fa": "فایل شخصی‌ای برای پشتیبان پیدا نشد." if fa else "No personal files found to back up."}
    blob = encrypt_bytes(password, json.dumps({"files": files}, ensure_ascii=False).encode("utf-8"))
    try:
        os.makedirs(os.path.dirname(os.path.abspath(dest_path)) or ".", exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(blob)
    except Exception as e:
        return {"ok": False, "message_fa": str(e)}
    return {"ok": True, "files": len(files), "path": dest_path,
            "message_fa": (f"پشتیبان رمزنگاری‌شده‌ی {len(files)} فایل ساخته شد: {dest_path}"
                           if fa else f"Encrypted backup of {len(files)} files created: {dest_path}")}


def restore_from(password: str, src_path: str, out_dir: str | None = None) -> dict[str, Any]:
    fa = is_fa()
    if not os.path.exists(src_path):
        return {"ok": False, "message_fa": "فایل پشتیبان پیدا نشد." if fa else "Backup file not found."}
    try:
        with open(src_path, "rb") as f:
            blob = f.read()
        data = json.loads(decrypt_bytes(password, blob).decode("utf-8"))
    except ValueError as e:
        return {"ok": False, "message_fa": ("رمز اشتباه است." if "wrong password" in str(e) else str(e))
                if fa and "wrong password" in str(e) else ("Wrong password." if "wrong password" in str(e) else str(e))}
    except Exception as e:
        return {"ok": False, "message_fa": str(e)}
    files = data.get("files") or {}
    base = out_dir or DATA_DIR
    restored = 0
    try:
        for name, b64 in files.items():
            name = os.path.basename(str(name))
            with open(os.path.join(base, name), "wb") as f:
                f.write(base64.b64decode(b64))
            restored += 1
    except Exception as e:
        return {"ok": False, "message_fa": str(e)}
    return {"ok": True, "restored": restored,
            "message_fa": (f"{restored} فایل بازگردانی شد." if fa else f"{restored} files restored.")}
