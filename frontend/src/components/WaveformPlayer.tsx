"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import WaveSurfer from "wavesurfer.js";
import { Phrase } from "@/lib/types";

interface WaveformPlayerProps {
  audioUrl: string | null;
  phrases?: Phrase[];
  onRegionSelect?: (startMs: number, endMs: number) => void;
  height?: number;
  color?: string;
  label?: string;
  showPhraseMarkers?: boolean;
}

export default function WaveformPlayer({
  audioUrl,
  phrases = [],
  onRegionSelect,
  height = 80,
  color = "#6366f1",
  label,
  showPhraseMarkers = true,
}: WaveformPlayerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WaveSurfer | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    if (!containerRef.current || !audioUrl) return;

    const ws = WaveSurfer.create({
      container: containerRef.current,
      waveColor: color + "66",
      progressColor: color,
      cursorColor: "#fff",
      cursorWidth: 2,
      height,
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      normalize: true,
    });

    ws.load(audioUrl);

    ws.on("ready", () => {
      setDuration(ws.getDuration() * 1000);
    });

    ws.on("audioprocess", () => {
      setCurrentTime(ws.getCurrentTime() * 1000);
    });

    ws.on("play", () => setIsPlaying(true));
    ws.on("pause", () => setIsPlaying(false));

    ws.on("click", () => {
      if (onRegionSelect) {
        const clickTime = ws.getCurrentTime() * 1000;
        // Find nearest phrase boundary
        const nearestPhrase = phrases.reduce(
          (best, p) => {
            const dist = Math.abs(p.start_ms - clickTime);
            return dist < best.dist ? { phrase: p, dist } : best;
          },
          { phrase: phrases[0], dist: Infinity },
        );
        if (nearestPhrase.phrase) {
          onRegionSelect(nearestPhrase.phrase.start_ms, nearestPhrase.phrase.end_ms);
        }
      }
    });

    wsRef.current = ws;

    return () => {
      ws.destroy();
      wsRef.current = null;
    };
  }, [audioUrl, color, height]);

  const togglePlay = useCallback(() => {
    wsRef.current?.playPause();
  }, []);

  const formatTime = (ms: number) => {
    const s = Math.floor(ms / 1000);
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  return (
    <div className="relative">
      {label && (
        <div className="text-xs text-zinc-400 mb-1 font-medium uppercase tracking-wider">
          {label}
        </div>
      )}
      <div className="bg-zinc-900 rounded-lg p-3 border border-zinc-800">
        <div ref={containerRef} className="w-full" />

        {/* Phrase markers */}
        {showPhraseMarkers && phrases.length > 0 && duration > 0 && (
          <div className="relative h-4 mt-1">
            {phrases.map((p, i) => (
              <div
                key={i}
                className="absolute top-0 h-full border-l border-zinc-600"
                style={{ left: `${(p.start_ms / duration) * 100}%` }}
                title={`${p.type} (${p.bars} bars)`}
              >
                <span className="text-[9px] text-zinc-500 ml-1">{p.type}</span>
              </div>
            ))}
          </div>
        )}

        <div className="flex items-center justify-between mt-2">
          <button
            onClick={togglePlay}
            className="w-8 h-8 flex items-center justify-center rounded-full bg-zinc-800 hover:bg-zinc-700 transition-colors"
          >
            {isPlaying ? (
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M5 4h3v12H5V4zm7 0h3v12h-3V4z" />
              </svg>
            ) : (
              <svg className="w-4 h-4 ml-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
              </svg>
            )}
          </button>
          <span className="text-xs text-zinc-400 font-mono">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>
        </div>
      </div>
    </div>
  );
}
