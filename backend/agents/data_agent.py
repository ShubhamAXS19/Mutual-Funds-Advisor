from graph.state import MFAdvisorState
from tools.mfapi import fetch_funds_for_risk


async def data_agent(state: MFAdvisorState) -> MFAdvisorState:
    """
    Data Agent — Node 1 in the LangGraph pipeline.

    Responsibilities:
    - Read user risk level from state
    - Fetch a universe of relevant mutual funds from MFAPI
    - Write fund_universe back to state

    Does NOT compute any metrics — that is Analyst Agent's job.
    """
    state["current_step"] = "data_agent"

    try:
        risk_level = state["user_profile"].risk_level
        funds = await fetch_funds_for_risk(risk_level, max_funds=80)

        if not funds:
            state["errors"].append("data_agent: No funds fetched. MFAPI may be down.")
            state["fund_universe"] = []
        else:
            state["fund_universe"] = funds
            print(f"[data_agent] Fetched {len(funds)} funds for risk level: {risk_level}")

    except Exception as e:
        state["errors"].append(f"data_agent: {str(e)}")
        state["fund_universe"] = []

    return state