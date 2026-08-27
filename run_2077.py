# -*- coding: utf-8 -*-
"""
Entry point of NexusMed 2077.
Run:
  python run_2077.py          -> desktop UI (tkinter)
  python run_2077.py --web    -> local web version (http://localhost:2077)
"""
from __future__ import annotations

import argparse
import sys
import os
# make sure sibling .py files are importable (frozen exe or source run)
sys.path.insert(0, os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__)))

# ALL MODULES — PyInstaller needs these top-level to bundle everything
import common_2077
import i18n
import medical_engine
import bayesian_engine
import ml_classifier
import hybrid_engine
import knowledge_browser
import medical_catalog
import drugbank_connector
import drug_interaction
import lab_full
import lab_catalog
import lab_tests
import lab_visualizer
import health_tools
import synth_desc
import translit
import patient_profile
import health_vitals
import first_aid
import mental_health
import sleep_analyzer
import checkup_calendar
import doctor_referral
import auto_learning
import behavior_imitation
import semantic_rag
import clinical_dialogue
import medical_nlg
import ai_api_manager
import ai_client
import free_ai
import local_llm
import prescription_scanner
import image_caption
import image_type_detector
import lesion_analyzer
import ecg_analyzer
import openfda_connector
import clinical_trials_connector
import who_connector


def main() -> int:
    ap = argparse.ArgumentParser(description="NexusMed 2077 — دستیار هوشمند پزشکی فارسی")
    ap.add_argument("--web", action="store_true", help="اجرای نسخه‌ی وب محلی به‌جای دسکتاپ")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=2077)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()

    if args.web:
        from run_web import main as web_main
        sys.argv = ["run_web.py", "--host", args.host, "--port", str(args.port)]
        if args.no_browser:
            sys.argv.append("--no-browser")
        return web_main()

    # tkinter check - if missing just error out, no fallback
    try:
        import tkinter
        root_test = tkinter.Tk()
        root_test.destroy()
    except Exception as e:
        print("=" * 56)
        print("  ERROR: Desktop GUI is not available.")
        print(f"  Reason: {e}")
        print()
        print("  FIX: Reinstall Python 3.12 from python.org")
        print("       and check 'tcl/tk and IDLE' during install.")
        print()
        print("  For the web version, run: python run_web.py")
        print("=" * 56)
        input("  Press Enter to exit...")
        return 1

    from ui_2077 import run_app
    return run_app()


if __name__ == "__main__":
    sys.exit(main())
