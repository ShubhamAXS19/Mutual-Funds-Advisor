import math
from graph.state import MFAdvisorState, FundData, ScoredFund


def compute_cagr(nav_history: list[dict], years: int) -> float | None:
    """
    CAGR = (end_nav / start_nav) ^ (1 / years) - 1
    Returns None if insufficient data.
    """
    trading_days = years * 252
    if len(nav_history) < trading_days:
        return None

    start_nav = nav_history[-trading_days]["nav"]
    end_nav = nav_history[-1]["nav"]

    if start_nav <= 0:
        return None

    return (end_nav / start_nav) ** (1 / years) - 1


def compute_volatility(nav_history: list[dict], window: int = 252) -> float | None:
    """
    Annualised standard deviation of daily returns.
    Uses last `window` trading days (default 1 year).
    """
    if len(nav_history) < window + 1:
        return None

    recent = nav_history[-(window + 1):]
    daily_returns = [
        (recent[i + 1]["nav"] - recent[i]["nav"]) / recent[i]["nav"]
        for i in range(len(recent) - 1)
        if recent[i]["nav"] > 0
    ]

    if len(daily_returns) < 50:
        return None

    mean = sum(daily_returns) / len(daily_returns)
    variance = sum((r - mean) ** 2 for r in daily_returns) / len(daily_returns)
    std_dev = math.sqrt(variance)

    return std_dev * math.sqrt(252)     # annualise


def compute_sharpe(cagr: float | None, volatility: float | None, risk_free_rate: float = 0.065) -> float | None:
    """
    Simplified Sharpe = (CAGR - risk_free_rate) / volatility
    Using India's ~6.5% risk-free rate (10Y G-Sec approximate).
    """
    if cagr is None or volatility is None or volatility == 0:
        return None
    return (cagr - risk_free_rate) / volatility


def score_fund(sf: ScoredFund) -> float:
    """
    Composite score (higher is better).
    Weights: 3Y CAGR (40%), Sharpe (40%), 1Y CAGR (20%).
    Penalises missing data with 0.
    """
    cagr_3y_score = (sf.cagr_3y or 0) * 0.40
    sharpe_score = (sf.sharpe_ratio or 0) * 0.40
    cagr_1y_score = (sf.cagr_1y or 0) * 0.20
    return cagr_3y_score + sharpe_score + cagr_1y_score


async def analyst_agent(state: MFAdvisorState) -> MFAdvisorState:
    """
    Analyst Agent — Node 2 in the LangGraph pipeline.

    Responsibilities:
    - Read fund_universe from state
    - Compute CAGR (1Y, 3Y, 5Y), volatility, Sharpe ratio for each fund
    - Score and sort funds
    - Write scored_funds back to state
    """
    state["current_step"] = "analyst_agent"

    if not state.get("fund_universe"):
        state["errors"].append("analyst_agent: fund_universe is empty, skipping.")
        state["scored_funds"] = []
        return state

    scored = []

    for fund in state["fund_universe"]:
        nav = fund.nav_history

        cagr_1y = compute_cagr(nav, 1)
        cagr_3y = compute_cagr(nav, 3)
        cagr_5y = compute_cagr(nav, 5)
        vol = compute_volatility(nav)
        sharpe = compute_sharpe(cagr_3y, vol)

        sf = ScoredFund(
            fund=fund,
            cagr_1y=cagr_1y,
            cagr_3y=cagr_3y,
            cagr_5y=cagr_5y,
            volatility=vol,
            sharpe_ratio=sharpe,
            score=0.0,
        )
        sf.score = score_fund(sf)
        scored.append(sf)

    # Sort by composite score descending
    scored.sort(key=lambda x: x.score, reverse=True)

    state["scored_funds"] = scored
    print(f"[analyst_agent] Scored {len(scored)} funds. Top fund: {scored[0].fund.scheme_name if scored else 'N/A'}")

    return state