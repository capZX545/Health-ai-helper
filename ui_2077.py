# -*- coding: utf-8 -*-
"""
Desktop UI for NexusMed 2077 (tkinter), cyberpunk 2077 theme.
Persian-first and friendly for non-programmers; API settings live inside the app.
"""
from __future__ import annotations

import os
import sys
import threading
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, scrolledtext, ttk

from common_2077 import APP_NAME, APP_VERSION, DATA_DIR, MEDICAL_DISCLAIMER
import health_tools
import lab_full
import synth_desc
import translit

# ---------------------------------------------------------------- theme
C = {
    "bg": "#04060c", "panel": "#0b1220", "panel2": "#0e1730", "bd": "#16213e",
    "cy": "#00f0ff", "mg": "#ff2a6d", "yl": "#ffd60a", "gr": "#3bff9e",
    "tx": "#d7e3ff", "dim": "#6b7fa3",
}


_FONT_LOADED = False


def _load_bundled_fonts() -> None:
    """Load Vazirmatn from ./fonts into memory (Windows only, nothing installed).
    Falls back silently on other platforms or when the files are missing."""
    global _FONT_LOADED
    if _FONT_LOADED or sys.platform != "win32":
        return
    _FONT_LOADED = True
    try:
        import ctypes
        from ctypes import wintypes
        g32 = ctypes.windll.gdi32
        here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
        for name in ("Vazirmatn-Regular.ttf", "Vazirmatn-Bold.ttf",
                     "Inter-Regular.ttf", "Inter-Bold.ttf"):
            path = os.path.join(here, name)
            if not os.path.exists(path):
                continue
            with open(path, "rb") as f:
                data = f.read()
            buf = ctypes.create_string_buffer(data, len(data))
            n = wintypes.DWORD(0)
            g32.AddFontMemResourceEx(buf, len(data), None, ctypes.byref(n))
    except Exception:
        pass


def pick_font(size: int, bold: bool = False):
    _load_bundled_fonts()
    fams = set(tkfont.families())
    try:
        from i18n import get_lang
        english = get_lang() == "en"
    except Exception:
        english = False
    order = ("Inter", "Vazirmatn", "Segoe UI", "Tahoma") if english else \
            ("Vazirmatn", "B Nazanin", "IRANSans", "Inter", "Segoe UI", "Tahoma")
    for fam in order:
        if fam in fams:
            return (fam, size, "bold" if bold else "normal")
    return ("Tahoma", size, "bold" if bold else "normal")


def try_beep(freq: int = 880, dur: int = 140):
    try:
        import winsound
        winsound.Beep(freq, dur)
    except Exception:
        try:
            print("\a", end="", flush=True)
        except Exception:
            pass


# =======================================================================

