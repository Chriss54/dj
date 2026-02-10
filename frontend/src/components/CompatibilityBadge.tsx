"use client";

import { Compatibility } from "@/lib/types";

interface CompatibilityBadgeProps {
  compatibility: Compatibility;
}

export default function CompatibilityBadge({ compatibility }: CompatibilityBadgeProps) {
  const { bpm_diff, camelot_relation, harmonic_mixing_score, key_compatible } = compatibility;

  let level: "great" | "workable" | "challenging";
  let label: string;
  let description: string;

  if (
    (key_compatible === true || camelot_relation === "same" || camelot_relation === "adjacent") &&
    bpm_diff < 3
  ) {
    level = "great";
    label = "Great Match";
    description = "Compatible key and tempo — this should blend beautifully.";
  } else if (
    (camelot_relation === "adjacent" || camelot_relation === "relative") &&
    bpm_diff <= 6
  ) {
    level = "workable";
    label = "Workable";
    description = `BPM difference: ${bpm_diff.toFixed(1)}. Key relation: ${camelot_relation}. Tempo adjustment will be applied.`;
  } else {
    level = "challenging";
    label = "Challenging";
    description = `These songs have ${bpm_diff > 6 ? "a large BPM difference" : ""}${bpm_diff > 6 && key_compatible === false ? " and " : ""}${key_compatible === false ? "clashing keys" : ""}. The mix may sound rough.`;
  }

  const colors = {
    great: "bg-green-500/20 text-green-400 border-green-500/30",
    workable: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    challenging: "bg-red-500/20 text-red-400 border-red-500/30",
  };

  const icons = {
    great: (
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
      </svg>
    ),
    workable: (
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
      </svg>
    ),
    challenging: (
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
      </svg>
    ),
  };

  return (
    <div className={`rounded-lg border p-4 ${colors[level]}`}>
      <div className="flex items-center gap-2 font-semibold text-lg mb-1">
        {icons[level]}
        {label}
      </div>
      <p className="text-sm opacity-80">{description}</p>
      <div className="flex gap-4 mt-2 text-xs opacity-70">
        <span>BPM diff: {bpm_diff.toFixed(1)}</span>
        <span>Harmonic score: {(harmonic_mixing_score * 100).toFixed(0)}%</span>
        <span>Target BPM: {compatibility.recommended_target_bpm}</span>
      </div>
    </div>
  );
}
