"""Tests for Contract A and Contract B model validation."""

import pytest
from app.models.contracts import (
    ContractA, ContractB, SongAnalysis, Phrase, EnergyPoint,
    Compatibility, MixDecision, SongMixPoint, Transition,
    EQAutomation, EQAutomationEntry, SFXConfig,
)


def make_song_analysis(**overrides):
    defaults = dict(
        filename="test.mp3",
        duration_ms=240000,
        bpm=128.0,
        bpm_confidence=0.9,
        key="Am",
        key_confidence=0.8,
        camelot="8A",
        beats_ms=[0, 468.75, 937.5],
        downbeats_ms=[0, 1875.0],
        phrases=[Phrase(start_ms=0, end_ms=15000, bars=8, type="intro", avg_energy=0.3)],
        energy_curve=[EnergyPoint(ms=0, rms=0.5)],
    )
    defaults.update(overrides)
    return SongAnalysis(**defaults)


def make_compatibility(**overrides):
    defaults = dict(
        bpm_diff=2.0,
        bpm_ratio=1.016,
        key_compatible=True,
        camelot_distance=1,
        camelot_relation="adjacent",
        needs_tempo_adjustment=False,
        recommended_target_bpm=127.0,
        harmonic_mixing_score=0.85,
    )
    defaults.update(overrides)
    return Compatibility(**defaults)


class TestContractA:
    def test_valid_contract_a(self):
        sa = make_song_analysis(filename="a.mp3")
        sb = make_song_analysis(filename="b.mp3", bpm=126.0, key="Em", camelot="9A")
        compat = make_compatibility()
        contract = ContractA(song_a=sa, song_b=sb, compatibility=compat)
        assert contract.song_a.bpm == 128.0
        assert contract.song_b.key == "Em"
        assert contract.compatibility.key_compatible is True

    def test_key_compatible_unknown(self):
        compat = make_compatibility(key_compatible="unknown")
        assert compat.key_compatible == "unknown"

    def test_bpm_confidence_range(self):
        s = make_song_analysis(bpm_confidence=0.0)
        assert s.bpm_confidence == 0.0
        s = make_song_analysis(bpm_confidence=1.0)
        assert s.bpm_confidence == 1.0

    def test_warnings(self):
        s = make_song_analysis(bpm_warning="Low confidence", key_warning="Unable to detect")
        assert s.bpm_warning == "Low confidence"
        assert s.key_warning == "Unable to detect"


class TestContractB:
    def test_valid_contract_b(self):
        contract = ContractB(
            mix_decision=MixDecision(
                strategy="phrase_blend",
                confidence=0.87,
                reasoning="Test reasoning",
                song_a=SongMixPoint(out_point_ms=180000, fade_start_ms=170000, tempo_stretch_factor=1.01),
                song_b=SongMixPoint(in_point_ms=0, fade_end_ms=16000, tempo_stretch_factor=0.99),
                transition=Transition(
                    total_duration_ms=16000,
                    crossfade_curve="equal_power",
                    eq_automation=EQAutomation(
                        song_a_bass=EQAutomationEntry(
                            action="cut", start_ms=180000, end_ms=188000,
                            from_db=0, to_db=-24, curve="linear",
                        ),
                    ),
                ),
                sfx=SFXConfig(enabled=True, type="riser_sweep"),
            )
        )
        assert contract.mix_decision.strategy == "phrase_blend"
        assert contract.mix_decision.confidence == 0.87

    def test_incompatible_strategy(self):
        contract = ContractB(
            mix_decision=MixDecision(
                strategy="incompatible",
                confidence=0.0,
                reasoning="BPM too far apart",
                song_a=SongMixPoint(),
                song_b=SongMixPoint(),
                transition=Transition(
                    total_duration_ms=0,
                    eq_automation=EQAutomation(),
                ),
                suggestion="Try songs with closer BPM",
            )
        )
        assert contract.mix_decision.strategy == "incompatible"
        assert contract.mix_decision.suggestion is not None
