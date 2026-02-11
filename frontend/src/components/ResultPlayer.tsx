"use client";

import { useState } from "react";
import WaveformPlayer from "./WaveformPlayer";
import { MixDecision } from "@/lib/types";
import { getDownloadUrl } from "@/lib/api";

interface ResultPlayerProps {
  sessionId: string;
  mixDecision: MixDecision;
  downloadUrl: string;
  onRegenerate?: () => void;
  isRegenerating?: boolean;
}

export default function ResultPlayer({ sessionId, mixDecision, downloadUrl, onRegenerate, isRegenerating }: ResultPlayerProps) {
  const [showReasoning, setShowReasoning] = useState(false);

  const strategyLabels: Record<string, string> = {
    phrase_blend: "Phrase Blend",
    drop_swap: "Drop Swap",
    echo_out: "Echo Out",
    bass_swap: "Bass Swap",
    breakdown_bridge: "Breakdown Bridge",
    incompatible: "Incompatible",
  };

  return (
    <div className="bg-zinc-900/50 rounded-xl p-6 border border-zinc-800 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-zinc-200">Your Mix</h2>
        <div className="flex items-center gap-2">
          <span className={`px-2 py-1 rounded text-xs font-medium ${mixDecision.confidence >= 0.8 ? "bg-green-500/20 text-green-400" :
              mixDecision.confidence >= 0.5 ? "bg-yellow-500/20 text-yellow-400" :
                "bg-red-500/20 text-red-400"
            }`}>
            {strategyLabels[mixDecision.strategy] || mixDecision.strategy}
          </span>
          <span className="text-xs text-zinc-500">
            Confidence: {(mixDecision.confidence * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Waveform player for the mix */}
      <WaveformPlayer
        audioUrl={getDownloadUrl(sessionId)}
        color="#8b5cf6"
        label="Mixed Output"
        showPhraseMarkers={false}
      />

      {/* Download button */}
      <div className="flex gap-3">
        <a
          href={getDownloadUrl(sessionId)}
          download={`smart_dj_mix_${sessionId}.mp3`}
          className="flex-1 flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg py-3 px-4 font-medium transition-colors"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Download MP3 (320kbps)
        </a>
        {onRegenerate && (
          <button
            onClick={onRegenerate}
            disabled={isRegenerating}
            className={`flex items-center justify-center gap-2 rounded-lg py-3 px-5 font-medium transition-colors ${isRegenerating
                ? "bg-zinc-800 text-zinc-500 cursor-not-allowed"
                : "bg-zinc-700 hover:bg-zinc-600 text-zinc-200"
              }`}
          >
            <svg className={`w-5 h-5 ${isRegenerating ? "animate-spin" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {isRegenerating ? "Regenerating..." : "Regenerate"}
          </button>
        )}
      </div>

      {/* AI Reasoning panel */}
      <div className="border border-zinc-800 rounded-lg overflow-hidden">
        <button
          onClick={() => setShowReasoning(!showReasoning)}
          className="w-full flex items-center justify-between p-3 text-sm text-zinc-400 hover:text-zinc-300"
        >
          <span>AI Reasoning</span>
          <svg
            className={`w-4 h-4 transition-transform ${showReasoning ? "rotate-180" : ""}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {showReasoning && (
          <div className="p-3 pt-0 text-sm text-zinc-400 border-t border-zinc-800">
            <p className="whitespace-pre-wrap">{mixDecision.reasoning}</p>

            <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-zinc-500">
              <div>
                <span className="font-medium">Transition duration:</span>{" "}
                {(mixDecision.transition.total_duration_ms / 1000).toFixed(1)}s
              </div>
              <div>
                <span className="font-medium">Crossfade curve:</span>{" "}
                {mixDecision.transition.crossfade_curve}
              </div>
              <div>
                <span className="font-medium">Song A stretch:</span>{" "}
                {mixDecision.song_a.tempo_stretch_factor.toFixed(3)}x
              </div>
              <div>
                <span className="font-medium">Song B stretch:</span>{" "}
                {mixDecision.song_b.tempo_stretch_factor.toFixed(3)}x
              </div>
              {mixDecision.sfx.enabled && (
                <div className="col-span-2">
                  <span className="font-medium">SFX:</span>{" "}
                  {mixDecision.sfx.type} ({mixDecision.sfx.trigger_reason})
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
