# 🎧 SMART AI DJ – Master Prompt für den Team Leader

> **Zweck dieses Dokuments:** Dies ist der vollständige, produktionsreife Prompt, den der Team Leader an sein KI-Agenten-Team übergibt. Er enthält Architektur, Contracts, Rollen, Qualitätsstandards und Fallback-Strategien.

---

## Mission Statement

Build a **Smart AI DJ** web application that creates professional-quality transitions between two uploaded songs. The app must handle BPM matching, harmonic mixing, phrase-aligned transitions, and EQ automation — not just simple crossfades.

**Core Principle:** We are building a DJ tool, not a cutting tool. A transition is not a cut point — it's a musical story that unfolds over 16–32 bars.

---

## Architecture: 3-Tier "Analyze → Decide → Execute"

```
┌─────────────────────────────────────────────────────────┐
│  TIER 1: ANALYSIS ENGINE (Python – librosa/essentia)    │
│  Precise musical data extraction. No AI needed here.    │
│  Output: Analysis JSON (Contract A)                     │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  TIER 2: AI MIX STRATEGIST (Gemini 3 Pro API)           │
│  Creative decision-making based on structured data.     │
│  Input: Contract A → Output: Mix Decision (Contract B)  │
│  ⚠️ Gemini does NOT analyze audio directly.             │
│  ⚠️ Rule-based fallback if API fails or times out.      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  TIER 3: AUDIO RENDERER (FFmpeg + rubberband)           │
│  Executes the mix decision. Time-stretch, crossfade,    │
│  EQ automation, SFX overlay, final render.              │
└─────────────────────────────────────────────────────────┘
```

**Why this separation matters:**
- LLMs (including Gemini 3 Pro) are not reliable for millisecond-accurate beat detection. They process audio as token sequences and will hallucinate timestamps.
- Dedicated libraries (librosa, essentia, madmom) are purpose-built for Music Information Retrieval and achieve near-sample accuracy.
- Gemini 3 Pro excels at **creative reasoning**: choosing transition types, evaluating musical compatibility, suggesting energy flow — tasks that require musical intelligence, not signal processing.

---

## Phase 0: Research Sprint (BEFORE ANY CODE)

Spawn a Research Agent to confirm and document the following. All findings must be shared with the team before Phase 1 begins.

### Research Tasks:

1. **Gemini 3 Pro Audio API:**
   - Confirm the exact method to send audio (File API upload vs. inline base64).
   - Document supported audio formats, max file size, max duration.
   - Benchmark response latency for a 30-second audio analysis request.
   - Confirm JSON-mode output is available (structured output / response schema).

2. **Beat Detection Accuracy:**
   - Benchmark `librosa.beat.beat_track()` accuracy against 10 test songs across genres (EDM, Hip-Hop, Pop, Rock, Jazz).
   - If librosa's accuracy is insufficient for any genre, evaluate alternatives: `madmom.features.beats.DBNBeatTrackingProcessor`, `essentia BeatTrackerMultiFeature`.
   - **Key requirement:** Beat positions must be accurate within ±20ms for professional-quality transitions. If no library achieves this consistently, document the failure cases and propose a hybrid approach or user-assisted correction.

3. **Key Detection:**
   - Compare `librosa.feature.chroma_cqt` + Krumhansl-Schmuckler vs. `essentia KeyExtractor`.
   - Document accuracy rates. If key detection is unreliable, the system must flag uncertainty to the user rather than making bad transitions.

4. **FFmpeg Crossfade:**
   - Find the optimal FFmpeg filter chain for:
     - Beat-aligned crossfading with equal-power curve
     - Independent bass/mid/high EQ control during transition
     - Time-stretching integration (rubberband or SoundTouch via FFmpeg)
   - Document the exact command syntax.

5. **ElevenLabs Sound Effects API:**
   - Confirm the endpoint for generating sound effects (not speech).
   - Test generation of: risers, sweeps, vinyl scratches, white noise builds, reverb tails.
   - Benchmark latency and quality.
   - **Decision point:** If ElevenLabs SFX quality or latency is insufficient, fall back to a pre-produced SFX sample library (30+ categorized WAV files).

