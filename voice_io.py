"""
voice_io.py — text-to-speech and speech-to-text through the operating
system's built-in engines, so it stays fully offline:
Windows: SAPI via PowerShell, macOS: say, Linux: espeak/spd-say.
No external dependencies; every call degrades gracefully.
"""
from __future__ import annotations

import re
import subprocess
import threading
from typing import Any

from i18n import is_fa

_FA_CHARS = re.compile(r"[\u0600-\u06FF]")


def _clean_for_speech(text: str) -> str:
    t = str(text or "")
    t = re.sub(r"[*#`_>~|]+", " ", t)
    t = re.sub(r"https?://\S+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:1200]


def has_persian(text: str) -> bool:
    return bool(_FA_CHARS.search(str(text or "")))


def tts_available() -> bool:
    import sys
    if sys.platform.startswith("win"):
        return True
    if sys.platform == "darwin":
        return True
    for exe in ("espeak", "spd-say"):
        try:
            subprocess.run(["which", exe], capture_output=True, timeout=4)
            r = subprocess.run(["which", exe], capture_output=True, text=True, timeout=4)
            if r.returncode == 0:
                return True
        except Exception:
            continue
    return False


def speak(text: str, wait: bool = False) -> dict[str, Any]:
    fa = is_fa()
    t = _clean_for_speech(text)
    if not t:
        return {"ok": False, "message_fa": "متنی برای خواندن نیست." if fa else "No text to read."}
    import sys
    try:
        if sys.platform.startswith("win"):
            lang_xml = "fa-IR" if has_persian(t) else "en-US"
            ps = ("Add-Type -AssemblyName System.Speech;"
                  "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
                  "try { $v = $s.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -like '" + lang_xml[:2] + "*' } | Select-Object -First 1; if ($v) { $s.SelectVoice($v.VoiceInfo.Name) } } catch {};"
                  "$s.Speak([Runtime.InteropServices.Marshal]::StringToBSTR('" + t.replace("'", "''") + "'));")
            proc = subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
                                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            if wait:
                proc.wait(timeout=90)
            return {"ok": True, "message_fa": "در حال خواندن..." if fa else "Speaking..."}
        if sys.platform == "darwin":
            voice = "Tara" if has_persian(t) else "Samantha"
            subprocess.Popen(["say", "-v", voice, t])
            return {"ok": True, "message_fa": "در حال خواندن..." if fa else "Speaking..."}
        for exe, vflag in (("spd-say", None), ("espeak", None)):
            try:
                cmd = [exe]
                if has_persian(t) and exe == "espeak":
                    cmd += ["-v", "fa"]
                cmd.append(t)
                subprocess.run(cmd, capture_output=True, timeout=60)
                return {"ok": True, "message_fa": "خوانده شد." if fa else "Spoken."}
            except FileNotFoundError:
                continue
            except Exception:
                continue
        return {"ok": False, "message_fa": "موتور صوتی در این سیستم پیدا نشد." if fa
                else "No speech engine found on this system."}
    except Exception as e:
        return {"ok": False, "message_fa": f"{e}"}


def speak_async(text: str) -> None:
    threading.Thread(target=lambda: speak(text), daemon=True).start()


def stt_available() -> bool:
    import sys
    return sys.platform.startswith("win")


def listen(timeout_sec: int = 10) -> dict[str, Any]:
    fa = is_fa()
    import sys
    if not sys.platform.startswith("win"):
        return {"ok": False, "message_fa": "ورودی صوتی فقط روی ویندوز پشتیبانی می‌شود." if fa
                else "Voice input is only supported on Windows."}
    t = max(3, min(int(timeout_sec or 10), 30))
    ps = (
        "Add-Type -AssemblyName System.Speech;"
        "$r = New-Object System.Speech.Recognition.SpeechRecognitionEngine;"
        "$r.SetInputToDefaultAudioDevice();"
        "$g = New-Object System.Speech.Recognition.DictationGrammar;"
        "$r.LoadGrammar($g);"
        f"$r.InitialSilenceTimeout = New-Object System.TimeSpan(0,0,{t});"
        "try { $res = $r.Recognize(); if ($res) { Write-Output $res.Text } else { Write-Output '' } }"
        "catch { Write-Output '' }"
    )
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
                           capture_output=True, text=True, timeout=t + 20,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        said = (r.stdout or "").strip()
        if said:
            return {"ok": True, "text": said}
        return {"ok": False, "message_fa": "صدایی شنیده نشد؛ دوباره امتحان کن و واضح‌تر صحبت کن." if fa
                else "No speech detected; try again and speak clearly."}
    except Exception as e:
        return {"ok": False, "message_fa": f"{e}"}
