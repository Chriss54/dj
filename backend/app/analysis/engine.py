"""Tier 1: Audio Analysis Engine — extracts musical features from audio files."""

import subprocess
import tempfile
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

from ..models.contracts import (
    SongAnalysis, Phrase, EnergyPoint, Compatibility, ContractA,
)
from .key_detection import detect_key
from .camelot import key_to_camelot, camelot_distance, camelot_relation, harmonic_score
from ..config import SUPPORTED_FORMATS


def convert_to_wav(input_path: Path) -> Path:
    """Convert any supported audio format to WAV using ffmpeg."""
    if input_path.suffix.lower() == ".wav":
        return input_path
    output_path = input_path.with_suffix(".wav")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(input_path), "-ar", "22050", "-ac", "1", str(output_path)],
        capture_output=True, check=True,
    )
    return output_path


def analyze_song(file_path: Path) -> SongAnalysis:
    """Full analysis of a single song. Returns SongAnalysis matching Contract A."""
    wav_path = convert_to_wav(file_path)

    # Load audio
    y, sr = librosa.load(str(wav_path), sr=22050, mono=True)
    duration_ms = (len(y) / sr) * 1000

    # BPM detection
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    if isinstance(tempo, np.ndarray):
        bpm = float(tempo[0])
    else:
        bpm = float(tempo)

    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    beats_ms = [round(t * 1000, 1) for t in beat_times]

    # BPM confidence via onset strength autocorrelation
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    ac = librosa.autocorrelate(onset_env, max_size=sr // 512 * 4)
    if len(ac) > 0 and ac[0] > 0:
        bpm_confidence = min(1.0, float(np.max(ac[1:]) / ac[0]) if len(ac) > 1 else 0.5)
    else:
        bpm_confidence = 0.5

    bpm_warning = None
    if bpm_confidence < 0.6:
        bpm_warning = "Low confidence. Consider manual BPM entry."

    # Downbeats (every 4th beat)
    downbeats_ms = [beats_ms[i] for i in range(0, len(beats_ms), 4)]

    # Key detection
    key, key_confidence = detect_key(y, sr)
    camelot = key_to_camelot(key)

    key_warning = None
    if key_confidence < 0.5:
        key_warning = "Unable to determine key reliably."

    # Energy curve (RMS per second)
    hop_length = sr  # 1 second hops
    rms = librosa.feature.rms(y=y, frame_length=sr, hop_length=hop_length)[0]
    rms_max = rms.max() if rms.max() > 0 else 1.0
    energy_curve = [
        EnergyPoint(ms=round(i * 1000, 1), rms=round(float(v / rms_max), 3))
        for i, v in enumerate(rms)
    ]

    # Phrase detection via structural segmentation
    phrases = _detect_phrases(y, sr, beats_ms, downbeats_ms, energy_curve, duration_ms)

    return SongAnalysis(
        filename=file_path.name,
        duration_ms=round(duration_ms, 1),
        bpm=round(bpm, 1),
        bpm_confidence=round(bpm_confidence, 2),
        key=key,
        key_confidence=round(key_confidence, 2),
        camelot=camelot,
        beats_ms=beats_ms,
        downbeats_ms=downbeats_ms,
        phrases=phrases,
        energy_curve=energy_curve,
        bpm_warning=bpm_warning,
        key_warning=key_warning,
    )


def _detect_phrases(
    y: np.ndarray, sr: int,
    beats_ms: list[float], downbeats_ms: list[float],
    energy_curve: list[EnergyPoint], duration_ms: float,
) -> list[Phrase]:
    """Detect phrase boundaries using structural segmentation or fallback to 8-bar groups."""
    try:
        # Try librosa structural segmentation
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        bound_frames = librosa.segment.agglomerative(mfcc, k=None)
        bound_times = librosa.frames_to_time(bound_frames, sr=sr)
        bound_ms = sorted(set([0.0] + [round(t * 1000, 1) for t in bound_times] + [duration_ms]))

        if len(bound_ms) < 3:
            raise ValueError("Too few segments")

        phrases = []
        for i in range(len(bound_ms) - 1):
            start = bound_ms[i]
            end = bound_ms[i + 1]
            dur_bars = max(1, round((end - start) / (4 * 60000 / max(1, _avg_bpm(beats_ms)))))

            # Estimate phrase type from position and energy
            avg_e = _avg_energy_in_range(energy_curve, start, end)
            ptype = _classify_phrase(i, len(bound_ms) - 1, avg_e)

            phrases.append(Phrase(
                start_ms=start, end_ms=end, bars=dur_bars,
                type=ptype, avg_energy=round(avg_e, 2),
            ))
        return phrases

    except Exception:
        # Fallback: fixed 8-bar groupings aligned to downbeats
        return _fallback_phrases(downbeats_ms, energy_curve, duration_ms, beats_ms)


def _fallback_phrases(
    downbeats_ms: list[float], energy_curve: list[EnergyPoint],
    duration_ms: float, beats_ms: list[float],
) -> list[Phrase]:
    """Generate phrases as 8-bar groups aligned to downbeats."""
    phrases = []
    # Group every 8 downbeats (= 8 bars of 4/4)
    step = 8
    for i in range(0, len(downbeats_ms), step):
        start = downbeats_ms[i]
        end = downbeats_ms[min(i + step, len(downbeats_ms) - 1)] if i + step < len(downbeats_ms) else duration_ms
        if end <= start:
            end = duration_ms
        avg_e = _avg_energy_in_range(energy_curve, start, end)
        ptype = _classify_phrase(i // step, max(1, len(downbeats_ms) // step), avg_e)
        phrases.append(Phrase(
            start_ms=round(start, 1), end_ms=round(end, 1),
            bars=8, type=ptype, avg_energy=round(avg_e, 2),
        ))
    return phrases


def _avg_bpm(beats_ms: list[float]) -> float:
    if len(beats_ms) < 2:
        return 120.0
    intervals = [beats_ms[i + 1] - beats_ms[i] for i in range(len(beats_ms) - 1)]
    avg_interval = np.mean(intervals)
    return 60000.0 / avg_interval if avg_interval > 0 else 120.0


def _avg_energy_in_range(energy_curve: list[EnergyPoint], start_ms: float, end_ms: float) -> float:
    points = [p.rms for p in energy_curve if start_ms <= p.ms <= end_ms]
    return float(np.mean(points)) if points else 0.5


def _classify_phrase(index: int, total: int, energy: float) -> str:
    if total <= 1:
        return "verse"
    ratio = index / max(1, total - 1)
    if ratio < 0.1:
        return "intro"
    if ratio > 0.9:
        return "outro"
    if energy > 0.75:
        return "chorus"
    if energy < 0.3:
        return "breakdown"
    return "verse"


def compute_compatibility(song_a: SongAnalysis, song_b: SongAnalysis) -> Compatibility:
    """Compute compatibility metrics between two analyzed songs."""
    bpm_diff = abs(song_a.bpm - song_b.bpm)
    bpm_ratio = max(song_a.bpm, song_b.bpm) / min(song_a.bpm, song_b.bpm) if min(song_a.bpm, song_b.bpm) > 0 else 1.0

    cam_dist = camelot_distance(song_a.camelot, song_b.camelot)
    cam_rel = camelot_relation(song_a.camelot, song_b.camelot)
    harm_score = harmonic_score(song_a.camelot, song_b.camelot)

    key_compat: bool | str
    if song_a.key_confidence < 0.5 or song_b.key_confidence < 0.5:
        key_compat = "unknown"
    else:
        key_compat = cam_dist <= 1

    needs_tempo_adj = bpm_diff > 2.0
    target_bpm = round((song_a.bpm + song_b.bpm) / 2, 1)

    return Compatibility(
        bpm_diff=round(bpm_diff, 1),
        bpm_ratio=round(bpm_ratio, 3),
        key_compatible=key_compat,
        camelot_distance=cam_dist,
        camelot_relation=cam_rel,
        needs_tempo_adjustment=needs_tempo_adj,
        recommended_target_bpm=target_bpm,
        harmonic_mixing_score=round(harm_score, 2),
    )


async def analyze_pair(path_a: Path, path_b: Path) -> ContractA:
    """Analyze a pair of songs and return Contract A."""
    song_a = analyze_song(path_a)
    song_b = analyze_song(path_b)
    compat = compute_compatibility(song_a, song_b)
    return ContractA(song_a=song_a, song_b=song_b, compatibility=compat)
