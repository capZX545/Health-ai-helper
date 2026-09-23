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
            counts = np.bincount(block, minlength=16)
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


import vision_net as _vn_mod
DLAB = {n: i for i, n in enumerate(_vn_mod.LABELS_DEEP)}
_OLD2DEEP = None


def _to_deep(mask, fam):
    global _OLD2DEEP
    if fam in ("skin", "wound", "retina"):
        if _OLD2DEEP is None:
            _OLD2DEEP = {LAB[x]: DLAB[x] for x in vc.LABELS if x in DLAB}
        out = np.zeros_like(mask)
        for old_id, deep_id in _OLD2DEEP.items():
            out[mask == old_id] = deep_id
        return out
    return mask


def _ellipse(h, w, cy, cx, ry, rx):
    yy, xx = np.mgrid[0:h, 0:w]
    return (((yy - cy) / ry) ** 2 + ((xx - cx) / rx) ** 2) < 1.0


def gen_ct_head(rnd, kind="healthy"):
    h = w = IMG
    img = np.ones((h, w, 3)) * 8.0
    yy, xx = np.mgrid[0:h, 0:w]
    head = _ellipse(h, w, 128, 128, 96, 108)
    skull = _ellipse(h, w, 128, 128, 96, 108) & (~_ellipse(h, w, 128, 128, 89, 101))
    scalp = _ellipse(h, w, 128, 128, 103, 115) & (~_ellipse(h, w, 128, 128, 96, 108))
    brain = _ellipse(h, w, 128, 128, 89, 101)
    img[head] = 30.0
    img[brain] = rnd.uniform(96, 110)
    img[skull] = rnd.uniform(190, 225)
    img[scalp] = rnd.uniform(50, 70)
    gyri = (np.sin(xx / 7.0 + rnd.uniform(0, 6)) * np.cos(yy / 6.0 + rnd.uniform(0, 6)) * 4.0)
    img[brain] += gyri[brain][:, None]
    vl = _ellipse(h, w, 124, 112, 16, 10)
    vr = _ellipse(h, w, 124, 144, 16, 10)
    img[vl | vr] = rnd.uniform(35, 55)
    img += _noise(rnd, h, w, 3.5)
    mask = np.zeros((h, w), dtype=int)
    mask[~head] = DLAB["dark_bg"]
    if kind == "tumor":
        cy = rnd.uniform(95, 165)
        cx = rnd.uniform(75, 180)
        m = _blob_mask(h, w, cy, cx, rnd.uniform(17, 33), rnd.uniform(17, 33), rnd) & brain
        m &= ~((yy > cy + 60) | (yy < cy - 60))
        img[m] = img[m] * 0.35 + rnd.uniform(135, 160) * 0.65
        mask[m] = DLAB["mass_tumor"]
    elif kind == "hemorrhage":
        cy = rnd.uniform(100, 160)
        cx = rnd.uniform(90, 170)
        m = _blob_mask(h, w, cy, cx, rnd.uniform(10, 20), rnd.uniform(10, 20), rnd) & brain
        img[m] = img[m] * 0.25 + rnd.uniform(175, 205) * 0.75
        mask[m] = DLAB["hemorrhage"]
    elif kind == "infarct":
        side = 0 if rnd.random() < 0.5 else 1
        ang = rnd.uniform(-0.7, 0.7) + (0 if side else np.pi)
        cy = 128 + 62 * np.sin(ang)
        cx = 128 + 66 * np.cos(ang)
        yy2, xx2 = np.mgrid[0:h, 0:w]
        vec_a = np.arctan2(yy2 - cy, xx2 - cx)
        dist = np.sqrt((yy2 - cy) ** 2 + (xx2 - cx) ** 2)
        wedge = (np.abs(((vec_a - ang + np.pi) % (2 * np.pi)) - np.pi) < 0.5) & (dist < 58) & brain
        img[wedge] = img[wedge] * 0.3 + rnd.uniform(60, 78) * 0.7
        mask[wedge] = DLAB["infarct"]
    return img, mask


