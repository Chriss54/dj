"""Musical key detection using chroma features + Krumhansl-Schmuckler algorithm."""

import numpy as np
import librosa

# Krumhansl-Schmuckler key profiles
MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

KEY_NAMES_MAJOR = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
KEY_NAMES_MINOR = ["Cm", "C#m", "Dm", "Ebm", "Em", "Fm", "F#m", "Gm", "G#m", "Am", "Bbm", "Bm"]


def detect_key(y: np.ndarray, sr: int) -> tuple[str, float]:
    """
    Detect musical key using chroma CQT + Krumhansl-Schmuckler.
    Returns (key_name, confidence) where confidence is 0.0-1.0.
    """
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_mean = np.mean(chroma, axis=1)

    # Normalize
    if chroma_mean.max() > 0:
        chroma_mean = chroma_mean / chroma_mean.max()

    best_corr = -1.0
    best_key = "C"

    # Test all 24 keys (12 major + 12 minor)
    for i in range(12):
        rotated = np.roll(chroma_mean, -i)

        corr_major = np.corrcoef(rotated, MAJOR_PROFILE)[0, 1]
        corr_minor = np.corrcoef(rotated, MINOR_PROFILE)[0, 1]

        if corr_major > best_corr:
            best_corr = corr_major
            best_key = KEY_NAMES_MAJOR[i]

        if corr_minor > best_corr:
            best_corr = corr_minor
            best_key = KEY_NAMES_MINOR[i]

    # Normalize confidence to 0-1 range
    confidence = max(0.0, min(1.0, (best_corr + 1) / 2))

    return best_key, confidence
