# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import tempfile


def _wkhtmltopdf_available() -> str | None:
    for p in ("wkhtmltopdf", "/usr/bin/wkhtmltopdf",
              r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
              r"C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe"):
        try:
            subprocess.run([p, "--version"], capture_output=True, timeout=5)
            return p
        except Exception:
            continue
    return None


def _chrome_available() -> str | None:
    for p in ("google-chrome", "/usr/bin/google-chrome",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              "msedge"):
        try:
            subprocess.run([p, "--version"], capture_output=True, timeout=5)
            return p
        except Exception:
            continue
    return None


def html_to_pdf(html_path: str, pdf_path: str) -> dict:
    """Convert an HTML file to PDF using any available engine."""
    html_path = os.path.abspath(html_path)
    pdf_path = os.path.abspath(pdf_path)

    wk = _wkhtmltopdf_available()
    if wk:
        try:
            r = subprocess.run([wk, "--encoding", "utf-8", "--page-size", "A4",
                                "--margin-top", "15mm", "--margin-bottom", "15mm",
                                html_path, pdf_path],
                               capture_output=True, timeout=30)
            if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 100:
                return {"ok": True, "engine": "wkhtmltopdf", "path": pdf_path}
        except Exception:
            pass

    chrome = _chrome_available()
    if chrome:
        try:
            r = subprocess.run([chrome, "--headless", "--disable-gpu",
                                "--no-sandbox", "--print-to-pdf=" + pdf_path,
                                "--no-pdf-header-footer", html_path],
                               capture_output=True, timeout=30)
            if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 100:
                return {"ok": True, "engine": "chrome", "path": pdf_path}
        except Exception:
            pass

    return {"ok": False,
            "message_fa": "موتور PDF پیدا نشد. فایل HTML ذخیره شد — از مرورگر Ctrl+P بزن و PDF را انتخاب کن.",
            "message_en": "No PDF engine found. HTML saved — open in browser and Ctrl+P -> Save as PDF."}


def referral_pdf(html_path: str, base_name: str = "referral_report") -> dict:
    """Convert the referral HTML report to PDF alongside it."""
    d = os.path.dirname(html_path)
    pdf = os.path.join(d, base_name + ".pdf")
    return html_to_pdf(html_path, pdf)
