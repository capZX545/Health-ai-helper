"""
vision_net.py — a real convolutional neural network in pure NumPy:
conv3x3-relu-pool x3 + global-average-pool + fc-softmax, Adam optimizer.
Trained by vision_train.py on the synthetic medical corpus (skin, wounds,
X-ray, CT, MRI, retina) and exported to vision_cnn.json.gz. Runtime
inference needs only NumPy, so the same weights run on Windows, Android
and the web build with identical results.
"""
from __future__ import annotations

import gzip
import json
import os
from typing import Any

import numpy as np

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
CNN_PATH = os.path.join(DATA_DIR, "vision_cnn.json.gz")

LABELS_DEEP = ["healthy", "nevus", "melanoma_susp", "lesion", "bruise", "burn",
               "granulation", "slough", "eschar", "mass_tumor", "pneumonia",
               "fracture", "exudate", "hemorrhage", "infarct", "dark_bg"]
ABNORMAL_DEEP = {"nevus", "melanoma_susp", "lesion", "bruise", "burn", "granulation",
                 "slough", "eschar", "mass_tumor", "pneumonia", "fracture",
                 "exudate", "hemorrhage", "infarct"}
URGENT_DEEP = {"melanoma_susp", "mass_tumor", "pneumonia", "fracture",
               "hemorrhage", "eschar", "exudate", "burn", "infarct"}


def im2col(x: np.ndarray, kh: int, kw: int, stride: int, pad: int):
    if pad:
        x = np.pad(x, ((0, 0), (0, 0), (pad, pad), (pad, pad)))
    n, c, h, w = x.shape
    oh = (h - kh) // stride + 1
    ow = (w - kw) // stride + 1
    cols = np.empty((n, c * kh * kw, oh * ow), dtype=x.dtype)
    idx = 0
    for i in range(kh):
        for j in range(kw):
            cols[:, idx * c:(idx + 1) * c, :] = \
                x[:, :, i:i + oh * stride:stride, j:j + ow * stride:stride].reshape(n, c, oh * ow)
            idx += 1
    return cols, (oh, ow)


def col2im(dcols: np.ndarray, x_shape, kh: int, kw: int, stride: int, pad: int) -> np.ndarray:
    n, c, h, w = x_shape
    hp, wp = h + 2 * pad, w + 2 * pad
    dx = np.zeros((n, c, hp, wp), dtype=dcols.dtype)
    oh = (hp - kh) // stride + 1
    ow = (wp - kw) // stride + 1
    idx = 0
    for i in range(kh):
        for j in range(kw):
            g = dcols[:, idx * c:(idx + 1) * c, :].reshape(n, c, oh, ow)
            dx[:, :, i:i + oh * stride:stride, j:j + ow * stride:stride] += g
            idx += 1
    if pad:
        return dx[:, :, pad:pad + h, pad:pad + w]
    return dx


