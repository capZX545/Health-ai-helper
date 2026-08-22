# -*- coding: utf-8 -*-
"""
Pulls the official drug labels from openFDA and keeps only the useful
sections: indications, warnings, adverse reactions and the boxed warning.

The full export is around 2 GB, so parts are downloaded and processed one by
one and deleted right after to save disk. Section text is also truncated in
place because full labels are huge.

Output: drug_labels.json.gz next to the other data files.
"""
from __future__ import annotations

import gzip
import io
import json
import os
import time
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "drug_labels.json.gz")
TMP = "/tmp/labels"
UA = {"User-Agent": "NexusMed2077/2.0 (github.com/capZX545)"}
N_PARTS = 14
CAPS = {"ind": 900, "warn": 900, "adv": 900, "box": 600}
FIELDS = {"ind": "indications_and_usage", "warn": "warnings",
          "adv": "adverse_reactions", "box": "boxed_warning"}


def load_acc() -> dict:
    if os.path.exists(OUT):
        with gzip.open(OUT, "rt", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_acc(acc: dict) -> None:
    tmp = OUT + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=9) as f:
        json.dump(acc, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, OUT)
    print(f"  checkpoint: {len(acc)} دارو، {os.path.getsize(OUT)/1024/1024:.1f} MB gz")


def process_part(path: str, acc: dict) -> int:
    z = zipfile.ZipFile(path)
    n = 0
    with z.open(z.namelist()[0]) as f:
        import ijson
        for doc in ijson.items(f, "results.item"):
            n += 1
            ofd = doc.get("openfda") or {}
            gens = ofd.get("generic_name") or ([doc["generic_name"]] if doc.get("generic_name") else [])
            key = (gens[0] if gens else "").strip().lower()
            if not key:
                continue
            e = acc.get(key)
            if e is None:
                e = acc[key] = {"ind": "", "warn": "", "adv": "", "box": ""}
            for k, fld in FIELDS.items():
                if not e[k]:
                    val = doc.get(fld)
                    if isinstance(val, list):
                        val = next((x for x in val if isinstance(x, str) and x.strip()), "")
                    if isinstance(val, str) and val.strip():
                        v = " ".join(val.split())
                        e[k] = v[: CAPS[k]]
    return n


def download(part: int) -> str | None:
    name = f"part{part:02d}.zip"
    path = os.path.join(TMP, name)
    if os.path.exists(path) and os.path.getsize(path) > 10_000_000:
        return path  # already downloaded
    url = f"https://download.open.fda.gov/drug/label/drug-label-{part:04d}-of-{N_PARTS:04d}.json.zip"
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=900) as r, open(path, "wb") as f:
                f.write(r.read())
            if os.path.getsize(path) > 10_000_000:
                return path
        except Exception as e:  # noqa: BLE001
            print(f"  تلاش {attempt+1} ناموفق: {e}")
            time.sleep(25)
    return None


def main() -> None:
    os.makedirs(TMP, exist_ok=True)
    acc = load_acc()
    print(f"شروع — {len(acc)} دارو در بانک فعلی")
    for part in range(1, N_PARTS + 1):
        path = download(part)
        if not path:
            print(f"part{part:02d}: دانلود نشد — رد شد")
            continue
        n = process_part(path, acc)
        save_acc(acc)
        try:
            os.remove(path)
        except OSError:
            pass
        print(f"part{part:02d}: {n} لیبل پردازش شد (مجموع {len(acc)} دارو)")
        time.sleep(12)
    # keep only drugs that got at least one section
    acc = {k: v for k, v in acc.items() if v["ind"] or v["warn"] or v["adv"] or v["box"]}
    save_acc(acc)
    print(f"پایان: {len(acc)} دارو با لیبل کامل")


if __name__ == "__main__":
    main()
