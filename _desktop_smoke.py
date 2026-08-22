# -*- coding: utf-8 -*-
"""
Desktop smoke test.
Runs the App and every panel with a fake tkinter display to catch
plain python errors (not graphical ones). Test-only, not shipped in the ZIP.
"""
from __future__ import annotations

import sys
import types


class MockWidget:
    def __init__(self, *a, **kw):
        self.kw = kw
        self.children = []
        self._text = kw.get("text", "")
        self._vars = {}

    def pack(self, *a, **kw): return self
    def grid(self, *a, **kw): return self
    def place(self, *a, **kw): return self
    def config(self, **kw):
        self.kw.update(kw)
        if "text" in kw: self._text = kw["text"]
        return self
    configure = config
    def cget(self, k): return self.kw.get(k, "")
    def bind(self, *a, **kw): return self
    def destroy(self): pass
    def see(self, *a): pass
    def insert(self, *a, **kw): return self
    def delete(self, *a, **kw): return self
    def get(self, *a): return ""
    def set(self, v): self._value = v
    def getvar(self, *a): return getattr(self, "_value", "")
    def winfo_children(self): return self.children
    def winfo_toplevel(self): return self
    def transient(self, *a): return self
    def title(self, *a): return self
    def geometry(self, *a): return self
    def after(self, ms, fn): return self
    def after_cancel(self, *a): return self
    def update_idletasks(self): pass
    def protocol(self, *a): return self
    def mainloop(self): pass
    def minsize(self, *a): return self
    def focus_set(self): return self
    def lift(self): return self
    def selection_get(self): return ""
    def clipboard_clear(self): return self
    def clipboard_append(self, *a): return self
    def pack_propagate(self, *a): return self
    def state(self, *a): return "normal"
    def keys(self): return list(self.kw)
    def tag_configure(self, *a, **kw): return self
    tag_config = tag_configure
    def yview(self, *a, **kw): return self
    def xview(self, *a, **kw): return self
    def index(self, *a): return "1.0"
    def curselection(self): return ()
    def select(self, *a): return self
    def create_window(self, *a, **kw): return self
    def bbox(self, *a): return (0, 0, 100, 100)
    def itemconfig(self, *a, **kw): return self
    def yview_scroll(self, *a): return self
    def yview(self, *a, **kw): return self
    def winfo_width(self): return 600


class MockVar(MockWidget):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._value = kw.get("value", "" if "value" in kw else 0)

    def get(self):
        return self._value


class MockTk(MockWidget):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._after_jobs = []


def _make_mod():
    tk = types.ModuleType("tkinter")
    for name in ("Frame", "Label", "Button", "Entry", "Text", "Canvas", "Toplevel", "Scrollbar", "Menu", "Radiobutton", "Checkbutton", "LabelFrame", "PanedWindow"):
        setattr(tk, name, MockWidget)
    tk.Tk = MockTk
    for vname in ("StringVar", "IntVar", "BooleanVar", "DoubleVar"):
        setattr(tk, vname, MockVar)
    tk.END = "end"
    tk.DISABLED = "disabled"
    tk.NORMAL = "normal"
    tk.RIGHT = "right"
    tk.LEFT = "left"
    tk.TOP = "top"
    tk.BOTTOM = "bottom"
    tk.BOTH = "both"
    tk.X = "x"
    tk.Y = "y"
    tk.W = "w"
    tk.HORIZONTAL = "horizontal"
    tk.VERTICAL = "vertical"
    tk.FLAT = "flat"
    tk.RAISED = "raised"
    tk.WORD = "word"
    tk.INSERT = "insert"
    tk.CURRENT = "current"
    tk.ANCHOR = "anchor"
    tk.YES = "yes"

    def _askopenfilename(**kw):
        return "/tmp/_no_file.png"

    def _messagebox(*a, **kw):
        return "ok"

    filedialog = types.ModuleType("tkinter.filedialog")
    filedialog.askopenfilename = _askopenfilename
    filedialog.asksaveasfilename = _askopenfilename

    messagebox = types.ModuleType("tkinter.messagebox")
    for fn in ("showinfo", "showwarning", "showerror", "askyesno", "askokcancel"):
        setattr(messagebox, fn, lambda *a, **kw: "yes")

    font = types.ModuleType("tkinter.font")
    font.families = lambda *a, **kw: ["Tahoma"]

    ttk_mod = types.ModuleType("tkinter.ttk")
    ttk_mod.Style = lambda *a, **kw: MockWidget()
    for name in ("Combobox", "Button", "Frame", "Label", "Notebook", "Progressbar", "Scrollbar", "Treeview"):
        setattr(ttk_mod, name, MockWidget)
    ttk_mod.Style = lambda root=None: MockWidget()

    scrolled = types.ModuleType("tkinter.scrolledtext")
    scrolled.ScrolledText = MockWidget

    sys.modules["tkinter"] = tk
    sys.modules["tkinter.filedialog"] = filedialog
    sys.modules["tkinter.messagebox"] = messagebox
    sys.modules["tkinter.font"] = font
    sys.modules["tkinter.ttk"] = ttk_mod
    sys.modules["tkinter.scrolledtext"] = scrolled
    return tk


def main():
    _make_mod()
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    failures = []

    import ui_2077
    app = ui_2077.App(ui_2077.tk.Tk())

    panels = [m for m in dir(app) if m.startswith("_panel_")]
    print(f"App constructed OK | panels found: {len(panels)}")
    for name in sorted(panels):
        try:
            getattr(app, name)()
            print("PASS ", name)
        except Exception as e:
            failures.append((name, repr(e)[:150]))
            print("FAIL ", name, "->", repr(e)[:150])

    # chat: sending a text message spawns a thread; test the inner function directly instead
    try:
        app._user("test")
        app._bot("test", "bot", "meta")
        app._reset_dialogue()
        print("PASS  chat helpers")
    except Exception as e:
        failures.append(("chat helpers", repr(e)))
        print("FAIL  chat helpers ->", repr(e)[:120])

    # launch_web only creates a thread, skip it here
    try:
        app.set_lang("fa")
        app.set_lang("en")
        print("PASS  language switch (rebuild)")
    except Exception as e:
        failures.append(("set_lang", repr(e)))
        print("FAIL  set_lang ->", repr(e)[:120])

    print("=" * 50)
    if failures:
        print(f"{len(failures)} FAILURES:")
        for f in failures:
            print("  -", f)
        return 1
    print("DESKTOP SMOKE: ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
