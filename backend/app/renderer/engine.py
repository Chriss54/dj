"""Tier 3: Audio Renderer — executes mix decisions using FFmpeg + rubberband."""

import logging
import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf

from ..models.contracts import ContractB, EQAutomationEntry
from ..config import OUTPUT_DIR
from ..sfx.director import get_sfx_audio

logger = logging.getLogger(__name__)


async def render_mix(
    contract_b: ContractB,
    song_a_path: Path,
    song_b_path: Path,
    session_id: str,
) -> Path:
    """
    Render the final mix based on Contract B.
    Returns path to the output MP3 file.
    """
    md = contract_b.mix_decision
    work_dir = Path(tempfile.mkdtemp(prefix="dj_render_"))

    try:
        # Step 1: Convert inputs to WAV
        wav_a = _ensure_wav(song_a_path, work_dir / "a_full.wav")
        wav_b = _ensure_wav(song_b_path, work_dir / "b_full.wav")

        # Step 2: Extract segments from ORIGINAL audio (before time-stretch)
        # acrossfade always crossfades the LAST d seconds of input 1 with the
        # FIRST d seconds of input 2. To position the crossfade at fade_start,
        # we truncate Song A so its end = fade_start + transition_zone.
        fade_start = md.song_a.fade_start_ms or md.song_a.out_point_ms or 0
        in_point = md.song_b.in_point_ms or 0
        trans_dur = md.transition.total_duration_ms

        sa_sf = md.song_a.tempo_stretch_factor
        sb_sf = md.song_b.tempo_stretch_factor

        # Calculate the transition zone in original-tempo time.
        # trans_dur is at target BPM; in Song A's original tempo the same
        # number of bars spans a different duration: multiply by sa_sf
        # because after time-stretch (÷ sa_sf), it becomes exactly trans_dur.
        orig_trans_dur_a = trans_dur * sa_sf if sa_sf != 1.0 else trans_dur

        # Truncate Song A through the transition zone end
        seg_a_end_ms = fade_start + orig_trans_dur_a
        seg_a = _extract_segment(wav_a, 0, seg_a_end_ms, work_dir / "seg_a.wav")
        seg_b = _extract_segment(wav_b, in_point, None, work_dir / "seg_b.wav")

        # Step 3: Apply EQ automation
        # Song A: timestamps are absolute (segment starts at 0ms of original)
        seg_a = _apply_eq_automation(seg_a, md.transition.eq_automation, "a", 0, work_dir)
        # Song B: timestamps are relative to transition start (segment start)
        seg_b = _apply_eq_automation(seg_b, md.transition.eq_automation, "b", 0, work_dir)

        # Step 4: Time-stretch segments to target BPM
        if sa_sf != 1.0:
            seg_a = _time_stretch(seg_a, sa_sf, work_dir / "a_stretched.wav")
        if sb_sf != 1.0:
            seg_b = _time_stretch(seg_b, sb_sf, work_dir / "b_stretched.wav")

        # Step 5: Pitch-shift for key matching
        if md.song_a.pitch_shift_semitones != 0:
            seg_a = _pitch_shift(seg_a, md.song_a.pitch_shift_semitones, work_dir / "a_pitched.wav")
        if md.song_b.pitch_shift_semitones != 0:
            seg_b = _pitch_shift(seg_b, md.song_b.pitch_shift_semitones, work_dir / "b_pitched.wav")

        # Step 6: Crossfade (trans_dur is at target BPM, matching stretched segments)
        mixed = _crossfade(
            seg_a, seg_b,
            crossfade_start_in_a=fade_start * sa_sf if sa_sf != 1.0 else fade_start,
            crossfade_duration=trans_dur,
            curve=md.transition.crossfade_curve,
            work_dir=work_dir,
        )

        # Step 7: SFX overlay
        if md.sfx.enabled:
            mixed = await _overlay_sfx(mixed, md, fade_start, work_dir)

        # Step 8: Normalize and export
        output_mp3 = OUTPUT_DIR / f"{session_id}_mix.mp3"
        output_wav = OUTPUT_DIR / f"{session_id}_mix.wav"
        _normalize_and_export(mixed, output_mp3, output_wav)

        return output_mp3

    except Exception as e:
        logger.error(f"Render failed: {e}")
        # Retry with simplified settings
        return await _simplified_render(song_a_path, song_b_path, contract_b, session_id, work_dir)
    finally:
        # Cleanup work dir
        shutil.rmtree(work_dir, ignore_errors=True)


def _ensure_wav(input_path: Path, output_path: Path) -> Path:
    if input_path.suffix.lower() == ".wav":
        shutil.copy2(input_path, output_path)
        return output_path
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(input_path), "-ar", "44100", "-ac", "2", str(output_path)],
        capture_output=True, check=True,
    )
    return output_path


