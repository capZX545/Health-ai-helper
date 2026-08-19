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

    try:
        import tkinter  # noqa: F401
    except Exception:
        print("Tkinter در دسترس نیست؛ نسخه‌ی وب اجرا می‌شود...")
        from run_web import main as web_main
        sys.argv = ["run_web.py"]
        return web_main()

    from ui_2077 import run_app
    return run_app()


if __name__ == "__main__":
    sys.exit(main())
