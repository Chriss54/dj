"""SFX Director — ElevenLabs integration with local fallback library."""

import hashlib
import logging
from pathlib import Path
from typing import Optional

import httpx

from ..models.contracts import SFXConfig
from ..config import ELEVENLABS_API_KEY, ELEVENLABS_TIMEOUT_SEC, SFX_LIBRARY_DIR

logger = logging.getLogger(__name__)

# Cache generated SFX by prompt hash
_sfx_cache: dict[str, Path] = {}


async def get_sfx_audio(sfx_config: SFXConfig, work_dir: Path) -> Optional[Path]:
    """Get SFX audio file — try ElevenLabs first, fall back to local library."""
    if not sfx_config.enabled or sfx_config.type == "none":
        return None

    # Try ElevenLabs if configured and requested
    if sfx_config.source == "elevenlabs" and ELEVENLABS_API_KEY and sfx_config.elevenlabs_prompt:
        try:
            return await _generate_elevenlabs_sfx(sfx_config, work_dir)
        except Exception as e:
            logger.warning(f"ElevenLabs SFX generation failed: {e}")

    # Fallback to local library
    return _get_fallback_sfx(sfx_config)


async def _generate_elevenlabs_sfx(sfx_config: SFXConfig, work_dir: Path) -> Path:
    """Generate SFX using ElevenLabs Sound Effects API."""
    prompt_hash = hashlib.md5(sfx_config.elevenlabs_prompt.encode()).hexdigest()[:12]

    # Check cache
    if prompt_hash in _sfx_cache and _sfx_cache[prompt_hash].exists():
        return _sfx_cache[prompt_hash]

    url = "https://api.elevenlabs.io/v1/sound-generation"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": sfx_config.elevenlabs_prompt,
        "duration_seconds": sfx_config.duration_ms / 1000,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url, json=payload, headers=headers, timeout=ELEVENLABS_TIMEOUT_SEC,
        )
        resp.raise_for_status()

    output_path = work_dir / f"sfx_{prompt_hash}.wav"
    output_path.write_bytes(resp.content)

    # Validate duration
    _sfx_cache[prompt_hash] = output_path
    return output_path


def _get_fallback_sfx(sfx_config: SFXConfig) -> Optional[Path]:
    """Get SFX from local library."""
    # Try specific fallback file first
    if sfx_config.fallback_file:
        fallback = SFX_LIBRARY_DIR / Path(sfx_config.fallback_file).name
        if fallback.exists():
            return fallback

    # Try matching by type
    type_mapping = {
        "riser_sweep": "riser",
        "sweep": "sweep",
        "vinyl_scratch": "scratch",
        "reverb_tail": "reverb",
        "impact": "impact",
        "noise_build": "noise_build",
    }

    prefix = type_mapping.get(sfx_config.type, sfx_config.type)
    for f in SFX_LIBRARY_DIR.glob(f"{prefix}*.wav"):
        return f

    # Last resort: any SFX file
    for f in SFX_LIBRARY_DIR.glob("*.wav"):
        return f

    logger.warning("No SFX files found in library")
    return None