def _pitch_shift(input_wav: Path, semitones: int, output_path: Path) -> Path:
    """Pitch-shift without changing tempo, using rubberband or ffmpeg."""
    try:
        subprocess.run(
            ["rubberband", "-p", str(semitones), str(input_wav), str(output_path)],
            capture_output=True, check=True, timeout=30,
        )
        return output_path
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.warning(f"Rubberband pitch-shift failed ({e}), using ffmpeg asetrate")
        # Fallback: ffmpeg asetrate + aresample (changes speed slightly, less ideal)
        factor = 2 ** (semitones / 12.0)
        new_rate = int(44100 * factor)
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(input_wav),
             "-af", f"asetrate={new_rate},aresample=44100",
             str(output_path)],
            capture_output=True, check=True,
        )
        return output_path


def _time_stretch(input_wav: Path, factor: float, output_path: Path) -> Path:
    """Time-stretch using rubberband for high-quality pitch-preserving stretch.

    `factor` = target_bpm / song_bpm (>1 means speed up).
    rubberband -t expects a time ratio (>1 = slower), so we invert.
    ffmpeg atempo expects a speed ratio (>1 = faster), so we use factor directly.
    """
    rb_time_ratio = 1.0 / factor  # invert: speed-up → shorter duration
    try:
        subprocess.run(
            ["rubberband", "-t", str(rb_time_ratio), "-p", "0", str(input_wav), str(output_path)],
            capture_output=True, check=True, timeout=60,
        )
        return output_path
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.warning(f"Rubberband failed ({e}), trying ffmpeg atempo")
        # Fallback: ffmpeg atempo filter (less quality but always available)
        # atempo range is 0.5-2.0, chain for extreme values
        atempo_val = factor  # atempo >1 = faster (correct direction)
        atempo_chain = []
        while atempo_val > 2.0:
            atempo_chain.append("atempo=2.0")
            atempo_val /= 2.0
        while atempo_val < 0.5:
            atempo_chain.append("atempo=0.5")
            atempo_val *= 2.0
        atempo_chain.append(f"atempo={atempo_val:.4f}")

        subprocess.run(
            ["ffmpeg", "-y", "-i", str(input_wav), "-af", ",".join(atempo_chain), str(output_path)],
            capture_output=True, check=True,
        )
        return output_path


def _extract_segment(input_wav: Path, start_ms: float, end_ms: Optional[float], output_path: Path) -> Path:
    cmd = ["ffmpeg", "-y", "-i", str(input_wav), "-ss", f"{start_ms / 1000:.3f}"]
    if end_ms is not None:
        duration = (end_ms - start_ms) / 1000
        cmd += ["-t", f"{duration:.3f}"]
    cmd += ["-ar", "44100", "-ac", "2", str(output_path)]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def _apply_eq_automation(
    wav_path: Path, eq_auto, song_id: str, time_offset_ms: float, work_dir: Path,
) -> Path:
    """Apply EQ automation using FFmpeg filters."""
    filters = []

    entries = {
        "bass": getattr(eq_auto, f"song_{song_id}_bass", None),
        "highs": getattr(eq_auto, f"song_{song_id}_highs", None),
        "mids": getattr(eq_auto, f"song_{song_id}_mids", None),
    }

    for band, entry in entries.items():
        if entry is None:
            continue
        f = _eq_filter_for_band(entry, band, time_offset_ms)
        if f:
            filters.append(f)

    if not filters:
        return wav_path

    output = work_dir / f"eq_{song_id}.wav"
    filter_str = ",".join(filters)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(wav_path), "-af", filter_str, str(output)],
        capture_output=True, check=True,
    )
    return output


def _eq_filter_for_band(entry: EQAutomationEntry, band: str, offset_ms: float) -> Optional[str]:
    """Generate FFmpeg filter string for an EQ automation entry.

    Uses smooth volume expressions instead of binary on/off filters
    to avoid jarring volume drops at the transition point.
    """
    start_s = (entry.start_ms - offset_ms) / 1000
    end_s = (entry.end_ms - offset_ms) / 1000
    if start_s < 0:
        start_s = 0
    dur_s = end_s - start_s
    if dur_s <= 0:
        return None

    from_db = entry.from_db
    to_db = entry.to_db

    # Use an equalizer band filter with a smooth volume ramp via
    # the volume filter and enable expressions.
    # This creates a gradual gain change rather than a hard on/off.
    if band == "bass":
        freq = 100
        width = 120  # Hz bandwidth
    elif band == "highs":
        freq = 8000
        width = 4000
    elif band == "mids":
        freq = 1000
        width = 2000
    else:
        return None

    # Compute gain ramp: linearly interpolate between from_db and to_db
    # over the window [start_s, end_s] using ffmpeg expressions.
    # gain(t) = from_db + (to_db - from_db) * ((t - start_s) / dur_s)
    # Clamp to the window with enable.
    gain_expr = f"{from_db}+{to_db - from_db}*((t-{start_s:.3f})/{dur_s:.3f})"
    return (
        f"equalizer=f={freq}:width_type=h:width={width}"
        f":g='{gain_expr}'"
        f":enable='between(t,{start_s:.3f},{end_s:.3f})'"
    )


