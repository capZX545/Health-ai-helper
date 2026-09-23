"""
vision_core.py — the internal vision engine: extracts grid-cell features
from any medical photo, classifies every cell with a bundled random-forest
model (pure-JSON, version-proof, no sklearn needed at runtime), merges
abnormal cells into regions and reports WHERE the damage is and where the
tissue/image looks healthy. Fully offline; no external AI.
"""
from __future__ import annotations

import gzip
import json
import math
import os
from typing import Any

import numpy as np

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(DATA_DIR, "vision_model.json.gz")
GRID = 8

LABELS = ["healthy", "lesion", "bruise", "burn", "granulation", "slough",
          "eschar", "opacity", "exudate", "hemorrhage", "dark_bg"]
ABNORMAL = {"lesion", "bruise", "burn", "granulation", "slough", "eschar",
            "opacity", "exudate", "hemorrhage"}

_model_cache: dict[str, Any] | None = None


def load_image(image_bytes: bytes) -> np.ndarray | None:
    try:
        import io
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
        img = img.convert("RGB")
        return np.asarray(img, dtype=np.float64)
    except Exception:
        return None


def cell_features(arr: np.ndarray, grid: int = GRID) -> tuple[np.ndarray, int, int]:
    h, w = arr.shape[:2]
    gh = max(1, h // grid)
    gw = max(1, w // grid)
    r = arr[..., 0]
    g = arr[..., 1]
    b = arr[..., 2]
    luma = 0.299 * r + 0.587 * g + 0.114 * b
    mx = arr.max(axis=2)
    mn = arr.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1.0), 0.0)
    gy = np.abs(np.diff(luma, axis=0))
    gx = np.abs(np.diff(luma, axis=1))
    edge = np.zeros((h, w))
    edge[1:, :] += gy
    edge[:, 1:] += gx
    feats: list[np.ndarray] = []
    for i in range(grid):
        for j in range(grid):
            ys, ye = i * gh, min(h, (i + 1) * gh)
            xs, xe = j * gw, min(w, (j + 1) * gw)
            if ys >= ye or xs >= xe:
                feats.append(np.zeros(16))
                continue
            cr, cg, cb = r[ys:ye, xs:xe], g[ys:ye, xs:xe], b[ys:ye, xs:xe]
            cl = luma[ys:ye, xs:xe]
            feats.append(np.array([
                cr.mean(), cg.mean(), cb.mean(),
                cr.std(), cg.std(), cb.std(),
                max(0.0, cr.mean() - (cg.mean() + cb.mean()) / 2.0),
                max(0.0, cr.mean() + cg.mean() - 2.0 * cb.mean()),
                1.0 - cl.mean() / 255.0,
                cl.mean() / 255.0,
                sat[ys:ye, xs:xe].mean(),
                edge[ys:ye, xs:xe].mean(),
                (np.percentile(cl, 95) - np.percentile(cl, 5)) / 255.0,
                (np.abs(cr - cg) + np.abs(cg - cb)).mean() / 255.0,
                (i + 0.5) / grid,
                (j + 0.5) / grid,
            ]))
    return np.asarray(feats), grid, grid


def _load_model() -> dict[str, Any]:
    global _model_cache
    if _model_cache is None:
        try:
            with gzip.open(MODEL_PATH, "rt", encoding="utf-8") as f:
                _model_cache = json.load(f)
        except Exception:
            _model_cache = {"classes": ["healthy"], "trees": []}
    return _model_cache


def _tree_vote(node, x) -> int:
    while "leaf" not in node:
        if x[node["f"]] <= node["t"]:
            node = node["l"]
        else:
            node = node["r"]
    return node["leaf"]


