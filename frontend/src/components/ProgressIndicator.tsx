"use client";

import { PipelineStage } from "@/lib/types";

interface ProgressIndicatorProps {
  stage: PipelineStage;
  message: string;
  progress: number;
}

const STAGES = [
  { key: "analysis", icon: "hourglass", label: "Analyzing songs..." },
  { key: "strategy", icon: "brain", label: "AI is choosing the best transition..." },
  { key: "render", icon: "wrench", label: "Rendering your mix..." },
  { key: "complete", icon: "check", label: "Your mix is ready!" },
] as const;

export default function ProgressIndicator({ stage, message, progress }: ProgressIndicatorProps) {
  if (stage === "idle") return null;

  const currentIdx = STAGES.findIndex((s) => s.key === stage);

  return (
    <div className="bg-zinc-900/50 rounded-xl p-6 border border-zinc-800">
      {/* Progress bar */}
      <div className="h-2 bg-zinc-800 rounded-full overflow-hidden mb-4">
        <div
          className="h-full bg-gradient-to-r from-indigo-500 to-pink-500 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${progress * 100}%` }}
        />
      </div>

      {/* Stage indicators */}
      <div className="flex justify-between mb-4">
        {STAGES.map((s, i) => {
          const isActive = s.key === stage;
          const isDone = currentIdx > i || stage === "complete";

          return (
            <div
              key={s.key}
              className={`flex items-center gap-2 text-sm ${
                isActive ? "text-indigo-400 font-semibold" :
                isDone ? "text-green-400" : "text-zinc-600"
              }`}
            >
              <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs border ${
                isActive ? "border-indigo-500 bg-indigo-500/20" :
                isDone ? "border-green-500 bg-green-500/20" : "border-zinc-700"
              }`}>
                {isDone && s.key !== stage ? (
                  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clipRule="evenodd" />
                  </svg>
                ) : (
                  i + 1
                )}
              </span>
              <span className="hidden sm:inline">{s.label}</span>
            </div>
          );
        })}
      </div>

      {/* Current message */}
      <div className="text-center">
        {stage === "error" ? (
          <p className="text-red-400">{message}</p>
        ) : stage === "complete" ? (
          <p className="text-green-400 font-semibold">{message}</p>
        ) : (
          <div className="flex items-center justify-center gap-2 text-zinc-400">
            <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span>{message}</span>
          </div>
        )}
      </div>
    </div>
  );
}
