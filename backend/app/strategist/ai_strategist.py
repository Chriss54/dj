"""Tier 2: AI Mix Strategist — uses Gemini API for creative mix decisions."""

import json
import logging
from typing import Optional

import httpx

from ..models.contracts import ContractA, ContractB
from ..config import GEMINI_API_KEY, GEMINI_TIMEOUT_SEC, GEMINI_MODEL
from .fallback import rule_based_mix

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert DJ and music producer with 20 years of experience in live
mixing and studio production. You understand harmonic mixing (Camelot Wheel),
phrase structure, energy management, and EQ transitions.

You will receive a JSON analysis of two songs (BPM, key, beats, phrases,
energy curves, compatibility data) and a user-indicated transition zone.

Your job:
1. Choose the optimal transition strategy based on the musical data.
2. Align the transition to phrase boundaries (8 or 16 bar groups).
3. If BPM difference > 2, specify tempo adjustment factors.
4. Design EQ automation: at minimum, bass swap. Optionally mid/high automation.
5. Decide if an SFX transition effect would enhance the mix.
6. Explain your reasoning.

Transition strategies you may choose from:
- "phrase_blend": Long blend over 16-32 bars. Best for compatible keys/energy.
- "drop_swap": Cut at a drop/breakdown. Best for high-energy EDM transitions.
- "echo_out": Echo/reverb tail on Song A, hard cut to Song B. Dramatic effect.
- "bass_swap": Quick bass exchange over 4-8 bars. Classic DJ technique.
- "breakdown_bridge": Use a breakdown in Song A to introduce Song B elements.

Respond with ONLY valid JSON matching this schema:
{
  "mix_decision": {
    "strategy": "<strategy_name>",
    "confidence": <0.0-1.0>,
    "reasoning": "<explanation>",
    "song_a": {
      "out_point_ms": <ms>,
      "out_phrase": "<phrase_type>",
      "fade_start_ms": <ms>,
      "tempo_stretch_factor": <float>
    },
    "song_b": {
      "in_point_ms": <ms>,
      "in_phrase": "<phrase_type>",
      "fade_end_ms": <ms>,
      "tempo_stretch_factor": <float>
    },
    "transition": {
      "total_duration_ms": <ms>,
      "crossfade_curve": "equal_power|linear|exponential",
      "eq_automation": {
        "song_a_bass": {"action":"cut","start_ms":<>,"end_ms":<>,"from_db":0,"to_db":-24,"curve":"linear"},
        "song_b_bass": {"action":"boost","start_ms":<>,"end_ms":<>,"from_db":-24,"to_db":0,"curve":"linear"},
        "song_a_highs": {"action":"cut","start_ms":<>,"end_ms":<>,"from_db":0,"to_db":-12,"curve":"exponential"}
      }
    },
    "sfx": {
      "enabled": true|false,
      "type": "riser_sweep|sweep|vinyl_scratch|reverb_tail|impact|noise_build|none",
      "trigger_reason": "<why>",
      "position_ms": <ms>,
      "duration_ms": <ms>,
      "source": "elevenlabs|library",
      "elevenlabs_prompt": "<descriptive prompt>",
      "fallback_file": "sfx/<filename>.wav"
    }
  }
}

No markdown, no commentary, no code fences. Pure JSON.

If the songs are fundamentally incompatible (>8 BPM difference AND clashing
keys AND no viable phrase alignment), return:
{
  "mix_decision": {
    "strategy": "incompatible",
    "confidence": 0.0,
    "reasoning": "Explain why these songs don't mix well",
    "suggestion": "Recommend what the user could change"
  }
}"""


async def ai_mix_decision(
    contract_a: ContractA,
    transition_start_ms: Optional[float] = None,
    user_strategy: Optional[str] = None,
    mix_in_key: bool = False,
    song_b_in_point_ms: Optional[float] = None,
) -> ContractB:
    """
    Get mix decision from Gemini API, with automatic fallback to rule-based mixing.
    """
    if not GEMINI_API_KEY:
        logger.warning("No Gemini API key configured — using rule-based fallback")
        return rule_based_mix(contract_a, transition_start_ms, mix_in_key, song_b_in_point_ms)

    try:
        result = await _call_gemini(contract_a, transition_start_ms, user_strategy, song_b_in_point_ms)
        # Apply pitch shift if mix_in_key requested but Gemini didn't set it
        if mix_in_key and result.mix_decision.song_b.pitch_shift_semitones == 0:
            from ..analysis.camelot import pitch_shift_to_match
            shift = pitch_shift_to_match(
                contract_a.song_b.camelot, contract_a.song_a.camelot
            )
            result.mix_decision.song_b.pitch_shift_semitones = shift
        return result
    except Exception as e:
        logger.error(f"Gemini API failed: {e} — using rule-based fallback")
        return rule_based_mix(contract_a, transition_start_ms, mix_in_key, song_b_in_point_ms)


async def _call_gemini(
    contract_a: ContractA,
    transition_start_ms: Optional[float],
    user_strategy: Optional[str],
    song_b_in_point_ms: Optional[float] = None,
) -> ContractB:
    """Call Gemini API and parse the response into Contract B."""
    # Build user message with analysis data
    # Trim beats_ms to keep payload manageable (send every 4th beat)
    trimmed_a = contract_a.model_dump()
    for song_key in ("song_a", "song_b"):
        beats = trimmed_a[song_key]["beats_ms"]
        trimmed_a[song_key]["beats_ms"] = beats[::4]  # every 4th beat
        # Limit energy curve to every 2nd point
        ec = trimmed_a[song_key]["energy_curve"]
        trimmed_a[song_key]["energy_curve"] = ec[::2]

    user_msg = f"Analysis data:\n{json.dumps(trimmed_a, indent=2)}"
    if transition_start_ms is not None:
        user_msg += f"\n\nUser wants the transition to start around {transition_start_ms}ms in Song A."
    if song_b_in_point_ms is not None:
        user_msg += f"\n\nUser wants Song B to enter around {song_b_in_point_ms}ms (the in-point for Song B)."
    if user_strategy:
        user_msg += f"\n\nUser prefers transition strategy: {user_strategy}"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": user_msg}]}
        ],
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "generationConfig": {
            "temperature": 0.7,
            "responseMimeType": "application/json",
        },
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, timeout=GEMINI_TIMEOUT_SEC)
        resp.raise_for_status()

    data = resp.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    parsed = json.loads(text)

    return ContractB.model_validate(parsed)