6. **Latency Budget:**
   - The full pipeline (upload → analysis → AI decision → render → playback) will realistically take **10–20 seconds** for two full-length songs. This is acceptable.
   - Research and propose optimizations:
     - Pre-analyze songs on upload (before user requests a mix).
     - Stream partial results to frontend (show analysis while AI decides).
     - Cache analysis results for re-used songs.
     - Use WebSocket for progress updates instead of polling.
   - **Do not promise sub-3-second latency.** Design for transparency: show the user what's happening at each stage.

---

## Phase 1: JSON Contract Design (MANDATORY BEFORE ANY CODE)

All agents must review, discuss, and agree on these contracts. No implementation begins until contracts are locked.

### Contract A: Audio Analysis Output (Tier 1 → Tier 2)

```json
{
  "song_a": {
    "filename": "track_a.mp3",
    "duration_ms": 240000,
    "bpm": 124.5,
    "bpm_confidence": 0.94,
    "key": "Am",
    "key_confidence": 0.78,
    "camelot": "8A",
    "beats_ms": [0, 484, 968, 1452, 1936, 2420, ...],
    "downbeats_ms": [0, 1936, 3872, 5808, ...],
    "phrases": [
      {
        "start_ms": 0,
        "end_ms": 15488,
        "bars": 8,
        "type": "intro",
        "avg_energy": 0.35
      },
      {
        "start_ms": 15488,
        "end_ms": 46464,
        "bars": 16,
        "type": "verse",
        "avg_energy": 0.62
      },
      {
        "start_ms": 46464,
        "end_ms": 62000,
        "bars": 8,
        "type": "chorus",
        "avg_energy": 0.89
      }
    ],
    "energy_curve": [
      {"ms": 0, "rms": 0.12},
      {"ms": 1000, "rms": 0.15},
      {"ms": 2000, "rms": 0.31}
    ]
  },
  "song_b": {
    "...": "same structure"
  },
  "compatibility": {
    "bpm_diff": 3.5,
    "bpm_ratio": 1.028,
    "key_compatible": true,
    "camelot_distance": 1,
    "camelot_relation": "adjacent",
    "needs_tempo_adjustment": true,
    "recommended_target_bpm": 126.0,
    "harmonic_mixing_score": 0.85
  }
}
```

**Notes on Contract A:**
- `bpm_confidence` and `key_confidence` are critical. If confidence < 0.6, the system must warn the user and suggest manual verification.
- `phrases` must identify structural sections. If automatic segmentation fails, fall back to fixed 8-bar groupings aligned to downbeats.
- `energy_curve` uses RMS values normalized to 0.0–1.0, sampled every 1000ms.
- `camelot` uses the Camelot Wheel notation (1A–12A, 1B–12B) for harmonic compatibility.

### Contract B: AI Mix Decision (Tier 2 → Tier 3)

```json
{
  "mix_decision": {
    "strategy": "phrase_blend",
    "confidence": 0.87,
    "reasoning": "Outro of Song A (bars 56-64, energy declining from 0.72 to 0.35) aligns with intro of Song B (bars 1-8, energy rising from 0.20 to 0.55). Key transition Am → Em is Camelot 8A → 9A (adjacent, harmonically smooth). BPM difference of 3.5 requires gentle tempo adjustment to 126.0 BPM.",

    "song_a": {
      "out_point_ms": 185400,
      "out_phrase": "outro",
      "fade_start_ms": 177400,
      "tempo_stretch_factor": 1.012
    },
    "song_b": {
      "in_point_ms": 0,
      "in_phrase": "intro",
      "fade_end_ms": 32200,
      "tempo_stretch_factor": 0.984
    },

    "transition": {
      "total_duration_ms": 16000,
      "crossfade_curve": "equal_power",
      "eq_automation": {
        "song_a_bass": {
          "action": "cut",
          "start_ms": 185400,
          "end_ms": 193400,
          "from_db": 0,
          "to_db": -24,
          "curve": "linear"
        },
        "song_b_bass": {
          "action": "boost",
          "start_ms": 193400,
          "end_ms": 201400,
          "from_db": -24,
          "to_db": 0,
          "curve": "linear"
        },
        "song_a_highs": {
          "action": "cut",
          "start_ms": 189400,
          "end_ms": 201400,
          "from_db": 0,
          "to_db": -12,
          "curve": "exponential"
        }
      }
    },

    "sfx": {
      "enabled": true,
      "type": "riser_sweep",
      "trigger_reason": "energy_bridge",
      "position_ms": 189400,
      "duration_ms": 4000,
      "source": "elevenlabs|library",
      "elevenlabs_prompt": "A building cinematic riser sweep with white noise, 4 seconds, electronic music style",
      "fallback_file": "sfx/riser_electronic_01.wav"
    }
  }
}
```

