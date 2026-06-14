import os
import json
from groq import AsyncGroq
from graph.state import MFAdvisorState, ScoredFund

client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])
MODEL = "llama-3.1-8b-instant"


def build_fund_summary(sf: ScoredFund) -> str:
    def pct(val):
        return f"{val * 100:.1f}%" if val is not None else "N/A"

    expense = f"{sf.fund.expense_ratio}%" if sf.fund.expense_ratio else "N/A"
    aum = f"₹{sf.fund.aum_cr:.0f} Cr" if sf.fund.aum_cr else "N/A"

    return (
        f"Fund: {sf.fund.scheme_name}\n"
        f"Category: {sf.fund.category}\n"
        f"1Y CAGR: {pct(sf.cagr_1y)}  |  3Y CAGR: {pct(sf.cagr_3y)}  |  5Y CAGR: {pct(sf.cagr_5y)}\n"
        f"Annualised Volatility: {pct(sf.volatility)}\n"
        f"Sharpe Ratio: {f'{sf.sharpe_ratio:.2f}' if sf.sharpe_ratio else 'N/A'}\n"
        f"Expense Ratio: {expense}\n"
        f"AUM: {aum}"
    )


def build_prompt(sf: ScoredFund, user_profile) -> str:
    return f"""You are a SEBI-registered financial advisor assistant helping an Indian retail investor choose mutual funds.

User profile:
- Age: {user_profile.age}
- Monthly SIP: ₹{user_profile.monthly_sip:,.0f}
- Investment horizon: {user_profile.horizon_years} years
- Risk tolerance: {user_profile.risk_level}
- Goal: {user_profile.goal}

Fund data:
{build_fund_summary(sf)}

Respond ONLY with a valid JSON object in this exact format (no markdown, no preamble):
{{
  "summary": "3-4 sentence plain English explanation of why this fund suits this investor. Mention at least one specific number. Do not make guarantees about future returns.",
  "bullets": [
    "Reason 1 — specific and data-backed",
    "Reason 2 — specific and data-backed",
    "Reason 3 — specific and data-backed",
    "One honest caveat or risk specific to this fund"
  ]
}}

Rules:
- summary: flowing prose, no bullet points, no jargon
- bullets: exactly 4 items, each starting with a short bold label followed by an em dash
- Do NOT include markdown formatting inside the JSON strings
- The last bullet must be a caveat or risk warning
"""


async def explain_fund(sf: ScoredFund, user_profile) -> dict:
    """Call Groq and return {summary, bullets}. Falls back gracefully on parse error."""
    prompt = build_prompt(sf, user_profile)

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=500,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown fences if model adds them despite instructions
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw)
        return {
            "summary": parsed.get("summary", raw),
            "bullets": parsed.get("bullets", []),
        }
    except json.JSONDecodeError:
        # Fallback — return the raw text as summary, no bullets
        return {
            "summary": raw,
            "bullets": [],
        }


async def explainer_agent(state: MFAdvisorState) -> MFAdvisorState:
    """
    Explainer Agent — Node 4 in the LangGraph pipeline.
    Now returns structured {summary, bullets} per fund.
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
            explanations[sf.fund.scheme_code] = {
                "summary": f"Explanation unavailable: {str(e)}",
                "bullets": [],
            }

    state["explanation"] = explanations
    print(f"[explainer_agent] Generated explanations for {len(explanations)} funds.")
    return state