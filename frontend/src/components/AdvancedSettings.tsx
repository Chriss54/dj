"use client";

import { useState } from "react";

interface AdvancedSettingsProps {
  strategy: string | null;
  onStrategyChange: (strategy: string | null) => void;
  enableSfx: boolean;
  onSfxToggle: (enabled: boolean) => void;
  mixInKey: boolean;
  onMixInKeyToggle: (enabled: boolean) => void;
  bpmOverrideA: number | null;
  bpmOverrideB: number | null;
  onBpmOverrideA: (bpm: number | null) => void;
  onBpmOverrideB: (bpm: number | null) => void;
  keyOverrideA: string | null;
  keyOverrideB: string | null;
  onKeyOverrideA: (key: string | null) => void;
  onKeyOverrideB: (key: string | null) => void;
}

const STRATEGIES = [
  { value: "", label: "Auto (AI decides)" },
  { value: "phrase_blend", label: "Phrase Blend" },
  { value: "drop_swap", label: "Drop Swap" },
  { value: "echo_out", label: "Echo Out" },
  { value: "bass_swap", label: "Bass Swap" },
  { value: "breakdown_bridge", label: "Breakdown Bridge" },
];

export default function AdvancedSettings({
  strategy, onStrategyChange, enableSfx, onSfxToggle, mixInKey, onMixInKeyToggle,
  bpmOverrideA, bpmOverrideB, onBpmOverrideA, onBpmOverrideB,
  keyOverrideA, keyOverrideB, onKeyOverrideA, onKeyOverrideB,
}: AdvancedSettingsProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="border border-zinc-800 rounded-xl overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 text-sm text-zinc-400 hover:text-zinc-300 transition-colors"
      >
        <span>Advanced Settings</span>
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? "rotate-180" : ""}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="p-4 pt-0 space-y-4 border-t border-zinc-800">
          {/* Strategy override */}
          <div>
            <label className="block text-xs text-zinc-500 mb-1">Transition Strategy</label>
            <select
              value={strategy || ""}
              onChange={(e) => onStrategyChange(e.target.value || null)}
              className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-300"
            >
              {STRATEGIES.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>

          {/* SFX toggle */}
          <div className="flex items-center justify-between">
            <label className="text-xs text-zinc-500">Sound Effects (SFX)</label>
            <button
              onClick={() => onSfxToggle(!enableSfx)}
              className={`w-10 h-5 rounded-full transition-colors relative ${
                enableSfx ? "bg-indigo-500" : "bg-zinc-700"
              }`}
            >
              <span
                className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                  enableSfx ? "left-5" : "left-0.5"
                }`}
              />
            </button>
          </div>

          {/* Mix in Key toggle */}
          <div className="flex items-center justify-between">
            <div>
              <label className="text-xs text-zinc-500">Mix in Key</label>
              <p className="text-[10px] text-zinc-600">Pitch-shifts Song B to match Song A&apos;s key</p>
            </div>
            <button
              onClick={() => onMixInKeyToggle(!mixInKey)}
              className={`w-10 h-5 rounded-full transition-colors relative ${
                mixInKey ? "bg-indigo-500" : "bg-zinc-700"
              }`}
            >
              <span
                className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                  mixInKey ? "left-5" : "left-0.5"
                }`}
              />
            </button>
          </div>

          {/* BPM overrides */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-zinc-500 mb-1">Song A BPM Override</label>
              <input
                type="number"
                placeholder="Auto"
                value={bpmOverrideA ?? ""}
                onChange={(e) => onBpmOverrideA(e.target.value ? Number(e.target.value) : null)}
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-300"
                min={60} max={200} step={0.1}
              />
            </div>
            <div>
              <label className="block text-xs text-zinc-500 mb-1">Song B BPM Override</label>
              <input
                type="number"
                placeholder="Auto"
                value={bpmOverrideB ?? ""}
                onChange={(e) => onBpmOverrideB(e.target.value ? Number(e.target.value) : null)}
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-300"
                min={60} max={200} step={0.1}
              />
            </div>
          </div>

          {/* Key overrides */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-zinc-500 mb-1">Song A Key Override</label>
              <input
                type="text"
                placeholder="Auto (e.g. Am, C)"
                value={keyOverrideA ?? ""}
                onChange={(e) => onKeyOverrideA(e.target.value || null)}
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-300"
              />
            </div>
            <div>
              <label className="block text-xs text-zinc-500 mb-1">Song B Key Override</label>
              <input
                type="text"
                placeholder="Auto (e.g. Em, G)"
                value={keyOverrideB ?? ""}
                onChange={(e) => onKeyOverrideB(e.target.value || null)}
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-300"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
