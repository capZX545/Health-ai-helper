# -*- coding: utf-8 -*-
"""
NexusMed 2077 — Android launcher.
Starts the full Python backend server (with numpy + all data) and
replaces the Kivy view with a native Android WebView showing the app.
Everything is self-contained — no internet needed.
"""
import os
import sys
import threading
import time

APP_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(APP_DIR)
sys.path.insert(0, APP_DIR)
os.environ.setdefault("NEXUSMED_MOBILE", "1")

# start the server in a background thread
import run_web
from http.server import ThreadingHTTPServer

PORT = 8080
_server = None

def start_server():
    global _server
    try:
        run_web.HTML_FILE = os.path.join(APP_DIR, "clinic_2077.html")
        handler = run_web.Handler
        _server = ThreadingHTTPServer(("127.0.0.1", PORT), handler)
        threading.Thread(target=_server.serve_forever, daemon=True).start()
        print(f"[NexusMed] server on :{PORT}")
    except Exception as e:
        print(f"[NexusMed] server error: {e}")

start_server()

# --- now replace Kivy view with a native Android WebView ---
from kivy.app import App
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform

Window.clearcolor = (0.015, 0.02, 0.05, 1)  # #04060c


class NexusApp(App):
    def build(self):
        self.label = Label(
            text="NexusMed 2077\nStarting...",
            font_size="16sp",
            halign="center",
            color=(0, 0.94, 1, 1),
        )
        # after 0.5s, swap to WebView
        Clock.schedule_once(self.open_webview, 0.5)
        return self.label

    def open_webview(self, *args):
        if platform == "android":
            try:
                self._open_android_webview()
            except Exception as e:
                print(f"WebView error: {e}")
                self._open_browser()
        else:
            # desktop / test: open browser
            self._open_browser()

    def _open_android_webview(self):
        from jnius import autoclass, PythonJavaClass, java_method
        from android import mActivity

        # get the activity's window
        LayoutParams = autoclass("android.view.ViewGroup$LayoutParams")
        LinearLayout = autoclass("android.widget.LinearLayout")
        WebView = autoclass("android.webkit.WebView")
        WebSettings = autoclass("android.webkit.WebSettings")
        WebViewClient = autoclass("android.webkit.WebViewClient")
        Color = autoclass("android.graphics.Color")

        # create a WebView
        webview = WebView(mActivity)
        settings = webview.getSettings()
        settings.setJavaScriptEnabled(True)
        settings.setDomStorageEnabled(True)
        settings.setAllowFileAccess(True)
        settings.setLoadWithOverviewMode(True)
        settings.setUseWideViewPort(True)
        settings.setTextZoom(100)
        settings.setSupportZoom(False)
        settings.setCacheMode(WebSettings.LOAD_DEFAULT)
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW)
        webview.setBackgroundColor(Color.parseColor("#04060c"))
        webview.setWebViewClient(WebViewClient())

        # replace the Kivy view with the WebView
        content = mActivity.findViewById(0x01020002)  # android.R.id.content
        if content:
            content.removeAllViews()
            content.addView(webview, LayoutParams(
                LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT))

        # load the app
        webview.loadUrl(f"http://127.0.0.1:{PORT}/")

        # store reference for back button
        self._webview = webview

    def _open_browser(self):
        import webbrowser
        url = f"http://127.0.0.1:{PORT}/"
        try:
            webbrowser.open(url)
        except Exception:
            pass
        self.label.text = f"NexusMed 2077\n\nServer running on {url}\nOpen in browser"

    def on_pause(self):
        return True  # keep running in background

    def on_resume(self):
        pass


if __name__ == "__main__":
    NexusApp().run()
