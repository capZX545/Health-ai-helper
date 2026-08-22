# -*- coding: utf-8 -*-
"""
ecg_analyzer.py — offline, honest analysis of an ECG strip photo.
It extracts the dark trace from a light background, counts QRS-like
deflections and reports whether they look regular. It deliberately does
NOT estimate beats per minute (that needs the printed paper speed/scale)
and it never interprets ischemia or anything else clinical.
"""
from __future__ import annotations

import io
from typing import Any


def analyze_ecg(image_bytes: bytes) -> dict[str, Any]:
    from i18n import is_fa
    out: dict[str, Any] = {"visible": False, "deflections": 0, "regular": None,
                           "note_en": "", "note_fa": ""}
    try:
        import numpy as np
        from PIL import Image
        im = Image.open(io.BytesIO(image_bytes)).convert("L")
        if im.size[0] > 1400:
            im = im.resize((1400, int(im.size[1] * 1400 / im.size[0])))
        a = np.asarray(im).astype(float)
        dark = a < 120
        col_counts = dark.sum(axis=0)
        usable = col_counts >= 1
        if usable.mean() < 0.4:
            out["note_en"] = "no clear trace found in the image"
            out["note_fa"] = "ریتم واضحی در تصویر پیدا نشد"
            return out
        rows = np.arange(a.shape[0])
        trace = (dark * rows[:, None]).sum(axis=0) / np.maximum(col_counts, 1)
        t = trace[usable]
        base = np.median(t)
        dev = base - t          # upward deflection (smaller y) = positive
        thr = max(3.0, 2.5 * float(np.std(dev)))
        above = dev > thr
        groups = []
        start = None
        for i, flag in enumerate(above):
            if flag and start is None:
                start = i
            elif not flag and start is not None:
                groups.append((start, i))
                start = None
        if start is not None:
            groups.append((start, len(above)))
        groups = [g for g in groups if g[1] - g[0] >= 1]
        out["deflections"] = len(groups)
        if len(groups) < 3:
            out["note_en"] = "too few clear deflections for a regularity check"
            out["note_fa"] = "تعداد موج‌های واضح برای بررسی نظم کافی نیست"
            out["visible"] = True
            return out
        centers = [ (g0 + g1) / 2.0 for g0, g1 in groups ]
        rr = [centers[i + 1] - centers[i] for i in range(len(centers) - 1)]
        rr_arr = np.array(rr, dtype=float)
        mean_rr = float(rr_arr.mean())
        cov = float(rr_arr.std() / mean_rr) if mean_rr > 0 else 1.0
        out["visible"] = True
        out["regular"] = bool(cov < 0.18)
        out["rr_variability"] = round(cov, 3)
        out["note_en"] = (f"{len(groups)} beat-like deflections; rhythm appears "
                          + ("regular" if out["regular"] else "IRREGULAR")
                          + ". Beats-per-minute cannot be computed without the printed paper speed. "
                            "This is not an interpretation - a physician must read the strip.")
        out["note_fa"] = (f"{len(groups)} موج شبه‌ضربان؛ ریتم {'منظم' if out['regular'] else 'نامنظم'} به نظر می‌رسد. "
                          "بدون مقیاس چاپیِ سرعت کاغذ نمی‌توان ضربان دقیق را محاسبه کرد. "
                          "این یک تفسیر نیست — خواندن نوار فقط توسط پزشک است.")
        return out
    except Exception as e:
        out["note_en"] = "trace analysis failed: " + str(e)[:60]
        out["note_fa"] = "تحلیل ریتم ممکن نشد: " + str(e)[:60]
        return out
