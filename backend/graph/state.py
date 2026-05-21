from typing import TypedDict, Optional
from dataclasses import dataclass, field


@dataclass
class UserProfile:
    age: int
    monthly_sip: float          # INR
    horizon_years: int
    risk_level: str             # "low" | "medium" | "high"
    goal: str


@dataclass
class FundData:
    scheme_code: str
    scheme_name: str
    category: str               # SEBI category string
    sub_category: str           # risk level: "low" | "medium" | "high"
    aum_cr: Optional[float]
    expense_ratio: Optional[float]
    nav_history: list[dict]     # [{"date": "...", "nav": 123.45}, ...]


@dataclass
class ScoredFund:
    fund: FundData
    cagr_1y: Optional[float]
    cagr_3y: Optional[float]
    cagr_5y: Optional[float]
    volatility: Optional[float]
    sharpe_ratio: Optional[float]
    score: float


class MFAdvisorState(TypedDict):
    # Input
    user_profile: UserProfile

    # Agent outputs
    fund_universe: list[FundData]
    scored_funds: list[ScoredFund]
    recommended_funds: list[ScoredFund]
    explanation: dict               # {scheme_code: str}

    # Critic fields (Track C)
    critic_feedback: list[str]      # rejection reasons from critic
    critic_approved: bool           # True = proceed to explainer
    critic_iterations: int          # loop counter — max 2

    # Meta
    errors: list[str]
    current_step: str