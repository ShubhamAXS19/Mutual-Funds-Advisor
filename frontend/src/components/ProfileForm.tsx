"use client";

import { useState } from "react";
import { UserProfile } from "@/types";

interface Props {
  onSubmit: (profile: UserProfile) => void;
  loading: boolean;
}

const GOALS = [
  "Wealth creation",
  "Retirement planning",
  "Child education",
  "Tax saving",
  "Emergency fund",
  "Home purchase",
];

export default function ProfileForm({ onSubmit, loading }: Props) {
  const [form, setForm] = useState<UserProfile>({
    age: 28,
    monthly_sip: 5000,
    horizon_years: 7,
    risk_level: "medium",
    goal: "Wealth creation",
  });

  const [errors, setErrors] = useState<
    Partial<Record<keyof UserProfile, string>>
  >({});

  function validate(): boolean {
    const e: Partial<Record<keyof UserProfile, string>> = {};
    if (form.age < 18 || form.age > 80) e.age = "Age must be between 18–80";
    if (form.monthly_sip < 500) e.monthly_sip = "Minimum SIP is ₹500";
    if (form.horizon_years < 1 || form.horizon_years > 30)
      e.horizon_years = "Horizon must be 1–30 years";
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (validate()) onSubmit(form);
  }

  const riskOptions: {
    value: UserProfile["risk_level"];
    label: string;
    desc: string;
    color: string;
  }[] = [
    {
      value: "low",
      label: "Conservative",
      desc: "Debt & liquid funds",
      color: "border-blue-400 bg-blue-50 text-blue-700",
    },
    {
      value: "medium",
      label: "Moderate",
      desc: "Balanced & hybrid",
      color: "border-amber-400 bg-amber-50 text-amber-700",
    },
    {
      value: "high",
      label: "Aggressive",
      desc: "Equity & mid/small cap",
      color: "border-rose-400 bg-rose-50 text-rose-700",
    },
  ];

  return (
    <div className="w-full max-w-lg mx-auto">
      <div className="mb-8 text-center">
        <div className="inline-flex items-center justify-center h-14 w-14 rounded-2xl bg-indigo-600 mb-4">
          <span className="text-2xl">📈</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">MF Advisor</h1>
        <p className="text-gray-500 text-sm mt-1">
          AI-powered mutual fund recommendations for the Indian market
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-5"
      >
        {/* Age + SIP row */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1.5">
              Age
            </label>
            <input
              type="number"
              value={form.age}
              onChange={(e) => setForm({ ...form, age: +e.target.value })}
              className="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-transparent"
              placeholder="28"
            />
            {errors.age && (
              <p className="text-rose-500 text-xs mt-1">{errors.age}</p>
            )}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1.5">
              Monthly SIP (₹)
            </label>
            <input
              type="number"
              value={form.monthly_sip}
              onChange={(e) =>
                setForm({ ...form, monthly_sip: +e.target.value })
              }
              className="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-transparent"
              placeholder="5000"
            />
            {errors.monthly_sip && (
              <p className="text-rose-500 text-xs mt-1">{errors.monthly_sip}</p>
            )}
          </div>
        </div>

        {/* Horizon */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1.5">
            Investment horizon —{" "}
            <span className="text-indigo-600 font-semibold">
              {form.horizon_years} years
            </span>
          </label>
          <input
            type="range"
            min={1}
            max={30}
            value={form.horizon_years}
            onChange={(e) =>
              setForm({ ...form, horizon_years: +e.target.value })
            }
            className="w-full accent-indigo-600"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>1 yr</span>
            <span>30 yrs</span>
          </div>
        </div>

        {/* Risk level */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-2">
            Risk tolerance
          </label>
          <div className="grid grid-cols-3 gap-2">
            {riskOptions.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setForm({ ...form, risk_level: opt.value })}
                className={`rounded-xl border-2 p-3 text-left transition-all duration-150
                  ${form.risk_level === opt.value ? opt.color + " border-2" : "border-gray-100 bg-gray-50 text-gray-500 hover:border-gray-200"}
                `}
              >
                <p className="text-xs font-semibold">{opt.label}</p>
                <p className="text-xs opacity-75 mt-0.5">{opt.desc}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Goal */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1.5">
            Investment goal
          </label>
          <select
            value={form.goal}
            onChange={(e) => setForm({ ...form, goal: e.target.value })}
            className="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-transparent bg-white"
          >
            {GOALS.map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white font-semibold py-3 text-sm transition-colors duration-150"
        >
          {loading ? "Analysing..." : "Get recommendations →"}
        </button>
      </form>

      <p className="text-center text-xs text-gray-400 mt-4">
        Not financial advice. Always verify recommendations independently.
      </p>
    </div>
  );
}
