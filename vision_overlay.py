"""
vision_overlay.py — draws the vision engine's findings directly on the
photo: red boxes around each abnormal region with its bilingual label and
confidence, a healthy-area footer, producing an annotated PNG the user can
see, save or show to a doctor. Pure PIL, fully offline.
"""
from __future__ import annotations

import io
import os
import tempfile
from typing import Any


def _label_txt(label: str, conf: float, fa: bool) -> str:
    from vision_report import INFO
    info = INFO.get(label, {})
    name = info.get("n", (label, label))[1 if fa else 0]
    return f"{name} {int(conf * 100)}%"


def annotate(image_bytes: bytes, analysis: dict[str, Any], fa: bool = True) -> bytes | None:
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        w, h = img.size
        if max(w, h) > 1100:
            scale = 1100.0 / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)))
            w, h = img.size
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.load_default(size=15)
            font_small = ImageFont.load_default(size=12)
        except Exception:
            font = font_small = ImageFont.load_default()
        regions = (analysis or {}).get("regions") or []
        colors = {"urgent": (255, 42, 74), "routine": (0, 240, 255)}
        from vision_report import INFO
        for r in regions:
            x0, y0, x1, y1 = r["bbox"]
            px0, py0 = int(x0 * w), int(y0 * h)
            px1, py1 = int(x1 * w), int(y1 * h)
            lvl = INFO.get(r["label"], {}).get("lvl", "routine")
            col = colors.get(lvl, (0, 240, 255))
            for k in range(3):
                draw.rectangle([px0 - k, py0 - k, px1 + k, py1 + k], outline=col)
            txt = _label_txt(r["label"], r.get("conf", 0.0), fa)
            tw = draw.textlength(txt, font=font)
            ty = py0 - 20 if py0 > 24 else py1 + 4
            draw.rectangle([px0, ty - 2, px0 + tw + 8, ty + 18], fill=(2, 4, 3))
            draw.text((px0 + 4, ty), txt, fill=col, font=font)
        healthy = (analysis or {}).get("healthy_pct")
        if healthy is not None:
            foot = (f"سالم: {healthy}%" if fa else f"healthy: {healthy}%")
            if regions:
                foot += "  |  " + (f"{len(regions)} ناحیه‌ی مشکوک" if fa else f"{len(regions)} region(s)")
            draw.rectangle([0, h - 24, w, h], fill=(2, 4, 3))
            draw.text((10, h - 20), foot[:120], fill=(200, 245, 240), font=font_small)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return None


def save_annotated(image_bytes: bytes, analysis: dict[str, Any], fa: bool = True) -> dict[str, Any]:
    data = annotate(image_bytes, analysis, fa)
    if not data:
        return {"ok": False}
    path = os.path.join(tempfile.gettempdir(), "nexusmed_vision.png")
    try:
        with open(path, "wb") as f:
            f.write(data)
        return {"ok": True, "path": path, "png": data}
    except Exception:
        return {"ok": False, "png": data}
