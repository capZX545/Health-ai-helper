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
