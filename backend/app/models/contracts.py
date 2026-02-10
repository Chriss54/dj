"""Pydantic models for Contract A (Analysis) and Contract B (Mix Decision)."""

from typing import Optional, Union
from pydantic import BaseModel, Field


# ── Contract A: Audio Analysis Output (Tier 1 → Tier 2) ──

class Phrase(BaseModel):
    start_ms: float
    end_ms: float
    bars: int
    type: str  # intro, verse, chorus, bridge, outro, breakdown, drop
    avg_energy: float = Field(ge=0.0, le=1.0)


class EnergyPoint(BaseModel):
    ms: float
    rms: float = Field(ge=0.0, le=1.0)


class SongAnalysis(BaseModel):
    filename: str
    duration_ms: float
    bpm: float
    bpm_confidence: float = Field(ge=0.0, le=1.0)
    key: str
    key_confidence: float = Field(ge=0.0, le=1.0)
    camelot: str
    beats_ms: list[float]
    downbeats_ms: list[float]
    phrases: list[Phrase]
    energy_curve: list[EnergyPoint]
    bpm_warning: Optional[str] = None
    key_warning: Optional[str] = None


class Compatibility(BaseModel):
    bpm_diff: float
    bpm_ratio: float
    key_compatible: Union[bool, str]  # True, False, or "unknown"
    camelot_distance: int
    camelot_relation: str  # same, adjacent, relative, incompatible
    needs_tempo_adjustment: bool
    recommended_target_bpm: float
    harmonic_mixing_score: float = Field(ge=0.0, le=1.0)


class ContractA(BaseModel):
    """Complete analysis output from Tier 1."""
    song_a: SongAnalysis
    song_b: SongAnalysis
    compatibility: Compatibility


# ── Contract B: AI Mix Decision (Tier 2 → Tier 3) ──

class SongMixPoint(BaseModel):
    out_point_ms: Optional[float] = None
    in_point_ms: Optional[float] = None
    out_phrase: Optional[str] = None
    in_phrase: Optional[str] = None
    fade_start_ms: Optional[float] = None
    fade_end_ms: Optional[float] = None
    tempo_stretch_factor: float = 1.0
    pitch_shift_semitones: int = 0  # semitones to shift for key matching


class EQAutomationEntry(BaseModel):
    action: str  # cut, boost
    start_ms: float
    end_ms: float
    from_db: float
    to_db: float
    curve: str = "linear"  # linear, exponential


class EQAutomation(BaseModel):
    song_a_bass: Optional[EQAutomationEntry] = None
    song_b_bass: Optional[EQAutomationEntry] = None
    song_a_highs: Optional[EQAutomationEntry] = None
    song_b_highs: Optional[EQAutomationEntry] = None
    song_a_mids: Optional[EQAutomationEntry] = None
    song_b_mids: Optional[EQAutomationEntry] = None


class Transition(BaseModel):
    total_duration_ms: float
    crossfade_curve: str = "equal_power"  # linear, equal_power, exponential
    eq_automation: EQAutomation


class SFXConfig(BaseModel):
    enabled: bool = False
    type: str = "none"
    trigger_reason: str = ""
    position_ms: float = 0
    duration_ms: float = 4000
    source: str = "library"  # elevenlabs, library
    elevenlabs_prompt: str = ""
    fallback_file: str = ""


class MixDecision(BaseModel):
    strategy: str  # phrase_blend, drop_swap, echo_out, bass_swap, breakdown_bridge, incompatible
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    song_a: SongMixPoint
    song_b: SongMixPoint
    transition: Transition
    sfx: SFXConfig = SFXConfig()
    suggestion: Optional[str] = None  # used when strategy is "incompatible"


class ContractB(BaseModel):
    """Complete mix decision from Tier 2."""
    mix_decision: MixDecision
