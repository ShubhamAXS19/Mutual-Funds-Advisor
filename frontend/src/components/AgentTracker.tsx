"use client";

import { AgentStep } from "@/types";

const icons: Record<string, string> = {
  data_agent: "🔍",
  analyst_agent: "📊",
  recommendation_agent: "🎯",
  critic_agent: "🛡️",
  explainer_agent: "🤖",
};

interface Props {
  steps: AgentStep[];
  totalFunds?: number;
  criticIterations?: number;
}

export default function AgentTracker({
  steps,
  totalFunds,
  criticIterations,
}: Props) {
  return (
    <div className="w-full max-w-xl mx-auto">
      <h2 className="text-xl font-semibold text-gray-800 mb-1 text-center">
        Analysing funds for you
      </h2>
      <div className="flex items-center justify-center gap-3 mb-8 text-xs text-gray-400">
        {totalFunds && <span>{totalFunds} funds analysed</span>}
        {criticIterations !== undefined && criticIterations > 0 && (
          <>
            <span>·</span>
            <span className="text-amber-500 font-medium">
              🛡 Critic ran {criticIterations} validation loop
              {criticIterations > 1 ? "s" : ""}
            </span>
          </>
        )}
      </div>

      <div className="relative">
        <div className="absolute left-6 top-6 bottom-6 w-px bg-gray-200" />

        <div className="space-y-4">
          {steps.map((step) => {
            const isRunning = step.status === "running";
            const isDone = step.status === "done";
            const isIdle = step.status === "idle";
            const isCritic = step.key === "critic_agent";

            return (
              <div
                key={`${step.key}-${step.iteration ?? 0}`}
                className="relative flex items-start gap-4"
              >
                {/* Circle */}
                <div
                  className={`
                    relative z-10 flex h-12 w-12 shrink-0 items-center justify-center
                    rounded-full border-2 text-xl transition-all duration-500
                    ${isDone ? (isCritic ? "border-amber-500 bg-amber-50" : "border-emerald-500 bg-emerald-50") : ""}
                    ${isRunning ? (isCritic ? "border-amber-500 bg-amber-50 shadow-md shadow-amber-100" : "border-indigo-500 bg-indigo-50 shadow-md shadow-indigo-100") : ""}
                    ${isIdle ? "border-gray-200 bg-white" : ""}
                  `}
                >
                  {isDone ? (
                    <span
                      className={`text-base ${isCritic ? "text-amber-600" : "text-emerald-600"}`}
                    >
                      ✓
                    </span>
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
                <div className="pt-2 flex-1">
                  <div className="flex items-center gap-2">
                    <p
                      className={`font-medium text-sm transition-colors duration-300
                      ${isDone ? (isCritic ? "text-amber-700" : "text-emerald-700") : ""}
                      ${isRunning ? (isCritic ? "text-amber-700" : "text-indigo-700") : ""}
                      ${isIdle ? "text-gray-400" : ""}
                    `}
                    >
                      {step.label}
                    </p>
                    {step.iteration && step.iteration > 1 && (
                      <span className="text-xs bg-amber-100 text-amber-600 px-1.5 py-0.5 rounded-full">
                        retry {step.iteration}
                      </span>
                    )}
                  </div>
                  <p
                    className={`text-xs mt-0.5 transition-colors duration-300
                    ${isRunning ? (isCritic ? "text-amber-500" : "text-indigo-500") : "text-gray-400"}
                  `}
                  >
                    {isRunning
                      ? step.description
                      : isDone
                        ? "Complete"
                        : "Waiting..."}
                  </p>
                </div>

                {/* Badge */}
                {isRunning && (
                  <div className="pt-2.5">
                    <span
                      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium border
                      ${
                        isCritic
                          ? "bg-amber-50 text-amber-600 border-amber-100"
                          : "bg-indigo-50 text-indigo-600 border-indigo-100"
                      }`}
                    >
                      <span
                        className={`h-1.5 w-1.5 rounded-full animate-pulse
                        ${isCritic ? "bg-amber-500" : "bg-indigo-500"}`}
                      />
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
