export interface NavPoint {
  date: string;
  nav: number;
}

export interface FundRecommendation {
  scheme_code: string;
  scheme_name: string;
  category: string;
  cagr_1y: number | null;
  cagr_3y: number | null;
  cagr_5y: number | null;
  sharpe_ratio: number | null;
  volatility: number | null;
  expense_ratio: number | null;
  aum_cr: number | null;
  score: number;
  explanation: string;
  bullets: string[];
  nav_history: NavPoint[];
}

export interface RecommendResponse {
  recommendations: FundRecommendation[];
  errors: string[];
  critic_feedback: string[];
  critic_iterations: number;
  total_funds_analysed: number;
}

export interface UserProfile {
  age: number;
  monthly_sip: number;
  horizon_years: number;
  risk_level: "low" | "medium" | "high";
  goal: string;
}

export type AgentKey =
  | "data_agent"
  | "analyst_agent"
  | "recommendation_agent"
  | "critic_agent"
  | "explainer_agent";

export type AgentStatus = "idle" | "running" | "done";

export interface AgentStep {
  key: AgentKey;
  label: string;
  description: string;
  status: AgentStatus;
  iteration?: number;
}
