from graph.state import MFAdvisorState, ScoredFund

# Guardrail constants
MAX_EXPENSE_RATIO = 1.5     # percent
MIN_AUM_CR = 500            # crores


def passes_guardrails(sf: ScoredFund) -> bool:
    """
    Hard filters applied before recommending a fund.
    If data is unavailable (None), we let it pass — we can't penalise unknown.
    """
    if sf.fund.expense_ratio is not None and sf.fund.expense_ratio > MAX_EXPENSE_RATIO:
        return False
    if sf.fund.aum_cr is not None and sf.fund.aum_cr < MIN_AUM_CR:
        return False
    return True


def horizon_filter(sf: ScoredFund, horizon_years: int) -> bool:
    """
    Only recommend funds with enough return history for the user's horizon.
    Short horizon (< 3Y): 1Y CAGR must exist.
    Medium (3-5Y): 3Y CAGR must exist.
    Long (> 5Y): 5Y CAGR preferred but not mandatory.
    """
    if horizon_years < 3:
        return sf.cagr_1y is not None
    elif horizon_years <= 5:
        return sf.cagr_3y is not None
    else:
        return sf.cagr_3y is not None   # 5Y data is a bonus


async def recommendation_agent(state: MFAdvisorState) -> MFAdvisorState:
    """
    Recommendation Agent — Node 3 in the LangGraph pipeline.

    Responsibilities:
    - Apply expense ratio and AUM guardrails
    - Filter by user's investment horizon
    - Return top 5 funds
    """
    state["current_step"] = "recommendation_agent"

    if not state.get("scored_funds"):
        state["errors"].append("recommendation_agent: scored_funds is empty, skipping.")
        state["recommended_funds"] = []
        return state

    horizon = state["user_profile"].horizon_years

    filtered = [
        sf for sf in state["scored_funds"]
        if passes_guardrails(sf) and horizon_filter(sf, horizon)
    ]

    top_5 = filtered[:5]

    if not top_5:
        # Fallback: relax guardrails and take top 5 from scored_funds
        state["errors"].append("recommendation_agent: No funds passed guardrails. Falling back to top scored funds.")
        top_5 = state["scored_funds"][:5]

    state["recommended_funds"] = top_5
    print(f"[recommendation_agent] Recommended {len(top_5)} funds.")

    return state