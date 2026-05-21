import re
from graph.state import MFAdvisorState, ScoredFund

MAX_EXPENSE_RATIO = 1.5
MIN_AUM_CR = 100
MAX_PER_FUND_HOUSE = 1      # max 1 fund per fund house in final top 5
TOP_N = 5

# Known fund house prefixes — used to extract house name from scheme name
FUND_HOUSE_PREFIXES = [
    "Aditya Birla Sun Life", "HDFC", "ICICI Prudential", "SBI", "Nippon India",
    "Kotak", "Axis", "Mirae Asset", "UTI", "Franklin Templeton", "DSP",
    "Tata", "Sundaram", "Canara Robeco", "IDFC", "Edelweiss", "Invesco",
    "Motilal Oswal", "PGIM", "Quantum", "Union", "Bandhan", "Navi",
    "Parag Parikh", "WhiteOak", "Groww", "Mahindra Manulife",
]


def extract_fund_house(scheme_name: str) -> str:
    """
    Extract the fund house name from the scheme name.
    Falls back to first two words if no known prefix matches.
    """
    for prefix in FUND_HOUSE_PREFIXES:
        if scheme_name.lower().startswith(prefix.lower()):
            return prefix.lower()
    # Fallback: first two words
    words = scheme_name.split()
    return " ".join(words[:2]).lower()


def passes_guardrails(sf: ScoredFund, user_risk: str) -> tuple[bool, str]:
    fund_risk = sf.fund.sub_category
    if fund_risk != user_risk:
        return False, f"category risk mismatch: fund={fund_risk}, user={user_risk}"
    if sf.fund.expense_ratio is not None and sf.fund.expense_ratio > MAX_EXPENSE_RATIO:
        return False, f"expense ratio too high: {sf.fund.expense_ratio}%"
    if sf.fund.aum_cr is not None and sf.fund.aum_cr < MIN_AUM_CR:
        return False, f"AUM too low: ₹{sf.fund.aum_cr:.0f} Cr"
    return True, ""


def horizon_filter(sf: ScoredFund, horizon_years: int) -> bool:
    if horizon_years < 3:
        return sf.cagr_1y is not None
    elif horizon_years <= 5:
        return sf.cagr_3y is not None
    else:
        return sf.cagr_3y is not None


def pick_diverse_funds(
    scored_funds: list[ScoredFund],
    user_risk: str,
    horizon_years: int,
    n: int = TOP_N,
    excluded_names: set[str] = set(),
) -> list[ScoredFund]:
    """
    Pick top N funds ensuring:
    - Pass guardrails and horizon filter
    - Max 1 fund per fund house (prevents ICICI × 5 problem)
    - Not in excluded_names (critic feedback)
    - Ordered by composite score descending
    """
    selected: list[ScoredFund] = []
    fund_house_count: dict[str, int] = {}

    for sf in scored_funds:
        if len(selected) >= n:
            break

        # Skip critic-excluded funds
        if sf.fund.scheme_name in excluded_names:
            continue

        # Guardrails
        ok, _ = passes_guardrails(sf, user_risk)
        if not ok:
            continue

        # Horizon
        if not horizon_filter(sf, horizon_years):
            continue

        # Fund house diversity — max 1 per house
        house = extract_fund_house(sf.fund.scheme_name)
        if fund_house_count.get(house, 0) >= MAX_PER_FUND_HOUSE:
            continue

        selected.append(sf)
        fund_house_count[house] = fund_house_count.get(house, 0) + 1

    return selected


async def recommendation_agent(state: MFAdvisorState) -> MFAdvisorState:
    """
    Recommendation Agent — Node 3 in the LangGraph pipeline.

    Key fix: enforces 1 fund per fund house so we don't get
    5 variants of the same ICICI/Aditya Birla fund.
    """
    state["current_step"] = "recommendation_agent"

    if not state.get("scored_funds"):
        state["errors"].append("recommendation_agent: scored_funds is empty, skipping.")
        state["recommended_funds"] = []
        return state

    user_risk = state["user_profile"].risk_level
    horizon = state["user_profile"].horizon_years
    critic_feedback = state.get("critic_feedback", [])
    is_retry = state.get("critic_iterations", 0) > 0

    # Build exclusion set from critic feedback (per-fund issues)
    exclusions: set[str] = set()
    if is_retry and critic_feedback:
        import re
        for feedback in critic_feedback:
            matches = re.findall(r"'([^']+)'", feedback)
            # Only exclude if it looks like a fund name (not a category name)
            for m in matches:
                if not m.startswith("Equity") and not m.startswith("Hybrid") and not m.startswith("Debt"):
                    exclusions.add(m)
        if exclusions:
            print(f"[recommendation_agent] Retry — excluding: {exclusions}")

    top_n = pick_diverse_funds(
        state["scored_funds"], user_risk, horizon,
        n=TOP_N, excluded_names=exclusions
    )

    if not top_n:
        # Fallback: relax fund house diversity
        state["errors"].append(
            "recommendation_agent: Diverse selection failed. Falling back to top scored funds."
        )
        top_n = [
            sf for sf in state["scored_funds"]
            if horizon_filter(sf, horizon)
            and sf.fund.scheme_name not in exclusions
        ][:TOP_N]

    print(
        f"[recommendation_agent] Recommending {len(top_n)} funds "
        f"({'retry' if is_retry else 'first pass'}) "
        f"from {len(set(extract_fund_house(sf.fund.scheme_name) for sf in top_n))} fund houses."
    )

    state["recommended_funds"] = top_n
    return state