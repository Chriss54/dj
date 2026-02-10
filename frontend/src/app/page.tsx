"use client";

import { useState, useCallback } from "react";
import DualDeckUpload from "@/components/DualDeckUpload";
import AnalysisDashboard from "@/components/AnalysisDashboard";
import ProgressIndicator from "@/components/ProgressIndicator";
import ResultPlayer from "@/components/ResultPlayer";
import AdvancedSettings from "@/components/AdvancedSettings";
import { useWebSocket } from "@/hooks/useWebSocket";
import { createMix } from "@/lib/api";
import type {
  UploadResult, SongAnalysis, Compatibility, MixResult, PipelineStage,
} from "@/lib/types";

export default function Home() {
  // Upload state
  const [deckA, setDeckA] = useState<UploadResult | null>(null);
  const [deckB, setDeckB] = useState<UploadResult | null>(null);

  // Analysis state
  const [songA, setSongA] = useState<SongAnalysis | null>(null);
  const [songB, setSongB] = useState<SongAnalysis | null>(null);
  const [compatibility, setCompatibility] = useState<Compatibility | null>(null);

  // Mix state
  const [transitionStartMs, setTransitionStartMs] = useState<number | null>(null);
  const [songBInPointMs, setSongBInPointMs] = useState<number | null>(null);
  const [mixResult, setMixResult] = useState<MixResult | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Advanced settings
  const [strategy, setStrategy] = useState<string | null>(null);
  const [enableSfx, setEnableSfx] = useState(true);
  const [mixInKey, setMixInKey] = useState(false);
  const [bpmOverrideA, setBpmOverrideA] = useState<number | null>(null);
  const [bpmOverrideB, setBpmOverrideB] = useState<number | null>(null);
  const [keyOverrideA, setKeyOverrideA] = useState<string | null>(null);
  const [keyOverrideB, setKeyOverrideB] = useState<string | null>(null);

  // Progress
  const [pipelineStage, setPipelineStage] = useState<PipelineStage>("idle");
  const [progressMessage, setProgressMessage] = useState("");
  const [progressValue, setProgressValue] = useState(0);

  // WebSocket for real-time updates
  const wsSession = mixResult?.session_id || null;
  useWebSocket(wsSession);

  const handleUploadComplete = useCallback((deck: "a" | "b", result: UploadResult) => {
    if (deck === "a") {
      setDeckA(result);
      setSongA(result.analysis);
    } else {
      setDeckB(result);
      setSongB(result.analysis);
    }

    // If both songs are uploaded, compute compatibility
    if (deck === "a" && deckB) {
      setCompatibility(computeClientCompatibility(result.analysis, deckB.analysis));
    } else if (deck === "b" && deckA) {
      setCompatibility(computeClientCompatibility(deckA.analysis, result.analysis));
    }

    setMixResult(null);
    setError(null);
  }, [deckA, deckB]);

  const handleGenerateMix = useCallback(async () => {
    if (!deckA || !deckB) return;

    setIsGenerating(true);
    setError(null);
    setMixResult(null);
    setPipelineStage("analysis");
    setProgressMessage("Starting pipeline...");
    setProgressValue(0.05);

    try {
      setPipelineStage("strategy");
      setProgressMessage("AI is choosing the best transition...");
      setProgressValue(0.4);

      const result = await createMix({
        song_a_path: deckA.file_path,
        song_b_path: deckB.file_path,
        transition_start_ms: transitionStartMs ?? undefined,
        song_b_in_point_ms: songBInPointMs ?? undefined,
        strategy: strategy ?? undefined,
        enable_sfx: enableSfx,
        mix_in_key: mixInKey,
      });

      setPipelineStage("complete");
      setProgressMessage("Your mix is ready!");
      setProgressValue(1.0);
      setMixResult(result);
    } catch (e) {
      setPipelineStage("error");
      const msg = e instanceof Error ? e.message : "Mix generation failed";
      setProgressMessage(msg);
      setError(msg);
    } finally {
      setIsGenerating(false);
    }
  }, [deckA, deckB, transitionStartMs, songBInPointMs, strategy, enableSfx, mixInKey]);

  const bothUploaded = deckA !== null && deckB !== null;

  return (
    <div className="min-h-screen bg-zinc-950">
      {/* Header */}
      <header className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-pink-500 flex items-center justify-center text-lg font-bold">
              DJ
            </div>
            <div>
              <h1 className="text-lg font-bold text-zinc-100">Smart AI DJ</h1>
              <p className="text-xs text-zinc-500">Professional transitions powered by AI</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8 space-y-8">
        {/* Upload Section */}
        <section>
          <h2 className="text-xl font-bold text-zinc-200 mb-4">Upload Songs</h2>
          <DualDeckUpload onUploadComplete={handleUploadComplete} />
        </section>

        {/* Analysis Section */}
        {(songA || songB) && (
          <section>
            <AnalysisDashboard
              songA={songA}
              songB={songB}
              songAUrl={deckA ? `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/uploads/${deckA.file_path.split("/").pop()}` : null}
              songBUrl={deckB ? `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/uploads/${deckB.file_path.split("/").pop()}` : null}
              compatibility={compatibility}
              onTransitionSelect={setTransitionStartMs}
              onInPointSelect={setSongBInPointMs}
            />
          </section>
        )}

        {/* Transition point indicators */}
        {(transitionStartMs !== null || songBInPointMs !== null) && (
          <div className="text-sm text-zinc-400 bg-zinc-900/50 rounded-lg px-4 py-2 border border-zinc-800 flex flex-wrap gap-x-6 gap-y-1">
            {transitionStartMs !== null && (
              <span>
                Song A out: <span className="text-indigo-400 font-mono">
                  {(transitionStartMs / 1000).toFixed(1)}s
                </span>
                <button
                  onClick={() => setTransitionStartMs(null)}
                  className="ml-1 text-zinc-600 hover:text-zinc-400"
                >
                  (reset)
                </button>
              </span>
            )}
            {songBInPointMs !== null && (
              <span>
                Song B in: <span className="text-pink-400 font-mono">
                  {(songBInPointMs / 1000).toFixed(1)}s
                </span>
                <button
                  onClick={() => setSongBInPointMs(null)}
                  className="ml-1 text-zinc-600 hover:text-zinc-400"
                >
                  (reset)
                </button>
              </span>
            )}
          </div>
        )}

        {/* Advanced Settings */}
        {bothUploaded && (
          <AdvancedSettings
            strategy={strategy}
            onStrategyChange={setStrategy}
            enableSfx={enableSfx}
            onSfxToggle={setEnableSfx}
            mixInKey={mixInKey}
            onMixInKeyToggle={setMixInKey}
            bpmOverrideA={bpmOverrideA}
            bpmOverrideB={bpmOverrideB}
            onBpmOverrideA={setBpmOverrideA}
            onBpmOverrideB={setBpmOverrideB}
            keyOverrideA={keyOverrideA}
            keyOverrideB={keyOverrideB}
            onKeyOverrideA={setKeyOverrideA}
            onKeyOverrideB={setKeyOverrideB}
          />
        )}

        {/* Generate Mix Button */}
        {bothUploaded && !mixResult && (
          <button
            onClick={handleGenerateMix}
            disabled={isGenerating}
            className={`w-full py-4 rounded-xl text-lg font-bold transition-all ${
              isGenerating
                ? "bg-zinc-800 text-zinc-500 cursor-not-allowed"
                : "bg-gradient-to-r from-indigo-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-white shadow-lg shadow-indigo-500/20"
            }`}
          >
            {isGenerating ? "Generating..." : "Generate Mix"}
          </button>
        )}

        {/* Progress */}
        {pipelineStage !== "idle" && !mixResult && (
          <ProgressIndicator
            stage={pipelineStage}
            message={progressMessage}
            progress={progressValue}
          />
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400">
            <p className="font-medium">Something went wrong</p>
            <p className="text-sm mt-1">{error}</p>
            <button
              onClick={() => { setError(null); setPipelineStage("idle"); }}
              className="mt-2 text-sm underline hover:no-underline"
            >
              Try again
            </button>
          </div>
        )}

        {/* Result */}
        {mixResult && (
          <ResultPlayer
            sessionId={mixResult.session_id}
            mixDecision={mixResult.contract_b.mix_decision}
            downloadUrl={mixResult.download_url}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-800 mt-16 py-6 text-center text-xs text-zinc-600">
        Smart AI DJ v1.0 — Built with librosa, Gemini, FFmpeg & Next.js
      </footer>
    </div>
  );
}

/** Client-side compatibility computation (quick version for immediate feedback) */
function computeClientCompatibility(a: SongAnalysis, b: SongAnalysis): Compatibility {
  const bpmDiff = Math.abs(a.bpm - b.bpm);
  const bpmRatio = Math.max(a.bpm, b.bpm) / Math.min(a.bpm, b.bpm);

  const camA = a.camelot;
  const camB = b.camelot;
  let camDist = 6;
  let camRel = "incompatible";

  if (camA && camB && camA !== "?" && camB !== "?") {
    const numA = parseInt(camA);
    const numB = parseInt(camB);
    const letterA = camA.slice(-1);
    const letterB = camB.slice(-1);

    if (letterA === letterB) {
      const diff = Math.abs(numA - numB);
      camDist = Math.min(diff, 12 - diff);
    } else if (numA === numB) {
      camDist = 0;
    }

    if (camDist === 0) camRel = "same";
    else if (camDist === 1) camRel = "adjacent";
    else if (camDist === 2) camRel = "relative";
  }

  const harmScore = camDist <= 1 ? 0.9 : camDist <= 2 ? 0.6 : 0.2;

  return {
    bpm_diff: bpmDiff,
    bpm_ratio: bpmRatio,
    key_compatible: camDist <= 1,
    camelot_distance: camDist,
    camelot_relation: camRel,
    needs_tempo_adjustment: bpmDiff > 2,
    recommended_target_bpm: Math.round(((a.bpm + b.bpm) / 2) * 10) / 10,
    harmonic_mixing_score: harmScore,
  };
}
