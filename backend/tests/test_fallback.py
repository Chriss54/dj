"""Tests for rule-based fallback mixer."""

from app.models.contracts import (
    ContractA, SongAnalysis, Phrase, EnergyPoint, Compatibility,
)
from app.strategist.fallback import rule_based_mix


def make_contract_a(bpm_a=128.0, bpm_b=126.0, key_a="Am", key_b="Em"):
    sa = SongAnalysis(
        filename="a.mp3", duration_ms=240000, bpm=bpm_a, bpm_confidence=0.9,
        key=key_a, key_confidence=0.8, camelot="8A",
        beats_ms=[i * 468.75 for i in range(512)],
        downbeats_ms=[i * 1875.0 for i in range(128)],
        phrases=[
            Phrase(start_ms=0, end_ms=30000, bars=16, type="intro", avg_energy=0.3),
            Phrase(start_ms=30000, end_ms=120000, bars=48, type="verse", avg_energy=0.6),
            Phrase(start_ms=120000, end_ms=200000, bars=42, type="chorus", avg_energy=0.85),
            Phrase(start_ms=200000, end_ms=240000, bars=21, type="outro", avg_energy=0.4),
        ],
        energy_curve=[EnergyPoint(ms=i * 1000, rms=0.5) for i in range(240)],
    )
    sb = SongAnalysis(
        filename="b.mp3", duration_ms=200000, bpm=bpm_b, bpm_confidence=0.85,
        key=key_b, key_confidence=0.75, camelot="9A",
        beats_ms=[i * 476.19 for i in range(420)],
        downbeats_ms=[i * 1904.76 for i in range(105)],
        phrases=[
            Phrase(start_ms=0, end_ms=15000, bars=8, type="intro", avg_energy=0.25),
            Phrase(start_ms=15000, end_ms=100000, bars=45, type="verse", avg_energy=0.6),
        ],
        energy_curve=[EnergyPoint(ms=i * 1000, rms=0.5) for i in range(200)],
    )
    compat = Compatibility(
        bpm_diff=abs(bpm_a - bpm_b), bpm_ratio=max(bpm_a, bpm_b) / min(bpm_a, bpm_b),
        key_compatible=True, camelot_distance=1, camelot_relation="adjacent",
        needs_tempo_adjustment=abs(bpm_a - bpm_b) > 2,
        recommended_target_bpm=(bpm_a + bpm_b) / 2,
        harmonic_mixing_score=0.85,
    )
    return ContractA(song_a=sa, song_b=sb, compatibility=compat)


class TestRuleBasedMix:
    def test_produces_valid_contract_b(self):
        contract_a = make_contract_a()
        result = rule_based_mix(contract_a)
        assert result.mix_decision.strategy == "bass_swap"
        assert result.mix_decision.confidence == 0.5
        assert "Rule-based fallback" in result.mix_decision.reasoning

    def test_transition_within_song_duration(self):
        contract_a = make_contract_a()
        result = rule_based_mix(contract_a)
        md = result.mix_decision
        assert md.song_a.out_point_ms <= contract_a.song_a.duration_ms

    def test_bass_swap_eq_present(self):
        contract_a = make_contract_a()
        result = rule_based_mix(contract_a)
        eq = result.mix_decision.transition.eq_automation
        assert eq.song_a_bass is not None
        assert eq.song_b_bass is not None
        assert eq.song_a_bass.action == "cut"
        assert eq.song_b_bass.action == "boost"

    def test_no_sfx(self):
        contract_a = make_contract_a()
        result = rule_based_mix(contract_a)
        assert result.mix_decision.sfx.enabled is False

    def test_custom_transition_start(self):
        contract_a = make_contract_a()
        result = rule_based_mix(contract_a, transition_start_ms=150000)
        # Should snap to nearest downbeat
        md = result.mix_decision
        assert md.song_a.out_point_ms is not None

    def test_tempo_stretch_when_needed(self):
        contract_a = make_contract_a(bpm_a=128.0, bpm_b=122.0)
        result = rule_based_mix(contract_a)
        md = result.mix_decision
        assert md.song_a.tempo_stretch_factor != 1.0
        assert md.song_b.tempo_stretch_factor != 1.0
