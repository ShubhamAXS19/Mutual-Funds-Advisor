"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";

interface WatchlistEntry {
  id: string;
  schemeCode: string;
  schemeName: string;
  category: string;
  sipAmount: number;
  sipStartDate: string;
  addedAt: string;
}

function categoryColor(category: string): string {
  const lower = category.toLowerCase();
  if (lower.includes("equity"))
    return "bg-rose-50 text-rose-700 border-rose-100";
  if (lower.includes("debt") || lower.includes("income"))
    return "bg-blue-50 text-blue-700 border-blue-100";
  if (lower.includes("hybrid"))
    return "bg-amber-50 text-amber-700 border-amber-100";
  return "bg-gray-50 text-gray-600 border-gray-100";
}

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [watchlist, setWatchlist] = useState<WatchlistEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/auth/signin");
    }
  }, [status, router]);

  useEffect(() => {
    if (status === "authenticated") {
      fetch("/api/watchlist")
        .then((r) => r.json())
        .then((data) => {
          setWatchlist(data.watchlist ?? []);
          setLoading(false);
        });
    }
  }, [status]);

  async function removeFromWatchlist(schemeCode: string) {
    await fetch(`/api/watchlist/${schemeCode}`, { method: "DELETE" });
    setWatchlist((prev) => prev.filter((e) => e.schemeCode !== schemeCode));
  }

  if (status === "loading" || loading) {
    return (
      <main className="min-h-screen bg-gray-50">
        <div className="max-w-2xl mx-auto px-4 py-12">
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-28 bg-white rounded-2xl border border-gray-100 animate-pulse"
              />
            ))}
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Your watchlist</h1>
            <p className="text-sm text-gray-400 mt-0.5">
              {watchlist.length} fund{watchlist.length !== 1 ? "s" : ""} saved
            </p>
          </div>
          <Link
            href="/"
            className="text-sm font-medium text-indigo-600 border border-indigo-100 rounded-xl px-4 py-2 hover:bg-indigo-50 transition-colors"
          >
            + Get recommendations
          </Link>
        </div>

        {/* Empty state */}
        {watchlist.length === 0 && (
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-12 text-center">
            <div className="text-4xl mb-4">📭</div>
            <h2 className="text-base font-semibold text-gray-900 mb-1">
              No funds saved yet
            </h2>
            <p className="text-sm text-gray-400 mb-6">
              Get recommendations and save funds to track their performance.
            </p>
            <Link
              href="/"
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 text-white px-5 py-2.5 text-sm font-semibold hover:bg-indigo-700 transition-colors"
            >
              Get recommendations →
            </Link>
          </div>
        )}

        {/* Watchlist entries */}
        <div className="space-y-3">
          {watchlist.map((entry) => {
            const addedDate = new Date(entry.sipStartDate).toLocaleDateString(
              "en-IN",
              {
                day: "numeric",
                month: "short",
                year: "numeric",
              },
            );

            return (
              <div
                key={entry.id}
                className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`text-xs font-medium px-2 py-0.5 rounded-full border ${categoryColor(entry.category)}`}
                      >
                        {entry.category
                          .replace("Equity Scheme - ", "")
                          .replace("Hybrid Scheme - ", "")
                          .replace("Debt Scheme - ", "")}
                      </span>
                    </div>
                    <h3 className="font-semibold text-gray-900 text-sm leading-snug">
                      {entry.schemeName}
                    </h3>
                    <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                      <span>SIP from {addedDate}</span>
                      {entry.sipAmount > 0 && (
                        <>
                          <span>·</span>
                          <span>
                            ₹{entry.sipAmount.toLocaleString("en-IN")}/mo
                          </span>
                        </>
                      )}
                    </div>
                  </div>

                  <button
                    onClick={() => removeFromWatchlist(entry.schemeCode)}
                    className="shrink-0 text-xs text-gray-300 hover:text-rose-500 transition-colors pt-0.5"
                    title="Remove from watchlist"
                  >
                    ✕
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {watchlist.length > 0 && (
          <p className="text-center text-xs text-gray-400 mt-8">
            Performance tracking and market intelligence coming soon.
          </p>
        )}
      </div>
    </main>
  );
}
