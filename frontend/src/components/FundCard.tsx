"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import { FundRecommendation } from "@/types";
import NavChart from "./NavChart";

interface Props {
  fund: FundRecommendation;
  rank: number;
}

function pct(val: number | null): string {
  if (val === null) return "N/A";
  return `${(val * 100).toFixed(1)}%`;
}

function fmt(val: number | null, decimals = 2): string {
  if (val === null) return "N/A";
  return val.toFixed(decimals);
}

function inr(val: number | null): string {
  if (val === null) return "N/A";
  if (val >= 1000) return `₹${(val / 1000).toFixed(1)}K Cr`;
  return `₹${val.toFixed(0)} Cr`;
}

const CHART_COLORS = ["#6366f1", "#10b981", "#f59e0b", "#3b82f6", "#ec4899"];

const CATEGORY_COLORS: Record<string, string> = {
  equity: "bg-rose-50 text-rose-700 border-rose-100",
  debt: "bg-blue-50 text-blue-700 border-blue-100",
  hybrid: "bg-amber-50 text-amber-700 border-amber-100",
  default: "bg-gray-50 text-gray-600 border-gray-100",
};

function categoryBadge(category: string): string {
  const lower = category.toLowerCase();
  if (lower.includes("equity")) return CATEGORY_COLORS.equity;
  if (lower.includes("debt") || lower.includes("income"))
    return CATEGORY_COLORS.debt;
  if (lower.includes("hybrid")) return CATEGORY_COLORS.hybrid;
  return CATEGORY_COLORS.default;
}

function cagrColor(val: number | null): string {
  if (val === null) return "text-gray-400";
  return val >= 0 ? "text-emerald-600" : "text-rose-600";
}

type ExplainView = "hidden" | "summary" | "bullets";

