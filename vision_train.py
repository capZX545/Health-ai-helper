"""
vision_train.py — trains the internal vision model. Generates a seeded
synthetic dataset (skin with lesions/bruises/burns, wound beds with
granulation/slough/eschar, radiographs with and without opacity, retinas
with exudates/hemorrhages), extracts the exact same grid-cell features the
runtime uses, trains a random forest with scikit-learn and exports it to a
pure-JSON gzip (vision_model.json.gz) so the app never depends on the
sklearn version at runtime. Run:  python vision_train.py
"""
from __future__ import annotations

import gzip
import json
import os

import numpy as np

import vision_core as vc

SEED = 20770
IMG = 256
LAB = {n: i for i, n in enumerate(vc.LABELS)}


def _noise(rnd, h, w, s=6.0):
    return rnd.normal(0, s, (h, w, 3))


def _blob_mask(h, w, cy, cx, ry, rx, rnd, harmonics=4):
    yy, xx = np.mgrid[0:h, 0:w]
    ang = np.arctan2((yy - cy) / max(ry, 1), (xx - cx) / max(rx, 1))
    rr = np.sqrt(((yy - cy) / max(ry, 1)) ** 2 + ((xx - cx) / max(rx, 1)) ** 2)
    wob = np.zeros_like(rr)
    for k in range(2, harmonics + 2):
        wob += (rnd.uniform(0.05, 0.16) / k) * np.sin(k * ang + rnd.uniform(0, 6.28))
    return rr + wob < 1.0


def gen_skin(rnd, kind="healthy"):
    h = w = IMG
    base = rnd.uniform(150, 205, 3)
    arr = np.ones((h, w, 3)) * base
    grad = np.linspace(-14, 14, w)[None, :, None]
    arr += grad
    arr += _noise(rnd, h, w)
    mask = np.zeros((h, w), dtype=int)
    if kind == "healthy":
        return arr, mask
    cy = rnd.uniform(70, 185)
    cx = rnd.uniform(70, 185)
    ry = rnd.uniform(26, 58)
    rx = ry * rnd.uniform(0.75, 1.25)
    m = _blob_mask(h, w, cy, cx, ry, rx, rnd)
    if kind == "lesion":
        tone = np.array([rnd.uniform(90, 150), rnd.uniform(50, 90), rnd.uniform(50, 85)])
        arr[m] = arr[m] * 0.35 + tone * 0.65
        label = LAB["lesion"]
    elif kind == "bruise":
        tone = np.array([rnd.uniform(90, 130), rnd.uniform(60, 95), rnd.uniform(120, 165)])
        arr[m] = arr[m] * 0.45 + tone * 0.55
        label = LAB["bruise"]
    else:
        tone = np.array([rnd.uniform(200, 240), rnd.uniform(70, 105), rnd.uniform(70, 100)])
        arr[m] = arr[m] * 0.4 + tone * 0.6
        arr[m & (np.mgrid[0:h, 0:w][1] % 3 == 0)] *= 0.88
        label = LAB["burn"]
    mask[m] = label
    return arr, mask


def gen_wound(rnd):
    h = w = IMG
    arr = np.ones((h, w, 3)) * np.array([rnd.uniform(155, 205)] * 3)
    arr += _noise(rnd, h, w)
    mask = np.zeros((h, w), dtype=int)
    cy = rnd.uniform(85, 170)
    cx = rnd.uniform(85, 170)
    ry = rnd.uniform(42, 70)
    m = _blob_mask(h, w, cy, cx, ry, ry * rnd.uniform(0.8, 1.2), rnd)
    gran = np.array([rnd.uniform(185, 225), rnd.uniform(60, 95), rnd.uniform(65, 95)])
    arr[m] = gran + _noise(rnd, int(m.sum()) or 1, 1, 9).reshape(-1, 3)[:m.sum()]
    mask[m] = LAB["granulation"]
    n = rnd.integers(1, 4)
    for _ in range(n):
        sy = rnd.uniform(cy - ry * 0.7, cy + ry * 0.7)
        sx = rnd.uniform(cx - ry * 0.7, cx + ry * 0.7)
        sm = _blob_mask(h, w, sy, sx, rnd.uniform(12, 26), rnd.uniform(12, 26), rnd) & m
        if kind_r := (rnd.random() < 0.75):
            arr[sm] = arr[sm] * 0.2 + np.array([rnd.uniform(195, 235), rnd.uniform(165, 205), rnd.uniform(70, 110)]) * 0.8
            mask[sm] = LAB["slough"]
        else:
            arr[sm] = np.array([rnd.uniform(35, 65), rnd.uniform(25, 50), rnd.uniform(25, 50)])
            mask[sm] = LAB["eschar"]
    return arr, mask


def gen_radiograph(rnd, with_opacity):
    h = w = IMG
    arr = np.full((h, w, 3), rnd.uniform(70, 95))
    yy, xx = np.mgrid[0:h, 0:w]
    ribs = (np.sin(xx / 14.0) > 0.72).astype(float)
    arr += ribs[..., None] * rnd.uniform(45, 70)
    lung = (((xx > 34) & (xx < 118)) | ((xx > 138) & (xx < 222))) & (yy > 52) & (yy < 200)
    arr[lung] -= rnd.uniform(28, 40)
    arr += _noise(rnd, h, w, 5.0)
    mask = np.zeros((h, w), dtype=int)
    border = (xx < 16) | (xx > w - 16) | (yy < 14) | (yy > h - 14)
    mask[border] = LAB["dark_bg"]
    arr[border] *= 0.25
    if with_opacity:
        cx = rnd.uniform(45, 210)
        cy = rnd.uniform(70, 180)
        m = _blob_mask(h, w, cy, cx, rnd.uniform(20, 44), rnd.uniform(20, 44), rnd) & lung
        arr[m] += rnd.uniform(38, 62)
        mask[m] = LAB["opacity"]
    return arr, mask


