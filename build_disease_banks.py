# -*- coding: utf-8 -*-
"""
Builds the big open disease/symptom banks:
- wiki_diseases.json : every Wikidata disease with fa/en names, ICD/DOID/MeSH
                       codes, its symptoms (P780) and treatments (P2176)
- diseases_doid.json : Human Disease Ontology (DOID) with definitions and xrefs
- symptoms_hpo.json  : the full HPO phenotype vocabulary (all medical symptoms)

Run:  python build_disease_banks.py
Sources are all open data; the downloaded files are cached in /tmp.
"""
from __future__ import annotations

import gzip
import json
import os
import re
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "NexusMed2077/2.0 (github.com/capZX545)"}


def http(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=900) as r:
        return r.read()


def sparql(query: str) -> list[dict]:
    import urllib.parse as up
    url = "https://query.wikidata.org/sparql?" + up.urlencode({"format": "json", "query": query})
    d = json.loads(http(url))
    return [{k: v["value"] for k, v in b.items()} for b in d["results"]["bindings"]]


def build_wiki():
    core = sparql("""
      SELECT ?q ?en ?fa ?icd ?doid ?mesh WHERE {
        ?i wdt:P31/wdt:P279* wd:Q12136 . ?i rdfs:label ?en . FILTER(LANG(?en)="en")
        OPTIONAL { ?i rdfs:label ?fa . FILTER(LANG(?fa)="fa") }
        OPTIONAL { ?i wdt:P494 ?icd } OPTIONAL { ?i wdt:P699 ?doid } OPTIONAL { ?i wdt:P486 ?mesh }
        BIND(STRAFTER(STR(?i), "/entity/") AS ?q) }""")
    out: dict[str, dict] = {}
    for r in core:
        q = r["q"]
        e = out.setdefault(q, {})
        if not e.get("en"):
            e["en"] = r["en"]
        if r.get("fa") and not e.get("fa"):
            e["fa"] = r["fa"]
        for k in ("icd", "doid", "mesh"):
            v = r.get(k)
            if v and k not in e:
                e[k] = v
    try:
        syms = sparql("""
          SELECT ?q ?s WHERE { ?i wdt:P31/wdt:P279* wd:Q12136 ; wdt:P780 ?sym .
            ?sym rdfs:label ?s . FILTER(LANG(?s)="en") BIND(STRAFTER(STR(?i), "/entity/") AS ?q) }""")
        for r in syms:
            e = out.get(r["q"])
            if e is not None:
                e.setdefault("sym", [])
                if r["s"] not in e["sym"]:
                    e["sym"].append(r["s"])
    except Exception as ex:  # noqa: BLE001
        print("symptoms query failed:", ex)
    try:
        drugs = sparql("""
          SELECT ?q ?d WHERE { ?i wdt:P31/wdt:P279* wd:Q12136 ; wdt:P2176 ?drug .
            ?drug rdfs:label ?d . FILTER(LANG(?d)="en") BIND(STRAFTER(STR(?i), "/entity/") AS ?q) }""")
        for r in drugs:
            e = out.get(r["q"])
            if e is not None:
                e.setdefault("drug", [])
                if r["d"] not in e["drug"]:
                    e["drug"].append(r["d"])
    except Exception as ex:  # noqa: BLE001
        print("drugs query failed:", ex)
    with open(os.path.join(HERE, "wiki_diseases.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    n_sym = sum(1 for e in out.values() if e.get("sym"))
    n_drug = sum(1 for e in out.values() if e.get("drug"))
    n_fa = sum(1 for e in out.values() if e.get("fa"))
    print(f"wiki_diseases.json: {len(out)} diseases ({n_fa} with farsi name, "
          f"{n_sym} with symptoms, {n_drug} with treatments)")


def build_doid():
    path = "/tmp/doid.json"
    if not os.path.exists(path):
        with open(path, "wb") as f:
            f.write(http("https://raw.githubusercontent.com/DiseaseOntology/"
                         "HumanDiseaseOntology/main/src/ontology/doid.json"))
    d = json.load(open(path, encoding="utf-8"))
    out = []
    for g in d.get("graphs", []):
        for n in g.get("nodes", []):
            m = re.search(r"DOID_(\d+)$", n.get("id", ""))
            if not m or n.get("type") != "CLASS" or not n.get("lbl"):
                continue
            meta = n.get("meta") or {}
            xref_vals = [str(x.get("val", "")) for x in (meta.get("xrefs") or [])]
            e = {"doid": m.group(1), "name": n["lbl"]}
            dv = (meta.get("definition") or {}).get("val") or ""
            if dv:
                e["def"] = " ".join(dv.split())[:320]
            for xr in xref_vals:
                if xr.startswith("ICD10CM:") and "icd" not in e:
                    e["icd"] = xr.split("ICD10CM:")[1]
                elif xr.startswith("MESH:") and "mesh" not in e:
                    e["mesh"] = xr.split("MESH:")[1]
                elif xr.startswith("OMIM:") and "omim" not in e:
                    e["omim"] = xr.split("OMIM:")[1].replace("MIM:", "")
            keep = []
            for s in (meta.get("synonyms") or []):
                t = str(s.get("val", "") or s if isinstance(s, str) else s.get("val", ""))
                t = t.strip().strip('"')
                if t and t.lower() != e["name"].lower():
                    keep.append(t)
                if len(keep) >= 5:
                    break
            if keep:
                e["syn"] = keep
            out.append(e)
    out.sort(key=lambda x: x["name"].lower())
    with open(os.path.join(HERE, "diseases_doid.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"diseases_doid.json: {len(out)} diseases")


def build_hpo():
    path = "/tmp/hp.obo"
    if not os.path.exists(path):
        with open(path, "wb") as f:
            f.write(http("https://raw.githubusercontent.com/obophenotype/"
                         "human-phenotype-ontology/master/hp.obo"))
    out = []
    in_term = False
    tid = tname = None
    syns = []
    obsolete = False
    def flush():
        if in_term and tid and tname and not obsolete:
            e = {"id": tid, "name": tname}
            if syns:
                e["syn"] = syns[:5]
            out.append(e)
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line == "[Term]":
            flush()
            tid = tname = None
            syns = []
            obsolete = False
            in_term = True
        elif line.startswith("[") and line != "[Term]":
            flush()
            in_term = False
        elif in_term and line.startswith("id: HP:"):
            tid = line[4:].strip()
        elif in_term and line.startswith("name:") and tname is None:
            tname = line[5:].strip()
        elif in_term and line.startswith("synonym:"):
            m = re.match(r'synonym: "([^"]+)"', line)
            if m:
                syns.append(m.group(1))
        elif in_term and line.startswith("is_obsolete: true"):
            obsolete = True
    flush()
    with open(os.path.join(HERE, "symptoms_hpo.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"symptoms_hpo.json: {len(out)} phenotype terms")


if __name__ == "__main__":
    build_wiki()
    build_doid()
    build_hpo()