def gen_mri_brain(rnd, kind="healthy"):
    h = w = IMG
    img = np.ones((h, w, 3)) * 6.0
    head = _ellipse(h, w, 128, 128, 98, 108)
    skull = _ellipse(h, w, 128, 128, 98, 108) & (~_ellipse(h, w, 128, 128, 90, 100))
    scalp = _ellipse(h, w, 128, 128, 105, 115) & (~_ellipse(h, w, 128, 128, 98, 108))
    brain = _ellipse(h, w, 128, 128, 90, 100)
    wm = _ellipse(h, w, 128, 128, 62, 72)
    img[head] = 20.0
    img[brain] = rnd.uniform(98, 108)
    img[wm] = rnd.uniform(125, 140)
    img[skull] = rnd.uniform(10, 22)
    img[scalp] = rnd.uniform(140, 165)
    vl = _ellipse(h, w, 124, 112, 17, 10)
    vr = _ellipse(h, w, 124, 144, 17, 10)
    img[vl | vr] = rnd.uniform(165, 185)
    img += _noise(rnd, h, w, 3.0)
    mask = np.zeros((h, w), dtype=int)
    mask[~head] = DLAB["dark_bg"]
    if kind == "tumor":
        cy = rnd.uniform(95, 165)
        cx = rnd.uniform(80, 175)
        core = _blob_mask(h, w, cy, cx, rnd.uniform(13, 24), rnd.uniform(13, 24), rnd) & brain
        halo = _blob_mask(h, w, cy, cx, rnd.uniform(26, 40), rnd.uniform(26, 40), rnd) & brain & (~core)
        img[core] = img[core] * 0.2 + rnd.uniform(195, 225) * 0.8
        img[halo] = img[halo] * 0.45 + rnd.uniform(150, 170) * 0.55
        mask[core] = DLAB["mass_tumor"]
        mask[halo] = DLAB["mass_tumor"]
    elif kind == "infarct":
        ang = rnd.uniform(-0.7, 0.7) + (0 if rnd.random() < 0.5 else np.pi)
        cy = 128 + 60 * np.sin(ang)
        cx = 128 + 64 * np.cos(ang)
        yy2, xx2 = np.mgrid[0:h, 0:w]
        vec_a = np.arctan2(yy2 - cy, xx2 - cx)
        dist = np.sqrt((yy2 - cy) ** 2 + (xx2 - cx) ** 2)
        wedge = (np.abs(((vec_a - ang + np.pi) % (2 * np.pi)) - np.pi) < 0.55) & (dist < 55) & brain
        img[wedge] = img[wedge] * 0.35 + rnd.uniform(160, 180) * 0.65
        mask[wedge] = DLAB["infarct"]
    elif kind == "hemorrhage":
        cy = rnd.uniform(100, 160)
        cx = rnd.uniform(90, 170)
        m = _blob_mask(h, w, cy, cx, rnd.uniform(9, 18), rnd.uniform(9, 18), rnd) & brain
        img[m] = img[m] * 0.3 + rnd.uniform(60, 80) * 0.7
        mask[m] = DLAB["hemorrhage"]
    return img, mask


def gen_chest(rnd, kind="healthy"):
    h = w = IMG
    img = np.full((h, w, 3), rnd.uniform(60, 75))
    yy, xx = np.mgrid[0:h, 0:w]
    rib = (np.sin(xx / 13.0 + rnd.uniform(0, 1)) > 0.78).astype(float)
    img += rib[..., None] * rnd.uniform(45, 65)
    spine = (np.abs(xx - 128) < 14) & (yy > 40)
    img[spine] += rnd.uniform(50, 70)
    lung = (((xx > 30) & (xx < 115)) | ((xx > 141) & (xx < 226))) & (yy > 50) & (yy < 205)
    img[lung] -= rnd.uniform(25, 35)
    img += _noise(rnd, h, w, 4.0)
    mask = np.zeros((h, w), dtype=int)
    border = (xx < 14) | (xx > w - 14) | (yy < 12) | (yy > h - 12)
    mask[border] = DLAB["dark_bg"]
    img[border] *= 0.3
    if kind == "pneumonia":
        cx = rnd.uniform(50, 110) if rnd.random() < 0.5 else rnd.uniform(146, 206)
        cy = rnd.uniform(90, 175)
        m = _blob_mask(h, w, cy, cx, rnd.uniform(28, 48), rnd.uniform(28, 48), rnd) & lung
        img[m] += rnd.uniform(34, 50)
        mask[m] = DLAB["pneumonia"]
    elif kind == "mass":
        cx = rnd.uniform(55, 105) if rnd.random() < 0.5 else rnd.uniform(150, 200)
        cy = rnd.uniform(95, 165)
        m = _blob_mask(h, w, cy, cx, rnd.uniform(18, 32), rnd.uniform(18, 32), rnd, harmonics=6) & lung
        img[m] += rnd.uniform(48, 66)
        mask[m] = DLAB["mass_tumor"]
    elif kind == "fracture":
        rib_y = int(rnd.choice([70, 105, 140, 175]))
        seg = (np.abs(yy - rib_y) < 5) & (xx > 150) & (xx < 230)
        img[seg] += rnd.uniform(45, 60)
        gap_x = int(rnd.uniform(165, 215))
        gap = (np.abs(yy - rib_y) < 5) & (np.abs(xx - gap_x) < rnd.uniform(2, 3.5))
        img[gap] *= 0.35
        mask[(np.abs(yy - rib_y) < 8) & (np.abs(xx - gap_x) < 12)] = DLAB["fracture"]
    return img, mask


