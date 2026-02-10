"""API routes for the Smart AI DJ backend."""

import logging
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from ..config import UPLOAD_DIR, OUTPUT_DIR, MAX_FILE_SIZE_MB, SUPPORTED_FORMATS
from ..analysis.engine import analyze_song, analyze_pair, compute_compatibility
from ..strategist.ai_strategist import ai_mix_decision
from ..strategist.fallback import rule_based_mix
from ..renderer.engine import render_mix
from ..models.contracts import ContractA, ContractB

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory session storage
sessions: dict[str, dict] = {}
# WebSocket connections for progress updates
ws_connections: dict[str, WebSocket] = {}


async def send_progress(session_id: str, stage: str, message: str, progress: float):
    """Send progress update via WebSocket."""
    if session_id in ws_connections:
        try:
            await ws_connections[session_id].send_json({
                "type": "progress",
                "stage": stage,
                "message": message,
                "progress": progress,
            })
        except Exception:
            pass


@router.post("/upload/{deck}")
async def upload_song(deck: str, file: UploadFile = File(...)):
    """Upload a song to deck A or B."""
    if deck not in ("a", "b"):
        raise HTTPException(400, "Deck must be 'a' or 'b'")

    # Validate format
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        raise HTTPException(400, f"Unsupported format. Supported: {', '.join(SUPPORTED_FORMATS)}")

    # Read and validate size
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(400, f"File too large. Maximum: {MAX_FILE_SIZE_MB}MB")

    # Save file
    session_id = str(uuid.uuid4())[:8]
    file_path = UPLOAD_DIR / f"{session_id}_{deck}{suffix}"
    file_path.write_bytes(content)

    # Start analysis immediately
    try:
        analysis = analyze_song(file_path)
        return {
            "session_id": session_id,
            "deck": deck,
            "file_path": str(file_path),
            "analysis": analysis.model_dump(),
        }
    except Exception as e:
        logger.error(f"Analysis failed for {file.filename}: {e}")
        raise HTTPException(500, f"Analysis failed: {str(e)}")


@router.post("/analyze")
async def analyze_songs(song_a_path: str, song_b_path: str):
    """Analyze a pair of songs and return Contract A."""
    path_a = Path(song_a_path)
    path_b = Path(song_b_path)

    if not path_a.exists() or not path_b.exists():
        raise HTTPException(404, "One or both song files not found")

    try:
        contract_a = await analyze_pair(path_a, path_b)
        return contract_a.model_dump()
    except Exception as e:
        logger.error(f"Pair analysis failed: {e}")
        raise HTTPException(500, f"Analysis failed: {str(e)}")


@router.post("/mix")
async def create_mix(
    song_a_path: str,
    song_b_path: str,
    transition_start_ms: Optional[float] = None,
    song_b_in_point_ms: Optional[float] = None,
    strategy: Optional[str] = None,
    enable_sfx: bool = True,
    mix_in_key: bool = False,
):
    """Full pipeline: analyze → decide → render."""
    session_id = str(uuid.uuid4())[:8]
    path_a = Path(song_a_path)
    path_b = Path(song_b_path)

    if not path_a.exists() or not path_b.exists():
        raise HTTPException(404, "One or both song files not found")

    try:
        # Stage 1: Analysis
        await send_progress(session_id, "analysis", "Analyzing songs...", 0.1)
        contract_a = await analyze_pair(path_a, path_b)
        await send_progress(session_id, "analysis", "Analysis complete", 0.3)

        # Stage 2: AI Decision
        await send_progress(session_id, "strategy", "AI is choosing the best transition...", 0.4)
        contract_b = await ai_mix_decision(contract_a, transition_start_ms, strategy, mix_in_key, song_b_in_point_ms)

        if not enable_sfx:
            contract_b.mix_decision.sfx.enabled = False

        await send_progress(session_id, "strategy", "Mix strategy decided", 0.6)

        # Stage 3: Render
        await send_progress(session_id, "render", "Rendering your mix...", 0.7)
        output_path = await render_mix(contract_b, path_a, path_b, session_id)
        await send_progress(session_id, "complete", "Your mix is ready!", 1.0)

        # Store session data
        sessions[session_id] = {
            "contract_a": contract_a.model_dump(),
            "contract_b": contract_b.model_dump(),
            "output_path": str(output_path),
        }

        return {
            "session_id": session_id,
            "contract_a": contract_a.model_dump(),
            "contract_b": contract_b.model_dump(),
            "download_url": f"/api/download/{session_id}",
        }

    except Exception as e:
        logger.error(f"Mix pipeline failed: {e}")
        await send_progress(session_id, "error", str(e), 0)
        raise HTTPException(500, f"Mix failed: {str(e)}")


@router.get("/download/{session_id}")
async def download_mix(session_id: str):
    """Download the rendered mix."""
    if session_id not in sessions:
        raise HTTPException(404, "Session not found")

    output_path = Path(sessions[session_id]["output_path"])
    if not output_path.exists():
        raise HTTPException(404, "Mix file not found")

    return FileResponse(
        output_path,
        media_type="audio/mpeg",
        filename=f"smart_dj_mix_{session_id}.mp3",
    )


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket for real-time progress updates."""
    await websocket.accept()
    ws_connections[session_id] = websocket
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_connections.pop(session_id, None)
