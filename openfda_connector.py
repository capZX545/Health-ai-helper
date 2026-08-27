"""
Talks to openFDA (free, no key) for:
- reported adverse drug events
- official drug labels
- auto-learning from real-world data

API: https://api.fda.gov/drug/
Limit: 240 requests/min without a key
"""
from __future__ import annotations

import json
from typing import Any

from i18n import tt

BASE_URL = "https://api.fda.gov/drug"

try:
    import requests
except ImportError:
    requests = None


def _get(path: str, params: dict | None = None, timeout: int = 15) -> dict[str, Any] | None:
    """
    GET request to openFDA.
    """
    if requests is None:
        return None
    try:
        r = requests.get(f"{BASE_URL}/{path}", params=params or {}, timeout=timeout)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None


def search_adverse_events(drug_name: str, limit: int = 10) -> dict[str, Any]:
    """
    Reported adverse events for one drug (FAERS).
    """
    if not drug_name:
        return {"ok": False, "message_fa": tt("Enter a drug name.", "نام دارو را وارد کنید.")}
    q = f'patient.drug.medicinalproduct:"{drug_name}"'
    data = _get("event.json", {"search": q, "limit": limit})
    if not data:
        return {"ok": False, "message_fa": tt("No data found or service unavailable.", "داده‌ای پیدا نشد یا سرویس در دسترس نیست.")}
    events = data.get("results", [])
    if not events:
        return {"ok": False, "message_fa": tt("No adverse events reported for this drug.", "عارضه‌ی جانبی برای این دارو گزارش نشده است.")}
    reactions: dict[str, int] = {}
    total = data.get("meta", {}).get("results", {}).get("total", 0)
    for ev in events:
        for r in ev.get("patient", {}).get("reaction", []):
            term = r.get("reactionmeddrapt", "")
            if term:
                reactions[term] = reactions.get(term, 0) + 1
    top = sorted(reactions.items(), key=lambda x: x[1], reverse=True)[:15]
    return {
        "ok": True,
        "drug": drug_name,
        "total_reports": total,
        "top_reactions": [{"reaction": r, "count": c} for r, c in top],
        "source": "OpenFDA FAERS",
    }


def search_drug_label(drug_name: str, limit: int = 3) -> dict[str, Any]:
    """
    Official label lookup (usage, warnings, side effects).
    """
    if not drug_name:
        return {"ok": False, "message_fa": tt("Enter a drug name.", "نام دارو را وارد کنید.")}
    q = f'openfda.brand_name:"{drug_name}" OR openfda.generic_name:"{drug_name}"'
    data = _get("label.json", {"search": q, "limit": limit})
    if not data:
        return {"ok": False, "message_fa": tt("No label found.", "برچسبی پیدا نشد.")}
    results = []
    for item in data.get("results", []):
        results.append({
            "brand": ", ".join(item.get("openfda", {}).get("brand_name", []) or [""]),
            "generic": ", ".join(item.get("openfda", {}).get("generic_name", []) or [""]),
            "purpose": (item.get("purpose", [""]) or [""])[0][:200] if isinstance(item.get("purpose"), list) else str(item.get("purpose", ""))[:200],
            "warnings": (item.get("warnings", [""]) or [""])[0][:400] if isinstance(item.get("warnings"), list) else str(item.get("warnings", ""))[:400],
            "dosage": (item.get("dosage_and_administration", [""]) or [""])[0][:300] if isinstance(item.get("dosage_and_administration"), list) else str(item.get("dosage_and_administration", ""))[:300],
        })
    return {"ok": True, "drug": drug_name, "labels": results, "source": "OpenFDA Drug Labels"}


def learn_from_fda(drug_name: str) -> dict[str, Any]:
    """
    Learn from openFDA data into the offline brain.
    """
    ae = search_adverse_events(drug_name, 5)
    if ae.get("ok") and ae.get("top_reactions"):
        summary = f"OpenFDA adverse events for {drug_name} ({ae['total_reports']} reports): " + \
                  "; ".join(f"{r['reaction']}({r['count']})" for r in ae["top_reactions"][:8])
        try:
            from auto_learning import learn_from_exchange
            learn_from_exchange(f"[FDA] {drug_name}", summary,
                                provider="openfda", model="api",
                                meta={"source": "openfda", "drug": drug_name})
        except Exception:
            pass
        return {"ok": True, "learned": True, "summary": summary}
    return {"ok": False, "learned": False, "message_fa": ae.get("message_fa", "No data")}


def is_available() -> bool:
    """
    Check whether openFDA is reachable.
    """
    return _get("event.json", {"limit": 1}) is not None
