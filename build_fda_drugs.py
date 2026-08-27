"""
Builds the FDA drug bank from the NDC directory.
I rerun it whenever the source gets refreshed.

Downloads come from download.open.fda.gov; if that one is blocked the old
accessdata.fda.gov address is tried too.
Output: drugs_fda.json - one row per generic name, merged from all products.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
import urllib.request
import zipfile

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(DATA_DIR, "drugs_fda.json")
CACHE_ZIP = os.path.join(DATA_DIR, "drug-ndc.json.zip")

URLS = [
    "https://download.open.fda.gov/drug/ndc/drug-ndc-0001-of-0001.json.zip",
    "https://accessdata.fda.gov/cder/ndctext.zip",
]
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def fetch() -> list[dict]:
    src = None
    for url in URLS:
        try:
            print("دانلود:", url)
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=600) as r:
                src = r.read()
            break
        except Exception as e:
            print("  ناموفق:", e)
    if not src:
        print("خطا: دانلود دیتاست ممکن نشد — اینترنت را بررسی کنید.")
        sys.exit(1)

    z = zipfile.ZipFile(io.BytesIO(src))
    name = z.namelist()[0]
    with z.open(name) as f:
        if name.endswith(".json"):
            return json.load(f)["results"]
        text = io.TextIOWrapper(f, encoding="utf-8-sig", errors="replace")
        cols = text.readline().rstrip("\n").split("\t")
        idx = {c: i for i, c in enumerate(cols)}
        out = []
        for line in text:
            parts = line.rstrip("\n").split("\t")
            row = {}
            for col, i in idx.items():
                row[col] = parts[i] if i < len(parts) else ""
            out.append({
                "generic_name": row.get("NONPROPRIETARYNAME", ""),
                "brand_name": row.get("PROPRIETARYNAME", ""),
                "active_ingredients": [{"name": row.get("ACTIVEINGREDIENTSMOE", "")} if False else {"name": row.get("ACTIVE_NUMERATOR_STRENGTH", ""), "strength": ""}],
                "dosage_form": row.get("DOSAGEFORM", ""),
                "route": row.get("ROUTENAME", ""),
                "pharm_class": row.get("PHARM_CLASSES", ""),
                "marketing_category": row.get("MARKETINGCATEGORYNAME", ""),
                "product_type": row.get("PRODUCTTYPENAME", ""),
            })
        return out


def clean_class(tag: str) -> str:
    return re.sub(r"\s*\[(EPC|MoA|CS|PE|EXT)\]\s*", "", tag).strip()


def build(products: list[dict]) -> list[dict]:
    db: dict[str, dict] = {}
    for p in products:
        gen = (p.get("generic_name") or "").strip()
        if not gen or not re.match(r"^[A-Za-z0-9]", gen):
            continue
        key = gen.lower()
        e = db.get(key)
        if e is None:
            e = db[key] = {
                "g": gen,
                "brands": [],
                "ing": [],
                "forms": [],
                "routes": [],
                "class": [],
                "mkt": [],
                "type": (p.get("product_type") or "").replace("HUMAN ", "HUMAN_").replace(" ", "_"),
                "n": 0,
            }
        e["n"] += 1
        def _add(field, val, cap):
            v = (val or "").strip()
            if v and v not in e[field] and len(e[field]) < cap:
                e[field].append(v)
        _add("brands", p.get("brand_name_base") or p.get("brand_name"), 6)
        for ing in (p.get("active_ingredients") or []):
            _add("ing", (ing.get("name") or "").title(), 4)
        _add("forms", p.get("dosage_form"), 6)
        rt_val = p.get("route")
        if isinstance(rt_val, str):
            rt_val = rt_val.split(",")
        for rt in rt_val or []:
            _add("routes", str(rt), 4)
        pc = p.get("pharm_class")
        if isinstance(pc, str):
            for tag in pc.split(","):
                _add("class", clean_class(tag), 4)
        elif isinstance(pc, list):
            for tag in pc:
                _add("class", clean_class(str(tag)), 4)
        ofd = p.get("openfda") or {}
        for k in ("pharm_class_epc", "pharm_class_cs", "pharm_class_moa"):
            for tag in (ofd.get(k) or [])[:2]:
                _add("class", clean_class(str(tag)), 4)
        _add("mkt", p.get("marketing_category"), 3)
    out = sorted(db.values(), key=lambda x: x["g"].lower())
    return out


def main() -> None:
    if os.path.exists(CACHE_ZIP) and "--fresh" not in sys.argv:
        print("استفاده از نسخه‌ی دانلودشده:", CACHE_ZIP)
        products = json.load(zipfile.ZipFile(CACHE_ZIP).open(zipfile.ZipFile(CACHE_ZIP).namelist()[0]))["results"]
    else:
        products = fetch()
        try:
            with open(CACHE_ZIP, "wb") as f:
                f.write(b"")
        except Exception:
            pass
    db = build(products)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"source": "openFDA NDC Directory (FDA, USA)", "count": len(db), "drugs": db},
                  f, ensure_ascii=False, separators=(",", ":"))
    size = os.path.getsize(OUT_PATH) / 1024 / 1024
    print(f"ساخته شد: drugs_fda.json — {len(db)} داروی یکتا ({size:.1f} MB)")


if __name__ == "__main__":
    main()
