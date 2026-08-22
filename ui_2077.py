# -*- coding: utf-8 -*-
"""
ui_2077.py — رابط دسکتاپ NexusMed 2077 (Tkinter) با تم سایبرپانک ۲۰۷۷.
کاملاً فارسی، ساده برای کاربر غیر برنامه‌نویس؛ تنظیمات API از داخل خود برنامه.
"""
from __future__ import annotations

import os
import threading
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, scrolledtext, ttk

from common_2077 import APP_NAME, APP_VERSION, DATA_DIR, MEDICAL_DISCLAIMER

# ---------------------------------------------------------------- تم
C = {
    "bg": "#04060c", "panel": "#0b1220", "panel2": "#0e1730", "bd": "#16213e",
    "cy": "#00f0ff", "mg": "#ff2a6d", "yl": "#ffd60a", "gr": "#3bff9e",
    "tx": "#d7e3ff", "dim": "#6b7fa3",
}


def pick_font(size: int, bold: bool = False):
    fams = set(tkfont.families())
    for fam in ("Vazirmatn", "B Nazanin", "IRANSans", "Segoe UI", "Tahoma"):
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

    # --------------------------------------------------------------- ساخت
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
        # ستون ماژول‌ها قابل‌اسکرول است (مثل overflow-y:auto در نسخه‌ی وب)
        # تا در پنجره‌های کوتاه همه‌ی ماژول‌ها در دسترس بمانند
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
                return  # ماوس روی ستون نیست؛ ویجت دیگری (چت) خودش هندل کند
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
            (("Patient profile", "پروفایل بیمار"), self._panel_profile),
            (("Vitals", "علائم حیاتی"), self._panel_vitals),
            (("Lab analysis", "تحلیل آزمایش"), self._panel_labs),
            (("Prescription scan", "اسکن نسخه"), self._panel_rx),
            (("Drugs & interactions", "دارو و تداخلات"), self._panel_drugs),
            (("Medical image", "تحلیل تصویر پزشکی"), self._panel_image),
            (("Disease likelihood", "ارزیابی احتمال بیماری"), self._panel_assess),
            (("Symptoms (check & analyze)", "علائم (تیک و تحلیل)"), self._panel_symptoms),
            (("Diseases database", "بانک بیماری‌ها"), self._panel_diseases),
            (("Drugs database", "بانک داروها"), self._panel_drugs),
            (("Mental health", "سلامت روان"), self._panel_mental),
            (("Sleep analysis", "تحلیل خواب"), self._panel_sleep),
            (("Checkup calendar", "تقویم چکاپ"), self._panel_checkup),
            (("First aid / CPR", "کمک‌های اولیه / CPR"), self._panel_emergency),
            (("Referral report", "گزارش ارجاع"), self._panel_referral),
            (("Brain & learning", "مغز داخلی / یادگیری"), self._panel_brain),
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

    # -------------------------------------------------------------- موتور
    def _engine(self):
        if self.engine is None:
            from hybrid_engine import HybridEngine
            self.engine = HybridEngine()
        return self.engine

    def _hello(self):
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
        p = filedialog.askopenfilename(title="انتخاب تصویر پزشکی",
                                       filetypes=[("تصاویر", "*.jpg *.jpeg *.png *.webp *.bmp"), ("همه", "*.*")])
        if p:
            self.img_path = p
            self.attach_lbl.config(text=""+ os.path.basename(p))

    def _new_conversation(self):
        """گفتگوی جدید: قبلی را در تاریخچه ذخیره می‌کند."""
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
        """حالت دکتر: سناریوی بیمار → تشخیص افتراقی"""
        from i18n import is_fa
        w = self._win(self.L("Doctor Mode — Clinical Analysis", "حالت دکتر — تحلیل بالینی"))
        tk.Label(w, text=("Describe a patient scenario and get a clinical differential diagnosis." if not is_fa()
                          else "سناریوی بیمار را بنویسید و تشخیص افتراقی بالینی بگیرید."),
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
                # fallback: مغز داخلی مستقیم
                from medical_engine import analyze
                a = analyze(txt.get("1.0", "end").strip())
                lines = ["[offline] تشخیص افتراقی مغز داخلی:"]
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
        self._user(text or "[تصویر پزشکی]")
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
                    meta += "•  یادگیری ثبت شد"
                payload = (res.get("text", ""), tag, meta)
            except Exception as e:
                payload = ("خطا: "+ str(e)[:200], "emg", "")

            def apply():
                # آپدیت UI فقط در ترد اصلی (Tkinter thread-safe نیست)
                self._bot(*payload)
                self.send_btn.config(state="normal", text=self.L("Send", "ارسال"))
                self._refresh_status()
            try:
                self.root.after(0, apply)
            except tk.TclError:
                pass

        threading.Thread(target=work, daemon=True).start()

    # ------------------------------------------------------------- وضعیت
    def _refresh_status(self):
        def work():
            try:
                s = self._engine().status()
                ext = "AI خارجی فعال" if s.get("external_available") else "AI خارجی: کلید ندارد"
                brain = "مغز داخلی روشن" if s.get("settings", {}).get("brain_enabled") else "مغز خاموش (یادگیری پس‌زمینه فعال)"
                learned = s.get("learning", {}).get("entries", 0)
                msg = f"{ext} | {brain} |  حافظه: {learned} مورد"
            except Exception as e:
                msg = "وضعیت: خطا — "+ str(e)[:80]

            def apply():
                try:
                    self.status_lbl.config(text=msg)
                except tk.TclError:
                    pass
            try:
                self.root.after(0, apply)
            except tk.TclError:
                pass
        threading.Thread(target=work, daemon=True).start()


    # ============================================================= پنل‌ها
    def _win(self, title: str):
        w = tk.Toplevel(self.root)
        w.title(title)
        w.configure(bg=C["panel2"])
        # ارتفاع پنجره هرگز از صفحه بزرگ‌تر نشود (لپ‌تاپ‌های کوچک)
        try:
            scr_h = w.winfo_screenheight()
        except Exception:
            scr_h = 800
        win_h = max(400, min(640, scr_h - 140))
        w.geometry(f"660x{win_h}")
        w.minsize(500, min(400, win_h))
        w.transient(self.root)
        w.protocol("WM_DELETE_WINDOW", w.destroy)
        # اسکرول‌بار برای محتوا
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
        # هنگام تغییر اندازه‌ی پنجره هم عرض فرم داخلی با کانواس همگام شود
        def _canvas_resize(event):
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())
        canvas.bind("<Configure>", _canvas_resize)
        self._wheel_bind(w, canvas)
        w._scroll_frame = frame
        w._canvas = canvas
        # فریم قابل‌اسکرول را برمی‌گردانیم تا همه‌ی ویجت‌ها داخل آن قرار بگیرند
        return frame

    def _wheel_bind(self, w, canvas):
        """چرخ ماوس روی «همه‌ی» ویجت‌های پنجره‌ی w → اسکرول کانواس (با محافظ ماوس)."""
        def _in_this_window() -> bool:
            try:
                wid = w.winfo_containing(w.winfo_pointerx(), w.winfo_pointery())
            except tk.TclError:
                return False
            return bool(wid) and (wid is w or bool(wid.winfo_toplevel() is w))
        def _on_mousewheel(event):
            if not _in_this_window():
                return  # بگذار ویجت دیگری (مثل چت اصلی) خودش هندل کند
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
        """پنجره با نوار بالا ثابت + لیست قابل‌اسکرول + نوار پایین ثابت.
        خروجی: (پنجره، فریم بالای ثابت، فریم داخلیِ لیست، فریم پایین ثابت)"""
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
        w = self._win("پروفایل بیمار")
        ents = self._form(w, [("name", "نام", p.get("name", "")), ("age", "سن", p.get("age", "")),
                              ("gender", "جنسیت (مرد/زن)", p.get("gender", "")),
                              ("weight_kg", "وزن (kg)", p.get("weight_kg", "")),
                              ("height_cm", "قد (cm)", p.get("height_cm", "")),
                              ("conditions", "بیماری زمینه‌ای", p.get("conditions", "")),
                              ("allergies", "حساسیت دارویی/غذایی", p.get("allergies", "")),
                              ("medications", "داروهای فعلی", p.get("medications", ""))])

        def save():
            save_profile({k: e.get() for k, e in ents.items()})
            messagebox.showinfo("پروفایل", "ذخیره شد (patient_profile.json)", parent=w)
        tk.Button(w, text="ذخیره", command=save, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(pady=10, ipadx=24, ipady=4)

    def _panel_vitals(self):
        from health_vitals import history, record, trend
        w = self._win("علائم حیاتی")
        ents = self._form(w, [("systolic_bp", "فشار سیستول (مثلاً ۱۲۰)", ""),
                              ("diastolic_bp", "فشار دیاستول (مثلاً ۸۰)", ""),
                              ("weight_kg", "وزن (kg)", ""), ("height_cm", "قد (cm)", ""),
                              ("heart_rate", "نبض", ""), ("temp_c", "دمای بدن", ""), ("glucose", "قند خون", "")])
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
                lines.append(f"فشار: {r['bp']['systolic']}/{r['bp']['diastolic']} — {r['bp']['category_fa']}\n{r['bp']['action_fa']}")
            lines.append("\n— تاریخچه‌ی اخیر —")
            for h in history(6):
                lines.append(str(h))
            lines.append("روند: "+ str(trend()))
            box.delete("1.0", "end")
            box.insert("1.0", "\n\n".join(lines))
        tk.Button(w, text="ثبت و تحلیل", command=go, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(pady=8, ipadx=24, ipady=4)

    def _panel_labs(self):
        from lab_visualizer import analyze_text
        w = self._win("تحلیل آزمایش")
        tk.Label(w, text="هر خط یک آزمایش — مثال: FBS 132 / Hb 10.5 / TSH 6.2 / کلسترول 210",
                 bg=C["panel2"], fg=C["dim"], font=pick_font(10)).pack(padx=16, pady=8)
        txt = scrolledtext.ScrolledText(w, bg="#0a1424", fg=C["tx"], font=pick_font(12), height=6, relief="flat")
        txt.pack(fill="x", padx=16)
        box = self._result_box(w)

        def go():
            r = analyze_text(txt.get("1.0", "end"), save_html=True)
            box.delete("1.0", "end")
            box.insert("1.0", r.get("text_report", "") + "\n\n"+ "\n".join(r.get("summary_fa", [])))
            if r.get("html_path"):
                box.insert("end", "\n\n گزارش تصویری: "+ r["html_path"])
        tk.Button(w, text="تحلیل", command=go, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(pady=8, ipadx=24, ipady=4)

    def _panel_rx(self):
        from prescription_scanner import scan
        w = self._win("اسکن نسخه")
        tk.Label(w, text="متن نسخه/آزمایش را بنویس: BID, TID, PO, PRN, AC, QHS, WBC, FBS, TSH…",
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
                lines.append(f"دارو: {d['fa']} ({d['cat']})")
            for a in r.get("alerts", []):
                lines.append(""+ a)
            lines.append(r.get("disclaimer", ""))
            box.delete("1.0", "end")
            box.insert("1.0", "\n".join(lines) if lines else "چیزی شناسایی نشد.")
        tk.Button(w, text="ترجمه", command=go, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(pady=8, ipadx=24, ipady=4)

    def _panel_drugs(self):
        from drug_interaction import check_interaction, search_drug
        w = self._win("دارو و تداخلات")
        ents = self._form(w, [("a", "داروی اول (نام فارسی یا انگلیسی)", ""), ("b", "داروی دوم (برای بررسی تداخل)", "")])
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
            box.insert("1.0", "\n\n".join(lines) if lines else "نام دارو را وارد کن (مثلاً: وارفارین، ژلوفن، سیر، زنجبیل)")
        tk.Button(w, text="بررسی", command=go, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(pady=8, ipadx=24, ipady=4)

    def _panel_image(self):
        w = self._win("تحلیل تصویر پزشکی")
        tk.Label(w, text="۱) عکس را انتخاب کن ۲) توضیح بنویس (مثلاً: این لک قرمز ۳ روزه خارش دارد) ۳) ارسال",
                 bg=C["panel2"], fg=C["dim"], font=pick_font(10)).pack(padx=16, pady=8)
        path = {"p": ""}

        def pick():
            p = filedialog.askopenfilename(parent=w, filetypes=[("تصاویر", "*.jpg *.jpeg *.png *.webp *.bmp")])
            if p:
                path["p"] = p
                lbl.config(text=""+ os.path.basename(p))
        from i18n import is_fa
        tk.Label(w, text=("Image type (optional - auto-detected too)" if not is_fa() else "نوع تصویر (اختیاری — خودکار هم تشخیص داده می‌شود)"),
                 bg=C["panel2"], fg=C["dim"], font=pick_font(10)).pack(padx=16, pady=(8, 0))
        hint_var = tk.StringVar(value=("Auto-detect" if not is_fa() else "تشخیص خودکار"))
        hint_menu = ttk.Combobox(w, textvariable=hint_var, state="readonly", font=pick_font(10),
                                 values=(["Auto-detect", "Skin / rash", "Wound / burn", "X-ray / CT / MRI", "ECG", "Lab report / prescription", "Eye", "Dental / oral", "Device screen", "Other"] if not is_fa()
                                         else ["تشخیص خودکار", "پوست / جوش", "زخم / سوختگی", "رادیوگرافی / سی‌تی / ام‌آرآی", "نوار قلب", "برگه‌ی آزمایش / نسخه", "چشم", "دندان / دهان", "نمایشگر دستگاه", "سایر"]))
        hint_menu.pack(fill="x", padx=16)
        HINT_MAP = {"Auto-detect": "", "تشخیص خودکار": "", "Skin / rash": "skin", "پوست / جوش": "skin",
                    "Wound / burn": "wound", "زخم / سوختگی": "wound", "X-ray / CT / MRI": "xray",
                    "رادیوگرافی / سی‌تی / ام‌آرآی": "xray", "ECG": "ecg", "نوار قلب": "ecg",
                    "Lab report / prescription": "lab", "برگه‌ی آزمایش / نسخه": "lab",
                    "Eye": "eye", "چشم": "eye", "Dental / oral": "dental", "دندان / دهان": "dental",
                    "Device screen": "device", "نمایشگر دستگاه": "device", "Other": "other", "سایر": "other"}
        tk.Button(w, text=("Choose image" if not is_fa() else "انتخاب عکس"), command=pick, bg="#0d1930", fg=C["tx"], relief="flat",
                  font=pick_font(11)).pack(pady=4)
        lbl = tk.Label(w, text="—", bg=C["panel2"], fg=C["yl"], font=pick_font(10))
        lbl.pack()
        note = tk.Text(w, bg="#0a1424", fg=C["tx"], font=pick_font(12), height=3, relief="flat")
        note.pack(fill="x", padx=16, pady=8)
        box = self._result_box(w)

        def go():
            if not path["p"]:
                messagebox.showwarning("تصویر", "اول عکس را انتخاب کن.", parent=w)
                return
            from image_caption import analyze_image_file
            hint = HINT_MAP.get(hint_var.get(), "")
            r = analyze_image_file(path["p"], note.get("1.0", "end").strip(), hint=hint)
            box.delete("1.0", "end")
            box.insert("1.0", f"[{r.get('source','')}]\n\n"+ r.get("text", ""))
            self._refresh_status()
        tk.Button(w, text="تحلیل", command=go, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(pady=8, ipadx=24, ipady=4)

    def _panel_assess(self):
        from medical_engine import analyze, emergency_response
        from ml_classifier import predict as ml_predict
        w = self._win(self.L("Disease likelihood assessment", "ارزیابی احتمال بیماری‌ها"))
        from i18n import is_fa
        tk.Label(w, text=("Describe symptoms in one or a few lines (onset, severity, duration)" if not is_fa()
                          else "علائم را در یک یا چند خط بنویس (شروع، شدت، مدت)"),
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
            lines.append((("علائم: " if fa_mode else "Symptoms: ") + ("، ".join(a["symptoms"]) if fa_mode else ", ".join(a["symptoms"]))) or "—")
            if a["denied"]:
                lines.append(("ردشده: " if fa_mode else "Ruled out: ") + ("، ".join(a["denied"]) if fa_mode else ", ".join(a["denied"])))
            lines.append("")
            if a["candidates"]:
                lines.append("احتمالات (رتبه‌بندی احتمالی — تشخیص قطعی نیست):" if fa_mode else "Possibilities (probabilistic ranking - NOT a diagnosis):")
                for c in a["candidates"]:
                    lines.append(f"• {c['name']} ~{c['percent']}%  [{c['urgency']}]")
                    lines.append("   " + ("؛ ".join(c.get("advice", [])[:2])))
                    if c.get("doctor_when"):
                        lines.append("   -> " + c["doctor_when"])
            else:
                lines.append("اطلاعات کافی نیست." if fa_mode else "Not enough information yet.")
            # پیشنهاد تریاژ
            if a["candidates"]:
                urg = [c["urgency"] for c in a["candidates"][:3]]
                level = "emergency" if "emergency" in urg else ("urgent" if "urgent" in urg else "routine")
                where = {"emergency": ("Go to the emergency department NOW or call 115/112.", "همین حالا به اورژانس برو یا با ۱۱۵/۱۱۲ تماس بگیر."),
                         "urgent": ("See a clinician today or at the first opportunity.", "امروز یا در اولین فرصت به پزشک مراجعه کن."),
                         "routine": ("A routine visit is enough; monitor your symptoms.", "مراجعه‌ی سرپایی کافی است؛ علائم را زیر نظر بگیر.")}[level]
                lines.append("")
                lines.append(("پیشنهاد تریاژ: " if fa_mode else "Triage suggestion: ") + level)
                lines.append("   " + (where[1] if fa_mode else where[0]))
            try:
                ml = ml_predict(a["detected"], {}, None)
                if ml:
                    lines.append("")
                    lines.append(("سیگنال ML (دیتاست مصنوعی): " if fa_mode else "ML signal (synthetic dataset): ")
                                 + ("، ".join(f"{m['label']} (~{m['percent']}%)" for m in ml[:2])))
            except Exception:
                pass
            box.delete("1.0", "end")
            box.insert("1.0", "\n".join(lines))
        tk.Button(w, text=self.L("Assess", "ارزیابی"), command=go, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(pady=8, ipadx=24, ipady=4)

    def _panel_mental(self):
        from mental_health import GAD7, PHQ9
        w = self._win("سلامت روان — PHQ-9 / GAD-7")
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
                out = [f"نمره: {r['total']} — {r['band_fa']}"]
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
                for val, lbl in enumerate(("هرگز", "چند روز", "نیمی از روزها", "هر روز")):
                    tk.Radiobutton(rowf, text=lbl, variable=v, value=val, bg=C["panel2"], fg=C["dim"],
                                   selectcolor="#0a1424", activebackground=C["panel2"],
                                   activeforeground=C["cy"], font=pick_font(9)).pack(side="right", padx=8)
            tk.Button(frame, text="محاسبه", command=make_submit, bg="#0077b6", fg="#021018",
                      font=pick_font(11, True), relief="flat").pack(pady=10)
        top_bar = tk.Frame(w, bg=C["panel2"])
        top_bar.pack(fill="x", pady=6)
        tk.Radiobutton(top_bar, text="PHQ-9 (افسردگی)", variable=var_type, value="phq9", command=render,
                       bg=C["panel2"], fg=C["tx"], selectcolor="#0a1424", activebackground=C["panel2"],
                       activeforeground=C["cy"], font=pick_font(10)).pack(side="right", padx=14)
        tk.Radiobutton(top_bar, text="GAD-7 (اضطراب)", variable=var_type, value="gad7", command=render,
                       bg=C["panel2"], fg=C["tx"], selectcolor="#0a1424", activebackground=C["panel2"],
                       activeforeground=C["cy"], font=pick_font(10)).pack(side="right", padx=14)
        tk.Label(top_bar, text="تمرین تنفس ۴-۷-۸: دم ۴ ثانیه، نگه‌داشتن ۷، بازدم ۸ — چهار چرخه",
                 bg=C["panel2"], fg=C["dim"], font=pick_font(9)).pack(side="left", padx=10)
        frame.pack(fill="x")
        render()

    def _panel_sleep(self):
        from sleep_analyzer import questions, stopbang
        qs = questions()
        w = self._win("تحلیل خواب — STOP-BANG")
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
            out = [f"{r['total']} از ۸ — {r['risk_fa']}", "موارد مثبت: "+ ("، ".join(r["answers_fa"]) or "—")]
            out += r.get("recommendations_fa", [])
            out.append(r.get("note", ""))
            box.delete("1.0", "end")
            box.insert("1.0", "\n".join(out))
        tk.Button(w, text="محاسبه", command=go, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(pady=8, ipadx=24, ipady=4)

    def _panel_checkup(self):
        from checkup_calendar import recommendations
        w = self._win("تقویم چکاپ و واکسن")
        box = self._result_box(w)

        def go():
            r = recommendations()
            lines = [f"— چکاپ‌ها (سن {r.get('age') or '—'}) —"]
            lines += [f"• {c['title']}: {c['interval_fa']}" for c in r.get("checkups", [])]
            lines.append("\n— واکسن‌ها —")
            lines += [f"• {v['title']}: {v['interval_fa']}" for v in r.get("vaccines", [])]
            lines.append("\n"+ r.get("note_fa", ""))
            box.delete("1.0", "end")
            box.insert("1.0", "\n".join(lines))
        tk.Button(w, text="پیشنهاد بگیر", command=go, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(pady=8, ipadx=24, ipady=4)
        go()

    def _panel_emergency(self):
        from first_aid import TOPICS, cpr_timing
        w = self._win("کمک‌های اولیه / CPR")
        box = self._result_box(w)
        tk.Label(w, text="اورژانس: ایران ۱۱۵ | اروپا/فنلاند ۱۱۲", bg="#2a0d1a", fg="#ff8fab",
                 font=pick_font(12, True), pady=6).pack(fill="x")
        cpr = {"on": False, "job": None}
        timing = cpr_timing()
        cpr_btn = tk.Button(w, text=f"START/STOP مترونوم CPR — {timing['bpm']} BPM", relief="flat",
                            bg="#1c0a14", fg=C["mg"], font=pick_font(13, True))

        def beat():
            try_beep(880, 120)
            cpr["job"] = w.after(int(timing["interval_sec"] * 1000), beat)
        def toggle():
            if cpr["on"]:
                if cpr["job"]:
                    w.after_cancel(cpr["job"])
                cpr["on"] = False
                cpr_btn.config(text=f"START/STOP مترونوم CPR — {timing['bpm']} BPM")
            else:
                cpr["on"] = True
                beat()
        cpr_btn.config(command=toggle)
        cpr_btn.pack(fill="x", padx=16, pady=8, ipady=8)
        bar = tk.Frame(w, bg=C["panel2"])
        bar.pack(fill="x")
        for key, t in TOPICS.items():
            tk.Button(bar, text=t["title"], command=lambda k=key: show(k), bg="#0d1930",
                      fg=C["tx"], relief="flat", font=pick_font(10)).pack(side="right", padx=3, pady=4)

        def show(key):
            from first_aid import get_topic
            tp = get_topic(key) or {}
            lines = [tp.get("title", key), "="* 34, *(tp.get("steps") or []), ""]
            lines += list(tp.get("warnings") or [])
            lines.append(tp.get("disclaimer", ""))
            lines.append(f"\n{tp.get('emergency_line', '')} | عمق {timing['depth_cm']} | نسبت {timing['ratio']}")
            box.delete("1.0", "end")
            box.insert("1.0", "\n".join(lines))
        show("cpr")
        win = w.winfo_toplevel()  # w فقط فریم داخلی است؛ پنجره‌ی واقعی را می‌گیریم
        win.protocol("WM_DELETE_WINDOW", lambda: (toggle() if cpr["on"] else None, win.destroy()))

    # ------------------------------------------------ بانک علائم/بیماری/دارو
    def _panel_symptoms(self):
        """ماژول علائم: همه‌ی علائم با تیک + تحلیل احتمال بیماری‌ها."""
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

        for s in syms:
            v = tk.BooleanVar(value=False)
            vars_[s["id"]] = v
            row = tk.Frame(inner, bg=C["panel2"])
            cb = tk.Checkbutton(row, text=s["fa"], variable=v, command=upd_cnt,
                                bg=C["panel2"], fg=C["tx"], selectcolor="#0a1424",
                                activebackground=C["panel2"], activeforeground=C["cy"],
                                font=pick_font(11), anchor="e", justify="right", cursor="hand2")
            cb.pack(side="right", fill="x", expand=True)
            rel = "، ".join(d["name"] for d in (s.get("related_diseases") or [])[:3]) or "—"
            tk.Label(row, text=rel[:70], bg=C["panel2"], fg=C["dim"], font=pick_font(8),
                     anchor="e", wraplength=300, justify="right").pack(side="right", fill="x", expand=True)
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
            names = [s["fa"] for s in syms if vars_[s["id"]].get()]
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
                pct = f"{pct}٪" if pct not in (None, "") else ""
                urg = {"emergency": "اورژانس", "urgent": "فوری", "routine": "معمولی"}.get(c.get("urgency"), c.get("urgency", ""))
                lines.append(f"• {c.get('fa', c.get('name', ''))}  {pct}  [{urg}]")
                ms = c.get("matched_symptoms") or []
                if ms:
                    lines.append("    علائم منطبق: " + "، ".join(str(m) for m in ms[:6]))
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
        tk.Button(bar2, text=self.L("Analyze", "تحلیل علائم"), command=analyze_now, bg="#0077b6",
                  fg="#021018", font=pick_font(11, True), relief="flat").pack(side="right", padx=16, ipadx=14, ipady=3)
        tk.Button(bar2, text=self.L("Clear", "پاک‌کردن"), command=clear_all, bg="#0d1930",
                  fg=C["tx"], font=pick_font(10), relief="flat").pack(side="right", ipadx=8, ipady=3)
        box.pack(fill="both", expand=True, padx=16, pady=(4, 8))

    def _panel_diseases(self):
        """بانک بیماری‌ها: تعداد، علائم با احتمال، فوریت، توصیه."""
        from knowledge_browser import get_all_diseases
        dis = get_all_diseases()
        w, top, inner, bottom = self._win_list(self.L("Diseases database", "بانک بیماری‌ها"))

        urg_fa = {"emergency": ("اورژانس", "#ff2a6d"), "urgent": ("فوری", "#ffd60a"), "routine": ("معمولی", "#3bff9e")}
        tk.Label(top, text=self.L(f"Diseases in program: {len(dis)} — click one for details",
                                  f"بیماری‌های برنامه: {len(dis)} — برای جزئیات روی هرکدام کلیک کن"),
                 bg=C["panel2"], fg=C["cy"], font=pick_font(11, True), anchor="e").pack(fill="x", padx=16, pady=(10, 2))
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
                lines.append("علائم (با احتمال):")
                for s in sy:
                    lines.append(f"   • {s.get('name','')} — {int(round((s.get('probability') or 0) * 100))}٪")
            lines.append("")
            adv = d.get("advice") or []
            if adv:
                lines.append("توصیه:")
                for a in adv:
                    lines.append("   • " + str(a))
            if d.get("doctor_when"):
                lines.append("")
                lines.append("⏰ چه زمانی پزشک: " + str(d["doctor_when"]))
            lines.append("")
            lines.append(f"(فوریت: {u_fa} | شیوع پایه: {int(round((d.get('prior') or 0) * 1000) / 10)}٪)")
            box.delete("1.0", "end")
            box.insert("1.0", "\n".join(lines))
            box.tag_add("title", "1.0", "1.0 lineend")
            box.tag_config("title", foreground=u_col, font=pick_font(12, True))

        rows = []
        for d in dis:
            u_fa, u_col = urg_fa.get(d.get("urgency"), ("", C["tx"]))
            n_sym = len(d.get("symptoms") or [])
            row = tk.Frame(inner, bg=C["panel2"])
            b = tk.Button(row, text=f"{d.get('name','')}   [{u_fa}]", command=lambda dd=d: show_detail(dd),
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
        sv.trace_add("write", do_filter)
        box.pack(fill="both", expand=True, padx=16, pady=(4, 8))
        if dis:
            show_detail(dis[0])

    def _panel_drugs(self):
        """بانک داروها: خاصیت، دسته، عوارض/تداخل‌ها، بارداری و..."""
        from knowledge_browser import get_all_drugs
        drugs = get_all_drugs()
        w, top, inner, bottom = self._win_list(self.L("Drugs database", "بانک داروها"))

        sev_fa = {"major": ("تداخل شدید", "#ff2a6d"), "moderate": ("تداخل متوسط", "#ffd60a"),
                  "minor": ("تداخل خفیف", "#3bff9e")}
        tk.Label(top, text=self.L(f"Drugs: {len(drugs)} — click for properties & side effects",
                                  f"داروها: {len(drugs)} — برای خاصیت‌ها و تداخل‌ها کلیک کن"),
                 bg=C["panel2"], fg=C["cy"], font=pick_font(11, True), anchor="e").pack(fill="x", padx=16, pady=(10, 2))
        sv = tk.StringVar(value="")
        search = tk.Entry(top, textvariable=sv, bg="#0a1424", fg=C["tx"], relief="flat", font=pick_font(11),
                          justify="right", insertbackground=C["cy"])
        search.pack(fill="x", padx=16, ipady=4, pady=(0, 6))

        box = scrolledtext.ScrolledText(bottom, bg="#070d18", fg=C["tx"], font=pick_font(10),
                                        height=10, relief="flat", wrap="word")

        def show_detail(d):
            def row_fa(label, val):
                return f"  {label}: {val}" if val not in (None, "", []) else ""
            lines = [f"◀ {d.get('fa','')} ({d.get('en','')})"]
            cat = d.get("category")
            if cat:
                lines.append(f"  دسته: {cat}")
            for lbl, key in (("کلاس", "class"), ("کد ATC", "atc"), ("نیمه‌عمر", "half_life"),
                             ("متابولیسم", "metabolism"), ("راه مصرف", "routes"), ("بارداری", "pregnancy")):
                r = row_fa(lbl, d.get(key))
                if r:
                    lines.append(r)
            aliases = d.get("aliases_fa") or []
            if aliases:
                lines.append("  نام‌های دیگر: " + "، ".join(str(a) for a in aliases[:6]))
            inter = d.get("interactions") or []
            if inter:
                lines.append("")
                lines.append(f"عوارض/تداخل‌ها ({len(inter)}):")
                for it in inter:
                    s_fa, _col = sev_fa.get(it.get("severity"), (it.get("severity", ""), C["tx"]))
                    lines.append(f"   • با «{it.get('other','')}» — {s_fa}")
                    if it.get("detail"):
                        lines.append("      " + str(it["detail"])[:160])
            notes = d.get("notes")
            if notes:
                lines.append("")
                lines.append("نکته: " + str(notes))
            contra = d.get("contra")
            if contra:
                lines.append("منع مصرف: " + str(contra))
            box.delete("1.0", "end")
            box.insert("1.0", "\n".join(x for x in lines if x != ""))
            box.tag_add("title", "1.0", "1.0 lineend")
            box.tag_config("title", foreground=C["mg"], font=pick_font(12, True))

        rows = []
        for d in drugs:
            row = tk.Frame(inner, bg=C["panel2"])
            n_inter = len(d.get("interactions") or [])
            b = tk.Button(row, text=f"{d.get('fa','')}  —  {d.get('category','')}", command=lambda dd=d: show_detail(dd),
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
        sv.trace_add("write", do_filter)
        box.pack(fill="both", expand=True, padx=16, pady=(4, 8))
        if drugs:
            show_detail(drugs[0])

    def _panel_referral(self):
        from doctor_referral import generate
        from patient_profile import load_profile
        w = self._win("گزارش ارجاع به پزشک")
        box = self._result_box(w)

        def go():
            dlg = self._engine().dialogue.summary()
            r = generate(load_profile(), None, dlg.get("symptoms_fa"), [], dlg, "")
            box.delete("1.0", "end")
            if r.get("ok"):
                box.insert("1.0", "گزارش ساخته شد: "+ r["path"] + "\n(در مرورگر باز کنید و Ctrl+P بزنید)")
                try:
                    import webbrowser
                    webbrowser.open("file://"+ r["path"])
                except Exception:
                    pass
            else:
                box.insert("1.0", r.get("message_fa", "خطا"))
        tk.Button(w, text="تولید گزارش", command=go, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(pady=8, ipadx=24, ipady=4)

    def _panel_brain(self):
        w = self._win("مغز داخلی / یادگیری")
        box = self._result_box(w)

        def go():
            from auto_learning import recent, stats
            from semantic_rag import status as rag_status
            st = stats()
            lines = [f"موارد یادگرفته‌شده از AI خارجی: {st['entries']} (سقف {st['max']})",
                     f"موضوعات پرتکرار: "+ ("، ".join(st.get("top_topics", [])) or "—"),
                     f"RAG: {rag_status()}", "", "— ۵ مورد آخر —"]
            for e in recent(5):
                lines.append(f"[{e.get('ts', '')[:16]}] {e.get('topic', '')} ({e.get('provider', '')} / {e.get('model', '')})")
                lines.append(""+ (e.get("ai_summary", "") or "")[:120])
            lines.append("\nیادگیری پس‌زمینه همیشه از هر پاسخ AI خارجی انجام می‌شود؛")
            lines.append("تقلید فقط لحن/ساختار است، نه تولید محتوای پزشکی جعلی.")
            box.delete("1.0", "end")
            box.insert("1.0", "\n".join(lines))
        tk.Button(w, text="به‌روزرسانی", command=go, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(pady=8, ipadx=24, ipady=4)
        go()

    def _panel_gpu(self):
        from local_llm import get_config, save_config, test_setup
        w = self._win("هوش مصنوعی محلی (Ollama)")
        cfg = get_config()
        ent_on = tk.BooleanVar(value=bool(cfg.get("enabled")))
        ents = self._form(w, [("base_url", "آدرس Ollama", cfg.get("base_url", "")),
                              ("model", "مدل (پیش‌فرض qwen2.5:7b-instruct)", cfg.get("model", ""))])
        tk.Checkbutton(w, text="استفاده از مدل محلی در زنجیره‌ی پاسخ", variable=ent_on, bg=C["panel2"],
                       fg=C["tx"], selectcolor="#0a1424", activebackground=C["panel2"],
                       activeforeground=C["cy"], font=pick_font(10), anchor="e").pack(fill="x", padx=16)
        box = self._result_box(w)

        def save():
            save_config({"enabled": ent_on.get(), "base_url": ents["base_url"].get().strip(),
                         "model": ents["model"].get().strip()})
            box.delete("1.0", "end")
            box.insert("1.0", "ذخیره شد (local_llm_config.json)")
        def test():
            box.delete("1.0", "end")
            box.insert("1.0", "… در حال بررسی Ollama")
            def work():
                r = test_setup()
                out = r.get("message_fa", "") + "\nمدل‌ها: "+ ("، ".join(r.get("models", [])) or "—")
                def apply():
                    if box.winfo_exists():
                        box.delete("1.0", "end")
                        box.insert("1.0", out)
                try:
                    box.after(0, apply)
                except tk.TclError:
                    pass
            threading.Thread(target=work, daemon=True).start()
        bar = tk.Frame(w, bg=C["panel2"])
        bar.pack(pady=8)
        tk.Button(bar, text="ذخیره", command=save, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(side="right", padx=8)
        tk.Button(bar, text="بررسی و تست", command=test, bg="#0d1930", fg=C["tx"],
                  relief="flat", font=pick_font(11)).pack(side="right", padx=8)

    # ------------------------------------------------------ تنظیمات API
    def _panel_settings(self):
        from ai_api_manager import get_settings, set_api_key, test_connection
        from free_ai import OPENROUTER_FREE_MODELS
        import webbrowser
        s = get_settings()
        w = self._win("تنظیمات API — بدون نیاز به ری‌استارت")
        keys = {}
        for provider, title in (("openrouter", "کلید OpenRouter (پیشنهادی — رایگان)"),
                                ("openai", "کلید OpenAI"), ("deepseek", "کلید DeepSeek")):
            tk.Label(w, text=title, bg=C["panel2"], fg=C["dim"], font=pick_font(10), anchor="e").pack(fill="x", padx=16, pady=(8, 0))
            e = tk.Entry(w, bg="#0a1424", fg=C["tx"], relief="flat", font=pick_font(11),
                         justify="right", show="•", insertbackground=C["cy"])
            e.pack(fill="x", padx=16, ipady=4, side="top")
            keys[provider] = e
        top = tk.Frame(w, bg=C["panel2"])
        top.pack(fill="x", padx=16, pady=4)
        tk.Label(top, text="مدل OpenRouter", bg=C["panel2"], fg=C["dim"], font=pick_font(10)).pack(side="right", anchor="e")
        cb = ttk.Combobox(w, values=[m["id"] for m in OPENROUTER_FREE_MODELS], font=pick_font(10))
        cb.set(s.get("openrouter_model", "openai/gpt-oss-120b:free"))
        cb.pack(fill="x", padx=16, ipady=4)
        tk.Label(w, text="یا نوشتن دستی model id", bg=C["panel2"], fg=C["dim"], font=pick_font(9)).pack(anchor="e", padx=16)
        manual = tk.Entry(w, bg="#0a1424", fg=C["tx"], relief="flat", font=pick_font(11), justify="right", insertbackground=C["cy"])
        manual.insert(0, s.get("openrouter_model", ""))
        manual.pack(fill="x", padx=16, ipady=4)
        var_reason = tk.BooleanVar(value=bool(s.get("reasoning_enabled")))
        var_brain = tk.BooleanVar(value=bool(s.get("brain_enabled")))
        tk.Checkbutton(w, text="پشتیبانی از reasoning (پیش‌فرض خاموش؛ مصرف توکن بیشتر)", variable=var_reason,
                       bg=C["panel2"], fg=C["tx"], selectcolor="#0a1424", activebackground=C["panel2"],
                       activeforeground=C["cy"], font=pick_font(10), anchor="e", justify="right").pack(fill="x", padx=16)
        tk.Checkbutton(w, text="مغز داخلی روشن باشد (پاسخ آفلاین — یادگیری همیشه فعال است)", variable=var_brain,
                       bg=C["panel2"], fg=C["tx"], selectcolor="#0a1424", activebackground=C["panel2"],
                       activeforeground=C["cy"], font=pick_font(10), anchor="e", justify="right").pack(fill="x", padx=16)
        box = self._result_box(w)
        box.insert("1.0", "راهنما: کلید رایگان OpenRouter را از openrouter.ai/keys بگیر و همین‌جا وارد کن.")

        def save():
            for provider, e in keys.items():
                if e.get().strip():
                    set_api_key(provider, e.get().strip())
            from ai_api_manager import save_settings
            save_settings({"openrouter_model": manual.get().strip() or cb.get(),
                           "reasoning_enabled": var_reason.get(), "brain_enabled": var_brain.get()})
            box.insert("end", "\n ذخیره شد (فایل .env) — بدون نیاز به ری‌استارت اعمال می‌شود.")
            self._refresh_status()

        def test(provider):
            box.delete("1.0", "end")
            box.insert("1.0", "… در حال تست اتصال "+ provider)

            def work():
                r = test_connection(provider)
                out = r.get("message", "")
                def apply():
                    if box.winfo_exists():
                        box.delete("1.0", "end")
                        box.insert("1.0", out)
                try:
                    box.after(0, apply)
                except tk.TclError:
                    pass
            threading.Thread(target=work, daemon=True).start()
        bar = tk.Frame(w, bg=C["panel2"])
        bar.pack(pady=8)
        tk.Button(bar, text="ذخیره", command=save, bg="#0077b6", fg="#021018",
                  font=pick_font(11, True), relief="flat").pack(side="right", padx=6)
        tk.Button(bar, text="تست OpenRouter", command=lambda: test("openrouter"), bg="#0d1930",
                  fg=C["tx"], relief="flat", font=pick_font(10)).pack(side="right", padx=4)
        tk.Button(bar, text="تست OpenAI", command=lambda: test("openai"), bg="#0d1930",
                  fg=C["tx"], relief="flat", font=pick_font(10)).pack(side="right", padx=4)
        tk.Button(bar, text="تست DeepSeek", command=lambda: test("deepseek"), bg="#0d1930",
                  fg=C["tx"], relief="flat", font=pick_font(10)).pack(side="right", padx=4)
        tk.Button(bar, text="گرفتن کلید OpenRouter", command=lambda: webbrowser.open("https://openrouter.ai/keys"),
                  bg="#0d1930", fg=C["cy"], relief="flat", font=pick_font(10)).pack(side="left", padx=4)


def run_app() -> int:
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
