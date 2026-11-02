import logging
import os
import sys
from pathlib import Path
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, AliasChoices, field_validator

from src.config import get_config
from src.contracts.schemas import LessonInput, LuminaResponse
from src.swarm.orchestrator import LuminaSwarmOrchestrator
from src.aws.dynamo_ledger import DynamoImpactLedger
from src.swarm.error_translator import translate_swarm_error

# Configure high-visibility stdout logging for terminal monitoring
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger("luminalab.server")
logger.setLevel(logging.INFO)


class GenerateRequest(BaseModel):
    """Payload model for the lab generation request."""
    subject: str = Field(
        ...,
        min_length=1,
        validation_alias=AliasChoices("subject", "academic_subject"),
        description="Subject name"
    )
    topic: str = Field(
        ...,
        min_length=1,
        validation_alias=AliasChoices("topic", "concept", "lesson_topic"),
        description="Topic name"
    )
    raw_text: str = Field(
        ...,
        min_length=10,
        validation_alias=AliasChoices("raw_text", "text", "passage_text", "lesson_passage", "lesson_text"),
        description="Raw textbook content"
    )
    student_grade: int = Field(
        ...,
        ge=1,
        le=12,
        validation_alias=AliasChoices("student_grade", "grade", "target_grade"),
        description="Target student grade level (1-12)"
    )
    language: str = Field(
        default="ar",
        pattern="^(ar|en)$",
        validation_alias=AliasChoices("language", "lang"),
        description="Language code (ar or en)"
    )


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=2, description="Text to synthesize")
    language: str = Field(default="ar", pattern="^(ar|en)$", description="Language code (ar or en)")


from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure components are initialized on server startup."""
    _init_components()
    yield


app = FastAPI(
    title="LuminaLab Swarm API",
    description="Multi-agent swarm that transforms textbook content into interactive micro-labs",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for local UI and frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount src/ui as static assets
_ui_dir = Path(__file__).resolve().parent.parent / "ui"
app.mount("/static", StaticFiles(directory=str(_ui_dir)), name="static")

# Component singletons
orchestrator: LuminaSwarmOrchestrator | None = None
ledger: DynamoImpactLedger | None = None


def _init_components() -> None:
    """Initialize component singletons and link them."""
    global orchestrator, ledger
    ledger = DynamoImpactLedger()
    orchestrator = LuminaSwarmOrchestrator()
    orchestrator.dynamo_ledger = ledger


# Initialize on module load
_init_components()



@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/") or request.url.path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def serve_ui() -> HTMLResponse:
    """
    Serves the main student UI index.html with no-cache headers.
    """
    ui_path = Path(__file__).resolve().parent.parent / "ui" / "index.html"
    if ui_path.exists():
        return HTMLResponse(
            content=ui_path.read_text(encoding="utf-8"),
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
        )
    return HTMLResponse(content="<h1>LuminaLab — UI not built yet</h1>", status_code=200)


@app.post("/api/generate")
async def generate_lab(request: GenerateRequest) -> dict[str, Any]:
    """
    Receives educational request and executes full LuminaLab multi-agent swarm.
    """
    global orchestrator, ledger
    if orchestrator is None or ledger is None:
        _init_components()

    try:
        logger.info(
            f"[LuminaLab Swarm] Inbound generation request: subject='{request.subject}', "
            f"topic='{request.topic}', grade={request.student_grade}, lang='{request.language}'"
        )
        lesson_input = LessonInput(
            subject=request.subject,
            topic=request.topic,
            raw_text=request.raw_text,
            student_grade=request.student_grade,
            language=request.language,
        )
        response = orchestrator.run(lesson_input)
        result = response.model_dump()
        result["challenge"] = getattr(orchestrator, "last_challenge", None) or {
            "challenge_question": "What happens if you increase the primary input variable to its maximum?",
            "challenge_hint": "Observe how the calculated output or pointer changes dynamically.",
            "challenge_answer": "The output scales proportionally according to the defined educational formula.",
        }
        archetype = result.get("simulation_spec", {}).get("engine_type") or result.get("simulation_spec", {}).get("engine_archetype", "unknown")
        load_red = result.get("impact", {}).get("cognitive_load_reduction_pct", 0)
        size_kb = result.get("impact", {}).get("lab_size_kb", 0)
        logger.info(
            f"[LuminaLab Swarm] Lab generated successfully: engine='{archetype}', "
            f"cognitive_load_reduction={load_red}%, lab_size={size_kb} KB"
        )
        return result
    except Exception as e:
        logger.exception("[LuminaLab Swarm] Lab generation encountered an unhandled exception:")
        error_payload = translate_swarm_error(e, raw_text=request.raw_text)
        logger.error(
            f"[LuminaLab Swarm] Sanitized error response [{error_payload.get('error_code')}]: {error_payload.get('error')}"
        )
        return JSONResponse(status_code=500, content=error_payload)


@app.get("/api/stats")
async def get_impact_stats() -> dict[str, Any]:
    """
    Retrieves aggregate societal impact statistics from DynamoDB ledger.
    """
    global ledger
    if ledger is None:
        _init_components()
    return ledger.get_aggregate_stats()


@app.api_route("/api/audio/{filename}", methods=["GET", "HEAD"])
async def get_audio_stream(filename: str):
    """
    Streams audio narration directly to the browser with audio/mpeg headers.
    Enables low-latency streaming and local playback for Hackathon/Offline evaluations.
    """
    clean_name = os.path.basename(filename)
    # Check permanent UI assets directory first
    audio_path = Path(__file__).resolve().parent.parent / "ui" / "assets" / "audio" / clean_name
    if not audio_path.exists() and not clean_name.endswith(".mp3"):
        audio_path = Path(__file__).resolve().parent.parent / "ui" / "assets" / "audio" / f"{clean_name}.mp3"

    if not audio_path.exists():
        audio_path = Path("_mock_storage") / "audio" / clean_name
        if not audio_path.exists() and not clean_name.endswith(".mp3"):
            audio_path = Path("_mock_storage") / "audio" / f"{clean_name}.mp3"

    if audio_path.exists():
        return FileResponse(
            path=str(audio_path),
            media_type="audio/mpeg",
            headers={"Cache-Control": "public, max-age=86400", "Accept-Ranges": "bytes"}
        )
    raise HTTPException(status_code=404, detail="Audio file not found")


@app.post("/api/tts")
async def synthesize_tts(request: TTSRequest) -> dict[str, Any]:
    """
    On-demand text-to-speech endpoint returning 100% female neural AWS Polly audio.
    (Hala for Arabic, Joanna for English).
    """
    from src.aws.s3_polly_service import S3PollyService
    svc = S3PollyService()
    res = svc.synthesize_speech(request.text, language=request.language)
    return {
        "audio_url": res.get("local_url") or res.get("audio_url"),
        "voice_id": res.get("voice_id"),
        "language": res.get("language"),
        "status": res.get("status")
    }


@app.get("/api/health")
async def health_check() -> dict[str, Any]:
    """
    Health check returning service status, mock mode, and API version.
    """
    config = get_config()
    return {
        "status": "healthy",
        "mock_mode": config.LUMINA_MOCK_MODE,
        "has_api_key": bool(config.BEDROCK_API_KEY),
        "model_id": config.BEDROCK_MODEL_ID,
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
