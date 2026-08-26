# -*- coding: utf-8 -*-
"""
android/main.py — NexusMed 2077 Android launcher.
Starts the Python backend server and opens a WebView.
"""
import os
import sys
import threading
import time

# مسیر داده‌ها روی اندروید
APP_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(APP_DIR)
sys.path.insert(0, APP_DIR)

# data dir for personal files
DATA_DIR = APP_DIR
os.environ.setdefault("NEXUSMED_DATA_DIR", DATA_DIR)

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

_server_started = False
_server_port = 2077


def start_server():
    """Start the NexusMed web server in a background thread."""
    global _server_started, _server_port
    if _server_started:
        return
    _server_started = True
    try:
        from run_web import find_free_port
        from http.server import ThreadingHTTPServer
        import run_web

        # suppress output
        import io
        import contextlib

        run_web.HTML_FILE = os.path.join(APP_DIR, "clinic_2077.html")

        # find a free port
        _server_port = find_free_port(2077, 2097, "127.0.0.1") or 2077

        handler = run_web.Handler
        httpd = ThreadingHTTPServer(("127.0.0.1", _server_port), handler)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        print(f"[NexusMed] server on port {_server_port}")
    except Exception as e:
        print(f"[NexusMed] server error: {e}")


def open_webview():
    """Try to open a WebView using Android's Intent system."""
    try:
        from jnius import autoclass
        Intent = autoclass("android.content.Intent")
        Uri = autoclass("android.net.Uri")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        intent = Intent(Intent.ACTION_VIEW, Uri.parse(f"http://127.0.0.1:{_server_port}"))
        PythonActivity.mActivity.startActivity(intent)
    except Exception:
        try:
            import webbrowser
            webbrowser.open(f"http://127.0.0.1:{_server_port}")
        except Exception:
            pass


class NexusMedApp(App):
    def build(self):
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)

        self.label = Label(
            text="NexusMed 2077\n[b]دستیار پزشکی هوشمند[/b]\n\nStarting server...",
            markup=True,
            font_size="18sp",
            halign="center",
        )
        layout.add_widget(self.label)

        self.btn = Button(
            text="Open NexusMed\nباز کردن برنامه",
            font_size="16sp",
            size_hint_y=0.2,
            background_color=(0, 0.7, 0.8, 1),
        )
        self.btn.bind(on_press=lambda x: open_webview())
        layout.add_widget(self.btn)

        # سرور را شروع کن
        start_server()

        # بعد از یک ثانیه پیام عوض کن
        Clock.schedule_once(lambda dt: self.on_ready(), 1.5)
        return layout

    def on_ready(self):
        self.label.text = (
            f"NexusMed 2077\n[b]دستیار پزشکی هوشمند[/b]\n\n"
            f"Server running on port {_server_port}\n"
            f"Tap the button below to open\n"
            f"یا دکمه‌ی زیر را بزن"
        )


if __name__ == "__main__":
    NexusMedApp().run()