def _crossfade(
    seg_a: Path, seg_b: Path,
    crossfade_start_in_a: float,
    crossfade_duration: float,
    curve: str,
    work_dir: Path,
) -> Path:
    """Create crossfade between two segments using FFmpeg."""
    output = work_dir / "crossfaded.wav"
    dur_sec = crossfade_duration / 1000

    # Get duration of seg_a
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(seg_a)],
        capture_output=True, text=True,
    )
    seg_a_dur = float(probe.stdout.strip()) if probe.stdout.strip() else 60.0

    # Use ffmpeg acrossfade filter
    curve_type = "esin" if curve == "equal_power" else ("exp" if curve == "exponential" else "tri")

    subprocess.run(
        ["ffmpeg", "-y",
         "-i", str(seg_a), "-i", str(seg_b),
         "-filter_complex",
         f"acrossfade=d={dur_sec:.3f}:c1={curve_type}:c2={curve_type}",
         "-ar", "44100", "-ac", "2",
         str(output)],
        capture_output=True, check=True,
    )
    return output


async def _overlay_sfx(mixed_path: Path, md, fade_start: float, work_dir: Path) -> Path:
    """Overlay SFX at the specified position."""
    sfx_path = await get_sfx_audio(md.sfx, work_dir)
    if sfx_path is None:
        return mixed_path

    output = work_dir / "with_sfx.wav"
    position_s = md.sfx.position_ms / 1000

    # Mix SFX at -6dB relative to main
    subprocess.run(
        ["ffmpeg", "-y",
         "-i", str(mixed_path),
         "-i", str(sfx_path),
         "-filter_complex",
         f"[1:a]adelay={int(md.sfx.position_ms)}|{int(md.sfx.position_ms)},volume=0.5[sfx];"
         f"[0:a][sfx]amix=inputs=2:duration=longest",
         "-ar", "44100", "-ac", "2",
         str(output)],
        capture_output=True, check=True,
    )
    return output


def _normalize_and_export(wav_path: Path, output_mp3: Path, output_wav: Path) -> None:
    """Normalize to -1dB peak and export as MP3 + WAV."""
    # Export MP3 320kbps with loudnorm
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(wav_path),
         "-af", "loudnorm=I=-14:LRA=11:TP=-1",
         "-b:a", "320k", str(output_mp3)],
        capture_output=True, check=True,
    )
    # Export WAV
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(wav_path),
         "-af", "loudnorm=I=-14:LRA=11:TP=-1",
         str(output_wav)],
        capture_output=True, check=True,
    )


async def _simplified_render(
    song_a_path: Path, song_b_path: Path,
    contract_b: ContractB, session_id: str, work_dir: Path,
) -> Path:
    """Simplified render: simple crossfade without EQ automation."""
    logger.info("Attempting simplified render (no EQ, linear fade)")
    md = contract_b.mix_decision
    output_mp3 = OUTPUT_DIR / f"{session_id}_mix.mp3"

    wav_a = _ensure_wav(song_a_path, work_dir / "simple_a.wav")
    wav_b = _ensure_wav(song_b_path, work_dir / "simple_b.wav")

    # Extract segments if in-point is set (otherwise full songs)
    in_point = md.song_b.in_point_ms or 0
    if in_point > 0:
        wav_b = _extract_segment(wav_b, in_point, None, work_dir / "simple_b_seg.wav")

    dur_sec = md.transition.total_duration_ms / 1000

    # Two-pass: crossfade first, then normalize
    crossfaded = work_dir / "simple_crossfaded.wav"
    subprocess.run(
        ["ffmpeg", "-y",
         "-i", str(wav_a), "-i", str(wav_b),
         "-filter_complex",
         f"acrossfade=d={dur_sec:.3f}:c1=tri:c2=tri",
         "-ar", "44100", "-ac", "2",
         str(crossfaded)],
        capture_output=True, check=True,
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(crossfaded),
         "-af", "loudnorm=I=-14:LRA=11:TP=-1",
         "-b:a", "320k",
         str(output_mp3)],
        capture_output=True, check=True,
    )
    return output_mp3