def gen_skin_mole(rnd, kind):
    h = w = IMG
    yy, xx = np.mgrid[0:h, 0:w]
    base = rnd.uniform(150, 205, 3)
    arr = np.ones((h, w, 3)) * base + np.linspace(-12, 12, w)[None, :, None]
    arr += _noise(rnd, h, w)
    mask = np.zeros((h, w), dtype=int)
    cy = rnd.uniform(75, 180)
    cx = rnd.uniform(75, 180)
    if kind == "nevus":
        m = _ellipse(h, w, cy, cx, rnd.uniform(9, 17), rnd.uniform(9, 17))
        tone = np.array([rnd.uniform(120, 150), rnd.uniform(85, 110), rnd.uniform(65, 90)])
        arr[m] = arr[m] * 0.3 + tone * 0.7
        mask[m] = DLAB["nevus"]
    else:
        m = _blob_mask(h, w, cy, cx, rnd.uniform(17, 30), rnd.uniform(15, 28), rnd, harmonics=6)
        tone = np.array([rnd.uniform(55, 90), rnd.uniform(35, 60), rnd.uniform(28, 50)])
        arr[m] = arr[m] * 0.25 + tone * 0.75
        speck = m & (np.sin(xx * 0.9 + yy * 0.7) > 0.55)
        arr[speck] *= 0.55
        rim = m & (~_blob_mask(h, w, cy, cx, 10, 10, rnd))
        arr[rim & (np.sin(xx * 0.4) > 0.7)] = arr[rim & (np.sin(xx * 0.4) > 0.7)] * 0.5 + np.array([150, 60, 55]) * 0.5
        mask[m] = DLAB["melanoma_susp"]
    return arr, mask


DEEP_FAMILIES = [
    ("skin", "healthy"), ("skin", "lesion"), ("skin", "bruise"), ("skin", "burn"),
    ("mole", "nevus"), ("mole", "melanoma_susp"),
    ("wound", None), ("chest", "healthy"), ("chest", "pneumonia"), ("chest", "mass"),
    ("chest", "fracture"), ("ct", "healthy"), ("ct", "tumor"), ("ct", "hemorrhage"),
    ("ct", "infarct"), ("mri", "healthy"), ("mri", "tumor"), ("mri", "hemorrhage"),
    ("mri", "infarct"), ("retina", "healthy"), ("retina", "exudate"), ("retina", "hemorrhage"),
]


def gen_deep(rnd, fam, kind):
    if fam == "skin":
        return gen_skin(rnd, kind)
    if fam == "mole":
        return gen_skin_mole(rnd, kind)
    if fam == "wound":
        return gen_wound(rnd)
    if fam == "chest":
        return gen_chest(rnd, kind)
    if fam == "ct":
        return gen_ct_head(rnd, kind)
    if fam == "mri":
        return gen_mri_brain(rnd, kind)
    return gen_retina(rnd, kind)


def patch_label(mask: np.ndarray, abn_ids) -> int:
    block = mask.ravel()
    counts = np.bincount(block, minlength=16)
    share = counts / counts.sum()
    abnormal_share = sum(share[k] for k in abn_ids)
    if abnormal_share >= 0.25:
        return int(max((k for k in abn_ids), key=lambda k: counts[k]))
    return int(counts.argmax())