**Notes on Contract B:**
- `reasoning` is mandatory. The AI must explain its creative decision so the user (and developers) can evaluate quality.
- `eq_automation` is what separates this from amateur crossfade tools. Bass swap is the minimum; high/mid automation is optional but recommended.
- `sfx.source` indicates whether to attempt ElevenLabs generation or use a library file. Always include `fallback_file`.
- `tempo_stretch_factor` of 1.0 means no change. Values are relative to `recommended_target_bpm`.

---

## Phase 2: Build Team (Agent Roles)

### Agent 1: Audio Analysis Engine (Tier 1)

**Stack:** Python, librosa, essentia (optional), numpy, scipy

**Responsibilities:**
1. Accept uploaded audio files (MP3, WAV, FLAC, OGG, M4A).
2. Convert to WAV internally for analysis (ffmpeg).
3. Extract:
   - BPM via `librosa.beat.beat_track()` with confidence score
   - Key via chroma features + Krumhansl-Schmuckler algorithm
   - Camelot Wheel mapping from detected key
   - Full beat grid (all beat positions in ms)
   - Downbeat positions (every 4th beat, adjusted for time signature)
   - Phrase boundaries via structural segmentation (`librosa.segment`)
   - Energy curve via RMS computation per beat
4. Compute compatibility metrics between Song A and Song B.
5. Output: **Contract A JSON**.

**Performance target:** Full analysis of 2 songs (each ~4 min) in < 6 seconds on a standard server.

**Error handling:**
- If BPM detection confidence < 0.6: return `"bpm_warning": "Low confidence. Consider manual BPM entry."` and attempt secondary detection with `madmom`.
- If key detection confidence < 0.5: return `"key_warning": "Unable to determine key reliably."` and set `key_compatible` to `"unknown"`.
- If audio is corrupt or unreadable: return structured error, never crash.

---

### Agent 2: AI Mix Strategist (Tier 2)

**Stack:** Python, FastAPI, Gemini 3 Pro API

**Input:** Contract A JSON + user's transition window preference (approximate ms range).

**Role:** Creative decision-making ONLY. This agent never touches audio files directly.

**System Prompt for Gemini 3 Pro:**

```
You are an expert DJ and music producer with 20 years of experience in live
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

Respond with ONLY valid JSON matching Contract B schema. No markdown, no
commentary, no code fences. Pure JSON.

If the songs are fundamentally incompatible (>8 BPM difference AND clashing
keys AND no viable phrase alignment), return:
{
  "mix_decision": {
    "strategy": "incompatible",
    "confidence": 0.0,
    "reasoning": "Explain why these songs don't mix well",
    "suggestion": "Recommend what the user could change"
  }
}
```

**Fallback (Rule-Based Mixer):**
If Gemini 3 Pro is unavailable, times out (>12s), or returns invalid JSON, the system MUST still produce a mix using these rules:
1. Find the nearest downbeat to the user's marker in Song A.
2. Find the first downbeat of a phrase in Song B.
3. Apply 8-bar linear crossfade with bass swap.
4. If BPM diff > 2: stretch both songs to the average BPM.
5. No SFX.
6. Set `"confidence": 0.5` and `"reasoning": "Rule-based fallback (AI unavailable)"`.

**The app must NEVER fail because the AI is down.**

---

### Agent 3: Audio Renderer (Tier 3)

**Stack:** Python, ffmpeg-python or subprocess, rubberband-cli, pydub (optional)

**Input:** Contract B JSON + original audio files.

