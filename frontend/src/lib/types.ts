// Contract A types (Tier 1 → Tier 2)

export interface Phrase {
  start_ms: number;
  end_ms: number;
  bars: number;
  type: string;
  avg_energy: number;
}

export interface EnergyPoint {
  ms: number;
  rms: number;
}

export interface SongAnalysis {
  filename: string;
  duration_ms: number;
  bpm: number;
  bpm_confidence: number;
  key: string;
  key_confidence: number;
  camelot: string;
  beats_ms: number[];
  downbeats_ms: number[];
  phrases: Phrase[];
  energy_curve: EnergyPoint[];
  bpm_warning?: string;
  key_warning?: string;
}

export interface Compatibility {
  bpm_diff: number;
  bpm_ratio: number;
  key_compatible: boolean | string;
  camelot_distance: number;
  camelot_relation: string;
  needs_tempo_adjustment: boolean;
  recommended_target_bpm: number;
  harmonic_mixing_score: number;
}

export interface ContractA {
  song_a: SongAnalysis;
  song_b: SongAnalysis;
  compatibility: Compatibility;
}

// Contract B types (Tier 2 → Tier 3)

export interface EQAutomationEntry {
  action: string;
  start_ms: number;
  end_ms: number;
  from_db: number;
  to_db: number;
  curve: string;
}

export interface EQAutomation {
  song_a_bass?: EQAutomationEntry;
  song_b_bass?: EQAutomationEntry;
  song_a_highs?: EQAutomationEntry;
  song_b_highs?: EQAutomationEntry;
}

export interface SFXConfig {
  enabled: boolean;
  type: string;
  trigger_reason: string;
  position_ms: number;
  duration_ms: number;
  source: string;
  elevenlabs_prompt: string;
  fallback_file: string;
}

export interface MixDecision {
  strategy: string;
  confidence: number;
  reasoning: string;
  song_a: {
    out_point_ms?: number;
    out_phrase?: string;
    fade_start_ms?: number;
    tempo_stretch_factor: number;
  };
  song_b: {
    in_point_ms?: number;
    in_phrase?: string;
    fade_end_ms?: number;
    tempo_stretch_factor: number;
  };
  transition: {
    total_duration_ms: number;
    crossfade_curve: string;
    eq_automation: EQAutomation;
  };
  sfx: SFXConfig;
  suggestion?: string;
}

export interface ContractB {
  mix_decision: MixDecision;
}

// UI types

export type PipelineStage = "idle" | "uploading" | "analysis" | "strategy" | "render" | "complete" | "error";

export interface ProgressUpdate {
  type: "progress";
  stage: PipelineStage;
  message: string;
  progress: number;
}

export interface UploadResult {
  session_id: string;
  deck: string;
  file_path: string;
  analysis: SongAnalysis;
}

export interface MixResult {
  session_id: string;
  contract_a: ContractA;
  contract_b: ContractB;
  download_url: string;
}