def build_patch_dataset(n_per=24, patch=48, seed=SEED, n_patches=10):
    import vision_net as vn
    rnd = np.random.default_rng(seed)
    abn_ids = [vn.LABELS_DEEP.index(x) for x in vn.ABNORMAL_DEEP]
    lab16 = {n: i for i, n in enumerate(vn.LABELS_DEEP)}
    X, y = [], []
    for fam, kind in DEEP_FAMILIES:
        for _ in range(n_per):
            arr, mask = gen_deep(rnd, fam, kind)
            mask = _to_deep(mask, fam)
            h, w = mask.shape
            ys, xs = np.nonzero(mask >= 0)
            abn_ys, abn_xs = np.nonzero(np.isin(mask, abn_ids))
            picks = []
            if len(abn_ys):
                for _ in range(n_patches * 3 // 4):
                    i = int(rnd.integers(0, len(abn_ys)))
                    picks.append((int(abn_ys[i]), int(abn_xs[i])))
            while len(picks) < n_patches:
                i = int(rnd.integers(0, len(ys)))
                picks.append((int(ys[i]), int(xs[i])))
            for cy, cx in picks:
                y0 = int(np.clip(cy - patch // 2, 0, h - patch))
                x0 = int(np.clip(cx - patch // 2, 0, w - patch))
                win = np.clip(arr[y0:y0 + patch, x0:x0 + patch], 0, 255) / 255.0
                X.append(win.transpose(2, 0, 1))
                y.append(patch_label(mask[y0:y0 + patch, x0:x0 + patch], abn_ids))
    X = np.asarray(X, dtype=np.float32)
    y = np.asarray(y)
    return X, y


def train_cnn(epochs=45, batch=64, lr=0.007, seed=SEED):
    import vision_net as vn
    X, y = build_patch_dataset(seed=seed)
    print("patches:", X.shape, "classes used:", len(np.unique(y)), flush=True)
    net = vn.Net(len(vn.LABELS_DEEP), seed=seed)
    rnd = np.random.default_rng(seed + 1)
    n = len(y)
    counts = np.bincount(y, minlength=len(vn.LABELS_DEEP)).astype(float)
    inv = 1.0 / np.maximum(counts, 1.0)
    w_cls = (inv / inv.sum()) * len(vn.LABELS_DEEP)
    w_cls = w_cls ** 0.6
    for ep in range(epochs):
        order = rnd.permutation(n)
        for i0 in range(0, n, batch):
            idx = order[i0:i0 + batch]
            xb = np.array(X[idx], dtype=np.float64)
            flip = rnd.random(len(idx)) < 0.5
            xb = np.where(flip[:, None, None, None], xb[:, :, :, ::-1], xb)
            gain = rnd.uniform(0.85, 1.15, (len(idx), 1, 1, 1))
            bias = rnd.uniform(-0.08, 0.08, (len(idx), 1, 1, 1))
            xb = np.clip(xb * gain + bias, 0, 1)
            probs, cache = net.forward(xb)
            g = net.backward(probs, y[idx], cache, sample_w=w_cls[y[idx]])
            net.adam(g, lr=lr * (0.95 ** ep))
        acc, lss = chunk_eval(net, X, y)
        print(f"epoch {ep + 1}/{epochs} loss {lss:.4f} train-acc {acc:.4f}", flush=True)
    return net, X, y


def chunk_eval(net, X, y, chunk=384):
    acc_sum = 0.0
    loss_sum = 0.0
    n = len(y)
    for i0 in range(0, n, chunk):
        pr, _ = net.forward(X[i0:i0 + chunk])
        acc_sum += float((pr.argmax(1) == y[i0:i0 + chunk]).sum())
        loss_sum += float(-np.log(np.clip(pr[np.arange(len(y[i0:i0 + chunk])), y[i0:i0 + chunk]], 1e-9, 1)).sum())
    return acc_sum / n, loss_sum / n


def eval_cnn(net, seed=SEED + 4242):
    Xv, yv = build_patch_dataset(n_per=10, seed=seed, n_patches=10)
    acc, _ = chunk_eval(net, Xv, yv)
    return acc, Xv, yv


def main_cnn():
    import vision_net as vn
    net, X, y = train_cnn()
    acc, _, _ = eval_cnn(net)
    print("held-out patch acc:", round(float(acc), 4))
    vn.save(net)
    size = os.path.getsize(vn.CNN_PATH)
    print("cnn exported:", round(size / 1e6, 2), "MB")
    return 0


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
    import sys as _sys
    if "--cnn" in _sys.argv:
        raise SystemExit(main_cnn())
    raise SystemExit(main())
