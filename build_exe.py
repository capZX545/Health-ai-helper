# -*- coding: utf-8 -*-
"""
Builds the Windows executable with PyInstaller (run this on Windows).
Output: dist/NexusMed2077/NexusMed2077.exe (+ the data folder)
Afterwards Create_Setup_Installer.bat makes the setup with Inno Setup.
"""
from __future__ import annotations

import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
APP_NAME = "NexusMed2077"

# data files that must sit next to the EXE
DATA_FILES = [
    "clinic_2077.html",
    "manifest.json",
    "sw.js",
    "icon-192.svg",
    "icon-512.svg",
    ".env.example",
    "requirements.txt",
    "fonts/Vazirmatn-Regular.ttf",
    "fonts/Vazirmatn-Bold.ttf",
    "fonts/Inter-Regular.ttf",
    "fonts/Inter-Bold.ttf",
    # knowledge banks
    "nlm_conditions.json",
    "drugs_fda.json",
    "drug_labels.json.gz",
    "disease_symptoms_hpo.json.gz",
    "fa_names.json",
    "wiki_diseases.json",
    "diseases_doid.json",
    "symptoms_hpo.json",
    "diseases_extra.json",
    "diseases_offline.db",
    "fda_drugs.json",
    "medical_ml_test_dataset.csv",
]


def run(cmd: list[str]) -> int:
    print(">>", " ".join(cmd))
    return subprocess.call(cmd, cwd=BASE)


def main() -> int:
    if sys.platform.startswith("win"):
        pyinstaller = [sys.executable, "-m", "PyInstaller"]
    else:
        print("you are on linux; a real Windows exe can only be built on Windows.")
        print("run this script on windows with python and pyinstaller installed.")
        return 1

    sep = ";" if sys.platform.startswith("win") else ":"
    add_data = [a for f in ("clinic_2077.html", "diseases_extra.json", "medical_ml_test_dataset.csv", ".env.example") for a in ("--add-data", f + sep + ".")]

    cmd = pyinstaller + [
        "--noconfirm", "--clean", "--windowed", "--onedir",
        "--name", APP_NAME,
        "--collect-submodules", "sklearn",
        "--hidden-import", "health_tools",
        "--hidden-import", "lab_full",
        "--hidden-import", "synth_desc",
        "--hidden-import", "translit",
        "--hidden-import", "knowledge_browser",
        "--hidden-import", "medical_catalog",
        "--hidden-import", "drugbank_connector",
        "--hidden-import", "drug_interaction",
        "--hidden-import", "build_hpo_links",
        "--hidden-import", "clinical_trials_connector",
        "--hidden-import", "openfda_connector",
        "--hidden-import", "who_connector",
        *add_data,
        os.path.join(BASE, "run_2077.py"),
    ]
    code = run(cmd)
    if code != 0:
        print("pyinstaller failed.")
        return code

    # copy the data next to the EXE
    import shutil
    dest = os.path.join(BASE, "dist", APP_NAME)
    for f in DATA_FILES:
        src_path = os.path.join(BASE, f)
        if os.path.exists(src_path):
            os.makedirs(os.path.dirname(os.path.join(dest, f)) or dest, exist_ok=True)
            shutil.copy2(src_path, os.path.join(dest, f))
            print("copied:", f)
    print("exe built: dist/%s/%s.exe" % (APP_NAME, APP_NAME))
    print("next: Create_Setup_Installer.bat -> Output\\NexusMed_Setup.exe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
