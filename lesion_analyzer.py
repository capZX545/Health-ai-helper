# -*- coding: utf-8 -*-
"""
lesion_analyzer.py — offline, objective analysis of what is VISIBLE in a
skin/wound/eye photo. It measures the image (affected area, redness, dark
asymmetry, color variation, yellow-green discharge tones, scattered spots,
border irregularity) and translates the measurements into cautious plain
language: a finding + what it can mean + where to go.

It measures; it never diagnoses. Every statement is phrased as
"consistent with / can mean", and the output always defers to a clinician.
"""
from __future__ import annotations

import io
from typing import Any


def _load(image_bytes: bytes):
    import numpy as np
    from PIL import Image
    im = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    if max(im.size) > 400:
        s = 400.0 / max(im.size)
        im = im.resize((int(im.size[0] * s), int(im.size[1] * s)))
    return np.asarray(im).astype(float)


def _components(mask) -> list[tuple[int, int, int]]:
    """connected components on a small boolean grid via BFS; returns (size, cy, cx)."""
    h, w = mask.shape
    seen = [[False] * w for _ in range(h)]
    comps = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y][x]:
                stack = [(y, x)]
                seen[y][x] = True
                size = 0
                sy = sx = 0
                while stack:
                    cy, cx = stack.pop()
                    size += 1
                    sy += cy
                    sx += cx
                    for ny, nx in ((cy+1, cx), (cy-1, cx), (cy, cx+1), (cy, cx-1)):
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny][nx]:
                            seen[ny][nx] = True
                            stack.append((ny, nx))
                comps.append((size, sy // max(size, 1), sx // max(size, 1)))
    return sorted(comps, reverse=True)


def analyze_lesion(image_bytes: bytes) -> dict[str, Any]:
    out: dict[str, Any] = {"found": False, "measures": {}, "findings": []}
    try:
        import numpy as np
        arr = _load(image_bytes)
        h, w, _ = arr.shape
        r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
        # رنگ پایه‌ی پوست: حاشیه‌ی دور تصویر (اگر معتبر باشد)
        ring = np.concatenate([r[:max(2, h // 10), :].ravel(), r[-max(2, h // 10):, :].ravel()])
        ring_g = np.concatenate([g[:max(2, h // 10), :].ravel(), g[-max(2, h // 10):, :].ravel()])
        ring_b = np.concatenate([b[:max(2, h // 10), :].ravel(), b[-max(2, h // 10):, :].ravel()])
        base = np.array([np.median(ring), np.median(ring_g), np.median(ring_b)])
        dist = np.sqrt(((arr - base) ** 2).sum(axis=2))
        thr = max(40.0, float(np.percentile(dist, 80)) * 0.9)
        mask = dist > thr
        area_pct = float(mask.mean() * 100.0)
        out["measures"]["affected_area_pct"] = round(area_pct, 1)
        if area_pct < 1.5:
            out["findings"].append({
                "en": "no clearly demarcated lesion region was found by the measurement",
                "fa": "ناحیه‌ی ضایعه‌ی مشخصی با این اندازه‌گیری پیدا نشد",
                "meaning_en": "", "meaning_fa": "", "level": "routine"})
            return out
        out["found"] = True
        lesion = arr[mask]
        lr, lg, lb = lesion[..., 0], lesion[..., 1], lesion[..., 2]
        redness = float(np.clip(lr - (lg + lb) / 2.0, 0, 255).mean() / 255.0)
        darkness = float((lesion.max(axis=1) < 70).mean())
        yellow = float(((lr > 150) & (lg > 120) & (lb < 120) & (lr - lb > 40)).mean())
        _lum = lesion.mean(axis=1)
        color_var = float((np.percentile(_lum, 98) - np.percentile(_lum, 2)) / 255.0)
        # تقارن: مقایسه‌ی دو نیمِ بزرگ‌ترین مؤلفه
        small = mask[::2, ::2]
        comps = _components(small)
        asym = 0.0
        border_irr = 0.0
        n_comp = len([c for c in comps if c[0] >= 4])
        if comps:
            size, cy, cx = comps[0]
            ys, xs = np.nonzero(small)
            left = xs <= cx
            a_left = ys[left].std() + xs[left].std()
            right = ys[~left].std() + xs[~left].std()
            asym = float(abs(a_left - right) / max(a_left, right, 1e-6))
            area = float(len(ys))
            per = 0
            for y, x in zip(ys, xs):
                for ny, nx in ((y+1, x), (y-1, x), (y, x+1), (y, x-1)):
                    if not (0 <= ny < small.shape[0] and 0 <= nx < small.shape[1]) or not small[ny, nx]:
                        per += 1
            import math
            border_irr = float(per / (2 * math.sqrt(math.pi * area))) if area else 0.0
        out["measures"].update({
            "redness_index": round(redness, 3),
            "dark_ratio": round(darkness, 3),
            "yellow_tone_ratio": round(yellow, 3),
            "color_variation": round(color_var, 3),
            "asymmetry": round(asym, 3),
            "border_irregularity": round(border_irr, 2),
            "lesion_patches": n_comp,
        })
        # ---------- ترجمه‌ی محتاطانه‌ی اندازه‌ها به یافته ----------
        F = out["findings"]
        if redness > 0.15 and area_pct >= 2:
            F.append({
                "en": f"a reddened/inflamed-looking region covering about {area_pct:.0f}% of the photo",
                "fa": f"ناحیه‌ی قرمز/التهابی‌نما در حدود {area_pct:.0f}٪ کادر عکس",
                "meaning_en": "consistent with an inflammatory picture (irritation, allergy or infection spectrum)",
                "meaning_fa": "با تصویر التهابی سازگار است (طیف تحریک، آلرژی یا عفونت)",
                "level": "routine"})
        if yellow > 0.08:
            F.append({
                "en": "yellow-green tinted areas that can indicate discharge or pus",
                "fa": "نواحی با رنگ زرد-سبز که می‌تواند نشانه‌ی ترشح یا چرک باشد",
                "meaning_en": "a possible sign of infection - same-day clinical evaluation",
                "meaning_fa": "علامت ممکن عفونت — ارزیابی بالینی همان روز",
                "level": "urgent"})
        if darkness > 0.35 and area_pct < 15 and yellow < 0.05 and (asym > 0.28 or color_var > 0.08):
            F.append({
                "en": "a darker patch with noticeable asymmetry/color variation",
                "fa": "لک تیره‌تر با تقارن/تنوع رنگ قابل‌توجه",
                "meaning_en": "the ABCDE rule applies to pigmented spots (Asymmetry, Border, Color, Diameter, Evolving); have a doctor look at it - promptly if it is changing, bleeding or itching",
                "meaning_fa": "قاعده‌ی ABCDE برای لک‌های رنگی مطرح است (عدم تقارن، لبه، رنگ، قطر، تغییرپذیری)؛ پزشک ببیند — و اگر در حال تغییر/خونریزی/خارش است، سریع‌تر",
                "level": "urgent"})
        if n_comp >= 8:
            F.append({
                "en": f"multiple scattered spots (about {n_comp} separate patches)",
                "fa": f"لکه‌های پراکنده‌ی متعدد (حدود {n_comp} ناحیه‌ی جدا)",
                "meaning_en": "consistent with a rash-type picture rather than a single lesion",
                "meaning_fa": "با تصویر از نوع بثورات (نه یک ضایعه‌ی واحد) سازگار است",
                "level": "routine"})
        if border_irr > 1.7 and darkness > 0.15:
            F.append({
                "en": "an irregular border around the darker region",
                "fa": "لبه‌ی نامنظم پیرامون ناحیه‌ی تیره‌تر",
                "meaning_en": "irregular borders deserve a professional look; not a diagnosis by itself",
                "meaning_fa": "لبه‌ی نامنظم ارزش دیده‌شدن توسط پزشک را دارد؛ به‌تنهایی تشخیص نیست",
                "level": "routine"})
        if not F:
            F.append({
                "en": "a visible region different from the surrounding skin, without strongly alarming measured features",
                "fa": "ناحیه‌ای متمایز از پوست اطراف، بدون ویژگی اندازه‌گیری‌شده‌ی به‌طور مشخص هشداردهنده",
                "meaning_en": "monitor it and have it checked if it persists or changes",
                "meaning_fa": "زیر نظر بگیر و اگر ماندگار یا تغییرکننده بود بررسی شود",
                "level": "routine"})
        return out
    except Exception as e:
        out["findings"].append({"en": "image measurement failed: " + str(e)[:60],
                                "fa": "اندازه‌گیری تصویر ممکن نشد: " + str(e)[:60],
                                "meaning_en": "", "meaning_fa": "", "level": "routine"})
        return out