def predict_cells(feats: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    m = _load_model()
    classes = m.get("classes", [])
    trees = m.get("trees", [])
    n = feats.shape[0]
    if not classes or not trees:
        return np.zeros(n, dtype=int), np.zeros(n)
    votes = np.zeros((n, len(classes)))
    for t in trees:
        for i in range(n):
            votes[i, _tree_vote(t, feats[i])] += 1.0
    pred = votes.argmax(axis=1)
    conf = votes.max(axis=1) / len(trees)
    return pred, conf


def _where_words(cx: float, cy: float, fa: bool) -> str:
    v = ("بالا" if cy < 0.4 else "پایین" if cy > 0.62 else "وسط")
    hz = ("چپ" if cx < 0.4 else "راست" if cx > 0.62 else "وسط")
    if not fa:
        v = "upper" if cy < 0.4 else "lower" if cy > 0.62 else "middle"
        hz = "left" if cx < 0.4 else "right" if cx > 0.62 else "center"
    if v == hz == ("وسط" if fa else "center"):
        return "وسط تصویر" if fa else "the center of the image"
    return f"یک‌سوم {v} سمت {hz}" if fa else f"the {v} {hz} part"


_ABNORMAL_IDS = {LABELS.index(x) for x in ABNORMAL}


def _regions(pred: np.ndarray, conf: np.ndarray, grid: int) -> list[dict[str, Any]]:
    lab_grid = pred.reshape(grid, grid)
    conf_grid = conf.reshape(grid, grid)
    seen = np.zeros((grid, grid), dtype=bool)
    regions: list[dict[str, Any]] = []
    for i in range(grid):
        for j in range(grid):
            if seen[i, j] or lab_grid[i, j] not in _ABNORMAL_IDS:
                continue
            stack = [(i, j)]
            cells = []
            seen[i, j] = True
            while stack:
                y, x = stack.pop()
                cells.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1),
                               (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < grid and 0 <= nx < grid and not seen[ny, nx] and lab_grid[ny, nx] in _ABNORMAL_IDS:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            counts: dict[int, int] = {}
            for c in cells:
                counts[int(lab_grid[c[0], c[1]])] = counts.get(int(lab_grid[c[0], c[1]]), 0) + 1
            lab = max(counts, key=lambda k: counts[k])
            rows = [c[0] for c in cells]
            cols = [c[1] for c in cells]
            y0, y1 = min(rows), max(rows) + 1
            x0, x1 = min(cols), max(cols) + 1
            mean_conf = float(np.mean([conf_grid[c[0], c[1]] for c in cells]))
            regions.append({
                "label": LABELS[lab],
                "bbox": (x0 / grid, y0 / grid, x1 / grid, y1 / grid),
                "cells": len(cells),
                "area_pct": round(100.0 * len(cells) / (grid * grid), 1),
                "conf": round(mean_conf, 2),
                "where_fa": _where_words((x0 + x1) / 2 / grid, (y0 + y1) / 2 / grid, True),
                "where_en": _where_words((x0 + x1) / 2 / grid, (y0 + y1) / 2 / grid, False),
            })
    regions.sort(key=lambda r: -r["cells"])
    merged: list[dict[str, Any]] = []
    for r in regions:
        if r["cells"] < 2 and r["conf"] < 0.55:
            continue
        if r["label"] == "opacity" and r["conf"] < 0.72:
            continue
        merged.append(r)
    return merged[:4]




def _is_grayscale(arr: np.ndarray) -> bool:
    mx = arr.max(axis=2)
    mn = arr.min(axis=2)
    return float((mx - mn).mean()) < 14.0


def _crop_classify(arr: np.ndarray, x0: float, y0: float, x1: float, y1: float) -> tuple[str, float]:
    import vision_net as vn
    h, w = arr.shape[:2]
    px0 = max(0, int(x0 * w) - 6)
    py0 = max(0, int(y0 * h) - 6)
    px1 = min(w, int(x1 * w) + 6)
    py1 = min(h, int(y1 * h) + 6)
    if px1 - px0 < 16 or py1 - py0 < 16:
        return "", 0.0
    crop = arr[py0:py1, px0:px1]
    try:
        from PIL import Image as _I
        im = _I.fromarray(np.clip(crop, 0, 255).astype(np.uint8)).resize((48, 48))
        x = np.asarray(im, dtype=np.float64).transpose(2, 0, 1) / 255.0
        probs = vn.predict_proba(x[None])[0]
        abn = [(probs[i], vn.LABELS_DEEP[i]) for i in range(len(probs))
               if vn.LABELS_DEEP[i] in vn.ABNORMAL_DEEP]
        abn.sort(reverse=True)
        return abn[0][1], float(abn[0][0])
    except Exception:
        return "", 0.0


def _mole_scan(arr: np.ndarray) -> dict[str, Any] | None:
    import vision_net as vn
    h, w = arr.shape[:2]
    if h < 64 or w < 64:
        return None
    win = 48
    stride = 20
    best = None
    coords = [(y, x) for y in range(0, max(1, h - win + 1), stride)
              for x in range(0, max(1, w - win + 1), stride)]
    for i0 in range(0, len(coords), 128):
        chunk = coords[i0:i0 + 128]
        xb = np.stack([np.clip(arr[y:y + win, x:x + win], 0, 255) / 255.0
                       for y, x in chunk]).transpose(0, 3, 1, 2)
        probs = vn.predict_proba(xb)
        for (y, x), pr in zip(chunk, probs):
            for cls, thr_m in (("melanoma_susp", 0.62), ("nevus", 0.55)):
                c = float(pr[vn.LABELS_DEEP.index(cls)])
                if c >= thr_m and (best is None or c > best[0]):
                    best = (c, cls, x / w, y / h, (x + win) / w, (y + win) / h)
    if best is None:
        return None
    c, cls, x0, y0, x1, y1 = best
    return {"label": cls, "bbox": (x0, y0, x1, y1), "cells": 2,
            "area_pct": round(100.0 * (x1 - x0) * (y1 - y0), 1), "conf": round(c, 2),
            "where_fa": _where_words((x0 + x1) / 2, (y0 + y1) / 2, True),
            "where_en": _where_words((x0 + x1) / 2, (y0 + y1) / 2, False)}


def _radiology_regions(arr: np.ndarray) -> list[dict[str, Any]]:
    from scipy import ndimage
    lum = (0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2])
    h, w = lum.shape
    if max(h, w) > 512:
        sc = 512.0 / max(h, w)
        try:
            from PIL import Image as _I
            im = _I.fromarray(np.clip(lum, 0, 255).astype(np.uint8)).resize((int(w * sc), int(h * sc)))
            lum = np.asarray(im, dtype=np.float64)
            h, w = lum.shape
            sx, sy = 1.0 / sc, 1.0 / sc
        except Exception:
            return []
    else:
        sx = sy = 1.0
    body = ndimage.binary_erosion(ndimage.binary_opening(lum > 30, np.ones((5, 5))), np.ones((9, 9)))
    if body.sum() < 500:
        return []
    p20 = np.percentile(lum[body], 20)
    dark = body & (lum < p20 + 8)
    lab, n = ndimage.label(ndimage.binary_opening(dark, np.ones((7, 7))))
    left_union = np.zeros((h, w), dtype=bool)
    right_union = np.zeros((h, w), dtype=bool)
    mid = w / 2.0
    for i in range(1, n + 1):
        comp = lab == i
        area = int(comp.sum())
        if area < 0.02 * body.sum():
            continue
        ys, xs = np.nonzero(comp)
        if xs.min() <= 6 or xs.max() >= w - 7 or ys.min() <= 6 or ys.max() >= h - 7:
            continue
        cx = xs.mean()
        if cx < mid:
            left_union |= comp
        else:
            right_union |= comp
    lungs = []
    if left_union.sum() >= 0.05 * body.sum() and right_union.sum() >= 0.05 * body.sum():
        cy_l = np.nonzero(left_union)[1].mean()
        cy_r = np.nonzero(right_union)[1].mean()
        if abs(cy_l - mid) >= 0.14 * w and abs(cy_r - mid) >= 0.14 * w:
            lungs = [left_union, right_union]
    regions: list[dict[str, Any]] = []
    if len(lungs) == 2 and 0 < lungs[0].sum() and lungs[1].sum() and        max(lungs[0].sum(), lungs[1].sum()) < 3.0 * min(lungs[0].sum(), lungs[1].sum()):
        analysis = np.zeros_like(body)
        for comp in lungs:
            ys, xs = np.nonzero(comp)
            analysis[ys.min():ys.max() + 1, xs.min():xs.max() + 1] = True
        yy2, xx2 = np.mgrid[0:h, 0:w]
        analysis &= (np.abs(xx2 - mid) > 0.09 * w)
        analysis &= body
        lung_mode = float(np.median(lum[lungs[0] | lungs[1]]))
        thr = lung_mode + 20.0
        dev = analysis & (lum > thr)
        min_area = 900
        sign_hint = "lung"
    else:
        vals = lum[body]
        hist, edges = np.histogram(vals, bins=48, range=(0, 256))
        centers = (edges[:-1] + edges[1:]) / 2.0
        smooth = ndimage.gaussian_filter1d(hist.astype(float), 2.0)
        peak_ids = [i for i in range(2, len(smooth) - 2)
                    if smooth[i] >= 0.30 * smooth.max()
                    and smooth[i] == max(smooth[i - 2:i + 3])]
        two_mode = False
        if len(peak_ids) >= 2:
            i_lo, i_hi = peak_ids[0], peak_ids[-1]
            if i_hi - i_lo >= 5:
                valley = smooth[i_lo:i_hi + 1].min()
                two_mode = valley < 0.55 * min(smooth[i_lo], smooth[i_hi])
        if two_mode:
            lo, hi = centers[i_lo], centers[i_hi]
            dev_pos = body & (lum > hi + 16.0)
            dev_neg = body & (lum < lo - 16.0)
        else:
            mode = centers[int(hist.argmax())]
            spread = max(14.0, 1.2 * np.percentile(np.abs(vals - mode), 60))
            dev_pos = body & (lum > mode + spread)
            dev_neg = body & (lum < mode - spread)
        sign_hint = "brain"
    raw = []
    struct = np.ones((9, 9))
    if sign_hint == "lung":
        dev = ndimage.binary_closing(dev, np.ones((3, 27)))
        lab2, n2 = ndimage.label(ndimage.binary_opening(dev, struct))
        for i in range(1, n2 + 1):
            comp = lab2 == i
            if comp.sum() < min_area:
                continue
            ys, xs = np.nonzero(comp)
            hh = ys.max() - ys.min() + 1
            ww = xs.max() - xs.min() + 1
            if ww < 34 or comp.sum() < 0.35 * hh * ww:
                continue
            raw.append(("bright", comp, ys, xs, hh, ww))
    else:
        for sign, devx in (("bright", dev_pos), ("dark", dev_neg)):
            lab2, n2 = ndimage.label(ndimage.binary_opening(devx, struct))
            for i in range(1, n2 + 1):
                comp = lab2 == i
                if comp.sum() < 120:
                    continue
                ys, xs = np.nonzero(comp)
                hh = ys.max() - ys.min() + 1
                ww = xs.max() - xs.min() + 1
                if hh > 3 * ww or ww > 3 * hh:
                    continue
                raw.append((sign, comp, ys, xs, hh, ww))
        keep = []
        body_area = float(body.sum())
        for idx, (sign, comp, ys, xs, hh, ww) in enumerate(raw):
            if comp.sum() > 0.32 * body_area:
                continue
            mirrored = comp[:, ::-1]
            cx1 = (xs.min() + xs.max()) / 2.0
            twin = False
            for jdx, (s2, c2, ys2, xs2, hh2, ww2) in enumerate(raw):
                if jdx == idx or s2 != sign:
                    continue
                cx2 = (xs2.min() + xs2.max()) / 2.0
                near_mid = abs(cx1 - mid) < 0.07 * w and abs(cx2 - mid) < 0.07 * w
                y_ov = max(0, min(ys.max(), ys2.max()) - max(ys.min(), ys2.min()) + 1)
                if near_mid and y_ov >= 0.4 * min(hh, hh2):
                    twin = True
                    break
                if not (0.55 <= hh / max(hh2, 1) <= 1.8 and 0.55 <= ww / max(ww2, 1) <= 1.8):
                    continue
                thr_twin = 0.30 if min(int(comp.sum()), int(c2.sum())) < 250 else 0.45
                inter = int((mirrored & c2).sum())
                if inter > thr_twin * min(int(comp.sum()), int(c2.sum())):
                    twin = True
                    break
            if not twin:
                keep.append((sign, comp, ys, xs, hh, ww))
        raw = keep
    raw.sort(key=lambda r: -int(r[1].sum()))
    if sign_hint == "lung":
        whitelist = ("pneumonia", "mass_tumor")
    else:
        whitelist = (("mass_tumor", "hemorrhage") if sign == "bright" else ("infarct", "hemorrhage"))
    for sign, comp, ys, xs, hh, ww in raw[:3]:
        x0 = xs.min() * sx / arr.shape[1]
        y0 = ys.min() * sy / arr.shape[0]
        x1 = (xs.max() + 1) * sx / arr.shape[1]
        y1 = (ys.max() + 1) * sy / arr.shape[0]
        area_pct = round(100.0 * int(comp.sum()) / (h * w), 1)
        label, conf = _crop_classify(arr, x0, y0, x1, y1)
        if label not in whitelist:
            import vision_net as _vn0
            try:
                crop = arr[int(y0 * arr.shape[0]):int(y1 * arr.shape[0]) + 1,
                           int(x0 * arr.shape[1]):int(x1 * arr.shape[1]) + 1]
                from PIL import Image as _I0
                im = _I0.fromarray(np.clip(crop, 0, 255).astype(np.uint8)).resize((48, 48))
                probs = _vn0.predict_proba((np.asarray(im, dtype=np.float64).transpose(2, 0, 1) / 255.0)[None])[0]
                cands = sorted(((probs[_vn0.LABELS_DEEP.index(l)], l) for l in whitelist), reverse=True)
                label, conf = cands[0][1], float(cands[0][0])
            except Exception:
                label, conf = "", 0.0
        if not label or conf < 0.30:
            label = "density_abnormality"
            conf = max(conf, 0.5)
        regions.append({
            "label": label,
            "bbox": (x0, y0, x1, y1),
            "cells": max(1, int(area_pct * GRID * GRID / 100)),
            "area_pct": area_pct,
            "conf": round(min(conf, 0.97), 2),
            "where_fa": _where_words((x0 + x1) / 2, (y0 + y1) / 2, True),
            "where_en": _where_words((x0 + x1) / 2, (y0 + y1) / 2, False),
        })
    return regions


