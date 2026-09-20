"""
emergency_card.py — ICE (in case of emergency) card: blood type, allergies,
conditions and current medications gathered from the profile, exported as a
printable HTML card plus a scannable QR code for the phone lock screen.
"""
from __future__ import annotations

import os
import re
from typing import Any

from common_2077 import DATA_DIR, read_json, write_json
from i18n import is_fa

ICE_PATH = os.path.join(DATA_DIR, "ice_card.json")

BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]


def load_ice() -> dict[str, Any]:
    d = read_json(ICE_PATH, default=None)
    if not isinstance(d, dict):
        return {}
    return {k: d.get(k, "") for k in ("blood_type", "contact_name", "contact_phone", "notes")}


def save_ice(data: dict[str, Any]) -> dict[str, Any]:
    cur = load_ice()
    for k in ("blood_type", "contact_name", "contact_phone", "notes"):
        if k in data and data[k] is not None:
            cur[k] = str(data[k]).strip()
    write_json(ICE_PATH, cur)
    return {"ok": True, "ice": cur}


def _clean_lines(s: str) -> list[str]:
    return [p.strip() for p in re.split(r"[;,،\n]+", str(s or "")) if p.strip()]


def card_data() -> dict[str, Any]:
    from patient_profile import load_profile
    p = load_profile()
    ice = load_ice()
    meds = _clean_lines(p.get("medications"))
    try:
        from med_reminder_service import list_all
        for r in list_all():
            name = str(r.get("drug") or "").strip()
            if name and name not in meds and not str(r.get("off", "")).lower() in ("1", "true", "yes"):
                meds.append(name)
    except Exception:
        pass
    return {
        "name": str(p.get("name") or ""),
        "age": p.get("age") or "",
        "gender": p.get("gender") or "",
        "blood_type": ice.get("blood_type") or "",
        "allergies": _clean_lines(p.get("allergies")),
        "conditions": _clean_lines(p.get("conditions")),
        "medications": meds,
        "contact_name": ice.get("contact_name") or "",
        "contact_phone": ice.get("contact_phone") or "",
        "notes": ice.get("notes") or "",
    }


def card_text() -> str:
    d = card_data()
    lines = ["EMERGENCY / اورژانس 115"]
    if d["name"]:
        lines.append(f"Name: {d['name']}")
    if d["blood_type"]:
        lines.append(f"Blood type: {d['blood_type']}")
    if d["allergies"]:
        lines.append("Allergies: " + ", ".join(d["allergies"][:8]))
    if d["conditions"]:
        lines.append("Conditions: " + ", ".join(d["conditions"][:8]))
    if d["medications"]:
        lines.append("Medications: " + ", ".join(d["medications"][:8]))
    if d["contact_name"] or d["contact_phone"]:
        lines.append(f"Contact: {d['contact_name']} {d['contact_phone']}".strip())
    if d["notes"]:
        lines.append(f"Note: {str(d['notes'])[:120]}")
    return "\n".join(lines)


def qr_svg(text: str, border: int = 2) -> str | None:
    try:
        import io
        import qrcode
        import qrcode.image.svg
        img = qrcode.make(text, image_factory=qrcode.image.svg.SvgPathImage,
                          border=border, error_correction=qrcode.constants.ERROR_CORRECT_M)
        buf = io.BytesIO()
        img.save(buf)
        return buf.getvalue().decode("utf-8")
    except Exception:
        return None