export default function FundCard({ fund, rank }: Props) {
  const [explainView, setExplainView] = useState<ExplainView>("hidden");
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const { data: session } = useSession();

  async function saveToWatchlist() {
    if (!session) {
      window.location.href = "/auth/signin";
      return;
    }
    setSaving(true);
    try {
      await fetch("/api/watchlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          schemeCode: fund.scheme_code,
          schemeName: fund.scheme_name,
          category: fund.category,
          sipAmount: 0,
        }),
      });
      setSaved(true);
    } finally {
      setSaving(false);
    }
  }
  const chartColor = CHART_COLORS[(rank - 1) % CHART_COLORS.length];
  const returnPositive = fund.cagr_1y === null || fund.cagr_1y >= 0;
  const hasBullets = fund.bullets && fund.bullets.length > 0;

  function toggleView(view: ExplainView) {
    setExplainView((prev) => (prev === view ? "hidden" : view));
  }

  // Last bullet is caveat — style differently
  const reasonBullets = hasBullets ? fund.bullets.slice(0, -1) : [];
  const caveat = hasBullets ? fund.bullets[fund.bullets.length - 1] : null;

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden">
      {/* Header */}
      <div className="px-6 pt-5 pb-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 min-w-0">
            <div
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-white text-sm font-semibold"
              style={{ backgroundColor: chartColor }}
            >
              {rank}
            </div>
            <div className="min-w-0">
              <h3 className="font-semibold text-gray-900 text-sm leading-snug">
                {fund.scheme_name}
              </h3>
              <p className="text-xs text-gray-400 mt-0.5 truncate">
                {fund.scheme_code}
              </p>
            </div>
          </div>
          <span
            className={`shrink-0 text-xs font-medium px-2.5 py-0.5 rounded-full border ${categoryBadge(fund.category)}`}
          >
            {fund.category
              .replace("Equity Scheme - ", "")
              .replace("Hybrid Scheme - ", "")
              .replace("Debt Scheme - ", "")}
          </span>
        </div>

        {/* Metrics */}
        <div className="mt-4 grid grid-cols-5 gap-2 text-center">
          {[
            {
              label: "1Y Return",
              value: pct(fund.cagr_1y),
              color: cagrColor(fund.cagr_1y),
            },
            {
              label: "3Y Return",
              value: pct(fund.cagr_3y),
              color: cagrColor(fund.cagr_3y),
            },
            {
              label: "5Y Return",
              value: pct(fund.cagr_5y),
              color: cagrColor(fund.cagr_5y),
            },
            {
              label: "Sharpe",
              value: fmt(fund.sharpe_ratio),
              color: "text-gray-800",
            },
            {
              label: "Volatility",
              value: pct(fund.volatility),
              color: "text-gray-800",
            },
          ].map((m) => (
            <div key={m.label} className="bg-gray-50 rounded-xl px-1 py-2.5">
              <p className={`text-sm font-semibold ${m.color}`}>{m.value}</p>
              <p className="text-xs text-gray-400 mt-0.5 leading-tight">
                {m.label}
              </p>
            </div>
          ))}
        </div>

        {/* Fund details row */}
        <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <span className="text-gray-400">Expense ratio</span>
            <span className="font-medium text-gray-700">
              {fund.expense_ratio !== null ? `${fund.expense_ratio}%` : "N/A"}
            </span>
          </span>
          <span className="text-gray-200">|</span>
          <span className="flex items-center gap-1">
            <span className="text-gray-400">AUM</span>
            <span className="font-medium text-gray-700">
              {inr(fund.aum_cr)}
            </span>
          </span>
          <span className="text-gray-200">|</span>
          <span className="flex items-center gap-1">
            <span className="text-gray-400">Score</span>
            <span className="font-medium text-gray-700">
              {(fund.score * 100).toFixed(1)}
            </span>
          </span>
        </div>
      </div>

      {/* NAV Chart */}
      {fund.nav_history.length > 10 && (
        <div className="px-4 pb-2">
          <div className="flex items-center justify-between mb-1 px-1">
            <p className="text-xs text-gray-400 font-medium">
              NAV — last 1 year
            </p>
            <p
              className={`text-xs font-medium ${returnPositive ? "text-emerald-600" : "text-rose-600"}`}
            >
              {returnPositive ? "▲" : "▼"} {pct(fund.cagr_1y)} (1Y)
            </p>
          </div>
          <NavChart data={fund.nav_history} color={chartColor} />
        </div>
      )}

      {/* Explanation toggle row */}
      <div className="px-6 pb-5 pt-3 border-t border-gray-50">
        <div className="flex items-center gap-2">
          {/* Summary toggle */}
          <button
            onClick={() => toggleView("summary")}
            className={`flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full border transition-all duration-150
              ${
                explainView === "summary"
                  ? "bg-indigo-600 text-white border-indigo-600"
                  : "bg-white text-indigo-600 border-indigo-200 hover:bg-indigo-50"
              }`}
          >
            <span>📝</span>
            <span>Summary</span>
          </button>

          {/* Bullets toggle */}
          {hasBullets && (
            <button
              onClick={() => toggleView("bullets")}
              className={`flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full border transition-all duration-150
                ${
                  explainView === "bullets"
                    ? "bg-indigo-600 text-white border-indigo-600"
                    : "bg-white text-indigo-600 border-indigo-200 hover:bg-indigo-50"
                }`}
            >
              <span>✦</span>
              <span>Why this fund?</span>
            </button>
          )}
        </div>

        {/* Summary view */}
        {explainView === "summary" && (
          <div className="mt-3 text-sm text-gray-600 leading-relaxed bg-indigo-50 rounded-xl p-4 border border-indigo-100">
            {fund.explanation}
          </div>
        )}

        {/* Bullets view */}
        {explainView === "bullets" && hasBullets && (
          <div className="mt-3 bg-indigo-50 rounded-xl p-4 border border-indigo-100 space-y-2">
            {/* Reason bullets */}
            <ul className="space-y-2">
              {reasonBullets.map((bullet, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2.5 text-sm text-gray-700"
                >
                  <span
                    className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-white text-xs font-bold"
                    style={{ backgroundColor: chartColor }}
                  >
                    {i + 1}
                  </span>
                  <span className="leading-snug">{bullet}</span>
                </li>
              ))}
            </ul>

            {/* Caveat — last bullet, styled differently */}
            {caveat && (
              <div className="mt-3 pt-3 border-t border-indigo-100 flex items-start gap-2">
                <span className="text-amber-500 text-sm mt-0.5">⚠</span>
                <p className="text-xs text-amber-700 leading-snug">{caveat}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
