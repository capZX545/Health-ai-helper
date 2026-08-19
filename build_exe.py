# -*- coding: utf-8 -*-
"""
build_exe.py — ساخت فایل اجرایی ویندوز با PyInstaller (روی ویندوز اجرا شود).
خروجی: dist/NexusMed2077/NexusMed2077.exe  (+ پوشه‌ی داده‌ها)
سپس Create_Setup_Installer.bat با Inno Setup فایل Setup می‌سازد.
"""
from __future__ import annotations

import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
APP_NAME = "NexusMed2077"

# فایل‌های داده‌ای که باید کنار EXE کپی شوند
DATA_FILES = [
    "clinic_2077.html",
    "diseases_extra.json",
    "diseases_offline.db",
    "medical_ml_test_dataset.csv",
    ".env.example",
    "requirements.txt",
]


def run(cmd: list[str]) -> int:
    print(">>", " ".join(cmd))
    return subprocess.call(cmd, cwd=BASE)


def main() -> int:
    if sys.platform.startswith("win"):
        pyinstaller = [sys.executable, "-m", "PyInstaller"]
    else:
        print("شما روی لینوکس هستید؛ EXE واقعی ویندوز فقط روی ویندوز ساخته می‌شود.")
        print("این اسکریپت را روی ویندوز (پس از نصب Python و PyInstaller) اجرا کنید.")
        return 1

    sep = ";" if sys.platform.startswith("win") else ":"
    add_data = [a for f in ("clinic_2077.html", "diseases_extra.json", "medical_ml_test_dataset.csv", ".env.example") for a in ("--add-data", f + sep + ".")]

    cmd = pyinstaller + [
        "--noconfirm", "--clean", "--windowed", "--onedir",
        "--name", APP_NAME,
        "--collect-submodules", "sklearn",
        *add_data,
        os.path.join(BASE, "run_2077.py"),
    ]
    code = run(cmd)
    if code != 0:
        print("ساخت EXE ناموفق بود.")
        return code

    # کپی داده‌ها کنار EXE
    import shutil
    dest = os.path.join(BASE, "dist", APP_NAME)
    for f in DATA_FILES:
        src = os.path.join(BASE, f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dest, f))
            print("کپی شد:", f)
    print(f"EXE ساخته شد: dist\\{APP_NAME}\\{APP_NAME}.exe")
    print("قدم بعدی: Create_Setup_Installer.bat  →  Output\\NexusMed_Setup_v2.0.exe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
