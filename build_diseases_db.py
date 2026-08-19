# -*- coding: utf-8 -*-
"""
build_diseases_db.py — ساخت دیتابیس آفلاین SQLite (diseases_offline.db)
از روی پایه‌ی دانش داخلی + diseases_extra.json
اجرا: python build_diseases_db.py
"""
from __future__ import annotations

import json
import os
import sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "diseases_offline.db")
EXTRA_PATH = os.path.join(BASE, "diseases_extra.json")


def main() -> int:
    from medical_engine import DISEASES
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""CREATE TABLE diseases (
        id TEXT PRIMARY KEY, name_fa TEXT, name_en TEXT, urgency TEXT,
        symptoms TEXT, advice TEXT, doctor_when TEXT, source TEXT)""")
    rows = []
    for d in DISEASES:
        rows.append((d["id"], d["fa"], d["en"], d.get("urgency", "routine"),
                     json.dumps(d["symptoms"], ensure_ascii=False),
                     json.dumps(d.get("advice", []), ensure_ascii=False),
                     d.get("doctor_when", ""), "medical_engine"))
    with open(EXTRA_PATH, "r", encoding="utf-8") as f:
        extra = json.load(f)
    for d in extra.get("diseases", []):
        adv = d.get("advice_fa", "")
        if isinstance(adv, list):
            adv = json.dumps(adv, ensure_ascii=False)
        rows.append((d.get("id", ""), d.get("fa", ""), d.get("en", ""), d.get("urgency", "routine"),
                     d.get("symptoms_fa", ""), adv, d.get("doctor_when_fa", ""),
                     "diseases_extra.json"))
    cur.executemany("INSERT OR REPLACE INTO diseases VALUES (?,?,?,?,?,?,?,?)", rows)
    con.commit()
    n = cur.execute("SELECT COUNT(*) FROM diseases").fetchone()[0]
    con.close()
    print(f"✅ دیتابیس ساخته شد: {DB_PATH} — {n} بیماری")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
