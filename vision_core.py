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


def analyze_image(image_bytes: bytes) -> dict[str, Any]:
    arr = load_image(image_bytes)
    if arr is None or arr.shape[0] < 32 or arr.shape[1] < 32:
        return {"ok": False, "message_fa": "تصویر قابل خواندن نبود."}
    feats, gh, gw = cell_features(arr)
    pred, conf = predict_cells(feats)
    regions = _regions(pred, conf, GRID)
    lab_counts: dict[str, int] = {}
    for p in pred:
        lab_counts[LABELS[int(p)]] = lab_counts.get(LABELS[int(p)], 0) + 1
    abnormal_cells = sum(v for k, v in lab_counts.items() if k in ABNORMAL)
    healthy_pct = round(100.0 * (GRID * GRID - abnormal_cells) / (GRID * GRID), 1)
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