**Responsibilities:**
1. **Time-stretching** (if `tempo_stretch_factor ≠ 1.0`):
   - Use `rubberband` for high-quality pitch-preserving time-stretch.
   - Command: `rubberband -t {factor} -p 0 input.wav output.wav`
   - Verify output duration matches expectation (±50ms tolerance).

2. **Transition rendering:**
   - Extract relevant segments from both songs based on Contract B coordinates.
   - Apply crossfade with specified curve (linear, equal_power, exponential).
   - `equal_power` formula: `gain_a = cos(t * π/2)`, `gain_b = sin(t * π/2)` where t goes 0→1.

3. **EQ Automation:**
   - Use FFmpeg's `equalizer` or `highpass`/`lowpass` filters with timeline editing.
   - Bass cut: Apply progressive highpass filter (20Hz → 200Hz over specified duration).
   - Bass boost: Reverse (200Hz → 20Hz).
   - High cut: Apply progressive lowpass filter (20kHz → 5kHz).
   - All EQ changes must be sample-accurate to the timestamps in Contract B.

4. **SFX Overlay:**
   - If `sfx.enabled` is true:
     - First attempt: If `sfx.source` is "elevenlabs", call ElevenLabs Sound Effects API with the provided prompt. Timeout: 8 seconds.
     - If ElevenLabs fails or times out: use `sfx.fallback_file` from local library.
   - Mix SFX at specified position with -6dB relative to main mix.

5. **Final render:**
   - Output format: MP3 (320kbps) and WAV (for quality preview).
   - Normalize output to -1dB peak (prevent clipping).
   - Verify output contains no silence gaps or clicks at transition points.

**Performance target:** Complete render in < 10 seconds for a standard 16-bar transition.

---

### Agent 4: SFX Director (ElevenLabs Integration)

**Stack:** Python, ElevenLabs API (Sound Effects endpoint)

**Responsibilities:**
1. Receive SFX request from Contract B.
2. Call ElevenLabs Sound Effects API with descriptive prompt.
3. Validate returned audio:
   - Duration matches requested duration (±500ms).
   - No silence or artifacts.
   - Appropriate frequency range for a transition effect.
4. If validation fails: return fallback file path.
5. Maintain a cache of generated SFX keyed by prompt hash (avoid regenerating identical effects).

**SFX Categories and Example Prompts:**
| Category | ElevenLabs Prompt | Fallback File |
|----------|-------------------|---------------|
| Riser | "Building cinematic riser sweep with white noise, {duration}s, electronic" | sfx/riser_01.wav |
| Sweep | "Frequency sweep filter effect, low to high, {duration}s" | sfx/sweep_01.wav |
| Vinyl Scratch | "DJ vinyl scratch sound effect, short, rhythmic" | sfx/scratch_01.wav |
| Reverb Tail | "Long reverb decay tail, atmospheric, {duration}s" | sfx/reverb_01.wav |
| Impact | "Deep bass impact hit with sub-bass rumble" | sfx/impact_01.wav |
| White Noise Build | "White noise building crescendo, {duration}s, tension" | sfx/noise_build_01.wav |

**Fallback Library:**
Ship with a minimum of 30 pre-produced, royalty-free SFX files covering all categories above. These must work without any API call.

---

### Agent 5: Frontend Specialist (React/Next.js)

**Stack:** React 18+, Next.js 14+, TypeScript, wavesurfer.js, Tailwind CSS

**UI Components:**

1. **Dual Deck Upload Zone:**
   - Drag-and-drop or file picker for Song A and Song B.
   - Show upload progress. Begin Tier 1 analysis immediately on upload.
   - Display: filename, duration, format, file size.

2. **Analysis Dashboard (shown after Tier 1 completes):**
   - Song A and Song B side-by-side:
     - BPM (with confidence indicator: green ≥0.8, yellow ≥0.6, red <0.6)
     - Key + Camelot notation
     - Waveform visualization (wavesurfer.js)
     - Energy curve overlay on waveform
   - Compatibility Badge:
     - 🟢 "Great Match" — compatible key, BPM diff < 3
     - 🟡 "Workable" — adjacent key or BPM diff 3–6
     - 🔴 "Challenging" — clashing key and BPM diff > 6
   - If compatibility is red, show a non-blocking warning with the AI's suggestion.

