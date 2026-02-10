"""Rule-based fallback mixer — produces Contract B without any AI dependency."""

from typing import Optional

from ..models.contracts import (
    ContractA, ContractB, MixDecision, SongMixPoint,
    Transition, EQAutomation, EQAutomationEntry, SFXConfig,
)
from ..analysis.camelot import pitch_shift_to_match


def rule_based_mix(
    contract_a: ContractA,
    transition_start_ms: Optional[float] = None,
    mix_in_key: bool = False,
    song_b_in_point_ms: Optional[float] = None,
) -> ContractB:
    """
    Generate a mix decision using deterministic rules.
    Used when Gemini is unavailable, times out, or returns invalid data.
    """
    sa = contract_a.song_a
    sb = contract_a.song_b
    compat = contract_a.compatibility

    # Find out-point: nearest downbeat to user's marker, or last 25% of song A
    if transition_start_ms is not None:
        out_point = _nearest_downbeat(sa.downbeats_ms, transition_start_ms)
    else:
        # Default: start transition at ~75% through song A
        target_ms = sa.duration_ms * 0.75
        out_point = _nearest_downbeat(sa.downbeats_ms, target_ms)

    # Find in-point: user override, or first downbeat of a suitable phrase in Song B
    if song_b_in_point_ms is not None:
        in_point = _nearest_downbeat(sb.downbeats_ms, song_b_in_point_ms)
    else:
        in_point = 0.0
        for phrase in sb.phrases:
            if phrase.type in ("intro", "verse", "breakdown"):
                in_point = phrase.start_ms
                break

    # Transition duration: 8 bars at the target BPM
    target_bpm = compat.recommended_target_bpm
    ms_per_bar = (4 * 60000) / target_bpm  # 4 beats per bar
    transition_duration = ms_per_bar * 8  # 8 bars

    # Ensure we don't exceed song A duration
    if out_point + transition_duration > sa.duration_ms:
        transition_duration = sa.duration_ms - out_point

    # Tempo stretch factors
    if compat.needs_tempo_adjustment:
        stretch_a = target_bpm / sa.bpm
        stretch_b = target_bpm / sb.bpm
    else:
        stretch_a = 1.0
        stretch_b = 1.0

    # Pitch shift for key matching
    pitch_shift_b = 0
    key_note = ""
    if mix_in_key and compat.key_compatible is not True and compat.key_compatible != "unknown":
        pitch_shift_b = pitch_shift_to_match(sb.camelot, sa.camelot)
        if pitch_shift_b != 0:
            key_note = f" Song B pitch-shifted by {pitch_shift_b:+d} semitones for key compatibility."

    # EQ automation: bass swap over the transition
    # Song A EQ: absolute positions (segment starts at Song A time 0)
    # Song B EQ: relative to Song B segment start (segment starts at in_point)
    eq = EQAutomation(
        song_a_bass=EQAutomationEntry(
            action="cut",
            start_ms=out_point,
            end_ms=out_point + transition_duration / 2,
            from_db=0, to_db=-24,
            curve="linear",
        ),
        song_b_bass=EQAutomationEntry(
            action="boost",
            start_ms=transition_duration / 2,
            end_ms=transition_duration,
            from_db=-24, to_db=0,
            curve="linear",
        ),
    )

    # Build reasoning
    reasoning = (
        f"Rule-based fallback (AI unavailable). "
        f"8-bar linear crossfade with bass swap. "
        f"BPM difference: {compat.bpm_diff}. "
        f"Target BPM: {target_bpm}. "
        f"Key compatibility: {compat.camelot_relation}."
        f"{key_note}"
    )

    return ContractB(
        mix_decision=MixDecision(
            strategy="bass_swap",
            confidence=0.5,
            reasoning=reasoning,
            song_a=SongMixPoint(
                out_point_ms=round(out_point, 1),
                out_phrase=_phrase_at(sa.phrases, out_point),
                fade_start_ms=round(out_point, 1),
                tempo_stretch_factor=round(stretch_a, 4),
            ),
            song_b=SongMixPoint(
                in_point_ms=round(in_point, 1),
                in_phrase=_phrase_at(sb.phrases, in_point),
                fade_end_ms=round(in_point + transition_duration, 1),
                tempo_stretch_factor=round(stretch_b, 4),
                pitch_shift_semitones=pitch_shift_b,
            ),
            transition=Transition(
                total_duration_ms=round(transition_duration, 1),
                crossfade_curve="linear",
                eq_automation=eq,
            ),
            sfx=SFXConfig(enabled=False),
        )
    )


def _nearest_downbeat(downbeats_ms: list[float], target_ms: float) -> float:
    if not downbeats_ms:
        return target_ms
    return min(downbeats_ms, key=lambda d: abs(d - target_ms))


def _phrase_at(phrases: list, ms: float) -> str:
    for p in phrases:
        if p.start_ms <= ms <= p.end_ms:
            return p.type
    return "unknown"
