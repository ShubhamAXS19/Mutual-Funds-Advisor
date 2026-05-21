import os
from groq import AsyncGroq
from graph.state import MFAdvisorState, ScoredFund

client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])
MODEL = "llama-3.1-8b-instant"


def build_fund_summary(sf: ScoredFund) -> str:
    """Build a compact data string for the LLM to reason about."""
    def pct(val):
        return f"{val * 100:.1f}%" if val is not None else "N/A"

    return (
        f"Fund: {sf.fund.scheme_name}\n"
        f"Category: {sf.fund.category} — {sf.fund.sub_category}\n"
        f"1Y CAGR: {pct(sf.cagr_1y)}  |  3Y CAGR: {pct(sf.cagr_3y)}  |  5Y CAGR: {pct(sf.cagr_5y)}\n"
        f"Volatility (annualised): {pct(sf.volatility)}\n"
        f"Sharpe Ratio: {f'{sf.sharpe_ratio:.2f}' if sf.sharpe_ratio else 'N/A'}\n"
        f"Expense Ratio: {f'{sf.fund.expense_ratio}%' if sf.fund.expense_ratio else 'N/A'}\n"
        f"AUM: {f'₹{sf.fund.aum_cr:.0f} Cr' if sf.fund.aum_cr else 'N/A'}"
    )


def build_prompt(sf: ScoredFund, user_profile) -> str:
    fund_summary = build_fund_summary(sf)

    return f"""You are a SEBI-registered financial advisor assistant helping an Indian retail investor choose mutual funds.

User profile:
- Age: {user_profile.age}
- Monthly SIP: ₹{user_profile.monthly_sip:,.0f}
- Investment horizon: {user_profile.horizon_years} years
- Risk tolerance: {user_profile.risk_level}
- Goal: {user_profile.goal}

Fund data:
{fund_summary}

Write a 3–4 sentence plain English explanation of why this fund suits this investor.
Focus on: the fund's return consistency, risk level relative to the user's profile, and how it fits their horizon and goal.
Do NOT use jargon. Do NOT make guarantees about future returns.
End with one honest caveat specific to this fund's data.
"""


async def explain_fund(sf: ScoredFund, user_profile) -> str:
    """Call Groq to generate a rationale for a single fund."""
    prompt = build_prompt(sf, user_profile)

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()


async def explainer_agent(state: MFAdvisorState) -> MFAdvisorState:
    """
    Explainer Agent — Node 4 (final) in the LangGraph pipeline.

    Responsibilities:
    - For each recommended fund, call Groq LLM with fund metrics + user profile
    - Generate a plain English explanation
    - Write explanation dict {scheme_code: explanation} to state
    """
    state["current_step"] = "explainer_agent"

    if not state.get("recommended_funds"):
        state["errors"].append("explainer_agent: No recommended funds to explain.")
        state["explanation"] = {}
        return state

    user_profile = state["user_profile"]
    explanations = {}

    for sf in state["recommended_funds"]:
        try:
            explanation = await explain_fund(sf, user_profile)
            explanations[sf.fund.scheme_code] = explanation
        except Exception as e:
            explanations[sf.fund.scheme_code] = f"Explanation unavailable: {str(e)}"

    state["explanation"] = explanations
    print(f"[explainer_agent] Generated explanations for {len(explanations)} funds.")

    return state