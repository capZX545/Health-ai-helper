"""
Builds disease_symptoms_hpo.json.gz from the official HPO annotations
(phenotype.hpoa): disease name -> list of symptom names, ready to merge
into the unified disease bank and the symptom->diseases index.
Run:  python build_hpo_links.py   (after downloading phenotype.hpoa to /tmp)
"""
from __future__ import annotations

import gzip
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
HPOA = "/tmp/phenotype.hpoa"
HPO_TERMS = os.path.join(HERE, "symptoms_hpo.json")
OUT = os.path.join(HERE, "disease_symptoms_hpo.json.gz")


def main() -> None:
    hp_names = {t["id"]: t["name"] for t in json.load(open(HPO_TERMS, encoding="utf-8"))}
    dis: dict[str, list[str]] = {}
    n_rows = 0
    for line in open(HPOA, encoding="utf-8"):
        if line.startswith("#"):
            continue
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 12:
            continue
        db_id, dname, qualifier, hpo_id = parts[0], parts[1], parts[2], parts[3]
        if qualifier or parts[10] != "P":
            continue
        name = hp_names.get(hpo_id)
        if not name or not dname:
            continue
        key = dname.strip().lower()
        lst = dis.setdefault(key, [])
        if name not in lst and len(lst) < 14:
            lst.append(name)
        n_rows += 1
    with gzip.open(OUT, "wt", encoding="utf-8") as f:
        json.dump(dis, f, ensure_ascii=False, separators=(",", ":"))
    print(f"disease_symptoms_hpo.json.gz: {len(dis)} diseases, {n_rows} pairs, "
          f"{os.path.getsize(OUT)/1024/1024:.1f} MB")


if __name__ == "__main__":
    main()