class App:
    def __init__(self, root: tk.Tk):
        import queue as _queue
        self._uiq = _queue.Queue()
        root.after(120, self._poll_uiq)
        self.root = root
        root.geometry("1280x800")
        root.minsize(900, 600)
        root.configure(bg=C["bg"])
        self.engine = None
        self.img_path = None
        self._build()
        self._refresh_status()
        self._hello()

    def L(self, en: str, fa: str) -> str:
        from i18n import tt
        return tt(en, fa)

    def set_lang(self, lang: str):
        from i18n import set_lang as _sl
        _sl(lang)
        for w in self.root.winfo_children():
            w.destroy()
        self.engine = None
        self._build()
        self._refresh_status()
        self._hello()

    # --------------------------------------------------------------- build
    def _build(self):
        F, FB = pick_font(11), pick_font(11, True)
        F_SMALL, F_TITLE = pick_font(9), pick_font(15, True)
        top = tk.Frame(self.root, bg="#0c1526", height=58)
        top.pack(fill="x")
        tk.Label(top, text="NEXUS", bg="#0c1526", fg=C["cy"], font=F_TITLE).pack(side="right", padx=(16, 4))
        tk.Label(top, text="MED 2077", bg="#0c1526", fg=C["mg"], font=F_TITLE).pack(side="right", padx=4)
        self.root.title(self.L(f"{APP_NAME} - bilingual medical assistant v{APP_VERSION}",
                               f"{APP_NAME} — دستیار هوشمند پزشکی فارسی v{APP_VERSION}"))
        self.status_lbl = tk.Label(top, text=self.L("Status: checking...", "وضعیت: در حال بررسی…"), bg="#0c1526", fg=C["dim"], font=F_SMALL)
        self.status_lbl.pack(side="left", padx=12)
        from i18n import get_lang
        tk.Button(top, text=("Farsi" if get_lang() == "en" else "English"),
                  command=lambda: self.set_lang("fa" if get_lang() == "en" else "en"),
                  bg="#0d1930", fg=C["cy"], relief="flat", font=F).pack(side="left", padx=4, pady=12)


        tk.Button(top, text=self.L("Emergency 115/112", "اورژانس ۱۱۵/۱۱۲"), command=lambda: self._panel_emergency(),
                  bg="#2a0d1a", fg="#ff8fab", relief="flat", font=F).pack(side="left", padx=4, pady=12)
        tk.Button(top, text=self.L("API settings", "تنظیمات API"), command=self._panel_settings,
                  bg="#0d1930", fg=C["tx"], relief="flat", font=F).pack(side="left", padx=4, pady=12)

        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill="both", expand=True)

        nav = tk.Frame(body, bg=C["panel"], width=230)
        nav.pack(side="right", fill="y")
        nav.pack_propagate(False)
        # the sidebar scrolls (like overflow-y:auto in the web version)
        # so every module stays reachable on short windows
        from tkinter import ttk as _ttk
        nav_canvas = tk.Canvas(nav, bg=C["panel"], highlightthickness=0)
        nav_vsb = _ttk.Scrollbar(nav, orient="vertical", command=nav_canvas.yview)
        nav_canvas.configure(yscrollcommand=nav_vsb.set)
        nav_vsb.pack(side="left", fill="y")
        nav_canvas.pack(side="right", fill="both", expand=True)
        navf = tk.Frame(nav_canvas, bg=C["panel"])
        nav_item = nav_canvas.create_window((0, 0), window=navf, anchor="nw")
        def _nav_conf(_event):
            nav_canvas.configure(scrollregion=nav_canvas.bbox("all"))
            nav_canvas.itemconfig(nav_item, width=nav_canvas.winfo_width())
        navf.bind("<Configure>", _nav_conf)
        def _nav_in_nav() -> bool:
            try:
                wid = nav.winfo_containing(nav.winfo_pointerx(), nav.winfo_pointery())
            except tk.TclError:
                return False
            return bool(wid) and (wid is nav or nav is wid.master or _inside(wid, nav))
        def _inside(wid, ancestor):
            while wid:
                if wid is ancestor:
                    return True
                wid = wid.master
            return False
        def _nav_wheel(event):
            if not _nav_in_nav():
                return  # pointer not on the sidebar; let another widget (the chat) handle it
            nav_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"
        def _nav_wheel_linux(event, direction):
            if not _nav_in_nav():
                return
            nav_canvas.yview_scroll(direction, "units")
            return "break"
        nav.bind_all("<MouseWheel>", _nav_wheel, add="+")
        nav.bind_all("<Button-4>", lambda e: _nav_wheel_linux(e, -1), add="+")
        nav.bind_all("<Button-5>", lambda e: _nav_wheel_linux(e, 1), add="+")
        self._nav_canvas = nav_canvas
        items = [
            (("Chat (return)", "گفتگو (بازگشت)"), lambda: None),
            (("Patient profile", self.L("Patient profile", "پروفایل بیمار")), self._panel_profile),
            (("Vitals", self.L("Vitals", "علائم حیاتی")), self._panel_vitals),
            (("Lab analysis", self.L("Lab analysis", "تحلیل آزمایش")), self._panel_labs),
            (("Prescription scan", self.L("Prescription scan", "اسکن نسخه")), self._panel_rx),
            (("Drugs & interactions", self.L("Drugs & interactions", "دارو و تداخلات")), self._panel_drugs),
            (("Medical image", self.L("Medical image analysis", "تحلیل تصویر پزشکی")), self._panel_image),
            (("Disease likelihood", "ارزیابی احتمال بیماری"), self._panel_assess),
            (("Symptoms (check & analyze)", "علائم (تیک و تحلیل)"), self._panel_symptoms),
            (("Diseases database", "بانک بیماری‌ها"), self._panel_diseases),
            (("Drugs database", "بانک داروها"), self._panel_drugs),
            (("Research & articles", "پژوهش و مقالات"), self._panel_research),
            (("Laboratory", "آزمایشگاه"), self._panel_lab),
            (("Health tools", "ابزار سلامت"), self._panel_tools),
            (("Mental health", "سلامت روان"), self._panel_mental),
            (("Sleep analysis", "تحلیل خواب"), self._panel_sleep),
            (("Checkup calendar", "تقویم چکاپ"), self._panel_checkup),
            (("First aid / CPR", self.L("First aid / CPR", "کمک‌های اولیه / CPR")), self._panel_emergency),
            (("Referral report", "گزارش ارجاع"), self._panel_referral),
            (("Brain & learning", self.L("Internal brain & learning", "مغز داخلی / یادگیری")), self._panel_brain),
            (("Doctor Mode", "حالت دکتر"), self._panel_doctor),
            (("Local AI (GPU/Ollama)", "هوش محلی (GPU/Ollama)"), self._panel_gpu),
        ]
        tk.Label(navf, text=self.L("- modules -", "ـ ماژول‌ها ـ"), bg=C["panel"], fg=C["dim"], font=F_SMALL).pack(pady=8)
        for pair, cmd in items:
            txt = self.L(pair[0], pair[1])
            b = tk.Button(navf, text=txt, anchor="e", bg=C["panel"], fg=C["tx"], relief="flat",
                          font=F, activebackground="#101c36", activeforeground=C["cy"],
                          cursor="hand2", command=cmd)
            b.pack(fill="x", padx=8, pady=1)
            b.bind("<Enter>", lambda e, w=b: w.config(fg=C["cy"]))
            b.bind("<Leave>", lambda e, w=b: w.config(fg=C["tx"]))

        main = tk.Frame(body, bg=C["bg"])
        main.pack(side="left", fill="both", expand=True)
        self.chat = scrolledtext.ScrolledText(main, bg="#070d18", fg=C["tx"], wrap="word",
                                              relief="flat", font=pick_font(12), state="disabled",
                                              padx=14, pady=10, insertbackground=C["cy"])
        self.chat.pack(fill="both", expand=True, padx=10, pady=(10, 4))
        self.chat.tag_configure("user", foreground="#9ad8ff", justify="right")
        self.chat.tag_configure("bot", foreground=C["tx"], justify="right")
        self.chat.tag_configure("emg", foreground="#ff8fab", justify="right")
        self.chat.tag_configure("meta", foreground=C["dim"], justify="right", font=pick_font(8))
        self.chat.tag_configure("me", foreground=C["cy"], justify="right")

        bar = tk.Frame(main, bg=C["bg"])
        bar.pack(fill="x", padx=10, pady=(2, 4))
        self.attach_lbl = tk.Label(bar, text="", bg=C["bg"], fg=C["yl"], font=F_SMALL)
        self.attach_lbl.pack(side="right")
        tk.Button(bar, text=self.L("Attach medical image", "عکس پزشکی"), command=self._attach, bg="#0d1930", fg=C["tx"],
                  relief="flat", font=F).pack(side="left", padx=3)
        tk.Button(bar, text=self.L("New conversation", "گفتگوی جدید"), command=self._reset_dialogue, bg="#0d1930", fg=C["tx"],
                  relief="flat", font=F).pack(side="left", padx=3)

        inbar = tk.Frame(main, bg=C["bg"])
        inbar.pack(fill="x", padx=10, pady=(0, 6))
        self.entry = tk.Text(inbar, height=3, bg="#0a1424", fg=C["tx"], relief="flat",
                             font=pick_font(12), insertbackground=C["cy"], padx=12, pady=8, wrap="word")
        self.entry.pack(side="right", fill="both", expand=True, ipady=2)
        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<Shift-Return>", lambda e: None)
        self.root.bind("<Control-Return>", lambda e: self._send())
        self.root.bind("<Control-n>", lambda e: self._new_conversation())
        self.root.bind("<Control-N>", lambda e: self._new_conversation())
        self.root.bind("<Control-comma>", lambda e: self._panel_settings())
        self.root.bind("<Control-e>", lambda e: self._panel_emergency())
        self.root.bind("<Control-E>", lambda e: self._panel_emergency())
        self.root.bind("<F1>", lambda e: self._show_shortcuts())
        self.root.bind("<Escape>", lambda e: [w.destroy() for w in self.root.winfo_children() if isinstance(w, tk.Toplevel)])
        self.send_btn = tk.Button(inbar, text=self.L("Send", "ارسال"), command=self._send, bg="#0077b6",
                                  fg="#021018", font=pick_font(12, True), relief="flat")
        self.send_btn.pack(side="left", fill="y", padx=(6, 0))

        tk.Label(self.root, text=MEDICAL_DISCLAIMER(), bg="#070d18", fg="#41527a",
                 font=pick_font(8), pady=4).pack(fill="x", side="bottom")

    def _ui(self, fn):
        """
        Run a function on the main thread. Safe to call from any thread.
        """
        self._uiq.put(fn)

    def _poll_uiq(self):
        while True:
            try:
                fn = self._uiq.get_nowait()
            except Exception:
                break
            try:
                fn()
            except tk.TclError:
                pass
        try:
            self.root.after(120, self._poll_uiq)
        except tk.TclError:
            pass

    # -------------------------------------------------------------- engine
    def _engine(self):
        if self.engine is None:
            from hybrid_engine import HybridEngine
            self.engine = HybridEngine()
        return self.engine

    def _hello(self):
        ver = f"\n===== NexusMed 2077 v{APP_VERSION} =====\n"
        new_mods = "\n🆕 NEW MODULES:\n  • Health tools (10 calculators)\n  • Laboratory (96 tests)\n  • Expanded symptoms (240)\n  • Research (PubMed + Trials)\n================================"
        self._bot(ver + new_mods + "\n\n")
        self._bot(self.L(
            "Hello, I am Nexus, the bilingual medical assistant of NexusMed 2077.\n"
            "Describe your symptoms with details (onset, severity, duration) and we will go through them step by step.\n"
            "Emergency signs get immediate emergency guidance.\n"
            "To connect an external AI, open 'API settings' and paste your OpenRouter key.",
            "سلام! من نکسوس هستم — دستیار پزشکی دوزبانه NexusMed 2077.\n"
            "علائمت را با جزئیات (شروع، شدت، مدت) بنویس تا مرحله‌به‌مرحله بررسی کنیم.\n"
            "در علائم اورژانسی فوراً راهنمایی اورژانس می‌گیری.\n"
            "برای اتصال به AI خارجی، از دکمه‌ی «تنظیمات API» کلید OpenRouter را وارد کن."))

    def _bot(self, text: str, tag: str = "bot", meta: str = ""):
        self.chat.config(state="normal")
        self.chat.insert("end", text + "\n", tag)
        if meta:
            self.chat.insert("end", meta + "\n\n", "meta")
        else:
            self.chat.insert("end", "\n")
        self.chat.see("end")
        self.chat.config(state="disabled")

    def _user(self, text: str):
        self._bot(text, "user")

    def _on_enter(self, _e):
        self._send()
        return "break"

    def _attach(self):
        p = filedialog.askopenfilename(title=self.L("Attach medical image", "انتخاب تصویر پزشکی"),
                                       filetypes=[(self.L("Images", "تصاویر"), "*.jpg *.jpeg *.png *.webp *.bmp"), (self.L("All", "همه"), "*.*")])
        if p:
            self.img_path = p
            self.attach_lbl.config(text=""+ os.path.basename(p))

    def _new_conversation(self):
        """
        New conversation: archives the previous one into history.
        """
        eng = self._engine()
        dlg = eng.dialogue.summary()
        if dlg.get("turns", 0) > 0 and (eng.memory or []):
            from common_2077 import read_json, write_json, DATA_DIR
            import os as _os
            hist_path = _os.path.join(DATA_DIR, "conversation_history.json")
            hist = read_json(hist_path, default=[]) or []
            conv = {
                "ts": __import__("common_2077", fromlist=["now_iso"]).now_iso(),
                "turns": dlg["turns"],
                "symptoms": dlg.get("symptoms", []),
                "messages": [{"role": m["role"], "content": m["content"][:500]} for m in eng.memory[-20:]],
            }
            hist.insert(0, conv)
            hist = hist[:50]
            write_json(hist_path, hist)
        eng.dialogue.reset()
        eng.memory = []
        self.chat.config(state="normal")
        self.chat.delete("1.0", "end")
        self.chat.config(state="disabled")
        self._hello()
        self._refresh_status()

    def _reset_dialogue(self):
        self._new_conversation()

    def _show_shortcuts(self):
        from i18n import is_fa
        fa = is_fa()
        w = self._win(self.L("Keyboard Shortcuts", "میانبرهای کیبورد"))
        items = [
            ("Ctrl+Enter", self.L("Send message", "ارسال پیام")),
            ("Ctrl+N", self.L("New conversation (saves previous)", "گفتگوی جدید (قبلی ذخیره می‌شود)")),
            ("Ctrl+,", self.L("Settings", "تنظیمات")),
            ("Ctrl+E", self.L("Emergency panel", "پنل اورژانس")),
            ("F1", self.L("This help", "راهنمای میانبرها")),
            ("Esc", self.L("Close dialogs", "بستن پنجره‌ها")),
        ]
        for key, desc in items:
            tk.Label(w, text=f"{key}  →  {desc}", bg=C["panel2"], fg=C["tx"],
                     font=pick_font(11), anchor="e").pack(fill="x", padx=16, pady=3)

    def _panel_doctor(self):
        """
        Doctor mode: patient scenario -> differential diagnosis
        """
        from i18n import is_fa
        w = self._win(self.L("Doctor Mode — Clinical Analysis", "حالت دکتر — تحلیل بالینی"))
        tk.Label(w, text=("Describe a patient scenario and get a clinical differential diagnosis." if not is_fa()
                          else self.L("Describe a patient scenario and get a clinical differential.", "سناریوی بیمار را بنویسید و تشخیص افتراقی بالینی بگیرید.")),
                 bg=C["panel2"], fg=C["dim"], font=pick_font(10)).pack(padx=16, pady=8)
        txt = scrolledtext.ScrolledText(w, bg="#0a1424", fg=C["tx"], font=pick_font(12), height=5, relief="flat")
        txt.pack(fill="x", padx=16)
        box = self._result_box(w)

        def go():
            import json as _json
            import requests as _req
            try:
                r = _req.post("http://localhost:2077/api/doctor_mode",
                             json={"text": txt.get("1.0", "end").strip()}, timeout=120)
                d = r.json()
            except Exception:
                # fallback: straight to the offline brain
                from medical_engine import analyze
                a = analyze(txt.get("1.0", "end").strip())
                lines = [self.L("[offline] internal-brain differential:", "[offline] تشخیص افتراقی مغز داخلی:")]
                for c in a["candidates"][:5]:
                    lines.append(f"  • {c['name']} ~{c['percent']}% [{c['urgency']}]")
                box.delete("1.0", "end")
                box.insert("1.0", "\n".join(lines))
                return
            box.delete("1.0", "end")
            box.insert("1.0", f"[{d.get('source', '')}]\n\n" + d.get("text", d.get("message_fa", "error")))

        tk.Button(w, text=self.L("Clinical Analysis", "تحلیل بالینی"), command=go, bg="#0077b6",
                  fg="#021018", font=pick_font(11, True), relief="flat").pack(pady=8, ipadx=24, ipady=4)

    def _send(self):
        text = self.entry.get("1.0", "end").strip()
        if not text and not self.img_path:
            return
        self.entry.delete("1.0", "end")
        self._user(text or self.L("[medical image]", "[تصویر پزشکی]"))
        self.send_btn.config(state="disabled", text="…")
        note = text
        img_path = self.img_path
        self.img_path = None
        self.attach_lbl.config(text="")

        def work():
            try:
                if img_path:
                    from image_caption import analyze_image_file
                    res = analyze_image_file(img_path, note, self._engine())
                else:
                    res = self._engine().chat(text)
                tag = "emg" if res.get("red_flag") else "bot"
                meta = {"internal": self.L("offline brain", "مغز داخلی آفلاین"),
                        "internal-image": self.L("offline brain - image", "مغز داخلی — تحلیل تصویر"),
                        "internal-emergency": self.L("emergency", "اورژانسی")}.get(res.get("source", ""), res.get("source", ""))
                if res.get("image_type") and res["image_type"].get("label"):
                    meta += " | " + res["image_type"]["label"]
                if res.get("learned"):
                    meta += self.L("•  learned", "•  یادگیری ثبت شد")
                payload = (res.get("text", ""), tag, meta)
            except Exception as e:
                payload = (self.L("Error: ", "خطا: ")+ str(e)[:200], "emg", "")

            def apply():
                # UI updates on the main thread only (tkinter isn't thread-safe) (Tkinter thread-safe
                self._bot(*payload)
                self.send_btn.config(state="normal", text=self.L("Send", "ارسال"))
                self._refresh_status()
            self._ui(apply)

        threading.Thread(target=work, daemon=True).start()

    # ------------------------------------------------------------- status
    def _refresh_status(self):
        def work():
            try:
                s = self._engine().status()
                ext = self.L("external AI on", "AI خارجی فعال") if s.get("external_available") else self.L("external AI: no key", "AI خارجی: کلید ندارد")
                brain = self.L("offline brain on", "مغز داخلی روشن") if s.get("settings", {}).get("brain_enabled") else self.L("brain off (background learning on)", "مغز خاموش (یادگیری پس‌زمینه فعال)")
                learned = s.get("learning", {}).get("entries", 0)
                msg = f"{ext} | {brain} | " + self.L(f"memory: {learned}", f"حافظه: {learned} مورد")
            except Exception as e:
                msg = self.L("status: error — ", "وضعیت: خطا — ")+ str(e)[:80]

            def apply():
                try:
                    self.status_lbl.config(text=msg)
                except tk.TclError:
                    pass
            self._ui(apply)
        threading.Thread(target=work, daemon=True).start()


    # ============================================================= panels
    def _win(self, title: str):
        w = tk.Toplevel(self.root)
        w.title(title)
        w.configure(bg=C["panel2"])
        # window height never exceeds the screen (small laptops)
        try:
            scr_h = w.winfo_screenheight()
        except Exception:
            scr_h = 800
        win_h = max(400, min(640, scr_h - 140))
        w.geometry(f"660x{win_h}")
        w.minsize(500, min(400, win_h))
        w.transient(self.root)
        w.protocol("WM_DELETE_WINDOW", w.destroy)
        # scrollbar for the content
        canvas = tk.Canvas(w, bg=C["panel2"], highlightthickness=0)
        vsb = ttk.Scrollbar(w, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        frame = tk.Frame(canvas, bg=C["panel2"])
        canvas_window = canvas.create_window((0, 0), window=frame, anchor="nw")
        def _configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())
        frame.bind("<Configure>", _configure)
        # keep the inner frame width in sync on window resize
        def _canvas_resize(event):
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())
        canvas.bind("<Configure>", _canvas_resize)
        self._wheel_bind(w, canvas)
        w._scroll_frame = frame
        w._canvas = canvas
        # hand back the scrollable frame so panels can fill it
        return frame

    def _wheel_bind(self, w, canvas):
        """
        Mouse wheel over any widget of window w scrolls the canvas (pointer-guarded).
        """
        def _in_this_window() -> bool:
            try:
                wid = w.winfo_containing(w.winfo_pointerx(), w.winfo_pointery())
            except tk.TclError:
                return False
            return bool(wid) and (wid is w or bool(wid.winfo_toplevel() is w))
        def _on_mousewheel(event):
            if not _in_this_window():
                return  # let another widget (the main chat) handle the wheel
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"
        def _on_scroll_linux(event, direction):
            if not _in_this_window():
                return
            canvas.yview_scroll(direction, "units")
            return "break"
        _wheel_ids = [
            w.bind_all("<MouseWheel>", _on_mousewheel, add="+"),
            w.bind_all("<Button-4>", lambda e: _on_scroll_linux(e, -1), add="+"),
            w.bind_all("<Button-5>", lambda e: _on_scroll_linux(e, 1), add="+"),
        ]
        def _unbind_all(_event=None):
            for seq, fid in zip(("<MouseWheel>", "<Button-4>", "<Button-5>"), _wheel_ids):
                if not fid:
                    continue
                try:
                    w.unbind_all(seq, funcid=fid)
                except (tk.TclError, TypeError):
                    try:
                        w.unbind_all(seq)
                    except tk.TclError:
                        pass
        w.bind("<Destroy>", _unbind_all)

    def _win_list(self, title: str):
        """
        Window with a fixed top bar + scrollable middle + fixed bottom bar.
        Returns (window, top frame, inner list frame, bottom frame)
        """
        w = tk.Toplevel(self.root)
        w.title(title)
        w.configure(bg=C["panel2"])
        try:
            scr_h = w.winfo_screenheight()
        except Exception:
            scr_h = 800
        win_h = max(420, min(680, scr_h - 140))
        w.geometry(f"700x{win_h}")
        w.minsize(540, min(420, win_h))
        w.transient(self.root)
        w.protocol("WM_DELETE_WINDOW", w.destroy)
        top = tk.Frame(w, bg=C["panel2"])
        top.pack(side="top", fill="x")
        bottom = tk.Frame(w, bg=C["panel2"])
        bottom.pack(side="bottom", fill="x")
        canvas = tk.Canvas(w, bg=C["panel2"], highlightthickness=0)
        vsb = ttk.Scrollbar(w, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="left", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(canvas, bg=C["panel2"])
        cw = canvas.create_window((0, 0), window=inner, anchor="nw")
        def _conf(_event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(cw, width=canvas.winfo_width())
        inner.bind("<Configure>", _conf)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=canvas.winfo_width()))
        self._wheel_bind(w, canvas)
        w._canvas = canvas
        w._scroll_frame = inner
        return w, top, inner, bottom

    def _form(self, w, fields: list[tuple[str, str, str]]) -> dict[str, tk.Entry]:
        out = {}
        for key, label, default in fields:
            tk.Label(w, text=label, bg=C["panel2"], fg=C["dim"], font=pick_font(10), anchor="e").pack(fill="x", padx=16, pady=(8, 0))
            e = tk.Entry(w, bg="#0a1424", fg=C["tx"], relief="flat", font=pick_font(12),
                         justify="right", insertbackground=C["cy"])
            e.insert(0, default)
            e.pack(fill="x", padx=16, ipady=5)
            out[key] = e
        return out

    def _result_box(self, w):
        t = scrolledtext.ScrolledText(w, bg="#070d18", fg=C["tx"], font=pick_font(11), height=14,
                                      relief="flat", wrap="word")
        t.pack(fill="both", expand=True, padx=16, pady=10)
        return t

    def _panel_profile(self):
        from patient_profile import load_profile, save_profile
        p = load_profile()
        w = self._win(self.L("Patient profile", "پروفایل بیمار"))
        ents = self._form(w, [("name", self.L("Name", "نام"), p.get("name", "")), ("age", self.L("Age", "سن"), p.get("age", "")),
                              ("gender", self.L("Sex (male/female)", "جنسیت (مرد/زن)"), p.get("gender", "")),
                              ("weight_kg", self.L("Weight (kg)", "وزن (kg)"), p.get("weight_kg", "")),
                              ("height_cm", self.L("Height (cm)", "قد (cm)"), p.get("height_cm", "")),
                              ("conditions", self.L("Existing conditions", "بیماری زمینه‌ای"), p.get("conditions", "")),
                              ("allergies", self.L("Drug/food allergies", "حساسیت دارویی/غذایی"), p.get("allergies", "")),
                              ("medications", self.L("Current medications", "داروهای فعلی"), p.get("medications", ""))])

        def save():
            save_profile({k: e.get() for k, e in ents.items()})
            messagebox.showinfo(self.L("Profile", "پروفایل"), self.L("Saved (patient_profile.json)", "ذخیره شد (patient_profile.json)"), parent=w)
        tk.Button(w, text=self.L("Save", "ذخیره"), command=save, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(pady=10, ipadx=24, ipady=4)

    def _panel_vitals(self):
        from health_vitals import history, record, trend
        w = self._win(self.L("Vitals", "علائم حیاتی"))
        ents = self._form(w, [("systolic_bp", self.L("Systolic pressure (e.g. 120)", "فشار سیستول (مثلاً ۱۲۰)"), ""),
                              ("diastolic_bp", self.L("Diastolic pressure (e.g. 80)", "فشار دیاستول (مثلاً ۸۰)"), ""),
                              ("weight_kg", self.L("Weight (kg)", "وزن (kg)"), ""), ("height_cm", self.L("Height (cm)", "قد (cm)"), ""),
                              ("heart_rate", self.L("Pulse", "نبض"), ""), ("temp_c", self.L("Body temperature", "دمای بدن"), ""), ("glucose", self.L("Blood sugar", "قند خون"), "")])
        box = self._result_box(w)

        def go():
            data = {k: e.get().replace("۰", "0").replace("۱", "1").replace("۲", "2").replace("۳", "3").replace("۴", "4")
                     .replace("۵", "5").replace("۶", "6").replace("۷", "7").replace("۸", "8").replace("۹", "9")
                    for k, e in ents.items() if e.get().strip()}
            r = record(data)
            lines = []
            if r.get("bmi"):
                lines.append(f"BMI: {r['bmi']['bmi']} — {r['bmi']['category_fa']}\n{r['bmi']['tip_fa']}")
            if r.get("bp"):
                lines.append(self.L("Pressure: ", "فشار: ") + f"{r['bp']['systolic']}/{r['bp']['diastolic']} — {r['bp']['category_fa']}\n{r['bp']['action_fa']}")
            lines.append(self.L("\n— recent history —", "\n— تاریخچه‌ی اخیر —"))
            for h in history(6):
                lines.append(str(h))
            lines.append(self.L("Trend: ", "روند: ")+ str(trend()))
            box.delete("1.0", "end")
            box.insert("1.0", "\n\n".join(lines))
        tk.Button(w, text=self.L("Record & analyze", "ثبت و تحلیل"), command=go, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(pady=8, ipadx=24, ipady=4)

    def _panel_labs(self):
        from lab_visualizer import analyze_text
        w = self._win(self.L("Lab analysis", "تحلیل آزمایش"))
        tk.Label(w, text=self.L("One test per line — e.g. FBS 132 / Hb 10.5 / TSH 6.2 / cholesterol 210", "هر خط یک آزمایش — مثال: FBS 132 / Hb 10.5 / TSH 6.2 / کلسترول 210"),
                 bg=C["panel2"], fg=C["dim"], font=pick_font(10)).pack(padx=16, pady=8)
        txt = scrolledtext.ScrolledText(w, bg="#0a1424", fg=C["tx"], font=pick_font(12), height=6, relief="flat")
        txt.pack(fill="x", padx=16)
        box = self._result_box(w)

        def go():
            r = analyze_text(txt.get("1.0", "end"), save_html=True)
            box.delete("1.0", "end")
            box.insert("1.0", r.get("text_report", "") + "\n\n"+ "\n".join(r.get("summary_fa", [])))
            if r.get("html_path"):
                box.insert("end", self.L("\n\n visual report: ", "\n\n گزارش تصویری: ") + r["html_path"])
        tk.Button(w, text=self.L("Analyze", "تحلیل"), command=go, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(pady=8, ipadx=24, ipady=4)

    def _panel_rx(self):
        from prescription_scanner import scan
        w = self._win(self.L("Prescription scan", "اسکن نسخه"))
        tk.Label(w, text=self.L("Type the prescription/lab text: BID, TID, PO, PRN, AC, QHS, WBC, FBS, TSH…", "متن نسخه/آزمایش را بنویس: BID, TID, PO, PRN, AC, QHS, WBC, FBS, TSH…"),
                 bg=C["panel2"], fg=C["dim"], font=pick_font(10)).pack(padx=16, pady=8)
        txt = scrolledtext.ScrolledText(w, bg="#0a1424", fg=C["tx"], font=pick_font(12), height=6, relief="flat")
        txt.pack(fill="x", padx=16)
        box = self._result_box(w)

        def go():
            r = scan(txt.get("1.0", "end"))
            lines = []
            for t in r.get("translations", []):
                lines.append(f"{t['abbr']} → {t['fa']} ({t['type']})")
            for d in r.get("drugs", []):
                lines.append(self.L("Drug: ", "دارو: ") + f"{d['fa']} ({d['cat']})")
            for a in r.get("alerts", []):
                lines.append(""+ a)
            lines.append(r.get("disclaimer", ""))
            box.delete("1.0", "end")
            box.insert("1.0", "\n".join(lines) if lines else self.L("Nothing recognized.", "چیزی شناسایی نشد."))
        tk.Button(w, text=self.L("Translate", "ترجمه"), command=go, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(pady=8, ipadx=24, ipady=4)

    def _panel_drugs(self):
        from drug_interaction import check_interaction, search_drug
        w = self._win(self.L("Drugs & interactions", "دارو و تداخلات"))
        ents = self._form(w, [("a", self.L("First drug (english or persian)", "داروی اول (نام فارسی یا انگلیسی)"), ""), ("b", self.L("Second drug (to check interaction)", "داروی دوم (برای بررسی تداخل)"), "")])
        box = self._result_box(w)

        def go():
            lines = []
            for key in ("a", "b"):
                if ents[key].get().strip():
                    res = search_drug(ents[key].get())
                    if res:
                        lines.append(key + ": " + " | ".join(f"{d['fa']} ({d['cat']})" for d in res[:3]))
            if ents["a"].get().strip() and ents["b"].get().strip():
                r = check_interaction(ents["a"].get(), ents["b"].get())
                for it in r.get("interactions", [{}]):
                    lines.append(f"{it.get('severity_fa','')}: {it.get('detail_fa','')}")
                if r.get("message_fa"):
                    lines.append(r["message_fa"])
                lines.append(r.get("disclaimer", ""))
            box.delete("1.0", "end")
            box.insert("1.0", "\n\n".join(lines) if lines else self.L("Enter a drug (e.g. warfarin, ibuprofen, garlic, ginger)", "نام دارو را وارد کن (مثلاً: وارفارین، ژلوفن، سیر، زنجبیل)"))
        tk.Button(w, text=self.L("Check", "بررسی"), command=go, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(pady=8, ipadx=24, ipady=4)

    def _panel_image(self):
        w = self._win(self.L("Medical image analysis", "تحلیل تصویر پزشکی"))
        tk.Label(w, text=self.L("1) pick the photo 2) write a note (e.g. this red patch itches for 3 days) 3) send", "۱) عکس را انتخاب کن ۲) توضیح بنویس (مثلاً: این لک قرمز ۳ روزه خارش دارد) ۳) ارسال"),
                 bg=C["panel2"], fg=C["dim"], font=pick_font(10)).pack(padx=16, pady=8)
        path = {"p": ""}

        def pick():
            p = filedialog.askopenfilename(parent=w, filetypes=[(self.L("Images", "تصاویر"), "*.jpg *.jpeg *.png *.webp *.bmp")])
            if p:
                path["p"] = p
                lbl.config(text=""+ os.path.basename(p))
        from i18n import is_fa
        tk.Label(w, text=("Image type (optional - auto-detected too)" if not is_fa() else self.L("Image type (optional — auto-detected too)", "نوع تصویر (اختیاری — خودکار هم تشخیص داده می‌شود)")),
                 bg=C["panel2"], fg=C["dim"], font=pick_font(10)).pack(padx=16, pady=(8, 0))
        hint_var = tk.StringVar(value=("Auto-detect" if not is_fa() else self.L("Auto detect", "تشخیص خودکار")))
        hint_menu = ttk.Combobox(w, textvariable=hint_var, state="readonly", font=pick_font(10),
                                 values=(["Auto-detect", "Skin / rash", "Wound / burn", "X-ray / CT / MRI", "ECG", "Lab report / prescription", "Eye", "Dental / oral", "Device screen", "Other"] if not is_fa()
                                         else [self.L("Auto detect", "تشخیص خودکار"), self.L("Skin / acne", "پوست / جوش"), self.L("Wound / burn", "زخم / سوختگی"), self.L("Radiology / CT / MRI", "رادیوگرافی / سی‌تی / ام‌آرآی"), self.L("ECG strip", "نوار قلب"), self.L("Lab sheet / prescription", "برگه‌ی آزمایش / نسخه"), self.L("Eye", "چشم"), self.L("Tooth / mouth", "دندان / دهان"), self.L("Device monitor", "نمایشگر دستگاه"), self.L("Other", "سایر")]))
        hint_menu.pack(fill="x", padx=16)
        HINT_MAP = {"Auto-detect": "", self.L("Auto detect", "تشخیص خودکار"): "", "Skin / rash": "skin", self.L("Skin / acne", "پوست / جوش"): "skin",
                    "Wound / burn": "wound", self.L("Wound / burn", "زخم / سوختگی"): "wound", "X-ray / CT / MRI": "xray",
                    self.L("Radiology / CT / MRI", "رادیوگرافی / سی‌تی / ام‌آرآی"): "xray", "ECG": "ecg", self.L("ECG strip", "نوار قلب"): "ecg",
                    "Lab report / prescription": "lab", self.L("Lab sheet / prescription", "برگه‌ی آزمایش / نسخه"): "lab",
                    "Eye": "eye", self.L("Eye", "چشم"): "eye", "Dental / oral": "dental", self.L("Tooth / mouth", "دندان / دهان"): "dental",
                    "Device screen": "device", self.L("Device monitor", "نمایشگر دستگاه"): "device", "Other": "other", self.L("Other", "سایر"): "other"}
        tk.Button(w, text=("Choose image" if not is_fa() else self.L("Pick photo", "انتخاب عکس")), command=pick, bg="#0d1930", fg=C["tx"], relief="flat",
                  font=pick_font(11)).pack(pady=4)
        lbl = tk.Label(w, text="—", bg=C["panel2"], fg=C["yl"], font=pick_font(10))
        lbl.pack()
        note = tk.Text(w, bg="#0a1424", fg=C["tx"], font=pick_font(12), height=3, relief="flat")
        note.pack(fill="x", padx=16, pady=8)
        box = self._result_box(w)

        def go():
            if not path["p"]:
                messagebox.showwarning(self.L("Image", "تصویر"), self.L("Pick a photo first.", "اول عکس را انتخاب کن."), parent=w)
                return
            from image_caption import analyze_image_file
            hint = HINT_MAP.get(hint_var.get(), "")
            r = analyze_image_file(path["p"], note.get("1.0", "end").strip(), hint=hint)
            box.delete("1.0", "end")
            box.insert("1.0", f"[{r.get('source','')}]\n\n"+ r.get("text", ""))
            self._refresh_status()
        tk.Button(w, text=self.L("Analyze", "تحلیل"), command=go, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(pady=8, ipadx=24, ipady=4)

    def _panel_assess(self):
        from medical_engine import analyze, emergency_response
        from ml_classifier import predict as ml_predict
        w = self._win(self.L("Disease likelihood assessment", "ارزیابی احتمال بیماری‌ها"))
        from i18n import is_fa
        tk.Label(w, text=("Describe symptoms in one or a few lines (onset, severity, duration)" if not is_fa()
                          else self.L("Describe symptoms in one or more lines (onset, severity, duration)", "علائم را در یک یا چند خط بنویس (شروع، شدت، مدت)")),
                 bg=C["panel2"], fg=C["dim"], font=pick_font(10)).pack(padx=16, pady=8)
        txt = scrolledtext.ScrolledText(w, bg="#0a1424", fg=C["tx"], font=pick_font(12), height=4, relief="flat")
        txt.pack(fill="x", padx=16)
        box = self._result_box(w)

        def go():
            text = txt.get("1.0", "end").strip()
            if not text:
                return
            a = analyze(text)
            lines = []
            if a["red_flag"]:
                box.delete("1.0", "end")
                box.insert("1.0", emergency_response(a["red_flag_reasons"]))
                return
            from i18n import is_fa
            fa_mode = is_fa()
            lines.append(((self.L("Symptoms: ", "علائم: ") if fa_mode else "Symptoms: ") + ("، ".join(a["symptoms"]) if fa_mode else ", ".join(a["symptoms"]))) or "—")
            if a["denied"]:
                lines.append((self.L("Denied: ", "ردشده: ") if fa_mode else "Ruled out: ") + ("، ".join(a["denied"]) if fa_mode else ", ".join(a["denied"])))
            lines.append("")
            if a["candidates"]:
                lines.append(self.L("Likelihoods (probable ranking — not a diagnosis):", "احتمالات (رتبه‌بندی احتمالی — تشخیص قطعی نیست):") if fa_mode else "Possibilities (probabilistic ranking - NOT a diagnosis):")
                for c in a["candidates"]:
                    lines.append(f"• {c['name']} ~{c['percent']}%  [{c['urgency']}]")
                    lines.append("   " + ("؛ ".join(c.get("advice", [])[:2])))
                    if c.get("doctor_when"):
                        lines.append("   -> " + c["doctor_when"])
            else:
                lines.append(self.L("Not enough information yet.", "اطلاعات کافی نیست.") if fa_mode else "Not enough information yet.")
            # triage suggestion
            if a["candidates"]:
                urg = [c["urgency"] for c in a["candidates"][:3]]
                level = "emergency" if "emergency" in urg else ("urgent" if "urgent" in urg else "routine")
                where = {"emergency": ("Go to the emergency department NOW or call 115/112.", self.L("Go to the ER now or call 115/112.", "همین حالا به اورژانس برو یا با ۱۱۵/۱۱۲ تماس بگیر.")),
                         "urgent": ("See a clinician today or at the first opportunity.", self.L("See a doctor today or at the first chance.", "امروز یا در اولین فرصت به پزشک مراجعه کن.")),
                         "routine": ("A routine visit is enough; monitor your symptoms.", self.L("A routine visit is enough; keep an eye on symptoms.", "مراجعه‌ی سرپایی کافی است؛ علائم را زیر نظر بگیر."))}[level]
                lines.append("")
                lines.append((self.L("Triage suggestion: ", "پیشنهاد تریاژ: ") if fa_mode else "Triage suggestion: ") + level)
                lines.append("   " + (where[1] if fa_mode else where[0]))
            try:
                ml = ml_predict(a["detected"], {}, None)
                if ml:
                    lines.append("")
                    lines.append((self.L("ML signal (synthetic dataset): ", "سیگنال ML (دیتاست مصنوعی): ") if fa_mode else "ML signal (synthetic dataset): ")
                                 + ("، ".join(f"{m['label']} (~{m['percent']}%)" for m in ml[:2])))
            except Exception:
                pass
            box.delete("1.0", "end")
            box.insert("1.0", "\n".join(lines))
        tk.Button(w, text=self.L("Assess", "ارزیابی"), command=go, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(pady=8, ipadx=24, ipady=4)

    def _panel_mental(self):
        from mental_health import GAD7, PHQ9
        w = self._win(self.L("Mental health — PHQ-9 / GAD-7", "سلامت روان — PHQ-9 / GAD-7"))
        var_type = tk.StringVar(value="phq9")
        box = self._result_box(w)
        qs = {"phq9": [q["fa"] if __import__("i18n").is_fa() else q["en"] for q in PHQ9], "gad7": [q["fa"] if __import__("i18n").is_fa() else q["en"] for q in GAD7]}
        frame = tk.Frame(w, bg=C["panel2"])

        def render():
            for ch in frame.winfo_children():
                ch.destroy()
            rows = {}

            def make_submit():
                from mental_health import gad7, phq9
                n = 9 if var_type.get() == "phq9"else 7
                answers = [rows.get(i, tk.IntVar(value=0)).get() for i in range(n)]
                r = phq9(answers) if var_type.get() == "phq9"else gad7(answers)
                out = [self.L("Score: ", "نمره: ") + f"{r['total']} — {r['band_fa']}"]
                out += r.get("recommendations_fa", [])
                if r.get("crisis"):
                    out.append("\n"+ r["crisis_text"])
                out.append(r.get("note", ""))
                box.delete("1.0", "end")
                box.insert("1.0", "\n".join(out))
            for i, q in enumerate(qs[var_type.get()]):
                tk.Label(frame, text=q, bg=C["panel2"], fg=C["tx"], font=pick_font(10), anchor="e").pack(fill="x", padx=16, pady=(6, 0))
                rowf = tk.Frame(frame, bg=C["panel2"])
                rowf.pack(fill="x", padx=16)
                v = tk.IntVar(value=0)
                rows[i] = v
                for val, lbl in enumerate((self.L("Not at all", "هرگز"), self.L("Several days", "چند روز"), self.L("More than half the days", "نیمی از روزها"), self.L("Nearly every day", "هر روز"))):
                    tk.Radiobutton(rowf, text=lbl, variable=v, value=val, bg=C["panel2"], fg=C["dim"],
                                   selectcolor="#0a1424", activebackground=C["panel2"],
                                   activeforeground=C["cy"], font=pick_font(9)).pack(side="right", padx=8)
            tk.Button(frame, text=self.L("Score it", "محاسبه"), command=make_submit, bg="#0077b6", fg="#021018",
                      font=pick_font(11, True), relief="flat").pack(pady=10)
        top_bar = tk.Frame(w, bg=C["panel2"])
        top_bar.pack(fill="x", pady=6)
        tk.Radiobutton(top_bar, text=self.L("PHQ-9 (depression)", "PHQ-9 (افسردگی)"), variable=var_type, value="phq9", command=render,
                       bg=C["panel2"], fg=C["tx"], selectcolor="#0a1424", activebackground=C["panel2"],
                       activeforeground=C["cy"], font=pick_font(10)).pack(side="right", padx=14)
        tk.Radiobutton(top_bar, text=self.L("GAD-7 (anxiety)", "GAD-7 (اضطراب)"), variable=var_type, value="gad7", command=render,
                       bg=C["panel2"], fg=C["tx"], selectcolor="#0a1424", activebackground=C["panel2"],
                       activeforeground=C["cy"], font=pick_font(10)).pack(side="right", padx=14)
        tk.Label(top_bar, text=self.L("4-7-8 breathing: inhale 4s, hold 7s, exhale 8s — four cycles", "تمرین تنفس ۴-۷-۸: دم ۴ ثانیه، نگه‌داشتن ۷، بازدم ۸ — چهار چرخه"),
                 bg=C["panel2"], fg=C["dim"], font=pick_font(9)).pack(side="left", padx=10)
        frame.pack(fill="x")
        render()

    def _panel_sleep(self):
        from sleep_analyzer import questions, stopbang
        qs = questions()
        w = self._win(self.L("Sleep analysis — STOP-BANG", "تحلیل خواب — STOP-BANG"))
        box = self._result_box(w)
        vars_ = []
        f = tk.Frame(w, bg=C["panel2"])
        f.pack(fill="x")
        for q in qs["stopbang"]:
            v = tk.BooleanVar(value=False)
            vars_.append(v)
            tk.Checkbutton(f, text=f"{q['letter']} — {q['q_fa']}", variable=v, bg=C["panel2"], fg=C["tx"],
                           selectcolor="#0a1424", activebackground=C["panel2"], activeforeground=C["cy"],
                           font=pick_font(10), anchor="e", justify="right").pack(fill="x", padx=16, pady=1)

        def go():
            r = stopbang([1 if v.get() else 0 for v in vars_])
            out = [f"{r['total']} " + self.L("of 8 — ", "از ۸ — ") + r["risk_fa"], self.L("positives: ", "موارد مثبت: ") + ("، ".join(r["answers_fa"]) or "—")]
            out += r.get("recommendations_fa", [])
            out.append(r.get("note", ""))
            box.delete("1.0", "end")
            box.insert("1.0", "\n".join(out))
        tk.Button(w, text=self.L("Score it", "محاسبه"), command=go, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(pady=8, ipadx=24, ipady=4)

    def _panel_checkup(self):
        from checkup_calendar import recommendations
        w = self._win(self.L("Checkup & vaccine calendar", "تقویم چکاپ و واکسن"))
        box = self._result_box(w)

        def go():
            r = recommendations()
            lines = [self.L("— checkups (age ", "— چکاپ‌ها (سن ") + str(r.get('age') or '—') + " —"]
            lines += [f"• {c['title']}: {c['interval_fa']}" for c in r.get("checkups", [])]
            lines.append(self.L("\n— vaccines —", "\n— واکسن‌ها —"))
            lines += [f"• {v['title']}: {v['interval_fa']}" for v in r.get("vaccines", [])]
            lines.append("\n"+ r.get("note_fa", ""))
            box.delete("1.0", "end")
            box.insert("1.0", "\n".join(lines))
        tk.Button(w, text=self.L("Get suggestions", "پیشنهاد بگیر"), command=go, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(pady=8, ipadx=24, ipady=4)
        go()

    def _panel_emergency(self):
        from first_aid import TOPICS, cpr_timing
        w = self._win(self.L("First aid / CPR", "کمک‌های اولیه / CPR"))
        box = self._result_box(w)
        tk.Label(w, text=self.L("Emergency: Iran 115 | Europe/Finland 112", "اورژانس: ایران ۱۱۵ | اروپا/فنلاند ۱۱۲"), bg="#2a0d1a", fg="#ff8fab",
                 font=pick_font(12, True), pady=6).pack(fill="x")
        cpr = {"on": False, "job": None}
        timing = cpr_timing()
        cpr_btn = tk.Button(w, text=self.L("START/STOP CPR metronome", "START/STOP مترونوم CPR") + f" — {timing['bpm']} BPM", relief="flat",
                            bg="#1c0a14", fg=C["mg"], font=pick_font(13, True))

        def beat():
            try_beep(880, 120)
            cpr["job"] = w.after(int(timing["interval_sec"] * 1000), beat)
        def toggle():
            if cpr["on"]:
                if cpr["job"]:
                    w.after_cancel(cpr["job"])
                cpr["on"] = False
                cpr_btn.config(text=self.L("START/STOP CPR metronome", "START/STOP مترونوم CPR") + f" — {timing['bpm']} BPM")
            else:
                cpr["on"] = True
                beat()
        cpr_btn.config(command=toggle)
        cpr_btn.pack(fill="x", padx=16, pady=8, ipady=8)
        bar = tk.Frame(w, bg=C["panel2"])
        bar.pack(fill="x")
        from i18n import pick as _pick2
        for key, t in TOPICS.items():
            tk.Button(bar, text=_pick2(t["title"]), command=lambda k=key: show(k), bg="#0d1930",
                      fg=C["tx"], relief="flat", font=pick_font(10)).pack(side="right", padx=3, pady=4)

        def show(key):
            from first_aid import get_topic
            tp = get_topic(key) or {}
            lines = [tp.get("title", key), "="* 34, *(tp.get("steps") or []), ""]
            lines += list(tp.get("warnings") or [])
            lines.append(tp.get("disclaimer", ""))
            lines.append("\n" + str(tp.get('emergency_line', '')) + self.L(" | depth ", " | عمق ") + str(timing['depth_cm']) + self.L(" | ratio ", " | نسبت ") + str(timing['ratio']))
            box.delete("1.0", "end")
            box.insert("1.0", "\n".join(lines))
        show("cpr")
        win = w.winfo_toplevel()  # w is only the inner frame; grab the real toplevel
        win.protocol("WM_DELETE_WINDOW", lambda: (toggle() if cpr["on"] else None, win.destroy()))

    # ------------------------------------------------ symptom/disease/drug browsers
    def _panel_symptoms(self):
        """
        Symptoms module: tick symptoms, get a likelihood ranking.
        """
        from knowledge_browser import get_all_symptoms
        syms = get_all_symptoms()
        w, top, inner, bottom = self._win_list(self.L("Symptoms — check & analyze", "علائم — تیک بزن و تحلیل بگیر"))

        tk.Label(top, text=self.L(f"All symptoms ({len(syms)}) — check what you have:",
                                  f"همه‌ی علائم ({len(syms)}) — هر چی داری تیک بزن:"),
                 bg=C["panel2"], fg=C["cy"], font=pick_font(11, True), anchor="e").pack(fill="x", padx=16, pady=(10, 2))
        sv = tk.StringVar(value="")
        search = tk.Entry(top, textvariable=sv, bg="#0a1424", fg=C["tx"], relief="flat", font=pick_font(11),
                          justify="right", insertbackground=C["cy"])
        search.pack(fill="x", padx=16, ipady=4)
        cnt_lbl = tk.Label(top, text=self.L("selected: 0", "انتخاب‌شده: ۰"), bg=C["panel2"],
                           fg=C["yl"], font=pick_font(9), anchor="e")
        cnt_lbl.pack(fill="x", padx=16, pady=(0, 4))

        vars_: dict[str, tk.BooleanVar] = {}
        rows = []

        def upd_cnt():
            n = sum(1 for v in vars_.values() if v.get())
            cnt_lbl.config(text=self.L(f"selected: {n}", f"انتخاب‌شده: {n}"))

        from i18n import get_lang as _gl_s
        _fa_s = _gl_s() == "fa"
        def _sym_name(s):
            return s["fa"] if _fa_s else (s.get("en", "") or s["fa"])
        from knowledge_browser import symptom_checklist
        all_syms = symptom_checklist(240)
        _fa_chk = _gl_s() == "fa"
        for s in all_syms:
            v = tk.BooleanVar(value=False)
            vars_[s["id"]] = v
            row = tk.Frame(inner, bg=C["panel2"])
            _nm_chk = (s["fa"] or s["en"]) if _fa_chk else s["en"]
            _sub_chk = (" ✓engine" if s.get("engine") else f"  {s.get('count', 0)}")
            cb = tk.Checkbutton(row, text=_nm_chk, variable=v, command=upd_cnt,
                                bg=C["panel2"], fg=C["tx"], selectcolor="#0a1424",
                                activebackground=C["panel2"], activeforeground=C["cy"],
                                font=pick_font(10), anchor="e", justify="right", cursor="hand2")
            cb.pack(side="right", fill="x", expand=True)
            tk.Label(row, text=_sub_chk, bg=C["panel2"], fg=C["dim"], font=pick_font(8),
                     anchor="e").pack(side="right", padx=(0, 6))
            row.pack(fill="x", padx=10, pady=1)
            rows.append((row, (s["fa"] + " " + s["en"]).lower()))

        def do_filter(*_):
            q = sv.get().strip().lower()
            for row, txt in rows:
                row.pack() if q in txt else row.pack_forget()
        sv.trace_add("write", do_filter)

        box = scrolledtext.ScrolledText(bottom, bg="#070d18", fg=C["tx"], font=pick_font(10),
                                        height=10, relief="flat", wrap="word")

        def analyze_now():
            names = []
            for s2 in all_syms:
                if vars_.get(s2["id"]) and vars_[s2["id"]].get():
                    names.append((s2["fa"] or s2["en"]) if _fa_chk else s2["en"])
            box.delete("1.0", "end")
            if not names:
                box.insert("1.0", self.L("Check at least one symptom first.", "اول حداقل یک علامت تیک بزن."))
                return
            from medical_engine import analyze
            r = analyze("\n".join(names))
            lines = []
            if r.get("red_flag"):
                lines.append("‼ " + self.L("EMERGENCY signs — seek urgent care NOW (115/112).",
                                           "نشانه‌ی اورژانسی — همین حالا به اورژانس مراجعه کن (۱۱۵/۱۱۲)."))
                for reason in (r.get("red_flag_reasons") or [])[:4]:
                    lines.append("   • " + str(reason))
            lines.append(self.L(f"Detected symptoms: {len(r.get('symptoms', []))}",
                                f"علائم تشخیص داده‌شده: {len(r.get('symptoms', []))}"))
            lines.append("")
            for c in (r.get("candidates") or [])[:8]:
                pct = c.get("percent")
                pct = (str(pct) + self.L("%", "٪")) if pct not in (None, "") else ""
                urg = {"emergency": self.L("emergency", "اورژانس"), "urgent": self.L("urgent", "فوری"),
                       "routine": self.L("routine", "معمولی")}.get(c.get("urgency"), c.get("urgency", ""))
                from i18n import get_lang as _gl2
                _nm = c.get("fa", "") if _gl2() == "fa" else c.get("name", c.get("fa", ""))
                lines.append("• " + str(_nm or c.get("name", "")) + "  " + pct + "  [" + urg + "]")
                ms = c.get("matched_symptoms") or []
                if ms:
                    lines.append("    " + self.L("matched: ", "علائم منطبق: ") + "، ".join(str(m) for m in ms[:6]))
            lines.append("")
            lines.append(self.L("This is not a definitive diagnosis — a doctor's visit is necessary.",
                                "این تشخیص قطعی نیست — مراجعه به پزشک لازم است."))
            box.insert("1.0", "\n".join(lines))

        def clear_all():
            for v in vars_.values():
                v.set(False)
            upd_cnt()

        bar2 = tk.Frame(bottom, bg=C["panel2"])
        bar2.pack(fill="x", pady=(6, 0))
        def bank_match_now():
            picked = []
            for s2 in all_syms:
                if vars_.get(s2["id"]) and vars_[s2["id"]].get():
                    picked.append((s2["fa"] or s2["en"]) if _fa_chk else s2["en"])
            box.delete("1.0", "end")
            if not picked:
                box.insert("1.0", self.L("Tick at least one symptom first.", "اول حداقل یک علامت تیک بزن."))
                return
            from knowledge_browser import match_diseases_by_symptoms
            res = match_diseases_by_symptoms(picked, 12)
            _fa_bm = _gl_s() == "fa"
            lines = [self.L("— matches across the WHOLE disease bank —", "— تطبیق در کل بانک بیماری‌ها —")]
            for m in res:
                nm = (m.get("fa") or m["name"]) if _fa_bm else m["name"]
                lines.append(f"• {nm}  [{int(m['score']*100)}٪]  ({m['src']})")
                lines.append("    " + self.L("matched: ", "علائم منطبق: ") + "، ".join(m.get("matched", [])[:6]))
            lines.append("")
            lines.append(self.L("(simple overlap matching — not a diagnosis)", "(تطبیق ساده‌ی هم‌پوشانی علائم — تشخیص قطعی نیست)"))
            box.delete("1.0", "end")
            box.insert("1.0", "\n".join(lines))
        tk.Button(bar2, text=self.L("Search all diseases", "جستجو در همه‌ی بیماری‌ها"), command=bank_match_now, bg="#0d5a4a",
                  fg="#c8ffe9", font=pick_font(11, True), relief="flat").pack(side="right", padx=4, ipadx=10, ipady=3)
        tk.Button(bar2, text=self.L("Analyze", "تحلیل علائم"), command=analyze_now, bg="#0077b6",
                  fg="#021018", font=pick_font(11, True), relief="flat").pack(side="right", padx=16, ipadx=14, ipady=3)
        tk.Button(bar2, text=self.L("Clear", "پاک‌کردن"), command=clear_all, bg="#0d1930",
                  fg=C["tx"], font=pick_font(10), relief="flat").pack(side="right", ipadx=8, ipady=3)
        box.pack(fill="both", expand=True, padx=16, pady=(4, 8))

        # full HPO vocabulary search (about 20k terms)
        hpo_bar = tk.Frame(bottom, bg=C["panel2"])
        hpo_bar.pack(fill="x", pady=(6, 0), before=box)
        hpo_var = tk.StringVar(value="")
        hpo_entry = tk.Entry(hpo_bar, textvariable=hpo_var, bg="#0a1424", fg=C["tx"], relief="flat",
                             font=pick_font(10), justify="right", insertbackground=C["cy"])
        hpo_entry.pack(side="right", fill="both", expand=True, ipady=3, padx=(16, 0))
        tk.Button(hpo_bar, text=self.L("HPO search", "جستجوی HPO"), command=lambda: run_hpo(), bg="#0d1930",
                  fg=C["yl"], font=pick_font(9), relief="flat").pack(side="right", padx=(6, 0), ipadx=6)
        def run_hpo():
            q = hpo_var.get().strip()
            if not q:
                return
            try:
                from knowledge_browser import search_hpo, hpo_count
                res = search_hpo(q, 40)
                lines = [self.L("HPO (", "HPO (") + str(hpo_count()) + self.L(" terms) — results for: ", " اصطلاح) — نتایج «") + q + self.L("", "»:")]
                for t in res:
                    line = "• " + t["name"] + "  [" + t["id"] + "]"
                    if t.get("syn"):
                        line += "  — " + "، ".join(t["syn"][:2])
                    lines.append(line)
                out = "\n".join(lines) if res else self.L("Nothing found — try english (e.g. headache).", "چیزی پیدا نشد — انگلیسی امتحان کن (مثل headache).")
            except Exception as ex:
                out = self.L("Error: ", "خطا: ") + str(ex)[:100]
            box.delete("1.0", "end")
            box.insert("1.0", out)
        hpo_entry.bind("<Return>", lambda _e: run_hpo())



        # which diseases have a symptom (wiki + engine index)
        sd_bar = tk.Frame(bottom, bg=C["panel2"])
        sd_bar.pack(fill="x", pady=(6, 0), before=box)
        sd_var = tk.StringVar(value="")
        sd_entry = tk.Entry(sd_bar, textvariable=sd_var, bg="#0a1424", fg=C["tx"], relief="flat",
                            font=pick_font(10), justify="right", insertbackground=C["cy"])
        sd_entry.pack(side="right", fill="both", expand=True, ipady=3, padx=(16, 0))
        tk.Button(sd_bar, text=self.L("symptom → diseases", "این علامت کدام بیماری‌ها"), command=lambda: run_symdis(),
                  bg="#0d1930", fg=C["yl"], font=pick_font(9), relief="flat").pack(side="right", padx=(6, 0), ipadx=6)
        def run_symdis():
            q = sd_var.get().strip()
            if not q:
                return
            try:
                from knowledge_browser import search_symptom_diseases
                res = search_symptom_diseases(q, 20)
                _fa_sd = __import__("i18n").get_lang() == "fa"
                lines = [self.L("diseases carrying this symptom:", "بیماری‌هایی که این علامت را دارند:")]
                for s in res:
                    nm = (s.get("fa") or s.get("en")) if _fa_sd else s.get("en")
                    lines.append("• " + nm)
                    dis = [((d.get("fa") or d.get("en")) if _fa_sd else d.get("en")) for d in s.get("diseases", [])]
                    lines.append("    " + self.L("diseases: ", "بیماری‌ها: ") + (_fa_sd and "، " or ", ").join(dis))
                out = "\n".join(lines) if res else self.L("nothing found — try another wording", "چیزی پیدا نشد — عبارت دیگری امتحان کن")
            except Exception as ex:
                out = "Error: " + str(ex)[:100]
            box.delete("1.0", "end")
            box.insert("1.0", out)
        sd_entry.bind("<Return>", lambda _e: run_symdis())


    def _panel_diseases(self):
        """
        Disease database: counts, symptoms with probabilities, urgency, advice.
        """
        from knowledge_browser import get_all_diseases
        dis = get_all_diseases()
        w, top, inner, bottom = self._win_list(self.L("Diseases database", "بانک بیماری‌ها"))

        urg_fa = {"emergency": ("اورژانس", "#ff2a6d"), "urgent": ("فوری", "#ffd60a"), "routine": ("معمولی", "#3bff9e")}
        from medical_catalog import stats as cat_stats
        _cat_n = cat_stats().get("conditions", 0)
        tk.Label(top, text=self.L(f"Diagnostic engine: {len(dis)} diseases  |  Full ICD-10 catalog: {_cat_n:,} — type to search both",
                                  f"موتور تشخیص: {len(dis)} بیماری  |  کاتالوگ کامل ICD-10: {_cat_n:,} مورد — تایپ کن تا هر دو جستجو شوند"),
                 bg=C["panel2"], fg=C["cy"], font=pick_font(11, True), anchor="e", wraplength=640, justify="right").pack(fill="x", padx=16, pady=(10, 2))
        sv = tk.StringVar(value="")
        search = tk.Entry(top, textvariable=sv, bg="#0a1424", fg=C["tx"], relief="flat", font=pick_font(11),
                          justify="right", insertbackground=C["cy"])
        search.pack(fill="x", padx=16, ipady=4, pady=(0, 6))

        box = scrolledtext.ScrolledText(bottom, bg="#070d18", fg=C["tx"], font=pick_font(10),
                                        height=10, relief="flat", wrap="word")

        def show_detail(d):
            u_fa, u_col = urg_fa.get(d.get("urgency"), (d.get("urgency"), C["tx"]))
            lines = [f"◀ {d.get('name', '')}  [{u_fa}]", ""]
            sy = d.get("symptoms") or []
            if sy:
                lines.append(self.L("Symptoms (probability):", "علائم (با احتمال):"))
                for s in sy:
                    lines.append(f"   • {s.get('name','')} — {int(round((s.get('probability') or 0) * 100))}" + self.L("%", "٪"))
            lines.append("")
            # full bilingual treatment block
            from knowledge_browser import guess_treatment
            _tr_fa, _tr_en = guess_treatment(d.get("name", "") or d.get("en", ""))
            from i18n import get_lang as _gl_td
            lines.append(self.L("Treatment: ", "درمان: ") + ((_tr_fa if _gl_td() == "fa" else _tr_en)))
            lines.append("")
            labs = d.get("labs") or []
            if labs:
                from i18n import get_lang as _gl
                _fa = _gl() == "fa"
                _names = [x.get("fa", "") if _fa else x.get("en", "") for x in labs if isinstance(x, dict)]
                lines.append(self.L("Related lab tests: ", "🧪 آزمایش‌های مرتبط: ") + "، ".join(_names))
            adv = d.get("advice") or []
            if adv:
                lines.append(self.L("Advice:", "توصیه:"))
                for a in adv:
                    lines.append("   • " + str(a))
            if d.get("doctor_when"):
                lines.append("")
                lines.append(self.L("When to see a doctor: ", "⏰ چه زمانی پزشک: ") + str(d["doctor_when"]))
            lines.append("")
            lines.append(self.L("(urgency: ", "(فوریت: ") + u_fa + self.L(" | base prevalence: ", " | شیوع پایه: ") + f"{int(round((d.get('prior') or 0) * 1000) / 10)}" + self.L("%)", "٪)"))
            box.delete("1.0", "end")
            box.insert("1.0", "\n".join(lines))
            box.tag_add("title", "1.0", "1.0 lineend")
            box.tag_config("title", foreground=u_col, font=pick_font(12, True))

        urg_en = {"emergency": "emergency", "urgent": "urgent", "routine": "routine"}
        from i18n import get_lang as _gl_c
        _fa_c = _gl_c() == "fa"
        rows = []
        for d in dis:
            u_fa, u_col = urg_fa.get(d.get("urgency"), ("", C["tx"]))
            u_lbl = u_fa if _fa_c else urg_en.get(d.get("urgency"), str(d.get("urgency", "")))
            n_sym = len(d.get("symptoms") or [])
            row = tk.Frame(inner, bg=C["panel2"])
            b = tk.Button(row, text=str(d.get('name','')) + "   [" + u_lbl + "]", command=lambda dd=d: show_detail(dd),
                          anchor="e", bg="#0d1930", fg=u_col, relief="flat", font=pick_font(10, True),
                          activebackground="#101c36", activeforeground=C["cy"], cursor="hand2")
            b.pack(side="right", fill="x", expand=True)
            tk.Label(row, text=self.L(f"{n_sym} symptoms", f"{n_sym} علامت"), bg=C["panel2"],
                     fg=C["dim"], font=pick_font(8), anchor="e").pack(side="right", padx=(0, 8))
            row.pack(fill="x", padx=10, pady=1)
            rows.append((row, (str(d.get("name", "")) + " " + d.get("fa", "") + " " + d.get("en", "") + " " + d.get("id", "")).lower()))

        def do_filter(*_):
            q = sv.get().strip().lower()
            for row, txt in rows:
                row.pack() if q in txt else row.pack_forget()
            schedule_catalog()
        # ----- full ICD-10 catalog search (300ms after typing stops)
        cat_rows: list[tk.Widget] = []
        _deb = {"job": None}
        def show_bank_detail(name, defn="", code="", syms=None, drugs=None):
            _NR2 = self.L("not recorded in the open banks yet", "هنوز در بانک‌های آزاد ثبت نشده")
            box.delete("1.0", "end")
            lines = ["◀ " + name + ("   [" + code + "]" if code else ""), ""]
            lines.append(self.L("Definition: ", "تعریف: ") + (defn[:350] if defn else _NR2))
            lines.append("")
            lines.append(self.L("Symptoms: ", "علائم: ") + (("، ".join(str(s) for s in syms[:12])) if syms else _NR2))
            if drugs:
                lines.append(self.L("Treatments (Wikidata): ", "داروهای درمان (Wikidata): ") + "، ".join(str(d) for d in drugs[:12]))
            box.insert("1.0", "\n".join(lines))
            box.tag_add("title", "1.0", "1.0 lineend")
            box.tag_config("title", foreground="#3bff9e", font=pick_font(12, True))

        from knowledge_browser import ICD_CHAPTERS as _CHS
        _CH_EN = {fa: en for _r, en, fa in _CHS}
        def normalize_name(s):
            from common_2077 import normalize as _nz
            return _nz(s)

        def show_catalog_detail(name, code, chapter, fa_n=""):
            from knowledge_browser import fa_disease_name as _fdn, full_profile, icd_chapter as _ich
            from i18n import get_lang as _gl
            fa_n = fa_n or _fdn(icd=code, en=name)
            box.delete("1.0", "end")
            _fa_cd = _gl() == "fa"
            L = self.L
            # wiki data (real symptoms + drugs)
            from knowledge_browser import get_wiki_disease
            wk = get_wiki_disease(en=name, icd=code) or {}
            syms = [str(s) for s in (wk.get("sym") or [])][:12]
            drugs = [str(d) for d in (wk.get("drug") or [])][:12]
            sep = "، " if _fa_cd else ", "
            head = (fa_n if _fa_cd and fa_n else name)
            if _fa_cd and fa_n and fa_n != name:
                head += "  (" + name + ")"
            lines = ["◀ " + head]
            lines.append(L("ICD-10 code: ", "کد ICD-10: ") + str(code))
            from knowledge_browser import icd_chapter as _ich
            _ch_en = _ich(str(code)).get("en", "") or _CH_EN.get(chapter, chapter)
            lines.append(L("chapter: ", "فصل: ") + str((chapter if _fa_cd else _ch_en)))
            # about — guaranteed via full_profile
            lines.append("")
            lines.append(L("━━━ About ━━━", "━━━ درباره‌ی بیماری ━━━"))
            _p = full_profile(name, code, "", "", syms, drugs)
            lines.append((_p["about_fa"] if _fa_cd else _p["about_en"])[:600])
            if wk.get("sym") or wk.get("drug"):
                if wk.get("en") and normalize_name(wk.get("en","")) != normalize_name(name):
                    lines.append(L("Related entry: ", "ورودی مرتبط: ") + wk.get("en", ""))
            # symptoms — chapter-level fallback guaranteed
            lines.append("")
            lines.append(L("━━━ Symptoms ━━━", "━━━ علائم ━━━"))
            if syms:
                for s in syms:
                    lines.append("  • " + s)
            elif _p["sym_fb_en"]:
                lines.append("  " + (_p["sym_fb_fa"] if _fa_cd else _p["sym_fb_en"]))
            else:
                lines.append("  " + L("check the Symptoms module for a full check", "برای بررسی کامل از ماژول علائم استفاده کن"))
            # drugs
            lines.append("")
            lines.append(L("━━━ Medications ━━━", "━━━ داروهای مرتبط ━━━"))
            if drugs:
                lines.append("  " + sep.join(drugs))
            else:
                lines.append("  " + L("see the Drugs module", "بانک داروها را ببین"))
            # treatment
            lines.append("")
            lines.append(L("━━━ Treatment ━━━", "━━━ درمان ━━━"))
            lines.append("  " + (_p["treat_fa"] if _fa_cd else _p["treat_en"]))
            lines.append("")
            lines.append(L("See a doctor for confirmation. Emergency: 115/112.", "تشخیص نهایی با پزشک است. اورژانس: ۱۱۵/۱۱۲."))
            box.insert("1.0", "\n".join(lines))
            box.tag_add("title", "1.0", "1.0 lineend")
            box.tag_config("title", foreground=C["cy"], font=pick_font(12, True))
        def run_catalog_search():
            _deb["job"] = None
            q = sv.get().strip()
            for r in cat_rows:
                r.destroy()
            cat_rows.clear()
            if len(q) < 2:
                return
            # search EVERY bank: ICD catalog + DOID + Wikidata
            from knowledge_browser import get_catalog_diseases, search_doid, search_wiki_diseases
            res = get_catalog_diseases(q, 15).get("results") or []
            if res:
                sep = tk.Label(inner, text=self.L(f"— ICD-10 catalog ({len(res)}) —",
                                                 f"— نتایج ICD-10 ({len(res)}) —"),
                               bg="#0e1730", fg=C["yl"], font=pick_font(9, True), anchor="e")
                sep.pack(fill="x", padx=10, pady=(8, 2))
                cat_rows.append(sep)
                for c in res:
                    row = tk.Frame(inner, bg=C["panel2"])
                    fa_n = c.get("fa") or ""
                    btn_txt = c["name"] + (("  (" + fa_n + ")") if fa_n else "") + "   [" + c["icd10"] + "]"
                    b = tk.Button(row, text=btn_txt,
                                  command=lambda cc=c: show_catalog_detail(cc["name"], cc["icd10"], cc.get("chapter", ""), cc.get("fa", "")),
                                  anchor="e", bg="#101c36", fg=C["tx"], relief="flat", font=pick_font(9),
                                  activebackground="#101c36", activeforeground=C["cy"], cursor="hand2")
                    b.pack(side="right", fill="x", expand=True)
                    row.pack(fill="x", padx=10, pady=1)
                    cat_rows.append(row)
            doid = search_doid(q, 8)
            if doid:
                sep2 = tk.Label(inner, text=self.L(f"— Disease Ontology ({len(doid)}) —",
                                                  f"— نتایج بانک DOID ({len(doid)}) —"),
                                bg="#0e1730", fg="#3bff9e", font=pick_font(9, True), anchor="e")
                sep2.pack(fill="x", padx=10, pady=(8, 2))
                cat_rows.append(sep2)
                for d in doid:
                    row = tk.Frame(inner, bg=C["panel2"])
                    b = tk.Button(row, text=d["name"] + "   [DOID:" + d["doid"] + "]",
                                  command=lambda dd=d: show_catalog_detail(dd.get("name", ""), dd.get("icd", "") or ("DOID:" + dd.get("doid", "")), "", dd.get("def", "")),
                                  anchor="e", bg="#101c36", fg=C["tx"], relief="flat", font=pick_font(9),
                                  activebackground="#101c36", activeforeground=C["cy"], cursor="hand2")
                    b.pack(side="right", fill="x", expand=True)
                    row.pack(fill="x", padx=10, pady=1)
                    cat_rows.append(row)
            wiki = search_wiki_diseases(q, 40)[:8]
            if wiki:
                sep3 = tk.Label(inner, text=self.L(f"— Wikidata ({len(wiki)}) —",
                                                  f"— نتایج ویکی‌دیتا ({len(wiki)}) —"),
                                bg="#0e1730", fg="#00f0ff", font=pick_font(9, True), anchor="e")
                sep3.pack(fill="x", padx=10, pady=(8, 2))
                cat_rows.append(sep3)
                for e in wiki:
                    row = tk.Frame(inner, bg=C["panel2"])
                    title = e.get("en", "")
                    if e.get("fa"):
                        title += "  (" + e["fa"] + ")"
                    if e.get("icd"):
                        title += "   [" + e["icd"] + "]"
                    b = tk.Button(row, text=title,
                                  command=lambda ee=e: show_catalog_detail(ee.get("en", ""), ee.get("icd", ""), "", ""),
                                  anchor="e", bg="#101c36", fg=C["tx"], relief="flat", font=pick_font(9),
                                  activebackground="#101c36", activeforeground=C["cy"], cursor="hand2")
                    b.pack(side="right", fill="x", expand=True)
                    row.pack(fill="x", padx=10, pady=1)
                    cat_rows.append(row)
            # scroll to results
            w._canvas.yview_moveto(1.0)

        def schedule_catalog(*_):
            if _deb["job"]:
                try:
                    w.after_cancel(_deb["job"])
                except Exception:
                    pass
            _deb["job"] = w.after(300, run_catalog_search)
        sv.trace_add("write", do_filter)
        box.pack(fill="both", expand=True, padx=16, pady=(4, 8))
        if dis:
            show_detail(dis[0])

        # page-by-page browsing over every bank (about 45k diseases)
        browse_state = {"src": "all", "page": 1, "ch": "", "cat": ""}
        engine_row_widgets = list(rows)
        def clear_rows():
            for r_ in cat_rows:
                r_.destroy()
            cat_rows.clear()
            for row_, _t in engine_row_widgets:
                row_.pack_forget()
        def restore_rows():
            clear_rows()
            for row_, _t in engine_row_widgets:
                row_.pack(fill="x", padx=10, pady=1)
        def show_unified_detail(r_):
            from knowledge_browser import full_profile
            from i18n import get_lang as _gl
            _fa = _gl() == "fa"
            box.delete("1.0", "end")
            L = self.L
            sep = "، " if _fa else ", "
            p = full_profile(r_.get("name",""), r_.get("code",""), r_.get("ch",""),
                             r_.get("def",""), r_.get("sym"), r_.get("drug"),
                             r_.get("note_en",""), r_.get("note_fa",""))
            lines = []
            # heading
            head = p["name"] if not _fa else (r_.get("fa") or p["name"])
            if _fa and r_.get("fa") and r_.get("fa") != p["name"]:
                head += "  (" + p["name"] + ")"
            if p["code"]:
                head += "   [" + p["code"] + "]"
            lines.append("◀ " + head)
            # chapter
            if r_.get("ch_fa"):
                lines.append(L("Chapter: ", "فصل: ") + ((r_["ch_fa"] if _fa else (r_.get("ch_en") or r_["ch_fa"]))))
            # about (chapter clinical text if no specific definition)
            lines.append("")
            lines.append(L("━━━ About ━━━", "━━━ درباره‌ی بیماری ━━━"))
            lines.append((p["about_fa"] if _fa else p["about_en"])[:600])
            if (not r_.get("def")) and (p["chapter_en"] or p["chapter_fa"]):
                lines.append((p["chapter_fa"] if _fa else p["chapter_en"])[:400])
            # symptoms
            lines.append("")
            lines.append(L("━━━ Symptoms ━━━", "━━━ علائم ━━━"))
            if p["symptoms"]:
                for s in p["symptoms"]:
                    lines.append("  • " + s)
            elif p["sym_fb_en"]:
                lines.append("  " + (p["sym_fb_fa"] if _fa else p["sym_fb_en"]))
            else:
                lines.append("  " + L("check the Symptoms module", "از ماژول علائم استفاده کن"))
            # drugs
            lines.append("")
            lines.append(L("━━━ Medications ━━━", "━━━ داروهای مرتبط ━━━"))
            if p["drugs"]:
                lines.append("  " + sep.join(p["drugs"]))
            else:
                lines.append("  " + L("see the Drugs module", "بانک داروها را ببین"))
            # treatment
            lines.append("")
            lines.append(L("━━━ Treatment ━━━", "━━━ درمان ━━━"))
            lines.append("  " + (p["treat_fa"] if _fa else p["treat_en"]))
            lines.append("")
            lines.append(L("If symptoms are severe or worsening, see a doctor. In an emergency call 115/112.",
                           "اگر علائم شدید یا پیش‌رونده است به پزشک مراجعه کن. در اورژانس با ۱۱۵/۱۱۲ تماس بگیر."))
            box.insert("1.0", "\n".join(lines))
            box.tag_add("title", "1.0", "1.0 lineend")
            box.tag_config("title", foreground=C["cy"], font=pick_font(12, True))
        def load_browse(delta=0):
            browse_state["page"] = max(1, browse_state["page"] + delta)
            clear_rows()
            from knowledge_browser import browse_diseases, icd_chapter
            r_ = browse_diseases(browse_state["src"], browse_state["page"], 25,
                                 chapter=browse_state.get("ch", ""), cat=browse_state.get("cat", ""))
            r_["rows"] = [dict(x) for x in r_["rows"]]
            browse_state["page"] = r_["page"]
            pg_lbl.config(text=self.L("page ", "صفحه ") + str(r_['page']) + self.L(" of ", " از ") + f"{r_['pages']:,} — {r_['total']:,} " + self.L("diseases", "بیماری"))
            _fa_br = __import__("i18n").get_lang() == "fa"
            for e_ in r_["rows"]:
                row_ = tk.Frame(inner, bg=C["panel2"])
                title = e_["name"] + ((("  (" + e_["fa"] + ")") if e_.get("fa") else "") if _fa_br else "")
                if e_.get("ch_fa"):
                    title += "  — " + (e_["ch_fa"] if _fa_br else (e_.get("ch_en") or e_["ch_fa"]))
                b_ = tk.Button(row_, text=title,
                               command=lambda ee=e_: show_unified_detail(ee),
                               anchor="e", bg="#101c36", fg=C["tx"], relief="flat", font=pick_font(9),
                               activebackground="#101c36", activeforeground=C["cy"], cursor="hand2")
                b_.pack(side="right", fill="x", expand=True)
                if e_.get("code"):
                    tk.Label(row_, text=e_["code"], bg=C["panel2"], fg=C["dim"], font=pick_font(8)).pack(side="right", padx=(0, 8))
                row_.pack(fill="x", padx=10, pady=1)
                cat_rows.append(row_)
        browse_bar = tk.Frame(top, bg=C["panel2"])
        browse_bar.pack(fill="x", padx=16, pady=(2, 6))
        from knowledge_browser import disease_levels
        ch_box = ttk.Combobox(browse_bar, state="readonly", font=pick_font(8), width=30)
        _all_ch = self.L("— all chapters —", "— همه‌ی فصل‌ها —")
        ch_box["values"] = [_all_ch] + [f"{c['fa']} ({c['count']:,})" for c in disease_levels()["chapters"]]
        ch_box.current(0)
        ch_box.pack(fill="x")
        cat_box = ttk.Combobox(browse_bar, state="readonly", font=pick_font(8), width=20)
        cat_box["values"] = [self.L("— all —", "— همه —")]
        cat_box.current(0)
        cat_box.pack(fill="x", pady=(2, 0))
        from knowledge_browser import ICD_CHAPTERS as _CHAPTERS
        _ch_by_idx = {f"{c['fa']} ({c['count']:,})": c["key"] for c in disease_levels()["chapters"]}
        def on_ch_change(_e=None):
            browse_state["ch"] = _ch_by_idx.get(ch_box.get(), "")
            browse_state["cat"] = ""
            from knowledge_browser import disease_levels as _dl
            cats = _dl(browse_state["ch"]).get("cats") or [] if browse_state["ch"] else []
            cat_box["values"] = [self.L("— all —", "— همه —")] + [f"{c['code']} ({c['count']})" for c in cats]
            cat_box.current(0)
            browse_state["page"] = 1
            load_browse(0)
        def on_cat_change(_e=None):
            txt = cat_box.get()
            browse_state["cat"] = txt.split(" ")[0] if txt not in (self.L("— all —", "— همه —"), "") else ""
            browse_state["page"] = 1
            load_browse(0)
        ch_box.bind("<<ComboboxSelected>>", on_ch_change)
        cat_box.bind("<<ComboboxSelected>>", on_cat_change)
        pg_lbl = tk.Label(browse_bar, text="", bg=C["panel2"], fg=C["yl"], font=pick_font(8), anchor="e")
        pg_lbl.pack(fill="x")
        btn_bar = tk.Frame(browse_bar, bg=C["panel2"])
        btn_bar.pack(fill="x")
        for label, s_ in ((self.L("All", "همه"), "all"), ("ICD-10", "icd10"), ("DOID", "doid"), ("Wikidata", "wiki"), (self.L("engine", "موتور"), "engine")):
            tk.Button(btn_bar, text=label,
                      command=lambda ss=s_: (browse_state.update(src=ss, page=1), load_browse(0)),
                      bg="#0d1930", fg=C["tx"], relief="flat", font=pick_font(8)).pack(side="right", padx=2, ipadx=4)
        tk.Button(btn_bar, text="◀", command=lambda: load_browse(-1), bg="#0d1930", fg=C["cy"],
                  relief="flat", font=pick_font(9)).pack(side="left", padx=2)
        tk.Button(btn_bar, text="▶", command=lambda: load_browse(1), bg="#0d1930", fg=C["cy"],
                  relief="flat", font=pick_font(9)).pack(side="left", padx=2)
        tk.Button(btn_bar, text=self.L("normal list", "فهرست عادی"), command=restore_rows, bg="#0d1930", fg=C["gr"],
                  relief="flat", font=pick_font(8)).pack(side="left", padx=6)

    def _panel_drugs(self):
        """
        Drug database: category, class, side effects/interactions, pregnancy and more.
        """
        from knowledge_browser import get_all_drugs
        drugs = get_all_drugs()
        w, top, inner, bottom = self._win_list(self.L("Drugs database", "بانک داروها"))

        sev_fa = {"major": (self.L("severe interaction", "تداخل شدید"), "#ff2a6d"), "moderate": (self.L("moderate interaction", "تداخل متوسط"), "#ffd60a"),
                  "minor": (self.L("mild interaction", "تداخل خفیف"), "#3bff9e")}
        _fda_n = 0
        try:
            from knowledge_browser import get_fda_drug_count
            _fda_n = get_fda_drug_count()
        except Exception:
            _fda_n = 0
        tk.Label(top, text=self.L(f"Curated: {len(drugs)} drugs with interactions  |  Complete FDA bank: {_fda_n:,} — type to search both",
                                  f"داروهای منتخب: {len(drugs)} با تداخل‌ها  |  بانک کامل FDA: {_fda_n:,} دارو — تایپ کن تا هر دو جستجو شوند"),
                 bg=C["panel2"], fg=C["cy"], font=pick_font(11, True), anchor="e", wraplength=640, justify="right").pack(fill="x", padx=16, pady=(10, 2))
        sv = tk.StringVar(value="")
        search = tk.Entry(top, textvariable=sv, bg="#0a1424", fg=C["tx"], relief="flat", font=pick_font(11),
                          justify="right", insertbackground=C["cy"])
        search.pack(fill="x", padx=16, ipady=4, pady=(0, 6))

        box = scrolledtext.ScrolledText(bottom, bg="#070d18", fg=C["tx"], font=pick_font(10),
                                        height=10, relief="flat", wrap="word")

        def show_detail(d):
            def row_fa(label, val):
                return f"  {label}: {val}" if val not in (None, "", []) else ""
            _fa_hdr = __import__("i18n").get_lang() == "fa"
            _nm_hdr = (str(d.get("fa", "")) + " (" + str(d.get("en", "")) + ")") if _fa_hdr else (str(d.get("en", "")) or str(d.get("fa", "")))
            lines = ["◀ " + _nm_hdr]
            cat = (d.get("category") if _fa_hdr else (d.get("category_en") or d.get("category")))
            if cat:
                lines.append(self.L("  category: ", "  دسته: ") + str(cat))
            _en_md = not _fa_hdr
            def _pick_fld(fa_key, en_key):
                if _en_md and en_key:
                    v = d.get(en_key)
                    if v not in (None, "", []):
                        return v
                    return None if d.get(fa_key) in (None, "", []) else _NR_D
                return d.get(fa_key)
            for lbl, key, enk in ((self.L("Class", "کلاس"), "class", "class_en"), (self.L("ATC code", "کد ATC"), "atc", None), (self.L("Half-life", "نیمه‌عمر"), "half_life", None),
                             (self.L("Metabolism", "متابولیسم"), "metabolism", "metabolism_en"), (self.L("Route", "راه مصرف"), "routes", "routes_en"), (self.L("Pregnancy", "بارداری"), "pregnancy", "pregnancy_en")):
                if _en_md and enk:
                    _val = _pick_fld(key, enk)
                    if _val is not None and _val != "":
                        if isinstance(_val, list):
                            _val = ", ".join(str(x) for x in _val)
                        lines.append(f"  {lbl}: {_val}")
                    continue
                r = row_fa(lbl, d.get(key))
                if r:
                    lines.append(r)
            aliases = d.get("aliases_fa") or []
            if aliases:
                _al = d.get("aliases_en") if not _fa_hdr else aliases
                _al = [a for a in (_al or []) if not (_en_md and any("\u0600" <= ch <= "\u06ff" for ch in str(a)))][:6]
                _sep = "، " if _fa_hdr else ", "
                lines.append(self.L("  other names: ", "  نام‌های دیگر: ") + (_al and (_sep.join(str(a) for a in _al)) or _NR_D))
            inter = d.get("interactions") or []
            if inter:
                lines.append("")
                lines.append(self.L("Side effects/interactions (", "عوارض/تداخل‌ها (") + str(len(inter)) + "):")
                for it in inter:
                    s_fa, _col = sev_fa.get(it.get("severity"), (it.get("severity", ""), C["tx"]))
                    lines.append("   • " + self.L("with ", "با «") + str(it.get('other','')) + self.L(" — ", "» — ") + str(s_fa))
                    if it.get("detail"):
                        lines.append("      " + str(it["detail"])[:160])
            notes = d.get("notes")
            if notes:
                lines.append("")
                lines.append(self.L("Note: ", "نکته: ") + str(notes))
            contra = d.get("contra")
            if contra:
                lines.append(self.L("Contraindication: ", "منع مصرف: ") + str(contra))
            box.delete("1.0", "end")
            box.insert("1.0", "\n".join(x for x in lines if x != ""))
            box.tag_add("title", "1.0", "1.0 lineend")
            box.tag_config("title", foreground=C["mg"], font=pick_font(12, True))

        from i18n import get_lang as _gl_d
        _fa_d = _gl_d() == "fa"
        rows = []
        for d in drugs:
            row = tk.Frame(inner, bg=C["panel2"])
            n_inter = len(d.get("interactions") or [])
            _nm_d = (d.get("fa", "") if _fa_d else (d.get("en", "") or d.get("fa", "")))
            _cat_d = (d.get("category", "") if _fa_d else (d.get("category_en", "") or d.get("category", "")))
            b = tk.Button(row, text=_nm_d + (("  —  " + str(_cat_d)) if _cat_d else ""), command=lambda dd=d: show_detail(dd),
                          anchor="e", bg="#0d1930", fg=C["tx"], relief="flat", font=pick_font(10, True),
                          activebackground="#101c36", activeforeground=C["cy"], cursor="hand2")
            b.pack(side="right", fill="x", expand=True)
            if n_inter:
                tk.Label(row, text=str(n_inter), bg=C["panel2"], fg=C["yl"], font=pick_font(8)).pack(side="right", padx=(0, 8))
            row.pack(fill="x", padx=10, pady=1)
            rows.append((row, (" ".join([str(d.get("fa","")), str(d.get("en","")), str(d.get("category","")), str(d.get("id",""))] +
                                        [str(a) for a in (d.get("aliases_fa") or []) + (d.get("aliases_en") or [])])).lower()))

        def do_filter(*_):
            q = sv.get().strip().lower()
            for row, txt in rows:
                row.pack() if q in txt else row.pack_forget()
            schedule_fda()
        # ----- full FDA bank search (300ms after typing stops)
        fda_rows: list[tk.Widget] = []
        _deb = {"job": None}
        def show_fda_detail(d):
            from knowledge_browser import get_drug_label, fa_drug_name
            lines = [f"◀ {d.get('g','')}"]
            _fa = fa_drug_name(d.get("g", ""))
            if _fa:
                lines.append(f"  ({_fa})")
            lb = get_drug_label(d.get("g", "")) or {}
            _NR_F2 = self.L("not in the FDA label set", "در مجموعه لیبل FDA نیست")
            lines.append("  ▸ " + self.L("Indications (FDA label): ", "موارد مصرف (لیبل FDA): ") + (lb["ind"][:280] if lb.get("ind") else _NR_F2))
            if lb.get("box"):
                lines.append("  ▸ " + self.L("Boxed warning: ", "هشدار جعبه: ") + lb["box"][:220])
            lines.append("  ▸ " + self.L("Adverse reactions: ", "عوارض: ") + (lb["adv"][:280] if lb.get("adv") else _NR_F2))
            if lb.get("warn"):
                lines.append("  ▸ " + self.L("Warnings: ", "هشدارها: ") + lb["warn"][:220])
            if d.get("brands"):
                lines.append(self.L("  brand names: ", "  نام‌های تجاری: ") + "، ".join(d["brands"][:6]))
            if d.get("class"):
                lines.append(self.L("  drug class: ", "  کلاس دارویی: ") + "، ".join(d["class"][:4]))
            if d.get("ing"):
                lines.append(self.L("  active ingredient: ", "  ماده‌ی فعال: ") + " + ".join(d["ing"]))
            if d.get("forms"):
                lines.append(self.L("  dosage forms: ", "  فرم دارویی: ") + "، ".join(d["forms"][:5]))
            if d.get("routes"):
                lines.append(self.L("  routes: ", "  راه مصرف: ") + "، ".join(d["routes"][:4]))
            if d.get("mkt"):
                lines.append(self.L("  marketing category: ", "  دسته‌بندی بازاریابی: ") + "، ".join(d["mkt"]))
            lines.append(self.L("  registered FDA products: ", "  تعداد محصولات ثبت‌شده در FDA: ") + str(d.get('n', 0)))
            lines.append("")
            
            box.delete("1.0", "end")
            box.insert("1.0", "\n".join(lines))
            box.tag_add("title", "1.0", "1.0 lineend")
            box.tag_config("title", foreground=C["mg"], font=pick_font(12, True))
        def run_fda_search():
            _deb["job"] = None
            q = sv.get().strip()
            for r in fda_rows:
                r.destroy()
            fda_rows.clear()
            if len(q) < 2 or not _fda_n:
                return
            from knowledge_browser import search_fda_drugs
            res = search_fda_drugs(q, 25)
            if not res:
                return
            sep = tk.Label(inner, text=self.L(f"— FDA database matches ({len(res)}) —",
                                             f"— نتایج بانک کامل FDA ({len(res)}) —"),
                           bg="#0e1730", fg=C["yl"], font=pick_font(9, True), anchor="e")
            sep.pack(fill="x", padx=10, pady=(8, 2))
            fda_rows.append(sep)
            for d in res:
                row = tk.Frame(inner, bg=C["panel2"])
                brand = (d.get("brands") or [""])[0]
                title = f"{d['g']}" + (f"  ({brand})" if brand and brand.lower() != d["g"].lower() else "")
                b = tk.Button(row, text=title, command=lambda dd=d: show_fda_detail(dd),
                              anchor="e", bg="#101c36", fg=C["tx"], relief="flat", font=pick_font(9),
                              activebackground="#101c36", activeforeground=C["cy"], cursor="hand2")
                b.pack(side="right", fill="x", expand=True)
                tk.Label(row, text=str(d.get("n", "")), bg=C["panel2"], fg=C["dim"], font=pick_font(8)).pack(side="right", padx=(0, 8))
                row.pack(fill="x", padx=10, pady=1)
                fda_rows.append(row)
            w._canvas.yview_moveto(1.0)
        def schedule_fda(*_):
            if _deb["job"]:
                try:
                    w.after_cancel(_deb["job"])
                except Exception:
                    pass
            _deb["job"] = w.after(300, run_fda_search)
        sv.trace_add("write", do_filter)
        box.pack(fill="both", expand=True, padx=16, pady=(4, 8))
        if drugs:
            show_detail(drugs[0])

        # page-by-page browsing over the whole FDA bank (19k drugs)
        fb_state = {"page": 1, "cat": ""}
        drug_row_widgets = list(rows)
        fda_row_widgets: list[tk.Widget] = []
        def clear_fda():
            for r_ in fda_row_widgets:
                r_.destroy()
            fda_row_widgets.clear()
            for row_, _t in drug_row_widgets:
                row_.pack_forget()
            for r_ in fda_rows:
                r_.destroy()
            fda_rows.clear()
        def restore_drug_rows():
            clear_fda()
            for row_, _t in drug_row_widgets:
                row_.pack(fill="x", padx=10, pady=1)
        def load_fda_browse(delta=0):
            fb_state["page"] = max(1, fb_state["page"] + delta)
            clear_fda()
            from knowledge_browser import browse_fda_drugs
            r_ = browse_fda_drugs(fb_state["page"], 25, q=sv.get().strip(), cat=fb_state.get("cat", ""))
            fb_state["page"] = r_["page"]
            fpg_lbl.config(text=self.L("page ", "صفحه ") + str(r_['page']) + self.L(" of ", " از ") + f"{r_['pages']:,} — {r_['total']:,} " + self.L("drugs", "دارو"))
            for d_ in r_["rows"]:
                row_ = tk.Frame(inner, bg=C["panel2"])
                brand = (d_.get("brands") or [""])[0]
                title = d_["g"]
                if d_.get("fa"):
                    title += "  (" + d_["fa"] + ")"
                title += (("  " + brand) if brand and brand.lower() != d_["g"].lower() else "")
                if d_.get("cat"):
                    _fa_6 = __import__("i18n").get_lang() == "fa"
                    title += "  — " + (d_["cat"] if _fa_6 else d_.get("cat_en", d_["cat"]))
                b_ = tk.Button(row_, text=title,
                               command=lambda dd=d_: show_fda_detail(dd),
                               anchor="e", bg="#101c36", fg=C["tx"], relief="flat", font=pick_font(9),
                               activebackground="#101c36", activeforeground=C["cy"], cursor="hand2")
                b_.pack(side="right", fill="x", expand=True)
                row_.pack(fill="x", padx=10, pady=1)
                fda_row_widgets.append(row_)
        fb_bar = tk.Frame(top, bg=C["panel2"])
        fb_bar.pack(fill="x", padx=16, pady=(2, 6))
        from knowledge_browser import drug_levels
        dcat_box = ttk.Combobox(fb_bar, state="readonly", font=pick_font(8), width=30)
        _all_dc = self.L("— all categories —", "— همه‌ی دسته‌ها —")
        _dc_by_idx = {f"{c['fa']} ({c['count']:,})": c["fa"] for c in drug_levels()}
        dcat_box["values"] = [_all_dc] + list(_dc_by_idx.keys())
        dcat_box.current(0)
        dcat_box.pack(fill="x")
        def on_dcat(_e=None):
            fb_state["cat"] = _dc_by_idx.get(dcat_box.get(), "")
            fb_state["page"] = 1
            load_fda_browse(0)
        dcat_box.bind("<<ComboboxSelected>>", on_dcat)
        fpg_lbl = tk.Label(fb_bar, text="", bg=C["panel2"], fg=C["yl"], font=pick_font(8), anchor="e")
        fpg_lbl.pack(fill="x")
        fbtn = tk.Frame(fb_bar, bg=C["panel2"])
        fbtn.pack(fill="x")
        tk.Button(fbtn, text=self.L("Browse FDA bank", "مرور بانک FDA"), command=lambda: load_fda_browse(0), bg="#0d1930",
                  fg=C["yl"], relief="flat", font=pick_font(8)).pack(side="right", padx=2, ipadx=6)
        tk.Button(fbtn, text="◀", command=lambda: load_fda_browse(-1), bg="#0d1930", fg=C["cy"],
                  relief="flat", font=pick_font(9)).pack(side="left", padx=2)
        tk.Button(fbtn, text="▶", command=lambda: load_fda_browse(1), bg="#0d1930", fg=C["cy"],
                  relief="flat", font=pick_font(9)).pack(side="left", padx=2)
        tk.Button(fbtn, text=self.L("normal list", "فهرست عادی"), command=restore_drug_rows, bg="#0d1930", fg=C["gr"],
                  relief="flat", font=pick_font(8)).pack(side="left", padx=6)

    def _panel_research(self):
        """
        Research: live PubMed, clinical trials and FAERS side-effect search.
        """
        w, top, inner, bottom = self._win_list(self.L("Research & articles (live)", "پژوهش و مقالات (آنلاین)"))
        import requests as _rq
        UA = {"User-Agent": "NexusMed2077/2.0 (github.com/capZX545)"}

        tk.Label(top, text=self.L("Requires internet — searches PubMed, ClinicalTrials.gov and FDA FAERS live",
                                  "نیازمند اینترنت — جستجوی زنده در PubMed، ClinicalTrials.gov و بانک FAERS"),
                 bg=C["panel2"], fg=C["dim"], font=pick_font(8), anchor="e", wraplength=640, justify="right").pack(fill="x", padx=16, pady=(8, 4))

        def mk_section(title_en, title_fa, placeholder_en, placeholder_fa, btn_en, btn_fa):
            fr = tk.Frame(inner, bg=C["panel2"])
            tk.Label(fr, text=title_fa if not title_en else title_fa, bg=C["panel2"], fg=C["cy"],
                     font=pick_font(11, True), anchor="e").pack(fill="x", padx=10, pady=(10, 2))
            bar = tk.Frame(fr, bg=C["panel2"])
            bar.pack(fill="x", padx=10)
            e = tk.Entry(bar, bg="#0a1424", fg=C["tx"], relief="flat", font=pick_font(11),
                         justify="right", insertbackground=C["cy"])
            e.pack(side="right", fill="both", expand=True, ipady=4)
            lbl = tk.Label(fr, text="", bg=C["panel2"], fg=C["dim"], font=pick_font(9), anchor="e", justify="right", wraplength=620)
            lbl.pack(fill="x", padx=10, pady=(2, 8))
            fr.pack(fill="x")
            return fr, e, lbl

        fr1, e1, l1 = mk_section("", self.L("PubMed literature search (40M+)", "📄 جستجوی مقالات PubMed (۴۰ میلیون+ منبع)"), "", self.L("e.g. ibuprofen migraine", "مثلاً: ibuprofen migraine"), "", "")
        fr2, e2, l2 = mk_section("", self.L("Clinical trials (ClinicalTrials.gov)", "🧪 کارآزمایی‌های بالینی (ClinicalTrials.gov)"), "", self.L("e.g. diabetes", "مثلاً: diabetes"), "", "")
        fr3, e3, l3 = mk_section("", self.L("Reported drug side effects (FAERS/FDA)", "⚠️ عوارض گزارش‌شده‌ی دارو (FAERS/FDA)"), "", self.L("drug name, e.g. metformin", "نام دارو مثل: metformin"), "", "")
        fr4, e4, l4 = mk_section("", self.L("Standard drug identity (RxNorm — NIH)", "💊 شناسه‌ی استاندارد دارو (RxNorm — NIH)"), "", self.L("drug name, e.g. ibuprofen", "نام دارو مثل: ibuprofen"), "", "")

        def fetch(url):
            r = _rq.get(url, timeout=18, headers=UA)
            r.raise_for_status()
            return r.json()

        def run_async(job):
            threading.Thread(target=job, daemon=True).start()

        def do_pubmed(_e=None):
            q = e1.get().strip()   # read widgets on the main thread only
            self._ui(lambda: l1.config(text=self.L("searching…", "در حال جستجو…"), fg=C["yl"]))
            def work():
                import urllib.parse as up
                try:
                    es = fetch("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax=8&term=" + up.quote(q))
                    ids = es.get("esearchresult", {}).get("idlist", [])
                    su = fetch("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id=" + ",".join(ids)) if ids else {}
                    lines = ["~" + str(es.get("esearchresult", {}).get("count", "0")) + self.L(" results:", " نتیجه:")]
                    for pid in ids:
                        it = su.get("result", {}).get(pid, {})
                        lines.append("• " + str(it.get("title", "")))
                        lines.append("   " + str(it.get("source", "")) + " · " + str(it.get("pubdate", "")) + " — pubmed.ncbi.nlm.nih.gov/" + pid + "/")
                    out = "\n".join(lines) if ids else self.L("Nothing found.", "چیزی پیدا نشد.")
                except Exception as ex:
                    out = self.L("Error reaching PubMed: ", "خطا در اتصال به PubMed: ") + str(ex)[:120]
                self._ui(lambda: l1.winfo_exists() and l1.config(text=out, fg=C["tx"]))
            if q:
                run_async(work)

        def do_trials(_e=None):
            q = e2.get().strip()
            self._ui(lambda: l2.config(text=self.L("searching…", "در حال جستجو…"), fg=C["yl"]))
            def work():
                import urllib.parse as up
                try:
                    d = fetch("https://clinicaltrials.gov/api/v2/studies?query.term=" + up.quote(q) + "&pageSize=8&countTotal=true")
                    lines = ["~" + str(d.get("totalCount", 0)) + self.L(" trials:", " کارآزمایی:")]
                    for s in d.get("studies", []):
                        p = s.get("protocolSection", {})
                        im = p.get("identificationModule", {})
                        lines.append("• " + str(im.get("briefTitle", "")))
                        lines.append("   " + str(im.get("nctId", "")) + " · " + str(p.get("statusModule", {}).get("overallStatus", "")) + " · " + str((p.get("designModule", {}).get("phases") or ["—"])[0]))
                    out = "\n".join(lines) if d.get("studies") else self.L("Nothing found.", "چیزی پیدا نشد.")
                except Exception as ex:
                    out = self.L("Error reaching ClinicalTrials.gov: ", "خطا در اتصال به ClinicalTrials.gov: ") + str(ex)[:120]
                self._ui(lambda: l2.winfo_exists() and l2.config(text=out, fg=C["tx"]))
            if q:
                run_async(work)

        def do_faers(_e=None):
            q = e3.get().strip()
            self._ui(lambda: l3.config(text=self.L("checking…", "در حال بررسی…"), fg=C["yl"]))
            def work():
                import urllib.parse as up
                try:
                    rx = up.quote('patient.drug.medicinalproduct:"' + q + '"')
                    cnt = fetch("https://api.fda.gov/drug/event.json?search=" + rx + "&count=patient.reaction.reactionmeddrapt.exact&limit=12")
                    rs = cnt.get("results", [])
                    lines = ["≥" + str(sum(r.get("count", 0) for r in rs)) + self.L(" reports — most frequent reactions:", " گزارش — پرتکرارترین عوارض:")]
                    for r in rs:
                        lines.append("• " + str(r.get("term", "")).lower() + ": " + str(r.get("count", 0)))
                    out = "\n".join(lines) if rs else self.L("No reports found — try the exact english drug name.", "گزارشی پیدا نشد — نام دقیق انگلیسی دارو را امتحان کن.")
                    out += self.L("\n(reports do not prove causation — consult your doctor.)", "\n(گزارش‌ها علت-معلولی را ثابت نمی‌کنند — با پزشک مشورت کن.)")
                except Exception as ex:
                    out = self.L("Error reaching openFDA: ", "خطا در اتصال به openFDA: ") + str(ex)[:120]
                self._ui(lambda: l3.winfo_exists() and l3.config(text=out, fg=C["tx"]))
            if q:
                run_async(work)

        def do_rxnorm(_e=None):
            q = e4.get().strip()
            self._ui(lambda: l4.config(text=self.L("searching…", "در حال جستجو…"), fg=C["yl"]))
            def work():
                import urllib.parse as up
                try:
                    qq = up.quote(q)
                    rid = fetch("https://rxnav.nlm.nih.gov/REST/rxcui.json?name=" + qq)
                    rxcui = ((rid.get("idGroup", {}).get("rxnormId") or [""])[0])
                    lines = ["RxCUI: " + (rxcui or self.L("not found", "پیدا نشد"))]
                    if rxcui:
                        d = fetch("https://rxnav.nlm.nih.gov/REST/drugs.json?name=" + qq)
                        n = 0
                        for g in d.get("drugGroup", {}).get("conceptGroup", []):
                            for c in (g.get("conceptProperties") or [])[:3]:
                                lines.append("• [" + str(c.get("tty", "")) + "] " + str(c.get("name", "")) + "  (" + str(c.get("rxcui", "")) + ")")
                                n += 1
                                if n >= 10:
                                    break
                            if n >= 10:
                                break
                    out = "\n".join(lines)
                except Exception as ex:
                    out = self.L("Error reaching RxNav: ", "خطا در اتصال به RxNav: ") + str(ex)[:120]
                self._ui(lambda: l4.winfo_exists() and l4.config(text=out, fg=C["tx"]))
            if q:
                run_async(work)

        for ent, fn in ((e1, do_pubmed), (e2, do_trials), (e3, do_faers), (e4, do_rxnorm)):
            ent.bind("<Return>", fn)
            bar = ent.master
            tk.Button(bar, text=self.L("Search", "جستجو"), command=fn, bg="#0077b6", fg="#021018",
                      font=pick_font(10, True), relief="flat").pack(side="left", padx=(6, 0), ipadx=10)

    def _panel_lab(self):
        """Laboratory: full test catalog + value interpretation."""
        import lab_full
        w, top, inner, bottom = self._win_list(self.L("Laboratory — tests & interpretation", "آزمایشگاه — آزمون‌ها و تفسیر"))

        tk.Label(top, text=self.L(f"{len(lab_full.TESTS)} tests — pick one, enter the value, get an interpretation. "
                                  f"General adult ranges; your own lab sheet always wins.",
                                  f"{len(lab_full.TESTS)} آزمون — انتخاب کن، مقدار را وارد کن و تفسیر بگیر. "
                                  f"بازه‌ها عمومی است و برگه‌ی خودت ملاک است."),
                 bg=C["panel2"], fg=C["cy"], font=pick_font(9), anchor="e", wraplength=640, justify="right").pack(fill="x", padx=16, pady=(8, 4))

        from i18n import get_lang
        fa_mode = get_lang() == "fa"
        name_of = lambda t: t["fa"] if fa_mode else t["en"]

        # فیلتر و جستجو
        flt_bar = tk.Frame(top, bg=C["panel2"])
        flt_bar.pack(fill="x", padx=16, pady=(0, 4))
        cat_box = ttk.Combobox(flt_bar, state="readonly", font=pick_font(9), width=28)
        _all_c = self.L("— all categories —", self.L("— all categories —", "— همه‌ی دسته‌ها —"))
        _cats = lab_full.LAB_CATEGORIES
        cat_box["values"] = [_all_c] + [(_cats[c][1] if fa_mode else _cats[c][0]) for c in _cats]
        cat_box.current(0)
        cat_box.pack(side="right", fill="x", expand=True)
        sv2 = tk.StringVar(value="")
        q2 = tk.Entry(flt_bar, textvariable=sv2, bg="#0a1424", fg=C["tx"], relief="flat",
                      font=pick_font(10), justify="right", insertbackground=C["cy"])
        q2.pack(side="right", fill="x", expand=True, ipady=3, padx=(6, 0))

        # لیست
        rows_lab = []
        def draw():
            for r_ in rows_lab:
                r_.destroy()
            rows_lab.clear()
            q = sv2.get().strip().lower()
            ci = cat_box.current() - 1
            ckey = list(_cats)[ci] if ci >= 0 else ""
            n = 0
            for k, t in lab_full.TESTS.items():
                hay = (t["en"] + " " + t["fa"] + " " + k).lower()
                if q and q not in hay:
                    continue
                if ckey and t["cat"] != ckey:
                    continue
                rng = self.L("qualitative", "کیفی") if t["qual"] else f"{t['lo']} – {t['hi']}"
                b = tk.Button(inner, text=f"{name_of(t)}   [{rng} {'' if t['qual'] else t['unit']}]",
                              command=lambda kk=k: pick(kk), anchor="e", bg="#101c36", fg=C["tx"],
                              relief="flat", font=pick_font(9), activebackground="#101c36",
                              activeforeground=C["cy"], cursor="hand2")
                b.pack(fill="x", padx=10, pady=1)
                rows_lab.append(b)
                n += 1
                if n >= 200:
                    break
        sv2.trace_add("write", lambda *a: draw())
        cat_box.bind("<<ComboboxSelected>>", lambda e: draw())

        # فرم تفسیر در پایین
        form = tk.Frame(bottom, bg=C["panel2"])
        form.pack(fill="x", pady=(6, 0))
        sel_box = ttk.Combobox(form, state="readonly", font=pick_font(9), width=34)
        sel_box["values"] = [f"{name_of(t)}  ({k})" for k, t in lab_full.TESTS.items()]
        sel_box.current(0)
        sel_box.pack(side="right", fill="x", expand=True, ipady=2)
        val_e = tk.Entry(form, bg="#0a1424", fg=C["tx"], relief="flat", font=pick_font(10),
                         justify="center", width=10, insertbackground=C["cy"])
        val_e.pack(side="right", padx=6, ipady=3)
        res_lbl = tk.Label(bottom, text="", bg=C["panel2"], fg=C["tx"], font=pick_font(10),
                           anchor="e", justify="right", wraplength=640)
        res_lbl.pack(fill="x", padx=16, pady=(4, 8))

        def pick(k):
            for i, item in enumerate(sel_box["values"]):
                if item.endswith(f"({k})"):
                    sel_box.current(i)
                    break
            val_e.focus_set()

        def interpret(_e=None):
            item = sel_box.get()
            k = item.rsplit("(", 1)[-1].rstrip(")")
            v = val_e.get().strip()
            if not v:
                return
            r = lab_full.evaluate(k, v, fa_mode)
            if not r.get("ok"):
                res_lbl.config(text=self.L(r.get("message_en", ""), r.get("message_fa", "")), fg=C["yl"])
                return
            if r.get("qual"):
                col = C["gr"] if r["status"] == "normal" else C["mg"]
                txt = f"{r['test']}: {'مثبت' if fa_mode else 'positive' if r['status']=='positive' else ('منفی' if fa_mode else 'negative')}\n{r['note']}"
            else:
                st_fa = {"normal": self.L("normal", "نرمال"), "low": self.L("below range", "پایین‌تر از حد"), "high": self.L("above range", "بالاتر از حد"), "very_low": self.L("far below range", "خیلی پایین"),
                         "very_high": self.L("far above range", "خیلی بالا"), "crit_low": self.L("CRITICAL — low", "⚠️ خطرناک — پایین"), "crit_high": self.L("CRITICAL — high", "⚠️ خطرناک — بالا")}
                st_en = {"normal": "normal", "low": "below range", "high": "above range", "very_low": "far below",
                         "very_high": "far above", "crit_low": "CRITICAL LOW", "crit_high": "CRITICAL HIGH"}
                st = (st_fa if fa_mode else st_en).get(r["status"], r["status"])
                col = C["gr"] if r["status"] == "normal" else (C["mg"] if r["status"].startswith("crit") else C["yl"])
                dev = ("  (" + str(r['deviation_pct']) + self.L("%)", "٪)")) if r.get("deviation_pct") else ""
                txt = f"{r['test']}: {r['value']} {r.get('unit','')}  →  {st}{dev}\n"
                txt += (self.L("reference: ", "بازه‌ی مرجع: ") + r["range"] + "\n")
                if r.get("note"):
                    txt += r["note"] + "\n"
                txt += self.L("(general info — a doctor makes the final call)", "(اطلاعات عمومی — تشخیص نهایی با پزشک)")
            res_lbl.config(text=txt, fg=col)

        tk.Button(form, text=self.L("Interpret", "تفسیر"), command=interpret, bg="#0077b6",
                  fg="#021018", font=pick_font(10, True), relief="flat").pack(side="right", padx=6, ipadx=10)
        val_e.bind("<Return>", interpret)
        draw()

    def _panel_tools(self):
        """Health tools: unit converter, dose calc, pregnancy, multi-drug, due date, diary, growth, reminders, chat search, backup."""
        import health_tools as ht
        w, top, inner, bottom = self._win_list(self.L("Health tools — 10 practical tools", "ابزار سلامت — ۱۰ ابزار کاربردی"))
        _L = self.L
        tk.Label(top, text=_L("All offline — data stays on your machine", "همه آفلاین — اطلاعات فقط روی سیستم خودت می‌ماند"),
                 bg=C["panel2"], fg=C["dim"], font=pick_font(8), anchor="e").pack(fill="x", padx=16, pady=(8, 4))

        box = scrolledtext.ScrolledText(bottom, bg="#070d18", fg=C["tx"], font=pick_font(10), height=10, relief="flat", wrap="word")
        box.pack(fill="both", expand=True, padx=16, pady=(4, 8))

        def out(txt, color=C["tx"]):
            box.delete("1.0", "end")
            box.insert("1.0", txt)
            box.tag_add("t", "1.0", "1.0 lineend")
            box.tag_config("t", foreground=color, font=pick_font(11, True))

        # ---------- ۱) تبدیل واحد ----------
        f1 = tk.Frame(inner, bg=C["panel2"]); f1.pack(fill="x", padx=10, pady=2)
        tk.Label(f1, text="🔄 " + _L("Unit converter", "تبدیل واحد آزمایش"), bg=C["panel2"], fg=C["cy"],
                 font=pick_font(10, True), anchor="e").pack(fill="x")
        bar1 = tk.Frame(f1, bg=C["panel2"]); bar1.pack(fill="x")
        uc_t = ttk.Combobox(bar1, state="readonly", font=pick_font(8), width=18)
        uc_t["values"] = [f"{k} ({v['name_fa']})" for k, v in ht.UNITS.items()]
        uc_t.current(0); uc_t.pack(side="right", padx=2)
        uc_v = tk.Entry(bar1, bg="#0a1424", fg=C["tx"], relief="flat", font=pick_font(10), width=8, justify="center")
        uc_v.pack(side="right", padx=2, ipady=2)
        uc_d = ttk.Combobox(bar1, state="readonly", font=pick_font(8), width=12)
        uc_d["values"] = ["mg/dL → mmol", "mmol → mg/dL"]; uc_d.current(0); uc_d.pack(side="right", padx=2)
        def uc_go():
            key = uc_t.get().split(" (")[0]
            r = ht.convert_unit(key, uc_v.get() or 0, "mgdl" if uc_d.current() == 0 else "mmol")
            if r.get("ok"):
                out(f"{r['input']} = {r['output']}\n{r['ref_fa']}", C["cy"])
            else:
                out(r.get("message_fa", "خطا"), C["mg"])
        tk.Button(bar1, text=_L("Go", "تبدیل"), command=uc_go, bg="#0077b6", fg="#021018",
                  font=pick_font(9, True), relief="flat").pack(side="right", padx=2, ipadx=8)

        # ---------- ۲) دوز بر اساس وزن ----------
        f2 = tk.Frame(inner, bg=C["panel2"]); f2.pack(fill="x", padx=10, pady=2)
        tk.Label(f2, text="⚖️ " + _L("Weight-based dose", "دوز بر اساس وزن (کودک)"), bg=C["panel2"], fg=C["cy"],
                 font=pick_font(10, True), anchor="e").pack(fill="x")
        bar2 = tk.Frame(f2, bg=C["panel2"]); bar2.pack(fill="x")
        dc_t = ttk.Combobox(bar2, state="readonly", font=pick_font(8), width=20)
        dc_t["values"] = [f"{k} ({v['name_fa']})" for k, v in ht.DOSE_TABLE.items()]
        dc_t.current(0); dc_t.pack(side="right", padx=2)
        dc_w = tk.Entry(bar2, bg="#0a1424", fg=C["tx"], relief="flat", font=pick_font(10), width=6, justify="center")
        dc_w.insert(0, "20"); dc_w.pack(side="right", padx=2, ipady=2)
        def dc_go():
            key = dc_t.get().split(" (")[0]
            r = ht.calculate_dose(key, dc_w.get() or 0)
            if r.get("ok"):
                if r.get("note"):
                    out(f"{r['drug_fa']}: {r['note']}", C["yl"])
                    return
                lines = [f"{r['drug_fa']} — {r['single_dose_mg']} mg هر {r['interval_h']} ساعت",
                         f"({r['doses_per_day']}× در روز | سقف: {r['max_daily_mg']} mg/day)"]
                for fm in r.get("forms", [])[:3]:
                    lines.append(f"  • {fm}")
                lines.append(r["warning_fa"])
                out("\n".join(lines), C["gr"])
            else:
                out(r.get("message_fa", "خطا"), C["mg"])
        tk.Button(bar2, text=_L("Calc", "محاسبه"), command=dc_go, bg="#0077b6", fg="#021018",
                  font=pick_font(9, True), relief="flat").pack(side="right", padx=2, ipadx=8)

        # ---------- ۳) بارداری ----------
        f3 = tk.Frame(inner, bg=C["panel2"]); f3.pack(fill="x", padx=10, pady=2)
        tk.Label(f3, text="🤰 " + _L("Pregnancy safety (A-X)", "ایمنی بارداری (A-X)"), bg=C["panel2"], fg=C["cy"],
                 font=pick_font(10, True), anchor="e").pack(fill="x")
        bar3 = tk.Frame(f3, bg=C["panel2"]); bar3.pack(fill="x")
        ps_e = tk.Entry(bar3, bg="#0a1424", fg=C["tx"], relief="flat", font=pick_font(10), justify="right")
        ps_e.pack(side="right", fill="x", expand=True, padx=2, ipady=2)
        def ps_go():
            r = ht.check_pregnancy(ps_e.get())
            if r.get("found"):
                col = C["gr"] if r["category"] in "AB" else (C["mg"] if r["category"] == "X" else C["yl"])
                out(f"{r['drug'].upper()} → دسته {r['category']}\n{r['pregnancy_fa']}\n🤱 {r['lactation_fa']}", col)
            else:
                out(r["message_fa"], C["yl"])
        tk.Button(bar3, text=_L("Check", "بررسی"), command=ps_go, bg="#0077b6", fg="#021018",
                  font=pick_font(9, True), relief="flat").pack(side="right", padx=2, ipadx=8)

        # ---------- ۴) چند دارو ----------
        f4 = tk.Frame(inner, bg=C["panel2"]); f4.pack(fill="x", padx=10, pady=2)
        tk.Label(f4, text="💊 " + _L("Multi-drug interaction (3+)", "تداخل چند دارو (۳+)"), bg=C["panel2"], fg=C["cy"],
                 font=pick_font(10, True), anchor="e").pack(fill="x")
        md_e = tk.Entry(f4, bg="#0a1424", fg=C["tx"], relief="flat", font=pick_font(10), justify="right")
        md_e.pack(fill="x", padx=10, ipady=2)
        def md_go():
            drugs = [d.strip() for d in md_e.get().replace("،", ",").split(",") if d.strip()]
            if len(drugs) < 2:
                out("حداقل ۲ دارو با کاما جدا کن", C["yl"]); return
            r = ht.check_multi_drugs(drugs)
            if not r.get("ok"):
                out(r.get("message_fa", "خطا"), C["mg"]); return
            if not r["pairs"]:
                out("✓ تداخل مهمی یافت نشد", C["gr"]); return
            lines = [f"{r['message_fa']}:"]
            for p in r["pairs"]:
                lines.append(f"• {p['a']} + {p['b']} [{p['severity']}]")
                if p.get("detail"):
                    lines.append(f"  {p['detail'][:100]}")
            out("\n".join(lines), C["yl"])
        tk.Button(f4, text=_L("Check all", "بررسی همه"), command=md_go, bg="#0077b6", fg="#021018",
                  font=pick_font(9, True), relief="flat").pack(pady=2, ipadx=10)

        # ---------- ۵) تاریخ زایمان ----------
        f5 = tk.Frame(inner, bg=C["panel2"]); f5.pack(fill="x", padx=10, pady=2)
        tk.Label(f5, text="📅 " + _L("Due date calculator", "محاسبه‌گر تاریخ زایمان"), bg=C["panel2"], fg=C["cy"],
                 font=pick_font(10, True), anchor="e").pack(fill="x")
        bar5 = tk.Frame(f5, bg=C["panel2"]); bar5.pack(fill="x")
        dd_e = tk.Entry(bar5, bg="#0a1424", fg=C["tx"], relief="flat", font=pick_font(10), justify="center")
        dd_e.insert(0, "2026-08-01"); dd_e.pack(side="right", padx=2, ipady=2)
        def dd_go():
            r = ht.due_date(dd_e.get())
            if r.get("ok"):
                out(f"تاریخ زایمان: {r['due_date']}\n{r['message_fa']}", C["cy"])
            else:
                out(r["message_fa"], C["mg"])
        tk.Button(bar5, text=_L("Calc", "محاسبه"), command=dd_go, bg="#0077b6", fg="#021018",
                  font=pick_font(9, True), relief="flat").pack(side="right", padx=2, ipadx=8)

        # ---------- ۶) دفترچه علائم ----------
        f6 = tk.Frame(inner, bg=C["panel2"]); f6.pack(fill="x", padx=10, pady=2)
        tk.Label(f6, text="📔 " + _L("Symptom diary", "دفترچه علائم روزانه"), bg=C["panel2"], fg=C["cy"],
                 font=pick_font(10, True), anchor="e").pack(fill="x")
        bar6 = tk.Frame(f6, bg=C["panel2"]); bar6.pack(fill="x")
        sd_s = tk.Entry(bar6, bg="#0a1424", fg=C["tx"], relief="flat", font=pick_font(10), justify="right")
        sd_s.pack(side="right", fill="x", expand=True, padx=2, ipady=2)
        sd_sev = tk.Entry(bar6, bg="#0a1424", fg=C["tx"], relief="flat", font=pick_font(10), width=4, justify="center")
        sd_sev.insert(0, "5"); sd_sev.pack(side="right", padx=2, ipady=2)
        def sd_go():
            from datetime import date as _d
            ht.diary_add(_d.today().isoformat(), sd_s.get(), int(sd_sev.get() or 5))
            entries = ht.diary_list(10)
            lines = [_L("last entries:", "آخرین ثبت‌ها:")]
            for e in reversed(entries):
                lines.append(f"  {e['date']} — {e['symptom']} [{e['severity']}/10]")
            out("\n".join(lines), C["tx"])
        tk.Button(bar6, text=_L("Add", "ثبت"), command=sd_go, bg="#0077b6", fg="#021018",
                  font=pick_font(9, True), relief="flat").pack(side="right", padx=2, ipadx=8)

        # ---------- ۷) رشد کودک ----------
        f7 = tk.Frame(inner, bg=C["panel2"]); f7.pack(fill="x", padx=10, pady=2)
        tk.Label(f7, text="📏 " + _L("Growth chart (WHO percentiles)", "نمودار رشد (صدک WHO)"), bg=C["panel2"], fg=C["cy"],
                 font=pick_font(10, True), anchor="e").pack(fill="x")
        bar7 = tk.Frame(f7, bg=C["panel2"]); bar7.pack(fill="x")
        gc_age = tk.Entry(bar7, bg="#0a1424", fg=C["tx"], relief="flat", font=pick_font(10), width=5, justify="center")
        gc_age.insert(0, "12"); gc_age.pack(side="right", padx=1, ipady=2)
        gc_sex = ttk.Combobox(bar7, state="readonly", width=3, font=pick_font(8))
        gc_sex["values"] = ["♂", "♀"]; gc_sex.current(0); gc_sex.pack(side="right", padx=1)
        gc_h = tk.Entry(bar7, bg="#0a1424", fg=C["tx"], relief="flat", font=pick_font(10), width=5, justify="center")
        gc_h.insert(0, "76"); gc_h.pack(side="right", padx=1, ipady=2)
        gc_w = tk.Entry(bar7, bg="#0a1424", fg=C["tx"], relief="flat", font=pick_font(10), width=5, justify="center")
        gc_w.insert(0, "9.8"); gc_w.pack(side="right", padx=1, ipady=2)
        def gc_go():
            sex = "m" if gc_sex.current() == 0 else "f"
            r = ht.growth_percentile(int(gc_age.get() or 0), sex, float(gc_h.get() or 0), float(gc_w.get() or 0))
            lines = [_L("Growth percentiles (WHO):", "صدک‌های رشد (WHO):")]
            if "height_label" in r:
                lines.append(f"  {L('Height','قد')}: {r['height']} cm → {r['height_label']}")
            if "weight_label" in r:
                lines.append(f"  {L('Weight','وزن')}: {r['weight']} kg → {r['weight_label']}")
            out("\n".join(lines), C["cy"])
        def L(en, fa): return fa if __import__("i18n").get_lang() == "fa" else en
        tk.Button(bar7, text=_L("Check", "بررسی"), command=gc_go, bg="#0077b6", fg="#021018",
                  font=pick_font(9, True), relief="flat").pack(side="right", padx=2, ipadx=8)

        # ---------- ۸) یادآور دارو ----------
        f8 = tk.Frame(inner, bg=C["panel2"]); f8.pack(fill="x", padx=10, pady=2)
        tk.Label(f8, text="⏰ " + _L("Medication reminders", "یادآور دارو"), bg=C["panel2"], fg=C["cy"],
                 font=pick_font(10, True), anchor="e").pack(fill="x")
        bar8 = tk.Frame(f8, bg=C["panel2"]); bar8.pack(fill="x")
        mr_d = tk.Entry(bar8, bg="#0a1424", fg=C["tx"], relief="flat", font=pick_font(10), justify="right")
        mr_d.pack(side="right", fill="x", expand=True, padx=2, ipady=2)
        mr_t = tk.Entry(bar8, bg="#0a1424", fg=C["tx"], relief="flat", font=pick_font(10), width=12, justify="center")
        mr_t.insert(0, "08:00,20:00"); mr_t.pack(side="right", padx=2, ipady=2)
        def mr_go():
            times = [t.strip() for t in mr_t.get().split(",") if t.strip()]
            ht.reminders_add(mr_d.get(), times)
            rems = ht.reminders_list()
            lines = [_L("Active reminders:", "یادآورهای فعال:")]
            for m in rems:
                lines.append(f"  💊 {m['drug']} — {', '.join(m['times'])}")
            out("\n".join(lines), C["tx"])
        tk.Button(bar8, text=_L("Add", "افزودن"), command=mr_go, bg="#0077b6", fg="#021018",
                  font=pick_font(9, True), relief="flat").pack(side="right", padx=2, ipadx=8)

        # ---------- ۹) جستجوی چت ----------
        f9 = tk.Frame(inner, bg=C["panel2"]); f9.pack(fill="x", padx=10, pady=2)
        tk.Label(f9, text="🔍 " + _L("Search chat history", "جستجو در تاریخچه چت"), bg=C["panel2"], fg=C["cy"],
                 font=pick_font(10, True), anchor="e").pack(fill="x")
        cs_e = tk.Entry(f9, bg="#0a1424", fg=C["tx"], relief="flat", font=pick_font(10), justify="right")
        cs_e.pack(fill="x", padx=10, ipady=2)
        def cs_go():
            hits = ht.search_chat_history(cs_e.get())
            if not hits:
                out(_L("not found", "پیدا نشد"), C["yl"]); return
            lines = [f"{len(hits)} hits:"] if len(hits) > 1 else []
            for h in hits[:10]:
                lines.append(f"[{h['role']}] {h['text'][:120]}")
            out("\n".join(lines), C["tx"])
        tk.Button(f9, text=_L("Search", "جستجو"), command=cs_go, bg="#0077b6", fg="#021018",
                  font=pick_font(9, True), relief="flat").pack(pady=2, ipadx=10)

        # ---------- ۱۰) بکاپ ----------
        f10 = tk.Frame(inner, bg=C["panel2"]); f10.pack(fill="x", padx=10, pady=6)
        tk.Label(f10, text="💾 " + _L("Backup personal data", "بکاپ اطلاعات شخصی"), bg=C["panel2"], fg=C["cy"],
                 font=pick_font(10, True), anchor="e").pack(fill="x")
        def bk_go():
            r = ht.backup_all("backup")
            out(f"✓ {len(r['files'])} files → backup/", C["gr"])
        tk.Button(f10, text=_L("Backup now", "بکاپ بگیر"), command=bk_go, bg="#0d5a4a", fg="#c8ffe9",
                  font=pick_font(9, True), relief="flat").pack(pady=2, ipadx=12)

    def _panel_referral(self):
        from doctor_referral import generate
        from patient_profile import load_profile
        w = self._win(self.L("Referral report for the doctor", "گزارش ارجاع به پزشک"))
        box = self._result_box(w)

        def go():
            dlg = self._engine().dialogue.summary()
            r = generate(load_profile(), None, dlg.get("symptoms_fa"), [], dlg, "")
            box.delete("1.0", "end")
            if r.get("ok"):
                box.insert("1.0", self.L("Report generated: ", "گزارش ساخته شد: ") + r["path"] + self.L("\n(open it in the browser and press Ctrl+P)", "\n(در مرورگر باز کنید و Ctrl+P بزنید)"))
                try:
                    import webbrowser
                    webbrowser.open("file://"+ r["path"])
                except Exception:
                    pass
            else:
                box.insert("1.0", r.get("message_fa", self.L("Error", "خطا")))
        tk.Button(w, text=self.L("Generate report", "تولید گزارش"), command=go, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(pady=8, ipadx=24, ipady=4)

    def _panel_brain(self):
        w = self._win(self.L("Internal brain & learning", "مغز داخلی / یادگیری"))
        box = self._result_box(w)

        def go():
            from auto_learning import recent, stats
            from semantic_rag import status as rag_status
            st = stats()
            lines = [self.L("entries learned from external AI: ", "موارد یادگرفته‌شده از AI خارجی: ") + str(st['entries']) + self.L(" (cap ", " (سقف ") + str(st['max']) + ")",
                     self.L("frequent topics: ", "موضوعات پرتکرار: ") + ("، ".join(st.get("top_topics", [])) or "—"),
                     f"RAG: {rag_status()}", "", self.L("— last 5 entries —", "— ۵ مورد آخر —")]
            for e in recent(5):
                lines.append(f"[{e.get('ts', '')[:16]}] {e.get('topic', '')} ({e.get('provider', '')} / {e.get('model', '')})")
                lines.append(""+ (e.get("ai_summary", "") or "")[:120])
            lines.append(self.L("\nbackground learning happens with every external AI answer;", "\nیادگیری پس‌زمینه همیشه از هر پاسخ AI خارجی انجام می‌شود؛"))
            lines.append(self.L("imitation is tone/structure only, never fake medical content.", "تقلید فقط لحن/ساختار است، نه تولید محتوای پزشکی جعلی."))
            box.delete("1.0", "end")
            box.insert("1.0", "\n".join(lines))
        tk.Button(w, text=self.L("Refresh", "به‌روزرسانی"), command=go, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(pady=8, ipadx=24, ipady=4)
        go()

    def _panel_gpu(self):
        from local_llm import get_config, save_config, test_setup
        w = self._win(self.L("Local AI (Ollama)", "هوش مصنوعی محلی (Ollama)"))
        cfg = get_config()
        ent_on = tk.BooleanVar(value=bool(cfg.get("enabled")))
        ents = self._form(w, [("base_url", self.L("Ollama address", "آدرس Ollama"), cfg.get("base_url", "")),
                              ("model", self.L("Model (default qwen2.5:7b-instruct)", "مدل (پیش‌فرض qwen2.5:7b-instruct)"), cfg.get("model", ""))])
        tk.Checkbutton(w, text=self.L("Use the local model in the answer chain", "استفاده از مدل محلی در زنجیره‌ی پاسخ"), variable=ent_on, bg=C["panel2"],
                       fg=C["tx"], selectcolor="#0a1424", activebackground=C["panel2"],
                       activeforeground=C["cy"], font=pick_font(10), anchor="e").pack(fill="x", padx=16)
        box = self._result_box(w)

        def save():
            save_config({"enabled": ent_on.get(), "base_url": ents["base_url"].get().strip(),
                         "model": ents["model"].get().strip()})
            box.delete("1.0", "end")
            box.insert("1.0", self.L("Saved (local_llm_config.json)", "ذخیره شد (local_llm_config.json)"))
        def test():
            box.delete("1.0", "end")
            box.insert("1.0", self.L("… checking Ollama", "… در حال بررسی Ollama"))
            def work():
                r = test_setup()
                out = r.get("message_fa", "") + self.L("\nmodels: ", "\nمدل‌ها: ") + ("، ".join(r.get("models", [])) or "—")
                def apply():
                    if box.winfo_exists():
                        box.delete("1.0", "end")
                        box.insert("1.0", out)
                self._ui(apply)
            threading.Thread(target=work, daemon=True).start()
        bar = tk.Frame(w, bg=C["panel2"])
        bar.pack(pady=8)
        tk.Button(bar, text=self.L("Save", "ذخیره"), command=save, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(side="right", padx=8)
        tk.Button(bar, text=self.L("Check & test", "بررسی و تست"), command=test, bg="#0d1930", fg=C["tx"],
                  relief="flat", font=pick_font(11)).pack(side="right", padx=8)

    # ------------------------------------------------------ API settings
    def _panel_settings(self):
        from ai_api_manager import get_settings, set_api_key, test_connection
        from free_ai import OPENROUTER_FREE_MODELS
        import webbrowser
        s = get_settings()
        w = self._win(self.L("API settings — applies without restart", "تنظیمات API — بدون نیاز به ری‌استارت"))
        keys = {}
        for provider, title in (("openrouter", self.L("OpenRouter key (recommended — free)", "کلید OpenRouter (پیشنهادی — رایگان)")),
                                ("openai", self.L("OpenAI key", "کلید OpenAI")), ("deepseek", self.L("DeepSeek key", "کلید DeepSeek"))):
            tk.Label(w, text=title, bg=C["panel2"], fg=C["dim"], font=pick_font(10), anchor="e").pack(fill="x", padx=16, pady=(8, 0))
            e = tk.Entry(w, bg="#0a1424", fg=C["tx"], relief="flat", font=pick_font(11),
                         justify="right", show="•", insertbackground=C["cy"])
            e.pack(fill="x", padx=16, ipady=4, side="top")
            keys[provider] = e
        top = tk.Frame(w, bg=C["panel2"])
        top.pack(fill="x", padx=16, pady=4)
        tk.Label(top, text=self.L("OpenRouter model", "مدل OpenRouter"), bg=C["panel2"], fg=C["dim"], font=pick_font(10)).pack(side="right", anchor="e")
        cb = ttk.Combobox(w, values=[m["id"] for m in OPENROUTER_FREE_MODELS], font=pick_font(10))
        cb.set(s.get("openrouter_model", "openai/gpt-oss-120b:free"))
        cb.pack(fill="x", padx=16, ipady=4)
        tk.Label(w, text=self.L("or type a model id manually", "یا نوشتن دستی model id"), bg=C["panel2"], fg=C["dim"], font=pick_font(9)).pack(anchor="e", padx=16)
        manual = tk.Entry(w, bg="#0a1424", fg=C["tx"], relief="flat", font=pick_font(11), justify="right", insertbackground=C["cy"])
        manual.insert(0, s.get("openrouter_model", ""))
        manual.pack(fill="x", padx=16, ipady=4)
        var_reason = tk.BooleanVar(value=bool(s.get("reasoning_enabled")))
        var_brain = tk.BooleanVar(value=bool(s.get("brain_enabled")))
        tk.Checkbutton(w, text=self.L("Reasoning support (off by default; uses more tokens)", "پشتیبانی از reasoning (پیش‌فرض خاموش؛ مصرف توکن بیشتر)"), variable=var_reason,
                       bg=C["panel2"], fg=C["tx"], selectcolor="#0a1424", activebackground=C["panel2"],
                       activeforeground=C["cy"], font=pick_font(10), anchor="e", justify="right").pack(fill="x", padx=16)
        tk.Checkbutton(w, text=self.L("Keep the offline brain on (learning always stays on)", "مغز داخلی روشن باشد (پاسخ آفلاین — یادگیری همیشه فعال است)"), variable=var_brain,
                       bg=C["panel2"], fg=C["tx"], selectcolor="#0a1424", activebackground=C["panel2"],
                       activeforeground=C["cy"], font=pick_font(10), anchor="e", justify="right").pack(fill="x", padx=16)
        box = self._result_box(w)
        box.insert("1.0", self.L("Tip: get a free OpenRouter key at openrouter.ai/keys and paste it here.", "راهنما: کلید رایگان OpenRouter را از openrouter.ai/keys بگیر و همین‌جا وارد کن."))

        def save():
            for provider, e in keys.items():
                if e.get().strip():
                    set_api_key(provider, e.get().strip())
            from ai_api_manager import save_settings
            save_settings({"openrouter_model": manual.get().strip() or cb.get(),
                           "reasoning_enabled": var_reason.get(), "brain_enabled": var_brain.get()})
            box.insert("end", self.L("\n saved (.env) — applies without a restart.", "\n ذخیره شد (فایل .env) — بدون نیاز به ری‌استارت اعمال می‌شود."))
            self._refresh_status()

        def test(provider):
            box.delete("1.0", "end")
            box.insert("1.0", self.L("… testing connection ", "… در حال تست اتصال ") + provider)

            def work():
                r = test_connection(provider)
                out = r.get("message", "")
                def apply():
                    if box.winfo_exists():
                        box.delete("1.0", "end")
                        box.insert("1.0", out)
                self._ui(apply)
            threading.Thread(target=work, daemon=True).start()
        bar = tk.Frame(w, bg=C["panel2"])
        bar.pack(pady=8)
        tk.Button(bar, text=self.L("Save", "ذخیره"), command=save, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(side="right", padx=6)
        tk.Button(bar, text=self.L("Test OpenRouter", "تست OpenRouter"), command=lambda: test("openrouter"), bg="#0d1930",
                  fg=C["tx"], relief="flat", font=pick_font(10)).pack(side="right", padx=4)
        tk.Button(bar, text=self.L("Test OpenAI", "تست OpenAI"), command=lambda: test("openai"), bg="#0d1930",
                  fg=C["tx"], relief="flat", font=pick_font(10)).pack(side="right", padx=4)
        tk.Button(bar, text=self.L("Test DeepSeek", "تست DeepSeek"), command=lambda: test("deepseek"), bg="#0d1930",
                  fg=C["tx"], relief="flat", font=pick_font(10)).pack(side="right", padx=4)
        tk.Button(bar, text=self.L("Get an OpenRouter key", "گرفتن کلید OpenRouter"), command=lambda: webbrowser.open("https://openrouter.ai/keys"),
                  bg="#0d1930", fg=C["cy"], relief="flat", font=pick_font(10)).pack(side="left", padx=4)


def run_app() -> int:
    # VERSION STAMP — این فایل همیشه نوشته میشود تا بدانیم کدام نسخه اجرا شده
    try:
        from common_2077 import DATA_DIR as _DD
        import os as _os
        stamp = _os.path.join(_DD, "VERSION_STAMP.txt")
        if not _os.path.exists(_DD):
            _os.makedirs(_DD, exist_ok=True)
        # fallback: کنار خود برنامه
        if not _os.path.isdir(_DD):
            stamp = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "VERSION_STAMP.txt")
        with open(stamp, "w") as f:
            f.write(f"NexusMed 2077\nVersion: {APP_VERSION}\nStarted: {__import__('datetime').datetime.now().isoformat()}\n")
        print(f"[VERSION] {APP_VERSION} — stamp at {stamp}")
    except Exception as e:
        print(f"[VERSION] stamp error: {e}")

    root = tk.Tk()
    try:
        ttk.Style(root).theme_use("clam")
    except Exception:
        pass
    App(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(run_app())
