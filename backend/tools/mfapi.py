import httpx
import asyncio
from typing import Optional
from graph.state import FundData
from tools.amfi import fetch_amfi_nav_data, get_risk_for_category, get_expense_proxy, fetch_aum_data

MFAPI_BASE = "https://api.mfapi.in"


async def fetch_fund_details(scheme_code: str) -> Optional[dict]:
    """Fetch full fund metadata + NAV history from MFAPI."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{MFAPI_BASE}/mf/{scheme_code}")
        resp.raise_for_status()
        return resp.json()


async def fetch_funds_for_risk(risk_level: str, max_funds: int = 80) -> list[FundData]:
    """
    Main entry point for the Data Agent.

    Flow:
    1. Fetch AMFI NAVAll.txt — get proper SEBI categories for all funds
    2. Fetch AMFI AUM factsheet
    3. Filter funds whose SEBI category maps to the user's risk level
    4. Fetch NAV history from MFAPI for each matched fund (concurrent)
    5. Return enriched FundData list
    """

    # Step 1 & 2 — fetch AMFI data concurrently
    amfi_data, aum_data = await asyncio.gather(
        fetch_amfi_nav_data(),
        fetch_aum_data(),
    )

    print(f"[mfapi] AMFI nav data: {len(amfi_data)} funds | AUM data: {len(aum_data)} funds")

    # Step 3 — filter by risk level using proper SEBI categories
    matched = [
        (code, info)
        for code, info in amfi_data.items()
        if get_risk_for_category(info["category"]) == risk_level
    ][:max_funds]

    print(f"[mfapi] {len(matched)} funds matched risk level '{risk_level}'")

    if not matched:
        return []

    # Step 4 — fetch NAV history concurrently (cap at 10 simultaneous)
    semaphore = asyncio.Semaphore(10)

    async def fetch_one(scheme_code: str, amfi_info: dict) -> Optional[FundData]:
        async with semaphore:
            try:
                details = await fetch_fund_details(scheme_code)
                nav_history = [
                    {"date": e["date"], "nav": float(e["nav"])}
                    for e in reversed(details.get("data", [])[:365 * 5])
                    if e.get("nav") and e["nav"] != "N.A."
                ]

                if len(nav_history) < 60:   # skip funds with insufficient history
                    return None

                category = amfi_info["category"]
                risk = get_risk_for_category(category)
                expense_ratio = get_expense_proxy(risk)
                aum = aum_data.get(scheme_code)     # real AUM if available, else None

                return FundData(
                    scheme_code=scheme_code,
                    scheme_name=amfi_info["scheme_name"],
                    category=category,
                    sub_category=risk,
                    aum_cr=aum,
                    expense_ratio=expense_ratio,
                    nav_history=nav_history,
                )
            except Exception as e:
                print(f"[mfapi] skipping {scheme_code}: {e}")
                return None

    results = await asyncio.gather(*[fetch_one(code, info) for code, info in matched])
    valid = [r for r in results if r is not None]

    print(f"[mfapi] {len(valid)} funds with sufficient NAV history")
    return valid