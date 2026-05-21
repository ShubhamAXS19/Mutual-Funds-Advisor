from typing import TypedDict, Optional
from dataclasses import dataclass, field


@dataclass
class UserProfile:
    age: int
    monthly_sip: float          # INR
    horizon_years: int          # investment horizon
    risk_level: str             # "low" | "medium" | "high"
    goal: str                   # e.g. "wealth creation", "retirement"


@dataclass
class FundData:
    scheme_code: str
    scheme_name: str
    category: str               # Equity, Debt, Hybrid, etc.
    sub_category: str           # Large Cap, Mid Cap, etc.
    aum_cr: Optional[float]     # AUM in crores
    expense_ratio: Optional[float]
    nav_history: list[dict]     # [{"date": "2024-01-01", "nav": 123.45}, ...]


@dataclass
class ScoredFund:
    fund: FundData
    cagr_1y: Optional[float]
    cagr_3y: Optional[float]
    cagr_5y: Optional[float]
    volatility: Optional[float]     # annualised std dev of daily returns
    sharpe_ratio: Optional[float]   # simplified: cagr_3y / volatility
    score: float                    # composite score for ranking


class MFAdvisorState(TypedDict):
    # Input
    user_profile: UserProfile

    # Data agent output
    fund_universe: list[FundData]

    # Analyst agent output
    scored_funds: list[ScoredFund]

    # Recommendation agent output
    recommended_funds: list[ScoredFund]

    # Explainer agent output
    explanation: dict               # {scheme_code: "why this fund" string}

    # Meta
    errors: list[str]
    current_step: str