def analyze_image(image_bytes: bytes) -> dict[str, Any]:
    arr = load_image(image_bytes)
    if arr is None or arr.shape[0] < 32 or arr.shape[1] < 32:
        return {"ok": False, "message_fa": "تصویر قابل خواندن نبود."}
    if _is_grayscale(arr):
        try:
            regions = _radiology_regions(arr)
            lab_counts = {}
            for r in regions:
                lab_counts[r["label"]] = lab_counts.get(r["label"], 0) + r["cells"]
            abnormal_cells = sum(r["cells"] for r in regions)
            healthy_pct = round(100.0 * max(0, GRID * GRID - abnormal_cells) / (GRID * GRID), 1)
            luma = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
            blur = float(np.abs(np.diff(luma, axis=1)).mean())
            return {
                "ok": True,
                "regions": regions,
                "healthy_pct": healthy_pct,
                "label_counts": lab_counts,
                "quality": {"edge_sharpness": round(blur, 1),
                            "brightness": round(float(luma.mean()), 0)},
                "grid": GRID,
            }
        except Exception:
            regions = []
            feats, gh, gw = cell_features(arr)
            pred, conf = predict_cells(feats)
            regions = _regions(pred, conf, GRID)
    else:
        feats, gh, gw = cell_features(arr)
        pred, conf = predict_cells(feats)
        regions = _regions(pred, conf, GRID)
        try:
            import vision_net as _vn
            if _vn.available():
                for r in regions:
                    if r["label"] in ("lesion", "bruise", "burn", "granulation") and r["area_pct"] <= 25.0:
                        lab2, conf2 = _crop_classify(arr, *r["bbox"])
                        if lab2 in ("nevus", "melanoma_susp") and conf2 >= 0.45:
                            r["label"] = lab2
                            r["conf"] = round(max(r["conf"], conf2), 2)
                if not any(r["label"] in ("nevus", "melanoma_susp") for r in regions):
                    hit = _mole_scan(arr)
                    if hit:
                        regions.insert(0, hit)
                        regions = regions[:4]
        except Exception:
            pass
    lab_counts: dict[str, int] = {}
    for p in pred:
        lab_counts[LABELS[int(p)]] = lab_counts.get(LABELS[int(p)], 0) + 1
    abnormal_cells = sum(v for k, v in lab_counts.items() if k in ABNORMAL)
    for r in regions:
        pass
    healthy_pct = round(100.0 * max(0, GRID * GRID - sum(r["cells"] for r in regions)) / (GRID * GRID), 1)
    luma = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
    blur = float(np.abs(np.diff(luma, axis=1)).mean())
    return {
        "ok": True,
        "regions": regions,
        "healthy_pct": healthy_pct,
        "label_counts": lab_counts,
        "quality": {"edge_sharpness": round(blur, 1),
                    "brightness": round(float(luma.mean()), 0)},
        "grid": GRID,
    }
