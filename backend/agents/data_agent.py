from graph.state import MFAdvisorState
from tools.mfapi import fetch_funds_for_risk


async def data_agent(state: MFAdvisorState) -> MFAdvisorState:
    """
    Data Agent — Node 1 in the LangGraph pipeline.

    Track A changes:
    - Now uses AMFI NAVAll.txt for proper SEBI category filtering
      instead of keyword matching on scheme names
    - Funds now have real AUM (where available) and
      category-level expense ratio proxy
    """
    state["current_step"] = "data_agent"

    try:
        risk_level = state["user_profile"].risk_level
        funds = await fetch_funds_for_risk(risk_level, max_funds=80)

        if not funds:
            state["errors"].append(
                "data_agent: No funds fetched. AMFI or MFAPI may be down."
            )
            state["fund_universe"] = []
        else:
            state["fund_universe"] = funds
            print(
                f"[data_agent] {len(funds)} funds fetched "
                f"for risk='{risk_level}' using SEBI categories"
            )

    except Exception as e:
        state["errors"].append(f"data_agent: {str(e)}")
        state["fund_universe"] = []

    return state