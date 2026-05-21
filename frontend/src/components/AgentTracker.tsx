"use client";

import { AgentStep } from "@/types";

const icons: Record<string, string> = {
  data_agent: "🔍",
  analyst_agent: "📊",
  recommendation_agent: "🎯",
  explainer_agent: "🤖",
};

interface Props {
  steps: AgentStep[];
  totalFunds?: number;
}

export default function AgentTracker({ steps, totalFunds }: Props) {
  return (
    <div className="w-full max-w-xl mx-auto">
      <h2 className="text-xl font-semibold text-gray-800 mb-2 text-center">
        Analysing funds for you
      </h2>
      {totalFunds && (
        <p className="text-sm text-gray-500 text-center mb-8">
          {totalFunds} funds analysed
        </p>
      )}

      <div className="relative">
        {/* Vertical connector line */}
        <div className="absolute left-6 top-6 bottom-6 w-px bg-gray-200" />

        <div className="space-y-4">
          {steps.map((step, idx) => {
            const isRunning = step.status === "running";
            const isDone = step.status === "done";
            const isIdle = step.status === "idle";

            return (
              <div key={step.key} className="relative flex items-start gap-4">
                {/* Circle indicator */}
                <div
                  className={`
                    relative z-10 flex h-12 w-12 shrink-0 items-center justify-center
                    rounded-full border-2 text-xl transition-all duration-500
                    ${isDone ? "border-emerald-500 bg-emerald-50" : ""}
                    ${isRunning ? "border-indigo-500 bg-indigo-50 shadow-md shadow-indigo-100" : ""}
                    ${isIdle ? "border-gray-200 bg-white" : ""}
                  `}
                >
                  {isDone ? (
                    <span className="text-emerald-600 text-base">✓</span>
                  ) : isRunning ? (
                    <span className="animate-spin inline-block text-base">
                      ⟳
                    </span>
                  ) : (
                    <span className={isIdle ? "opacity-30" : ""}>
                      {icons[step.key]}
                    </span>
                  )}
                </div>

                {/* Text */}
                <div className="pt-2">
                  <p
                    className={`font-medium text-sm transition-colors duration-300
                      ${isDone ? "text-emerald-700" : ""}
                      ${isRunning ? "text-indigo-700" : ""}
                      ${isIdle ? "text-gray-400" : ""}
                    `}
                  >
                    {step.label}
                  </p>
                  <p
                    className={`text-xs mt-0.5 transition-colors duration-300
                      ${isRunning ? "text-indigo-500" : "text-gray-400"}
                    `}
                  >
                    {isRunning
                      ? step.description
                      : isDone
                        ? "Complete"
                        : "Waiting..."}
                  </p>
                </div>

                {/* Running pulse badge */}
                {isRunning && (
                  <div className="ml-auto pt-2.5">
                    <span className="inline-flex items-center gap-1 rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-medium text-indigo-600 border border-indigo-100">
                      <span className="h-1.5 w-1.5 rounded-full bg-indigo-500 animate-pulse" />
                      Running
                    </span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
