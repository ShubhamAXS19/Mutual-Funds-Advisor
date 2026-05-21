import httpx
import re

# Updated URL — AMFI moved to portal subdomain
AMFI_NAV_URL = "https://portal.amfiindia.com/spages/NAVAll.txt"
# AMFI moved factsheet to portal subdomain
FACTSHEET_URL = "https://portal.amfiindia.com/modules/LoadFundFactsheet"

# ── SEBI category → risk level mapping ───────────────────────────────────────
CATEGORY_RISK_MAP = {
    "equity scheme - large cap fund":               "high",
    "equity scheme - mid cap fund":                 "high",
    "equity scheme - small cap fund":               "high",
    "equity scheme - large & mid cap fund":         "high",
    "equity scheme - multi cap fund":               "high",
    "equity scheme - flexi cap fund":               "high",
    "equity scheme - elss":                         "high",
    "equity scheme - sectoral/thematic":            "high",
    "equity scheme - focused fund":                 "high",
    "equity scheme - dividend yield fund":          "high",
    "equity scheme - contra fund":                  "high",
    "equity scheme - value fund":                   "high",
    "hybrid scheme - aggressive hybrid fund":       "medium",
    "hybrid scheme - balanced hybrid fund":         "medium",
    "hybrid scheme - dynamic asset allocation":     "medium",
    "hybrid scheme - multi asset allocation":       "medium",
    "hybrid scheme - equity savings":               "medium",
    "hybrid scheme - arbitrage fund":               "low",
    "hybrid scheme - conservative hybrid fund":     "low",
    "debt scheme - liquid fund":                    "low",
    "debt scheme - overnight fund":                 "low",
    "debt scheme - ultra short duration fund":      "low",
    "debt scheme - low duration fund":              "low",
    "debt scheme - money market fund":              "low",
    "debt scheme - short duration fund":            "low",
    "debt scheme - medium duration fund":           "low",
    "debt scheme - medium to long duration fund":   "low",
    "debt scheme - long duration fund":             "low",
    "debt scheme - dynamic bond":                   "low",
    "debt scheme - corporate bond fund":            "low",
    "debt scheme - credit risk fund":               "low",
    "debt scheme - banking and psu fund":           "low",
    "debt scheme - gilt fund":                      "low",
    "debt scheme - floater fund":                   "low",
    "income":                                       "low",
    "other scheme - index funds":                   "high",
    "other scheme - etfs":                          "high",
    "other scheme - fund of funds":                 "medium",
}

CATEGORY_EXPENSE_PROXY = {
    "high":   1.05,
    "medium": 1.00,
    "low":    0.50,
}


async def fetch_amfi_nav_data() -> dict[str, dict]:
    """
    Fetch AMFI NAVAll.txt from the portal subdomain with redirect following.
    """
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(AMFI_NAV_URL)
        resp.raise_for_status()
        text = resp.text

    result: dict[str, dict] = {}
    current_category = "Unknown"

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        cat_match = re.match(r"Open Ended Schemes?\((.+?)\)", line, re.IGNORECASE)
        if cat_match:
            current_category = cat_match.group(1).strip()
            continue

        if line.startswith("Scheme Code"):
            continue

        parts = line.split(";")
        if len(parts) < 5:
            continue

        scheme_code = parts[0].strip()
        isin = parts[2].strip() or parts[1].strip()
        scheme_name = parts[3].strip()

        if not scheme_code.isdigit():
            continue

        result[scheme_code] = {
            "scheme_name": scheme_name,
            "category": current_category,
            "isin": isin,
        }

    return result


def get_risk_for_category(category: str) -> str:
    key = category.lower().strip()
    for cat_key, risk in CATEGORY_RISK_MAP.items():
        if cat_key in key:
            return risk
    return "medium"


def get_expense_proxy(risk_level: str) -> float:
    return CATEGORY_EXPENSE_PROXY.get(risk_level, 1.0)


async def fetch_aum_data() -> dict[str, float]:
    """Fetch AUM data with redirect following. Returns empty dict on failure."""
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(FACTSHEET_URL)
            resp.raise_for_status()
            text = resp.text
    except Exception as e:
        print(f"[amfi] AUM fetch failed (non-critical): {e}")
        return {}

    aum_map: dict[str, float] = {}
    for line in text.splitlines():
        parts = line.split("|")
        if len(parts) < 6:
            continue
        try:
            scheme_code = parts[0].strip()
            aum_str = parts[5].strip().replace(",", "")
            if scheme_code.isdigit() and aum_str:
                aum_map[scheme_code] = float(aum_str)
        except (ValueError, IndexError):
            continue

    return aum_map