def gen_retina(rnd, kind):
    h = w = IMG
    arr = np.zeros((h, w, 3))
    yy, xx = np.mgrid[0:h, 0:w]
    fund = (((yy - 128) / 105.0) ** 2 + ((xx - 128) / 105.0) ** 2) < 1.0
    arr[fund] = np.array([rnd.uniform(115, 150), rnd.uniform(45, 70), rnd.uniform(45, 70)])
    arr += _noise(rnd, h, w, 5.0)
    mask = np.zeros((h, w), dtype=int)
    mask[fund] = LAB["healthy"]
    mask[~fund] = LAB["dark_bg"]
    if kind == "exudate":
        for _ in range(rnd.integers(3, 7)):
            cy = rnd.uniform(70, 186)
            cx = rnd.uniform(70, 186)
            m = _blob_mask(h, w, cy, cx, rnd.uniform(8, 16), rnd.uniform(8, 16), rnd) & fund
            arr[m] = np.array([rnd.uniform(225, 250), rnd.uniform(205, 235), rnd.uniform(140, 185)])
            mask[m] = LAB["exudate"]
    elif kind == "hemorrhage":
        for _ in range(rnd.integers(2, 5)):
            cy = rnd.uniform(70, 186)
            cx = rnd.uniform(70, 186)
            m = _blob_mask(h, w, cy, cx, rnd.uniform(10, 24), rnd.uniform(10, 24), rnd) & fund
            arr[m] = np.array([rnd.uniform(55, 85), rnd.uniform(15, 35), rnd.uniform(15, 35)])
            mask[m] = LAB["hemorrhage"]
    return arr, mask


def cell_labels(mask: np.ndarray, grid: int) -> list[int]:
    h, w = mask.shape
    gh, gw = h // grid, w // grid
    abn = {LAB[x] for x in vc.ABNORMAL}
    out = []
    for i in range(grid):
        for j in range(grid):
            block = mask[i * gh:(i + 1) * gh, j * gw:(j + 1) * gw].ravel()
            if block.size == 0:
                out.append(LAB["healthy"])
                continue
            counts = np.bincount(block, minlength=len(vc.LABELS))
            share = counts / counts.sum()
            abnormal_share = sum(share[k] for k in abn if k < len(share))
            if abnormal_share >= 0.25:
                best = max((k for k in abn if k < len(share)), key=lambda k: counts[k])
                out.append(int(best))
            else:
                out.append(int(counts.argmax()))
    return out


def build_dataset(n_per=45, seed=SEED, grid=vc.GRID):
    rnd = np.random.default_rng(seed)
    X, y = [], []
    kinds = [("skin", "healthy"), ("skin", "lesion"), ("skin", "bruise"), ("skin", "burn"),
             ("wound", None), ("rad", True), ("rad", False),
             ("retina", "healthy"), ("retina", "exudate"), ("retina", "hemorrhage")]
    for fam, kind in kinds:
        for _ in range(n_per):
            if fam == "skin":
                arr, mask = gen_skin(rnd, kind)
            elif fam == "wound":
                arr, mask = gen_wound(rnd)
            elif fam == "rad":
                arr, mask = gen_radiograph(rnd, kind)
            else:
                arr, mask = gen_retina(rnd, kind)
            feats, _, _ = vc.cell_features(np.clip(arr, 0, 255), grid)
            X.append(feats)
            y.extend(cell_labels(mask, grid))
    return np.vstack(X), np.asarray(y)


def export_json(model, path):
    trees = []
    for est in model.estimators_:
        t = est.tree_

        def walk(i):
            if t.children_left[i] == -1:
                return {"leaf": int(t.value[i].argmax())}
            return {"f": int(t.feature[i]), "t": float(t.threshold[i]),
                    "l": walk(t.children_left[i]), "r": walk(t.children_right[i])}
        trees.append(walk(0))
    data = {"classes": vc.LABELS, "trees": trees}
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))


def main():
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, f1_score
    X, y = build_dataset()
    print("samples:", X.shape[0], "features:", X.shape[1])
    model = RandomForestClassifier(n_estimators=120, max_depth=15,
                                   min_samples_leaf=4, class_weight="balanced",
                                   random_state=SEED, n_jobs=-1)
    model.fit(X, y)
    pred = model.predict(X)
    print("train acc:", round(accuracy_score(y, pred), 4))
    Xv, yv = build_dataset(n_per=14, seed=SEED + 999)
    pv = model.predict(Xv)
    print("held-out acc:", round(accuracy_score(yv, pv), 4))
    print("held-out macro F1:", round(f1_score(yv, pv, average="macro"), 4))
    export_json(model, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vision_model.json.gz"))
    size = os.path.getsize(os.path.join(os.path.dirname(os.path.abspath(__file__)), "vision_model.json.gz"))
    print("model exported:", round(size / 1e6, 2), "MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
