# -*- coding: utf-8 -*-
"""
run_2077.py — نقطه‌ی ورود NexusMed 2077.
اجرا:
  python run_2077.py          → رابط دسکتاپ (Tkinter)
  python run_2077.py --web    → نسخه‌ی وب محلی (http://localhost:2077)
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

    # بررسی Tkinter (ممکن است روی ویندوز ناقص نصب باشد)
    try:
        import tkinter
        root_test = tkinter.Tk()
        root_test.destroy()
    except Exception as e:
        print("=" * 56)
        print("  رابط گرافیکی (Tkinter) در دسترس نیست.")
        print(f"  علت: {e}")
        print()
        print("  راه حل ۱: Python را دوباره نصب کنید و حتماً تیک")
        print("            'tcl/tk and IDLE' را بزنید (Download from python.org)")
        print("  راه حل ۲: نسخه‌ی وب را استفاده کنید (همان امکانات):")
        print()
        print("            python run_web.py")
        print()
        print("  الان نسخه‌ی وب برای شما اجرا می‌شود...")
        print("=" * 56)
        from run_web import main as web_main
        sys.argv = ["run_web.py"]
        return web_main()

    from ui_2077 import run_app
    return run_app()


if __name__ == "__main__":
    sys.exit(main())
