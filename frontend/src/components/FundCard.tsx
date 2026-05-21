"use client";

import { useState } from "react";
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

// Return info for positive/negative CAGR colouring
function cagrColor(val: number | null): string {
  if (val === null) return "text-gray-400";
  return val >= 0 ? "text-emerald-600" : "text-rose-600";
}

export default function FundCard({ fund, rank }: Props) {
  const [expanded, setExpanded] = useState(false);
  const chartColor = CHART_COLORS[(rank - 1) % CHART_COLORS.length];

  // Determine 1Y return direction for chart label
  const returnPositive = fund.cagr_1y === null || fund.cagr_1y >= 0;

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden">
      {/* Header */}
      <div className="px-6 pt-5 pb-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 min-w-0">
            {/* Rank badge */}
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
          {/* Category pill */}
          <span
            className={`shrink-0 text-xs font-medium px-2.5 py-0.5 rounded-full border ${categoryBadge(fund.category)}`}
          >
            {fund.category
              .replace("Equity Scheme - ", "")
              .replace("Hybrid Scheme - ", "")}
          </span>
        </div>

        {/* Metrics row */}
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

      {/* Explanation */}
      <div className="px-6 pb-5 pt-2 border-t border-gray-50">
        <button
          className="flex items-center gap-1.5 text-xs font-medium text-indigo-600 hover:text-indigo-800 transition-colors mt-2 mb-2"
          onClick={() => setExpanded(!expanded)}
        >
          <span>{expanded ? "Hide" : "Why this fund?"}</span>
          <span
            className={`transition-transform duration-200 ${expanded ? "rotate-180" : ""}`}
          >
            ↓
          </span>
        </button>
        {expanded && (
          <p className="text-sm text-gray-600 leading-relaxed bg-indigo-50 rounded-xl p-4 border border-indigo-100">
            {fund.explanation}
          </p>
        )}
      </div>
    </div>
  );
}