3. **Transition Zone Selector:**
   - On Song A's waveform: draggable region selector for "where should the transition begin?"
   - Snap-to-phrase option (default ON): selector snaps to nearest phrase boundary.
   - On Song B's waveform: optional selector for "where should Song B enter?" (defaults to first phrase).
   - Show phrase markers on waveform as subtle vertical lines.

4. **Mix Control Panel:**
   - "Generate Mix" button (primary CTA).
   - Progress indicator with stages:
     - ⏳ "Analyzing songs..." (Tier 1)
     - 🧠 "AI is choosing the best transition..." (Tier 2)
     - 🔧 "Rendering your mix..." (Tier 3)
     - ✅ "Your mix is ready!"
   - Estimated time remaining.

5. **Result Player:**
   - Play the final mixed audio.
   - A/B comparison: toggle between "Mix" and "Original Song A → Song B" (hard cut).
   - Visual overlay showing where the transition happens on a combined waveform.
   - Show the AI's reasoning (from Contract B) in a collapsible panel.
   - Download button (MP3 320kbps).

6. **Advanced Settings (collapsed by default):**
   - Override transition strategy (phrase_blend, drop_swap, echo_out, bass_swap).
   - Enable/disable SFX.
   - Manual BPM override for each song.
   - Manual key override for each song.

**Technical requirements:**
- WebSocket connection for real-time progress updates.
- Responsive design (desktop-first, mobile-friendly).
- Error states for every failure mode (upload fail, analysis fail, API timeout, render fail).
- Accessible (keyboard navigation, screen reader support, sufficient contrast).

---

## Phase 3: Integration & Error Handling

### Pipeline Flow (Happy Path):

```
User uploads Song A & Song B
       │
       ▼
Tier 1 analyzes both (parallel) ──→ Contract A JSON
       │
       ▼
User selects transition zone on waveform
       │
       ▼
Tier 2 receives Contract A + user preference ──→ Contract B JSON
       │
       ▼
Tier 3 renders mix using Contract B ──→ Final MP3/WAV
       │
       ▼
Frontend plays result, shows AI reasoning
```

### Error Handling Matrix:

| Failure | Behavior | User Message |
|---------|----------|--------------|
| Song upload fails | Retry 2x, then show error | "Upload failed. Please try again or use a different file format." |
| Tier 1 BPM confidence < 0.6 | Continue but warn user | "We're not 100% sure about the BPM. You can enter it manually." |
| Tier 1 key detection fails | Set key to "unknown", skip harmonic analysis | "Couldn't detect the key. The mix will focus on rhythm matching." |
| Gemini 3 Pro timeout (>12s) | Switch to rule-based fallback | "Our AI DJ is busy. Using classic mixing rules instead." |
| Gemini 3 Pro returns invalid JSON | Parse what's possible, fill gaps with rules | Same as above |
| Gemini 3 Pro says "incompatible" | Show warning, offer to proceed anyway | "These songs are tricky to mix. Here's why: [reasoning]. Want to try anyway?" |
| ElevenLabs SFX fails | Use fallback WAV from library | Silent fallback, no user-facing error |
| FFmpeg render fails | Retry 1x with simpler settings (no EQ, linear fade) | "Rendering with simplified settings..." |
| Rubberband time-stretch fails | Skip time-stretch, warn about BPM mismatch | "Couldn't match tempos. The transition may sound slightly off-beat." |

**Rule: The app must ALWAYS produce some output. A degraded mix is better than no mix.**

---

## Phase 4: Quality Gates (Testing Requirements)

Before any feature is considered complete, test against these scenarios:

### Functional Tests:

