# -*- coding: utf-8 -*-
"""
image_type_detector.py — offline heuristic classifier for medical photos.
It looks at simple image statistics (color, edges, layout) and makes an
honest guess about the kind of medical image it is dealing with:
skin/wound photo, radiograph (X-ray/CT/MRI), ECG strip, lab report or
prescription scan, eye photo, or a generic photo.

These are structural guesses only. They are never a diagnosis and the
confidence numbers are rough margins, not probabilities of anything
clinical. The user's explicit hint always overrides the heuristic.
"""
from __future__ import annotations

import io
from typing import Any

TYPES: dict[str, dict[str, Any]] = {
    "skin_photo": {
        "en": "skin photo (lesion / rash)",
        "fa": "عکس پوست (ضایعه / جوش / لک)",
        "hint_label": {"en": "Skin / rash", "fa": "پوست / جوش"},
    },
    "wound_photo": {
        "en": "wound / ulcer photo",
        "fa": "عکس زخم / سوختگی",
        "hint_label": {"en": "Wound / burn", "fa": "زخم / سوختگی"},
    },
    "radiograph": {
        "en": "grayscale radiograph (X-ray / CT / MRI)",
        "fa": "تصویر رادیولوژی سیاه‌وسفید (رادیوگرافی / سی‌تی / ام‌آرآی)",
        "hint_label": {"en": "X-ray / CT / MRI", "fa": "رادیوگرافی / سی‌تی / ام‌آرآی"},
    },
    "ecg_strip": {
        "en": "ECG strip",
        "fa": "نوار قلب (الکتروکاردیوگرام)",
        "hint_label": {"en": "ECG", "fa": "نوار قلب"},
    },
    "document_report": {
        "en": "scanned report (lab result / prescription)",
        "fa": "عکس برگه‌ی آزمایش یا نسخه",
        "hint_label": {"en": "Lab report / prescription", "fa": "برگه‌ی آزمایش / نسخه"},
    },
    "eye_photo": {
        "en": "eye photo",
        "fa": "عکس چشم",
        "hint_label": {"en": "Eye", "fa": "چشم"},
    },
    "dental_photo": {
        "en": "dental / oral photo",
        "fa": "عکس دندان / داخل دهان",
        "hint_label": {"en": "Dental / oral", "fa": "دندان / دهان"},
    },
    "device_screen": {
        "en": "medical device screen (BP/glucose/thermometer)",
        "fa": "صفحه‌نمایش دستگاه پزشکی (فشارسنج/قندسنج/دماسنج)",
        "hint_label": {"en": "Device screen", "fa": "نمایشگر دستگاه"},
    },
    "other_photo": {
        "en": "general photo",
        "fa": "عکس عمومی",
        "hint_label": {"en": "Other", "fa": "سایر"},
    },
}

HINT_ALIASES = {
    "skin": "skin_photo", "rash": "skin_photo", "lesion": "skin_photo",
    "wound": "wound_photo", "burn": "wound_photo", "ulcer": "wound_photo",
    "xray": "radiograph", "x-ray": "radiograph", "radiograph": "radiograph",
    "ct": "radiograph", "mri": "radiograph", "radiology": "radiograph",
    "ecg": "ecg_strip", "ekg": "ecg_strip",
    "lab": "document_report", "report": "document_report", "document": "document_report",
    "prescription": "document_report",
    "eye": "eye_photo",
    "dental": "dental_photo", "teeth": "dental_photo", "oral": "dental_photo", "mouth": "dental_photo",
    "device": "device_screen", "monitor": "device_screen", "bp": "device_screen", "glucometer": "device_screen",
    "other": "other_photo",
}


def _stats(image_bytes: bytes) -> dict[str, float]:
    import numpy as np
    from PIL import Image

    im = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    w, h = im.size
    scale = 256.0 / max(w, h)
    im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))))
    arr = np.asarray(im).astype(float)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    mx, mn = arr.max(2), arr.min(2)
    sat = mx - mn                                   # 0-255 per pixel
    gray_ratio = float((sat < 22).mean())
    sat_mean = float(sat.mean())
    bright = float(arr.mean() / 255.0)
    white_ratio = float((mn > 235).mean())
    dark_ratio = float((mx < 40).mean())
    gray = arr.mean(2)
    # simple gradients instead of sobel, good enough for edge/blur measuring
    dx = np.abs(np.diff(gray, axis=1))
    dy = np.abs(np.diff(gray, axis=0))
    grad = np.concatenate([dx.ravel(), dy.ravel()])
    edge_density = float((grad > 18).mean())
    sharpness = float(grad.std())
    non_white = mn <= 235
    redness = float(np.clip(r - (g + b) / 2.0, 0, 255)[non_white].mean() / 255.0) if non_white.any() else 0.0
    aspect = float(w) / float(h) if h else 1.0
    return {"gray_ratio": gray_ratio, "sat_mean": sat_mean, "brightness": bright,
            "white_ratio": white_ratio, "dark_ratio": dark_ratio,
            "edge_density": edge_density, "sharpness": sharpness, "redness": redness,
            "aspect": aspect, "width": w, "height": h}


