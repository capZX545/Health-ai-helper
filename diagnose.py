# -*- coding: utf-8 -*-
"""
diagnose.py — عیب‌یابی کامل برنامه NexusMed 2077
اجرا: python diagnose.py
"""
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("  NexusMed 2077 - DIAGNOSTIC")
print("=" * 60)
print()

# ۱) نسخه پایتون
py_ver = sys.version_info
print(f"1) Python: {py_ver.major}.{py_ver.minor}.{py_ver.micro}")
if py_ver < (3, 10):
    print("   ERROR: Need Python 3.10+ (get from python.org)")
elif py_ver >= (3, 14):
    print("   WARNING: Python 3.14 is unstable, use 3.12 instead")
else:
    print("   OK")

# ۲) کتابخانه‌ها
print(f"\n2) Libraries:")
missing = []
for lib_name, import_name in [
    ("requests", "requests"),
    ("Pillow", "PIL"),
    ("numpy", "numpy"),
    ("scikit-learn", "sklearn"),
]:
    try:
        __import__(import_name)
        print(f"   {lib_name}: OK")
    except ImportError:
        print(f"   {lib_name}: MISSING")
        missing.append(lib_name)

if missing:
    print(f"\n   FIX: pip install {' '.join(missing)}")
else:
    print("   All OK (but program works without them too)")

# ۳) فایل‌های ضروری
print(f"\n3) Files:")
for f in ("run_web.py", "run_2077.py", "clinic_2077.html", "medical_engine.py", "common_2077.py"):
    if os.path.exists(f):
        print(f"   {f}: OK")
    else:
        print(f"   {f}: MISSING!")

# ۴) تست سرور وب
print(f"\n4) Web Server Test:")
try:
    from run_web import find_free_port
    port = find_free_port(2077, 2087)
    if port:
        print(f"   Port {port} available: OK")
    else:
        print(f"   ERROR: No free port 2077-2087!")
except Exception as e:
    print(f"   ERROR: {e}")

# ۵) تست موتور تشخیص
print(f"\n5) Brain Test:")
try:
    from medical_engine import analyze
    result = analyze("سردرد و تب")
    if result["candidates"]:
        top = result["candidates"][0]
        print(f"   OK: '{top['fa']}' at {top['percent']}%")
    else:
        print(f"   WARNING: No candidates (brain works but empty result)")
except Exception as e:
    print(f"   ERROR: {e}")

# ۶) تست چت کامل
print(f"\n6) Full Chat Test:")
try:
    from hybrid_engine import HybridEngine
    eng = HybridEngine()
    r = eng.chat("سردرد و تب دارم")
    if r["ok"] and r["text"]:
        print(f"   OK: got {len(r['text'])} chars response")
        print(f"   Source: {r['source']}")
        print(f"   First 60 chars: {r['text'][:60]}")
    else:
        print(f"   ERROR: chat returned ok={r['ok']}")
except Exception as e:
    print(f"   ERROR: {e}")

# ۷) تست سرور HTTP
print(f"\n7) HTTP Server Test:")
try:
    from http.server import ThreadingHTTPServer
    from run_web import Handler
    import threading
    test_port = find_free_port(2090, 2099)
    if test_port:
        httpd = ThreadingHTTPServer(("127.0.0.1", test_port), Handler)
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        import urllib.request
        r = urllib.request.urlopen(f"http://127.0.0.1:{test_port}/api/status", timeout=5)
        if r.status == 200:
            print(f"   OK: server responded on port {test_port}")
        else:
            print(f"   ERROR: status {r.status}")
        httpd.shutdown()
    else:
        print("   ERROR: no free test port")
except Exception as e:
    print(f"   ERROR: {e}")

# ۸) Tkinter
print(f"\n8) Desktop GUI (Tkinter):")
try:
    import tkinter
    root = tkinter.Tk()
    root.destroy()
    print("   OK: Tkinter works")
except Exception as e:
    print(f"   NOT AVAILABLE: {e}")
    print("   (web version works fine without this)")

print(f"\n" + "=" * 60)
print("  SUMMARY")
print("=" * 60)
print()
print("  If all tests pass, run:")
print("    Web:     python run_web.py")
print("    Desktop: python run_2077.py")
print()
print("  Then open: http://localhost:2077")
print()

input("  Press Enter to exit...")
