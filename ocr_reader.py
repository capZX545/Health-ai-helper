"""
ocr_reader.py — offline OCR for photos of lab reports and prescriptions
using the OCR engine built into Windows 10/11 (Windows.Media.Ocr via
PowerShell). No extra dependencies. On other systems it degrades to a
clear bilingual message.
"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
from typing import Any

from i18n import is_fa

_PS_SCRIPT = r"""
Add-Type -AssemblyName System.Runtime.WindowsRuntime | Out-Null
$null = [Windows.Media.Ocr.OcrEngine,Windows.Media.Ocr,ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime]
$null = [Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime]
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($WinRtTask, $ResultType) {
  $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
  $netTask = $asTask.Invoke($null, @($WinRtTask))
  $netTask.Wait(-1) | Out-Null
  $netTask.Result
}
$path = $args[0]
try {
  $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($path)) ([Windows.Storage.StorageFile])
  $stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
  $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
  $bmp = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
  $ocr = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
  if ($null -eq $ocr) { Write-Output "__NO_ENGINE__"; exit }
  $res = Await ($ocr.RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult])
  Write-Output $res.Text
} catch {
  Write-Output "__OCR_FAIL__"
}
"""


def ocr_available() -> bool:
    import sys
    return sys.platform.startswith("win")


def ocr_image(path_or_bytes) -> dict[str, Any]:
    fa = is_fa()
    import sys
    if not sys.platform.startswith("win"):
        return {"ok": False,
                "message_fa": ("OCR عکس فقط روی ویندوز ۱۰/۱۱ کار می‌کند — روی این سیستم متن را دستی وارد کن."
                               if fa else "Photo OCR works on Windows 10/11 only - type the text manually on this system.")}
    tmp_path = None
    path = path_or_bytes
    if isinstance(path_or_bytes, (bytes, bytearray)):
        fd, tmp_path = tempfile.mkstemp(suffix=".png")
        with os.fdopen(fd, "wb") as f:
            f.write(bytes(path_or_bytes))
        path = tmp_path
    try:
        ps_file = os.path.join(tempfile.gettempdir(), "nexusmed_ocr.ps1")
        with open(ps_file, "w", encoding="utf-8") as f:
            f.write(_PS_SCRIPT)
        r = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_file, str(path)],
            capture_output=True, text=True, timeout=90,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        out = (r.stdout or "").strip()
        if out == "__NO_ENGINE__":
            return {"ok": False,
                    "message_fa": ("موتور OCR ویندوز برای زبان‌های نصب‌شده فعال نیست. از Settings > Time & Language > Language یک بسته‌ی زبان (فارسی یا انگلیسی) با گپشن OCR اضافه کن."
                                   if fa else "The Windows OCR engine is not available for your installed languages. Add a language pack with OCR from Windows Settings > Time & Language > Language.")}
        if out == "__OCR_FAIL__" or not out:
            return {"ok": False,
                    "message_fa": ("از این عکس متنی خوانده نشد؛ عکس واضح‌تر، صاف و با نور کافی بگیر."
                                   if fa else "No text could be read from this photo; take a sharper, well-lit, straight photo.")}
        return {"ok": True, "text": out}
    except Exception as e:
        return {"ok": False, "message_fa": f"{e}"}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def ocr_and_lab(path_or_bytes) -> dict[str, Any]:
    fa = is_fa()
    r = ocr_image(path_or_bytes)
    if not r.get("ok"):
        return r
    text = r.get("text", "")
    from lab_visualizer import analyze_text
    res = analyze_text(text, save_html=False)
    res["ocr_text"] = text
    if not (res.get("found") or res.get("text_report")):
        res["message_fa"] = ("متنی از عکس خوانده شد اما آزمایش شناخته‌شده‌ای پیدا نشد — متن را بررسی و دستی اصلاح کن."
                             if fa else "Text was read from the photo but no known test was found - review and edit the text manually.")
    return res
