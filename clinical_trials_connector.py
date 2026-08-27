"""
Clinical trial search against ClinicalTrials.gov.
API: https://clinicaltrials.gov/api/v2/studies
Free, no key needed.
"""
from __future__ import annotations

from typing import Any

from i18n import tt

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

try:
    import requests
except ImportError:
    requests = None


def search_trials(condition: str = "", intervention: str = "", status: str = "RECRUITING",
                  limit: int = 5) -> dict[str, Any]:
    """
    Search clinical trials by disease or drug.
    """
    if requests is None:
        return {"ok": False, "message_fa": tt("The requests library is not installed.", "کتابخانه‌ی requests نصب نیست.")}
    params: dict[str, Any] = {"pageSize": limit, "format": "json"}
    query_parts = []
    if condition:
        query_parts.append(f'AREA[ConditionSearch]{condition}')
    if intervention:
        query_parts.append(f'AREA[InterventionSearch]{intervention}')
    if status:
        query_parts.append(f'AREA[OverallStatus]{status}')
    if not query_parts:
        return {"ok": False, "message_fa": tt("Enter a condition or drug name.", "نام بیماری یا دارو را وارد کنید.")}
    params["query.term"] = " AND ".join(query_parts)
    try:
        r = requests.get(BASE_URL, params=params, timeout=20)
        if r.status_code != 200:
            return {"ok": False, "message_fa": tt("Service unavailable.", "سرویس در دسترس نیست.")}
        data = r.json()
    except Exception:
        return {"ok": False, "message_fa": tt("Connection failed.", "ارتباط برقرار نشد.")}
    studies = data.get("studies", [])
    results = []
    for s in studies[:limit]:
        proto = s.get("protocolSection", {})
        ident = proto.get("identificationModule", {})
        status_mod = proto.get("statusModule", {})
        design = proto.get("designModule", {})
        conditions = proto.get("conditionsModule", {}).get("conditions", [])
        interventions = []
        for arm in proto.get("armsInterventionsModule", {}).get("interventions", []):
            interventions.extend(arm.get("interventionNamesList", []) or [arm.get("interventionName", "")])
        results.append({
            "nct_id": ident.get("nctId", ""),
            "title": ident.get("briefTitle", ""),
            "status": status_mod.get("overallStatus", ""),
            "phase": design.get("phases", [""]),
            "conditions": conditions[:3],
            "interventions": [i for i in interventions if i][:3],
            "start_date": status_mod.get("startDateStruct", {}).get("date", ""),
            "enrollment": design.get("enrollmentInfo", {}).get("count"),
        })
    return {"ok": True, "total": data.get("totalCount", len(results)), "trials": results, "source": "ClinicalTrials.gov"}


def is_available() -> bool:
    if requests is None:
        return False
    try:
        r = requests.get(BASE_URL, params={"pageSize": 1, "format": "json"}, timeout=10)
        return r.status_code == 200
    except Exception:
        return False
