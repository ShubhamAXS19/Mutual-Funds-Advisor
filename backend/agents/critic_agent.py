from graph.state import MFAdvisorState, ScoredFund
from collections import Counter

MAX_ITERATIONS = 2
MAX_SAME_CATEGORY = 3

VOLATILITY_LIMITS = {
    "low":    0.08,
    "medium": 0.18,
    "high":   0.35,
}


def check_category_match(sf: ScoredFund, user_risk: str) -> str | None:
    if sf.fund.sub_category != user_risk:
        return (
            f"'{sf.fund.scheme_name}' is a {sf.fund.sub_category}-risk fund "
            f"but user requested {user_risk}-risk"
        )
    return None


def check_volatility(sf: ScoredFund, user_risk: str) -> str | None:
    if sf.volatility is None:
        return None
    limit = VOLATILITY_LIMITS.get(user_risk, 0.35)
    if sf.volatility > limit:
        return (
            f"'{sf.fund.scheme_name}' volatility {sf.volatility * 100:.1f}% "
            f"exceeds {user_risk}-risk limit of {limit * 100:.0f}%"
        )
    return None


def enforce_concentration_limit(funds: list[ScoredFund]) -> tuple[list[ScoredFund], list[str]]:
    """
    If more than MAX_SAME_CATEGORY funds share the same category,
    keep only the top MAX_SAME_CATEGORY by score and drop the rest.
    Returns (trimmed_funds, issues).
    """
    issues: list[str] = []
    category_buckets: dict[str, list[ScoredFund]] = {}

    for sf in funds:
        category_buckets.setdefault(sf.fund.category, []).append(sf)

    result: list[ScoredFund] = []
    for cat, bucket in category_buckets.items():
        if len(bucket) > MAX_SAME_CATEGORY:
            # Sort by score desc, keep top N
            bucket.sort(key=lambda x: x.score, reverse=True)
            dropped = bucket[MAX_SAME_CATEGORY:]
            kept = bucket[:MAX_SAME_CATEGORY]
            result.extend(kept)
            issues.append(
                f"Over-concentration in '{cat}': kept top {MAX_SAME_CATEGORY}, "
                f"dropped {len(dropped)} fund(s): "
                f"{', '.join(d.fund.scheme_name for d in dropped)}"
            )
        else:
            result.extend(bucket)

    # Re-sort by score
    result.sort(key=lambda x: x.score, reverse=True)
    return result, issues


def check_minimum(funds: list[ScoredFund]) -> str | None:
    if len(funds) < 3:
        return f"Only {len(funds)} fund(s) after filtering — minimum is 3"
    return None


async def critic_agent(state: MFAdvisorState) -> MFAdvisorState:
    """
    Critic Agent — validates recommendations and either approves or trims them.

    Unlike Phase 1 where we looped back to recommendation_agent,
    the concentration fix now happens directly here:
    - Per-fund issues (category mismatch, volatility) → remove the fund, loop back
    - Concentration → trim in place, no loop needed
    """
    state["current_step"] = "critic_agent"
    state["critic_iterations"] = state.get("critic_iterations", 0) + 1
    iteration = state["critic_iterations"]

    funds = state.get("recommended_funds", [])
    user_risk = state["user_profile"].risk_level

    if not funds:
        state["critic_approved"] = True
        state["critic_feedback"] = []
        return state

    issues: list[str] = []
    approved: list[ScoredFund] = []

    # Per-fund checks
    for sf in funds:
        fund_issues = []
        cat_issue = check_category_match(sf, user_risk)
        if cat_issue:
            fund_issues.append(cat_issue)
        vol_issue = check_volatility(sf, user_risk)
        if vol_issue:
            fund_issues.append(vol_issue)

        if fund_issues:
            issues.extend(fund_issues)
        else:
            approved.append(sf)

    # Concentration check — fix in place
    approved, concentration_issues = enforce_concentration_limit(approved)
    issues.extend(concentration_issues)

    # Minimum check
    min_issue = check_minimum(approved)
    if min_issue:
        issues.append(min_issue)

    per_fund_issues = [i for i in issues if i not in concentration_issues and min_issue not in [i]]
    has_per_fund_issues = len(per_fund_issues) > 0

    print(f"[critic_agent] Iteration {iteration} — "
          f"{len(approved)}/{len(funds)} funds approved, "
          f"{len(issues)} issue(s)")
    for issue in issues:
        print(f"  {'✗' if issue in per_fund_issues else '⚠'} {issue}")

    if not issues:
        print("[critic_agent] ✓ All checks passed.")
        state["recommended_funds"] = approved
        state["critic_approved"] = True
        state["critic_feedback"] = []

    elif has_per_fund_issues and iteration < MAX_ITERATIONS:
        # Per-fund issues remain — loop back to get replacements
        print(f"[critic_agent] Per-fund issues found, looping back (iteration {iteration})")
        state["recommended_funds"] = approved
        state["critic_approved"] = False
        state["critic_feedback"] = per_fund_issues

    else:
        # Concentration-only issues (already fixed in place) or max iterations hit
        if iteration >= MAX_ITERATIONS and has_per_fund_issues:
            state["errors"].append(
                f"Critic reached max iterations ({MAX_ITERATIONS}). "
                f"Proceeding with best available funds."
            )
        print("[critic_agent] ✓ Approving — concentration issues resolved in place.")
        state["recommended_funds"] = approved if approved else funds
        state["critic_approved"] = True
        state["critic_feedback"] = concentration_issues  # surface as info, not blocking

    return state