| # | Scenario | Expected Behavior |
|---|----------|-------------------|
| 1 | Two EDM songs, same BPM (128), compatible keys | Perfect phrase-aligned blend, no tempo adjustment |
| 2 | Pop + Hip-Hop, 5 BPM difference | Tempo adjustment applied, smooth transition |
| 3 | Two songs in clashing keys (C major + F# major) | AI warns about clash, still produces best possible mix |
| 4 | Very short song (<90 seconds) | Adapts transition length, doesn't exceed song duration |
| 5 | Live recording with irregular beats (jazz, acoustic) | Graceful degradation, warns user about beat irregularity |
| 6 | Same song uploaded twice | Detects and handles gracefully |
| 7 | Gemini 3 Pro is down | Rule-based fallback produces acceptable mix |
| 8 | ElevenLabs is down | Local SFX library used, no visible error |
| 9 | User selects transition point at very start/end of song | Adjusts to nearest viable phrase boundary |
| 10 | Songs with vastly different energy profiles | AI explains energy management strategy in reasoning |

### Audio Quality Tests (Manual, by team):

- [ ] No audible clicks or pops at transition boundaries.
- [ ] Bass swap sounds natural, no frequency "hole" during transition.
- [ ] Time-stretched audio has no metallic artifacts.
- [ ] SFX sits in the mix naturally (not too loud, not buried).
- [ ] Overall loudness is consistent (no sudden jumps or drops).
- [ ] Final MP3 plays correctly in: Chrome, Firefox, Safari, VLC, iTunes.

---

## Collaboration Rules

1. **Contract First:** JSON Contracts A and B must be finalized, reviewed by all agents, and locked before ANY implementation code is written. Changes to contracts require team consensus.

2. **Integration Tests Against Contracts:** Each agent writes tests that validate their output against the contract schema. Tier 2 must accept any valid Contract A. Tier 3 must accept any valid Contract B.

3. **Fallback Is Not Optional:** The rule-based fallback mixer (no AI dependency) must be built and tested BEFORE the Gemini integration. The app must work with zero external API calls.

4. **Progressive Enhancement:** Ship a working app with rule-based mixing first. Add Gemini intelligence second. Add ElevenLabs SFX third. Each layer improves quality but is not required for basic functionality.

5. **Latency Transparency:** Never show a spinner without context. Always show the current pipeline stage and estimated time remaining. Target total pipeline time: 10–20 seconds. Optimize with pre-analysis on upload and caching.

6. **Audio Format Support:** The pipeline must handle MP3, WAV, FLAC, OGG, and M4A. Convert to WAV internally for analysis. Output as MP3 (320kbps) for download.

7. **Supported Audio Formats:** MP3, WAV, FLAC, OGG, M4A. Max file size: 50MB per song. Max duration: 10 minutes per song.

---

## Tech Stack Summary

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Frontend | React 18, Next.js 14, TypeScript | UI framework |
| Waveform | wavesurfer.js | Audio visualization |
| Styling | Tailwind CSS | Responsive design |
| Backend API | Python, FastAPI | API layer |
| Audio Analysis | librosa, essentia (optional), numpy | BPM, key, beats, energy |
| AI Reasoning | Gemini 3 Pro API | Creative mix decisions |
| Time-Stretching | rubberband-cli | Pitch-preserving tempo change |
| Audio Rendering | FFmpeg (ffmpeg-python or subprocess) | Cut, crossfade, EQ, overlay |
| SFX Generation | ElevenLabs Sound Effects API | Dynamic transition effects |
| SFX Fallback | Pre-produced WAV library (30+ files) | Offline SFX capability |
| Real-time Updates | WebSocket | Progress communication |
| File Storage | Temporary (auto-delete after 1 hour) | Privacy and storage management |

---

## Definition of Done

The Smart AI DJ is **done** when:

- [ ] A user can upload two songs and receive a mixed transition in under 20 seconds.
- [ ] The transition is phrase-aligned (not at an arbitrary point).
- [ ] BPM differences up to 8 are handled via time-stretching.
- [ ] Key compatibility is detected and influences the transition strategy.
- [ ] EQ automation (at minimum bass swap) is applied during transitions.
- [ ] The app works fully even when Gemini 3 Pro and ElevenLabs are both offline.
- [ ] All 10 functional test scenarios pass.
- [ ] All audio quality checks pass.
- [ ] The frontend shows real-time progress with stage indicators.
- [ ] The AI's reasoning is displayed to the user.

---

*This prompt is version 1.0. Update the version number when contracts or architecture change.*