def _pool2(a: np.ndarray) -> np.ndarray:
    n, c, h, w = a.shape
    return a.reshape(n, c, h // 2, 2, w // 2, 2).max(axis=(3, 5))


def _pool2_back(da: np.ndarray, a: np.ndarray) -> np.ndarray:
    n, c, h, w = a.shape
    dh, dw = da.shape[2], da.shape[3]
    ar = a.reshape(n, c, dh, 2, dw, 2)
    mask = (ar == ar.max(axis=(3, 5), keepdims=True))
    grad = da.reshape(n, c, dh, 1, dw, 1) * mask
    return grad.reshape(n, c, h, w)


class Net:
    def __init__(self, k: int, seed: int = 2077):
        rng = np.random.default_rng(seed)
        self.k = k
        self.p: dict[str, np.ndarray] = {
            "W1": rng.normal(0, 0.09, (8, 27)),
            "b1": np.zeros(8),
            "W2": rng.normal(0, 0.07, (16, 72)),
            "b2": np.zeros(16),
            "W3": rng.normal(0, 0.05, (32, 144)),
            "b3": np.zeros(32),
            "W4": rng.normal(0, 0.06, (k, 32)),
            "b4": np.zeros(k),
        }
        self.m = {kk: np.zeros_like(v) for kk, v in self.p.items()}
        self.v = {kk: np.zeros_like(v) for kk, v in self.p.items()}
        self.t = 0

    def forward(self, x: np.ndarray):
        n = x.shape[0]
        c1, s1 = im2col(x, 3, 3, 1, 1)
        z1 = self.p["W1"] @ c1 + self.p["b1"][:, None]
        a1 = np.maximum(z1, 0)
        r1 = a1.reshape(n, 8, *s1)
        p1 = _pool2(r1)
        c2, s2 = im2col(p1, 3, 3, 1, 1)
        z2 = self.p["W2"] @ c2 + self.p["b2"][:, None]
        a2 = np.maximum(z2, 0)
        r2 = a2.reshape(n, 16, *s2)
        p2 = _pool2(r2)
        c3, s3 = im2col(p2, 3, 3, 1, 1)
        z3 = self.p["W3"] @ c3 + self.p["b3"][:, None]
        a3 = np.maximum(z3, 0)
        r3 = a3.reshape(n, 32, *s3)
        p3 = _pool2(r3)
        gap = p3.mean(axis=(2, 3))
        z4 = gap @ self.p["W4"].T + self.p["b4"]
        z4 = z4 - z4.max(axis=1, keepdims=True)
        e = np.exp(z4)
        probs = e / e.sum(axis=1, keepdims=True)
        cache = (x, c1, s1, a1, r1, p1, c2, s2, a2, r2, p2, c3, s3, a3, r3, p3, gap, probs)
        return probs, cache

    def backward(self, probs, y, cache, sample_w=None):
        (x, c1, s1, a1, r1, p1, c2, s2, a2, r2, p2, c3, s3, a3, r3, p3, gap, _) = cache
        n = x.shape[0]
        g: dict[str, np.ndarray] = {}
        dz4 = probs.copy()
        dz4[np.arange(n), y] -= 1.0
        if sample_w is not None:
            dz4 = dz4 * (sample_w / max(float(sample_w.mean()), 1e-8))[:, None]
        dz4 /= n
        g["W4"] = dz4.T @ gap
        g["b4"] = dz4.sum(axis=0)
        dgap = dz4 @ self.p["W4"]
        dp3 = np.repeat(dgap[:, :, None, None], p3.shape[2] * p3.shape[3], axis=2).reshape(p3.shape)
        dp3 = dp3 / (p3.shape[2] * p3.shape[3])
        dr3 = _pool2_back(dp3, r3)
        dz3flat = (dr3 * (r3 > 0)).reshape(n, 32, -1)
        g["W3"] = np.zeros_like(self.p["W3"])
        for i in range(n):
            g["W3"] += dz3flat[i] @ c3[i].T
        g["b3"] = dz3flat.sum(axis=(0, 2))
        dc3 = (self.p["W3"].T @ dz3flat)
        dp2 = col2im(dc3, p2.shape, 3, 3, 1, 1)
        dr2 = _pool2_back(dp2, r2)
        dz2flat = (dr2 * (r2 > 0)).reshape(n, 16, -1)
        g["W2"] = np.zeros_like(self.p["W2"])
        for i in range(n):
            g["W2"] += dz2flat[i] @ c2[i].T
        g["b2"] = dz2flat.sum(axis=(0, 2))
        dc2 = (self.p["W2"].T @ dz2flat)
        dp1 = col2im(dc2, p1.shape, 3, 3, 1, 1)
        dr1 = _pool2_back(dp1, r1)
        dz1flat = (dr1 * (r1 > 0)).reshape(n, 8, -1)
        g["W1"] = np.zeros_like(self.p["W1"])
        for i in range(n):
            g["W1"] += dz1flat[i] @ c1[i].T
        g["b1"] = dz1flat.sum(axis=(0, 2))
        return g

    def adam(self, g, lr=0.002, beta1=0.9, beta2=0.999, wd=1e-5):
        self.t += 1
        for kk in self.p:
            grad = g[kk] + wd * self.p[kk]
            self.m[kk] = beta1 * self.m[kk] + (1 - beta1) * grad
            self.v[kk] = beta2 * self.v[kk] + (1 - beta2) * (grad ** 2)
            mh = self.m[kk] / (1 - beta1 ** self.t)
            vh = self.v[kk] / (1 - beta2 ** self.t)
            self.p[kk] -= lr * mh / (np.sqrt(vh) + 1e-8)

    def loss(self, probs, y):
        return float(-np.log(np.clip(probs[np.arange(len(y)), y], 1e-9, 1)).mean())


def save(net: Net, path: str = CNN_PATH) -> None:
    data = {"labels": LABELS_DEEP, "arch": "cnn-gap-8-16-32",
            "params": {k: np.asarray(v, dtype=np.float16).tolist() for k, v in net.p.items()}}
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))


_infer_net: Net | None = None
_infer_ok = False


def load_infer(path: str = CNN_PATH) -> bool:
    global _infer_net, _infer_ok
    if _infer_net is not None:
        return _infer_ok
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            data = json.load(f)
        net = Net(len(data["labels"]))
        for k, v in data["params"].items():
            net.p[k] = np.asarray(v, dtype=np.float64)
        _infer_net = net
        _infer_ok = True
    except Exception:
        _infer_net = Net(len(LABELS_DEEP))
        _infer_ok = False
    return _infer_ok


def available() -> bool:
    return os.path.exists(CNN_PATH) and load_infer()


def predict_proba(x: np.ndarray) -> np.ndarray:
    load_infer()
    probs, _ = _infer_net.forward(x)
    return probs
