import httpx
import asyncio
from typing import Optional
from graph.state import FundData

MFAPI_BASE = "https://api.mfapi.in"

# AMFI category → risk level mapping
RISK_CATEGORY_MAP = {
    "low": ["Debt", "Liquid", "Overnight", "Money Market", "Ultra Short Duration"],
    "medium": ["Hybrid", "Balanced", "Conservative Hybrid", "Equity Savings"],
    "high": ["Equity", "ELSS", "Sectoral", "Thematic", "Small Cap", "Mid Cap", "Flexi Cap"],
}


async def fetch_all_funds() -> list[dict]:
    """Fetch the complete list of mutual funds from MFAPI."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{MFAPI_BASE}/mf")
        resp.raise_for_status()
        return resp.json()  # [{"schemeCode": 100033, "schemeName": "..."}, ...]


async def fetch_nav_history(scheme_code: str, limit: int = 365 * 5) -> list[dict]:
    """
    Fetch NAV history for a given scheme code.
    Returns last `limit` entries (default 5 years worth).
    MFAPI returns newest-first; we reverse to oldest-first for calculations.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{MFAPI_BASE}/mf/{scheme_code}")
        resp.raise_for_status()
        data = resp.json()

    nav_data = data.get("data", [])        # [{"date": "01-01-2024", "nav": "123.45"}, ...]
    nav_data = nav_data[:limit]            # trim to limit
    nav_data = list(reversed(nav_data))    # oldest first

    return [
        {"date": entry["date"], "nav": float(entry["nav"])}
        for entry in nav_data
        if entry.get("nav") and entry["nav"] != "N.A."
    ]


async def fetch_fund_details(scheme_code: str) -> Optional[dict]:
    """Fetch full fund metadata including scheme info."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{MFAPI_BASE}/mf/{scheme_code}")
        resp.raise_for_status()
        return resp.json()


def get_target_categories(risk_level: str) -> list[str]:
    """Return fund category keywords relevant to the user's risk level."""
    return RISK_CATEGORY_MAP.get(risk_level, RISK_CATEGORY_MAP["medium"])


async def fetch_funds_for_risk(risk_level: str, max_funds: int = 80) -> list[FundData]:
    """
    Main entry point for the Data Agent.
    Fetches all funds, filters by risk-appropriate categories,
    then fetches NAV history for each (with concurrency limit).
    """
    all_funds = await fetch_all_funds()
    target_categories = get_target_categories(risk_level)

    # Filter by category keywords in scheme name (MFAPI doesn't expose category directly)
    filtered = [
        f for f in all_funds
        if any(cat.lower() in f["schemeName"].lower() for cat in target_categories)
    ][:max_funds]

    # Fetch NAV history concurrently (cap at 10 concurrent requests)
    semaphore = asyncio.Semaphore(10)

    async def fetch_one(fund: dict) -> Optional[FundData]:
        async with semaphore:
            try:
                code = str(fund["schemeCode"])
                details = await fetch_fund_details(code)
                meta = details.get("meta", {})
                nav_history = [
                    {"date": e["date"], "nav": float(e["nav"])}
                    for e in reversed(details.get("data", [])[:365 * 5])
                    if e.get("nav") and e["nav"] != "N.A."
                ]
                return FundData(
                    scheme_code=code,
                    scheme_name=meta.get("scheme_name", fund["schemeName"]),
                    category=meta.get("scheme_category", "Unknown"),
                    sub_category=meta.get("scheme_type", "Unknown"),
                    aum_cr=None,            # MFAPI doesn't provide AUM; can extend later
                    expense_ratio=None,     # same — extend with Value Research scraper
                    nav_history=nav_history,
                )
            except Exception:
                return None

    results = await asyncio.gather(*[fetch_one(f) for f in filtered])
    return [r for r in results if r is not None and len(r.nav_history) >= 60]