def _esc(s: Any) -> str:
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_html(lang: str | None = None) -> str:
    fa = (lang == "fa") if lang else is_fa()
    d = card_data()
    svg = qr_svg(card_text())
    if fa:
        title = "کارت اضطراری پزشکی"
        lbl_name, lbl_blood = "نام", "گروه خونی"
        lbl_all, lbl_cond, lbl_med = "حساسیت‌ها", "بیماری‌ها", "داروها"
        lbl_contact, lbl_notes = "تماس اضطراری", "یادداشت"
        empty = "ثبت نشده"
        foot = "این کارت را در قفل گوشی یا کیف نگه دارید — امدادگر با اسکن QR همه‌چیز را می‌بیند."
        none_txt = "داده‌ای ثبت نشده — اول پروفایل بیمار را کامل کن."
    else:
        title = "Medical Emergency Card"
        lbl_name, lbl_blood = "Name", "Blood type"
        lbl_all, lbl_cond, lbl_med = "Allergies", "Conditions", "Medications"
        lbl_contact, lbl_notes = "Emergency contact", "Notes"
        empty = "not set"
        foot = "Keep this card on your phone lock screen or wallet - paramedics scan the QR and see everything."
        none_txt = "No data recorded yet - complete the patient profile first."
    has_any = any((d["name"], d["blood_type"], d["allergies"], d["conditions"], d["medications"], d["contact_phone"]))
    rows = ""
    for label, val in ((lbl_name, d["name"] or empty), (lbl_blood, d["blood_type"] or empty),
                       (lbl_all, ", ".join(d["allergies"]) or empty),
                       (lbl_cond, ", ".join(d["conditions"]) or empty),
                       (lbl_med, ", ".join(d["medications"]) or empty),
                       (lbl_contact, (d["contact_name"] + " " + d["contact_phone"]).strip() or empty),
                       (lbl_notes, d["notes"] or empty)):
        rows += (f'<tr><th style="text-align:{"right" if fa else "left"};padding:6px 10px;'
                 f'border-bottom:1px solid #d8dee9;font-size:14px;color:#455770">{_esc(label)}</th>'
                 f'<td style="padding:6px 10px;border-bottom:1px solid #d8dee9;font-size:15px;'
                 f'font-weight:700;color:#0f1b30">{_esc(val)}</td></tr>')
    qr_div = (f'<div style="width:190px">{svg}</div>' if svg else
              f'<div style="color:#8a97ab;font-size:12px">{"QR در دسترس نیست (کتابخانه نصب نیست)" if fa else "QR unavailable (library not installed)"}</div>')
    empty_note = "" if has_any else (f'<p style="color:#b23b3b;font-weight:700">{none_txt}</p>')
    return f"""<!doctype html><html lang="{("fa" if fa else "en")}" dir="{("rtl" if fa else "ltr")}">
<head><meta charset="utf-8"><title>{_esc(title)}</title></head>
<body style="margin:0;font-family:Vazirmatn,Tahoma,Arial,sans-serif;background:#eef1f6">
<div style="max-width:640px;margin:18px auto;background:#fff;border-radius:14px;overflow:hidden;
box-shadow:0 4px 22px #0f1b3022">
<div style="background:#b3261e;color:#fff;padding:14px 18px;font-size:20px;font-weight:800;
letter-spacing:.5px">{_esc(title)} &nbsp;•&nbsp; ICE</div>
<div style="display:flex;gap:18px;padding:18px;align-items:flex-start;flex-wrap:wrap">
<div style="flex:1;min-width:240px"><table style="border-collapse:collapse;width:100%">{rows}</table>
{empty_note}</div>
{qr_div}</div>
<div style="background:#0f1b30;color:#c9d6ea;padding:10px 18px;font-size:12px">{_esc(foot)}</div>
</div></body></html>"""


def save_card(path: str | None = None, lang: str | None = None) -> dict[str, Any]:
    import tempfile
    fa = (lang == "fa") if lang else is_fa()
    path = path or os.path.join(tempfile.gettempdir(), "nexusmed_ice_card.html")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(build_html(lang))
        return {"ok": True, "path": path,
                "message_fa": ("کارت ذخیره شد — در مرورگر باز می‌شود؛ از آن پرینت یا عکس بگیر."
                               if fa else "Card saved - opening in the browser; print it or take a screenshot.")}
    except Exception as e:
        return {"ok": False, "message_fa": str(e)}
