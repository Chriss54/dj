"""Camelot Wheel mapping and compatibility computation."""

# Key → Camelot code mapping
KEY_TO_CAMELOT = {
    "C major": "8B", "Db major": "3B", "D major": "10B", "Eb major": "5B",
    "E major": "12B", "F major": "7B", "F# major": "2B", "Gb major": "2B",
    "G major": "9B", "Ab major": "4B", "A major": "11B", "Bb major": "6B",
    "B major": "1B",
    "C minor": "5A", "C# minor": "12A", "Db minor": "12A", "D minor": "7A",
    "Eb minor": "2A", "E minor": "9A", "F minor": "4A", "F# minor": "11A",
    "Gb minor": "11A", "G minor": "6A", "G# minor": "1A", "Ab minor": "1A",
    "A minor": "8A", "Bb minor": "3A", "B minor": "10A",
    # Short form
    "C": "8B", "Cm": "5A", "C#": "3B", "C#m": "12A",
    "Db": "3B", "Dbm": "12A", "D": "10B", "Dm": "7A",
    "D#": "5B", "D#m": "2A", "Eb": "5B", "Ebm": "2A",
    "E": "12B", "Em": "9A", "F": "7B", "Fm": "4A",
    "F#": "2B", "F#m": "11A", "Gb": "2B", "Gbm": "11A",
    "G": "9B", "Gm": "6A", "G#": "4B", "G#m": "1A",
    "Ab": "4B", "Abm": "1A", "A": "11B", "Am": "8A",
    "A#": "6B", "A#m": "3A", "Bb": "6B", "Bbm": "3A",
    "B": "1B", "Bm": "10A",
}

CAMELOT_TO_KEY = {v: k for k, v in KEY_TO_CAMELOT.items() if " " in k}


def key_to_camelot(key: str) -> str:
    return KEY_TO_CAMELOT.get(key, "?")


def camelot_distance(cam_a: str, cam_b: str) -> int:
    """Compute the minimum distance on the Camelot wheel (0-6)."""
    if cam_a == "?" or cam_b == "?":
        return -1
    try:
        num_a, letter_a = int(cam_a[:-1]), cam_a[-1]
        num_b, letter_b = int(cam_b[:-1]), cam_b[-1]
    except (ValueError, IndexError):
        return -1

    if letter_a == letter_b:
        # Same inner/outer ring
        diff = abs(num_a - num_b)
        return min(diff, 12 - diff)
    else:
        # Different rings — check if same number (relative major/minor)
        if num_a == num_b:
            return 0  # relative major/minor is compatible
        diff = abs(num_a - num_b)
        return min(diff, 12 - diff) + 1


def camelot_relation(cam_a: str, cam_b: str) -> str:
    dist = camelot_distance(cam_a, cam_b)
    if dist < 0:
        return "unknown"
    if dist == 0:
        return "same"
    if dist == 1:
        return "adjacent"
    if dist == 2:
        return "relative"
    return "incompatible"


def harmonic_score(cam_a: str, cam_b: str) -> float:
    dist = camelot_distance(cam_a, cam_b)
    if dist < 0:
        return 0.5
    scores = {0: 1.0, 1: 0.85, 2: 0.6, 3: 0.4, 4: 0.2, 5: 0.1, 6: 0.05}
    return scores.get(dist, 0.05)


# Camelot code → pitch class (tonic as semitones above C)
_CAMELOT_TO_PITCH = {
    "1A": 8, "2A": 3, "3A": 10, "4A": 5, "5A": 0, "6A": 7,
    "7A": 2, "8A": 9, "9A": 4, "10A": 11, "11A": 6, "12A": 1,
    "1B": 11, "2B": 6, "3B": 1, "4B": 8, "5B": 3, "6B": 10,
    "7B": 5, "8B": 0, "9B": 7, "10B": 2, "11B": 9, "12B": 4,
}


def pitch_shift_to_match(cam_source: str, cam_target: str) -> int:
    """
    Calculate the semitone pitch shift needed to move cam_source
    to be harmonically compatible with cam_target.
    Returns the shift in semitones (-6 to +6) for the smallest movement.
    Returns 0 if already compatible or if keys are unknown.
    """
    if camelot_distance(cam_source, cam_target) <= 1:
        return 0  # already compatible

    pitch_src = _CAMELOT_TO_PITCH.get(cam_source)
    pitch_tgt = _CAMELOT_TO_PITCH.get(cam_target)
    if pitch_src is None or pitch_tgt is None:
        return 0

    # Find shortest path in semitones
    diff = (pitch_tgt - pitch_src) % 12
    if diff > 6:
        diff -= 12  # prefer shifting down
    return diff
