# -*- coding: utf-8 -*-
"""
Connector for the WHO Global Health Observatory (GHO) API.
Health indicators for 194 countries: disease stats, mortality, burden.
API: https://ghoapi.azureedge.net/api/
"""
from __future__ import annotations

from typing import Any

from i18n import tt

BASE_URL = "https://ghoapi.azureedge.net/api"

try:
    import requests
except ImportError:
    requests = None

# the handy indicators
INDICATORS = {
    "life_expectancy": "WHS4_100",
    "under5_mortality": "MDG_0000000001",
    "maternal_mortality": "MDG_0000000026",
    "hiv_deaths": "WHS7_100",
    "tb_incidence": "MDG_0000000018",
    "malaria_cases": "MDG_0000000024",
    "ncd_mortality": "NCDMORT307000",
    "road_traffic": "RS_196",
    "suicide_rate": "MH_12",
    "diabetes_prevalence": "NCD_RGB1_04",
    "hypertension": "NCD_HYP_30",
    "obesity_adult": "NCD_BMI_30A",
    "smoking_adult": "M_Est_smk_curr",
}


def _get(path: str, params: dict | None = None, timeout: int = 15) -> dict[str, Any] | None:
    if requests is None:
        return None
    try:
        r = requests.get(f"{BASE_URL}/{path}", params=params or {}, timeout=timeout)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None


def get_indicator(indicator_code: str, country: str = "IRN", latest: bool = True) -> dict[str, Any]:
    """
    Fetch one indicator for one country.
    """
    data = _get(f"Indicator/{indicator_code}", {"SpatialDim": country} if latest else {})
    if not data or not data.get("value"):
        return {"ok": False, "message_fa": tt("No data available.", "داده‌ای در دسترس نیست.")}
    rows = data["value"]
    if latest and rows:
        rows.sort(key=lambda x: x.get("TimeDim", 0), reverse=True)
        rows = rows[:3]
    results = []
    for r in rows:
        results.append({
            "year": r.get("TimeDim"),
            "value": r.get("NumericValue"),
            "unit": r.get("Unit", ""),
            "sex": r.get("Dim1", "BTSX"),
            "country": r.get("SpatialDim", country),
        })
    return {"ok": True, "indicator": indicator_code, "country": country, "data": results, "source": "WHO GHO"}


def get_country_profile(country_code: str = "IRN") -> dict[str, Any]:
    """
    A country's short health profile from the key indicators.
    """
    out = {"ok": True, "country": country_code, "indicators": {}, "source": "WHO GHO"}
    names_fa = {
        "life_expectancy": ("امید به زندگی", "سال"),
        "under5_mortality": ("مرگ‌ومیر زیر ۵ سال", "در ۱۰۰۰ تولد زنده"),
        "hiv_deaths": ("مرگ HIV", "نفر"),
        "tb_incidence": ("شیوع سل", "در ۱۰۰هزار"),
        "ncd_mortality": ("مرگ بیماری‌های غیرواگیر", "در ۱۰۰هزار"),
        "suicide_rate": ("نرخ خودکشی", "در ۱۰۰هزار"),
        "diabetes_prevalence": ("شیوع دیابت", "درصد"),
        "obesity_adult": ("چاقی بزرگسالان", "درصد"),
    }
    for key, code in INDICATORS.items():
        r = get_indicator(code, country_code, latest=True)
        if r.get("ok") and r.get("data"):
            latest_val = r["data"][0]
            label, unit = names_fa.get(key, (key, latest_val.get("unit", "")))
            out["indicators"][key] = {
                "value": latest_val["value"],
                "year": latest_val["year"],
                "label_fa": label,
                "unit_fa": unit,
            }
    return out


def is_available() -> bool:
    return _get("Indicator", {"$top": 1}) is not None


def learn_who_data(country_code: str = "IRN") -> dict[str, Any]:
    """
    Feed WHO data into the offline brain.
    """
    profile = get_country_profile(country_code)
    if not profile.get("ok") or not profile.get("indicators"):
        return {"ok": False, "learned": False}
    summary_parts = []
    for key, info in profile["indicators"].items():
        summary_parts.append(f"{info['label_fa']}: {info['value']} {info['unit_fa']} ({info['year']})")
    summary = f"WHO health profile {country_code}: " + "; ".join(summary_parts[:10])
    try:
        from auto_learning import learn_from_exchange
        learn_from_exchange(f"[WHO] {country_code}", summary,
                            provider="who_gho", model="api",
                            meta={"source": "who", "country": country_code})
    except Exception:
        pass
    return {"ok": True, "learned": True, "summary": summary, "indicators": profile["indicators"]}
