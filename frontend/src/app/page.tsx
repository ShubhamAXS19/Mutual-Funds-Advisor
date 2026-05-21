"use client";

import { useState } from "react";
import ProfileForm from "@/components/ProfileForm";
import AgentTracker from "@/components/AgentTracker";
import FundCard from "@/components/FundCard";
import { UserProfile, FundRecommendation, AgentStep, AgentKey } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const INITIAL_STEPS: AgentStep[] = [
  {
    key: "data_agent",
    label: "Data agent",
    description: "Fetching mutual fund universe from MFAPI",
    status: "idle",
  },
  {
    key: "analyst_agent",
    label: "Analyst agent",
    description: "Computing CAGR, Sharpe ratio, and volatility",
    status: "idle",
  },
  {
    key: "recommendation_agent",
    label: "Recommendation agent",
    description: "Filtering top 5 funds for your profile",
    status: "idle",
  },
  {
    key: "explainer_agent",
    label: "Explainer agent",
    description: "Generating plain-English rationale via LLM",
    status: "idle",
  },
];

type Screen = "form" | "loading" | "results" | "error";

export default function Home() {
  const [screen, setScreen] = useState<Screen>("form");
  const [steps, setSteps] = useState<AgentStep[]>(INITIAL_STEPS);
  const [results, setResults] = useState<FundRecommendation[]>([]);
  const [totalAnalysed, setTotalAnalysed] = useState(0);
  const [errorMsg, setErrorMsg] = useState("");
  const [profile, setProfile] = useState<UserProfile | null>(null);

  function updateStep(key: AgentKey, status: AgentStep["status"]) {
    setSteps((prev) => prev.map((s) => (s.key === key ? { ...s, status } : s)));
  }

  async function handleSubmit(p: UserProfile) {
    setProfile(p);
    setSteps(INITIAL_STEPS);
    setResults([]);
    setScreen("loading");

    try {
      const response = await fetch(`${API_BASE}/recommend/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(p),
      });

      if (!response.ok || !response.body) {
        throw new Error(`Server error: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        let eventType = "";
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith("data: ")) {
            const payload = JSON.parse(line.slice(6));

            if (eventType === "agent_start") {
              updateStep(payload.agent as AgentKey, "running");
            } else if (eventType === "agent_done") {
              updateStep(payload.agent as AgentKey, "done");
            } else if (eventType === "complete") {
              setResults(payload.recommendations);
              setTotalAnalysed(payload.total_funds_analysed);
              setScreen("results");
            } else if (eventType === "error") {
              throw new Error(payload.message);
            }
          }
        }
      }
    } catch (err: any) {
      setErrorMsg(err.message ?? "Something went wrong");
      setScreen("error");
    }
  }

  function reset() {
    setScreen("form");
    setSteps(INITIAL_STEPS);
    setResults([]);
    setErrorMsg("");
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-12">
        {/* FORM */}
        {screen === "form" && (
          <ProfileForm onSubmit={handleSubmit} loading={false} />
        )}

        {/* LOADING — agent tracker */}
        {screen === "loading" && (
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8">
            <AgentTracker steps={steps} />
          </div>
        )}

        {/* RESULTS */}
        {screen === "results" && (
          <div>
            {/* Results header */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-bold text-gray-900">
                  Top {results.length} funds for you
                </h2>
                <p className="text-sm text-gray-400 mt-0.5">
                  {totalAnalysed} funds analysed · {profile?.risk_level} risk ·{" "}
                  {profile?.horizon_years}yr horizon
                </p>
              </div>
              <button
                onClick={reset}
                className="text-sm text-indigo-600 hover:text-indigo-800 font-medium border border-indigo-100 rounded-xl px-4 py-2 hover:bg-indigo-50 transition-colors"
              >
                ← Start over
              </button>
            </div>

            {/* Agent tracker — collapsed/done state */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 mb-6">
              <AgentTracker
                steps={steps.map((s) => ({ ...s, status: "done" }))}
                totalFunds={totalAnalysed}
              />
            </div>

            {/* Fund cards */}
            <div className="space-y-4">
              {results.map((fund, idx) => (
                <FundCard key={fund.scheme_code} fund={fund} rank={idx + 1} />
              ))}
            </div>

            <p className="text-center text-xs text-gray-400 mt-8">
              Past performance is not indicative of future returns. Not
              SEBI-registered financial advice.
            </p>
          </div>
        )}

        {/* ERROR */}
        {screen === "error" && (
          <div className="bg-white rounded-2xl border border-rose-100 shadow-sm p-8 text-center">
            <div className="text-4xl mb-4">⚠️</div>
            <h2 className="text-lg font-semibold text-gray-900 mb-2">
              Something went wrong
            </h2>
            <p className="text-sm text-gray-500 mb-6">{errorMsg}</p>
            <button
              onClick={reset}
              className="rounded-xl bg-indigo-600 text-white px-6 py-2.5 text-sm font-semibold hover:bg-indigo-700"
            >
              Try again
            </button>
          </div>
        )}
      </div>
    </main>
  );
}