def _classify(s: dict[str, float]) -> tuple[str, float, str]:
    """(type_key, confidence 0..1, reason) — reason is a short honest explanation."""
    # 1) ECG strip: wide white background + wide ratio + thin lines
    if s["white_ratio"] > 0.45 and 2.0 <= s["aspect"] <= 10.0 and s["gray_ratio"] > 0.75 and s["edge_density"] < 0.09:
        conf = min(0.9, 0.55 + s["white_ratio"] * 0.3 + (1.0 if 3.0 <= s["aspect"] <= 8.0 else 0.0) * 0.1)
        return "ecg_strip", round(conf, 2), "white background, wide strip, thin dark trace"
    # 2) lab sheet/prescription: white bg + text (dense edges) + page ratio
    if s["white_ratio"] > 0.45 and s["edge_density"] >= 0.02 and s["aspect"] < 2.0 and s["redness"] < 0.05:
        conf = min(0.88, 0.5 + s["white_ratio"] * 0.35 + min(s["edge_density"], 0.1))
        return "document_report", round(conf, 2), "white page with dense small text-like edges"
    # 3) radiology: nearly colorless, no white bg (dark or flat gray)
    if s["gray_ratio"] > 0.82 and s["white_ratio"] < 0.45 and (s["dark_ratio"] > 0.01 or s["brightness"] < 0.72):
        conf = min(0.88, 0.5 + s["gray_ratio"] * 0.3 + min(s["dark_ratio"], 0.3) * 0.4)
        return "radiograph", round(conf, 2), "grayscale, no white page background"
    # 4) wound/burn: very strong redness, or red plus dark patches
    if s["redness"] > 0.35 or (s["redness"] > 0.11 and s["dark_ratio"] > 0.02 and s["sat_mean"] > 12):
        conf = min(0.85, 0.5 + s["redness"] * 1.2)
        return "wound_photo", round(conf, 2), "strong red component, wound-like"
    # 5) skin photo: mild color/redness
    if s["sat_mean"] > 18 or s["redness"] > 0.05:
        conf = min(0.85, 0.5 + s["sat_mean"] / 200.0 + s["redness"])
        return "skin_photo", round(conf, 2), "colorful skin-toned photo"
    # 6) eye photo: white around + roundish shape; weak guess at best
    if s["white_ratio"] > 0.25 and s["redness"] > 0.03 and 0.7 <= s["aspect"] <= 1.6:
        return "eye_photo", 0.45, "round-ish shape with white surroundings (weak guess)"
    return "other_photo", 0.4, "no strong structural signal"


def classify_image(image_bytes: bytes, hint: str | None = None) -> dict[str, Any]:
    """Classify a medical image. hint (from the user) overrides the heuristic.
    Broken image data degrades gracefully instead of raising."""
    from i18n import is_fa
    try:
        s = _stats(image_bytes)
    except Exception:
        info = TYPES["other_photo"]
        return {"type": "other_photo", "label": info["fa"] if is_fa() else info["en"],
                "confidence": 0.0, "reason": "unreadable image data", "user_hint": bool(HINT_ALIASES.get((hint or "").strip().lower())),
                "features": {}, "size": "?", "quality": ["unreadable" if not is_fa() else "ناخوانا"],
                "hint_options": [{"value": k, "label": v["hint_label"]["fa" if is_fa() else "en"]} for k, v in TYPES.items()]}
    used_hint = False
    hint_key = HINT_ALIASES.get((hint or "").strip().lower())
    if hint_key:
        key, conf, reason = hint_key, 1.0, "user-selected type"
        used_hint = True
    else:
        key, conf, reason = _classify(s)
    info = TYPES[key]
    quality = []
    if s["sharpness"] < 9:
        quality.append("possibly blurry" if not is_fa() else "احتمالاً تار/لرزان")
    if s["brightness"] < 0.15:
        quality.append("very dark" if not is_fa() else "خیلی تیره")
    if s["brightness"] > 0.92:
        quality.append("overexposed" if not is_fa() else "روشنایی بیش از حد")
    return {
        "type": key,
        "label": info["fa"] if is_fa() else info["en"],
        "confidence": conf,
        "reason": reason,
        "user_hint": used_hint,
        "features": {k: round(v, 3) for k, v in s.items() if k not in ("width", "height")},
        "size": f'{int(s["width"])}x{int(s["height"])}',
        "quality": quality,
        "hint_options": [{"value": k, "label": v["hint_label"]["fa" if is_fa() else "en"]}
                         for k, v in TYPES.items()],
    }


def hint_keys() -> list[str]:
    return list(TYPES.keys())
