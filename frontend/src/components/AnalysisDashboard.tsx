"use client";

import { SongAnalysis, Compatibility } from "@/lib/types";
import WaveformPlayer from "./WaveformPlayer";
import CompatibilityBadge from "./CompatibilityBadge";

interface AnalysisDashboardProps {
  songA: SongAnalysis | null;
  songB: SongAnalysis | null;
  songAUrl: string | null;
  songBUrl: string | null;
  compatibility: Compatibility | null;
  onTransitionSelect?: (startMs: number) => void;
  onInPointSelect?: (startMs: number) => void;
}

function SongCard({ song, audioUrl, label, color, onRegionSelect }: {
  song: SongAnalysis;
  audioUrl: string | null;
  label: string;
  color: string;
  onRegionSelect?: (startMs: number, endMs: number) => void;
}) {
  const bpmColor =
    song.bpm_confidence >= 0.8 ? "text-green-400" :
    song.bpm_confidence >= 0.6 ? "text-yellow-400" : "text-red-400";

  const keyColor =
    song.key_confidence >= 0.8 ? "text-green-400" :
    song.key_confidence >= 0.6 ? "text-yellow-400" : "text-red-400";

  return (
    <div className="bg-zinc-900/50 rounded-xl p-4 border border-zinc-800">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-bold text-zinc-200">{label}</h3>
        <span className="text-xs text-zinc-500 font-mono">{song.filename}</span>
      </div>

      {audioUrl && (
        <WaveformPlayer
          audioUrl={audioUrl}
          phrases={song.phrases}
          onRegionSelect={onRegionSelect}
          color={color}
        />
      )}

      <div className="grid grid-cols-3 gap-3 mt-3">
        <div className="bg-zinc-800/50 rounded-lg p-2 text-center">
          <div className="text-xs text-zinc-500 mb-1">BPM</div>
          <div className={`text-xl font-bold ${bpmColor}`}>{song.bpm.toFixed(1)}</div>
          <div className="text-[10px] text-zinc-600">
            conf: {(song.bpm_confidence * 100).toFixed(0)}%
          </div>
        </div>
        <div className="bg-zinc-800/50 rounded-lg p-2 text-center">
          <div className="text-xs text-zinc-500 mb-1">Key</div>
          <div className={`text-xl font-bold ${keyColor}`}>{song.key}</div>
          <div className="text-[10px] text-zinc-600">
            {song.camelot}
          </div>
        </div>
        <div className="bg-zinc-800/50 rounded-lg p-2 text-center">
          <div className="text-xs text-zinc-500 mb-1">Duration</div>
          <div className="text-xl font-bold text-zinc-300">
            {Math.floor(song.duration_ms / 60000)}:{String(Math.floor((song.duration_ms % 60000) / 1000)).padStart(2, "0")}
          </div>
          <div className="text-[10px] text-zinc-600">
            {song.phrases.length} phrases
          </div>
        </div>
      </div>

      {song.bpm_warning && (
        <div className="mt-2 text-xs text-yellow-400 bg-yellow-500/10 rounded px-2 py-1">
          {song.bpm_warning}
        </div>
      )}
      {song.key_warning && (
        <div className="mt-2 text-xs text-yellow-400 bg-yellow-500/10 rounded px-2 py-1">
          {song.key_warning}
        </div>
      )}
    </div>
  );
}

export default function AnalysisDashboard({
  songA, songB, songAUrl, songBUrl, compatibility, onTransitionSelect, onInPointSelect,
}: AnalysisDashboardProps) {
  if (!songA && !songB) return null;

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-zinc-200">Analysis</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {songA && (
          <SongCard
            song={songA}
            audioUrl={songAUrl}
            label="Song A"
            color="#6366f1"
            onRegionSelect={onTransitionSelect ? (start) => onTransitionSelect(start) : undefined}
          />
        )}
        {songB && (
          <SongCard
            song={songB}
            audioUrl={songBUrl}
            label="Song B"
            color="#ec4899"
            onRegionSelect={onInPointSelect ? (start) => onInPointSelect(start) : undefined}
          />
        )}
      </div>

      {compatibility && (
        <CompatibilityBadge compatibility={compatibility} />
      )}
    </div>
  );
}
