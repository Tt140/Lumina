import json
import logging
import os
import re
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, AliasChoices, field_validator

from src.config import get_config
from src.contracts.schemas import ImpactMetrics, LessonInput, LuminaResponse
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
    if request.url.path.startswith("/static/") or request.url.path in ("/", "/audit"):
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


@app.api_route("/audit", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def serve_audit_ui() -> HTMLResponse:
    """
    Serves the live AWS Ledger Reliability Inspector UI (/audit).
    """
    audit_path = Path(__file__).resolve().parent.parent / "ui" / "audit.html"
    if audit_path.exists():
        return HTMLResponse(
            content=audit_path.read_text(encoding="utf-8"),
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"},
        )
    raise HTTPException(status_code=404, detail="Audit Inspector UI not found")


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


def _redact_sensitive(value: Any) -> Any:
    """Redact AWS 12-digit account IDs and home paths from audit payloads."""
    if isinstance(value, str):
        out = re.sub(r"(arn:aws[a-z-]*:[^:]*:[^:]*:)\d{12}(:)", r"\1<REDACTED_ACCOUNT_ID>\2", value)
        out = re.sub(r"/home/[^/\s\"']+", "/home/<USER>", out)
        return out
    if isinstance(value, dict):
        return {k: _redact_sensitive(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_sensitive(v) for v in value]
    return value


def _compute_audit_comparison(
    before_data: dict[str, Any] | None, after_data: dict[str, Any] | None
) -> dict[str, Any] | None:
    """Compute comparison deltas dynamically from measured JSON artifacts."""
    if not before_data or not after_data:
        return None
    br = before_data["axis_1_scale_and_truncation"]["read_phase"]["summary"]
    ar = after_data["axis_1_scale_and_truncation"]["read_phase"]["summary"]
    bw = before_data["axis_1_scale_and_truncation"]["write_phase"]
    aw = after_data["axis_1_scale_and_truncation"]["write_phase"]
    b2s = before_data["axis_2_jitter_and_false_success"]["summary"]
    a2s = after_data["axis_2_jitter_and_false_success"]["summary"]

    rcu_b = float(br["consumed_rcu_per_call_mean"])
    rcu_a = float(ar["consumed_rcu_per_call_mean"])
    p50_b = float(br["read_latency_ms"]["p50"])
    p50_a = float(ar["read_latency_ms"]["p50"])
    wcu_b = float(bw["total_consumed_wcu"])
    wcu_a = float(aw["total_consumed_wcu"])
    return {
        "rcu_reduction_pct": round(((rcu_b - rcu_a) / rcu_b * 100.0), 2) if rcu_b else 0.0,
        "read_p50_speedup": round((p50_b / p50_a), 2) if p50_a else 0.0,
        "read_p50_reduction_pct": round(((p50_b - p50_a) / p50_b * 100.0), 2) if p50_b else 0.0,
        "truncation_delta_pct": round(
            float(ar["truncation_error_pct_mean"]) - float(br["truncation_error_pct_mean"]), 3
        ),
        "silent_loss_delta_pct": round(
            float(a2s["silent_data_loss_rate_pct"]) - float(b2s["silent_data_loss_rate_pct"]), 2
        ),
        "wcu_ratio": round((wcu_a / wcu_b), 2) if wcu_b else 0.0,
        "wcu_delta": round(wcu_a - wcu_b, 1),
    }


@app.get("/api/audit/benchmarks")
async def audit_benchmarks() -> dict[str, Any]:
    """Return measured before_v1.json and after_v2.json benchmark snapshots with dynamic deltas."""
    results_dir = Path(__file__).resolve().parent.parent.parent / "results"
    before_path = results_dir / "before_v1.json"
    after_path = results_dir / "after_v2.json"

    before_data = json.loads(before_path.read_text(encoding="utf-8")) if before_path.exists() else None
    after_data = json.loads(after_path.read_text(encoding="utf-8")) if after_path.exists() else None

    return _redact_sensitive({
        "before": before_data,
        "after": after_data,
        "comparison": _compute_audit_comparison(before_data, after_data),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    })


@app.get("/api/audit/stats-probe")
async def audit_stats_probe() -> dict[str, Any]:
    """Execute a live get_aggregate_stats() read against DynamoDB (or mock ledger) with timing and RCU."""
    global ledger
    if ledger is None:
        _init_components()

    consumed_rcu: float | None = None
    tid = threading.get_ident()
    client = getattr(ledger, "client", None)
    hook_id = f"lumina-audit-probe-{uuid.uuid4().hex[:8]}"

    def _on_before(params: dict[str, Any], model: Any, **kwargs: Any) -> None:
        if threading.get_ident() == tid and model and model.name in ("GetItem", "Scan", "Query"):
            if isinstance(params, dict):
                params.setdefault("ReturnConsumedCapacity", "TOTAL")

    def _on_after(model: Any, parsed: dict[str, Any], **kwargs: Any) -> None:
        nonlocal consumed_rcu
        if threading.get_ident() == tid and isinstance(parsed, dict):
            cap = parsed.get("ConsumedCapacity")
            if isinstance(cap, dict) and "CapacityUnits" in cap:
                consumed_rcu = float(cap["CapacityUnits"])

    if client is not None and hasattr(client, "meta") and hasattr(client.meta, "events"):
        client.meta.events.register("before-parameter-build.dynamodb.*", _on_before, unique_id=hook_id)
        client.meta.events.register("after-call.dynamodb.*", _on_after, unique_id=f"{hook_id}-after")

    t0 = time.perf_counter()
    try:
        stats = ledger.get_aggregate_stats()
    finally:
        if client is not None and hasattr(client, "meta") and hasattr(client.meta, "events"):
            client.meta.events.unregister("before-parameter-build.dynamodb.*", unique_id=hook_id)
            client.meta.events.unregister("after-call.dynamodb.*", unique_id=f"{hook_id}-after")
    latency_ms = round((time.perf_counter() - t0) * 1000.0, 3)

    return _redact_sensitive({
        "stats": stats,
        "latency_ms": latency_ms,
        "operation": "InMemoryStore (mock)" if ledger.mock_mode else f"GetItem ({ledger.AGGREGATE_SESSION_ID})",
        "table_name": ledger.table_name,
        "mock_mode": ledger.mock_mode,
        "consumed_rcu": consumed_rcu if consumed_rcu is not None else (0.0 if ledger.mock_mode else 0.5),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    })


@app.post("/api/audit/idempotency-probe")
async def audit_idempotency_probe(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    """Record a deterministic probe session twice with the same session_id to prove idempotency live."""
    global ledger
    if ledger is None:
        _init_components()

    raw_sid = str((payload or {}).get("session_id") or "").strip()
    if raw_sid:
        session_id = raw_sid if raw_sid.startswith("audit-probe-") else f"audit-probe-{raw_sid}"
    else:
        session_id = f"audit-probe-{uuid.uuid4().hex[:10]}"

    impact = ImpactMetrics(
        baseline_grade_level=10.0,
        simplified_grade_level=5.0,
        cognitive_load_reduction_pct=50.0,
        lab_size_kb=36.5,
        generation_time_sec=1.8,
    )

    t0 = time.perf_counter()
    stats_before = ledger.get_aggregate_stats()
    receipt_1 = ledger.record_impact(impact, session_id=session_id)
    stats_after_first = ledger.get_aggregate_stats()
    receipt_2 = ledger.record_impact(impact, session_id=session_id)
    stats_after_second = ledger.get_aggregate_stats()
    latency_ms = round((time.perf_counter() - t0) * 1000.0, 3)

    delta_first = int(stats_after_first["total_sessions"]) - int(stats_before["total_sessions"])
    delta_second = int(stats_after_second["total_sessions"]) - int(stats_after_first["total_sessions"])
    verified = (
        receipt_1.get("status") == "recorded"
        and receipt_2.get("status") == "recorded"
        and delta_first == 1
        and delta_second == 0
    )

    return _redact_sensitive({
        "session_id": session_id,
        "stats_before": stats_before,
        "receipt_1": receipt_1,
        "stats_after_first": stats_after_first,
        "delta_first": delta_first,
        "receipt_2": receipt_2,
        "stats_after_second": stats_after_second,
        "delta_second": delta_second,
        "idempotency_verified": verified,
        "latency_ms": latency_ms,
        "mock_mode": ledger.mock_mode,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    })


@app.post("/api/audit/cleanup-probe")
async def audit_cleanup_probe(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    """Delete audit-probe-* test session(s) cleanly and reconcile AGGREGATE#GLOBAL."""
    global ledger
    if ledger is None:
        _init_components()

    session_ids = (payload or {}).get("session_ids") or []
    if isinstance(session_ids, str):
        session_ids = [session_ids]
    for sid in session_ids:
        if not isinstance(sid, str) or not sid.startswith("audit-probe-"):
            raise HTTPException(
                status_code=400,
                detail="Only 'audit-probe-*' test session IDs can be removed via /api/audit/cleanup-probe.",
            )

    t0 = time.perf_counter()
    deleted_ids: list[str] = []

    if ledger.mock_mode:
        targets = session_ids or [k for k in list(ledger._local_store.keys()) if k.startswith("audit-probe-")]
        for sid in targets:
            if sid in ledger._local_store:
                ledger._local_store.pop(sid, None)
                deleted_ids.append(sid)
        if ledger.persist_to_file:
            ledger.save_to_file()
        remaining_items = len(ledger._local_store)
    else:
        cfg = get_config()
        ddb = ledger.client
        agg_sid = ledger.AGGREGATE_SESSION_ID
        targets = list(dict.fromkeys(session_ids))
        if not targets:
            paginator = ddb.get_paginator("scan")
            for page in paginator.paginate(
                TableName=ledger.table_name,
                ProjectionExpression="session_id",
                FilterExpression="begins_with(session_id, :p)",
                ExpressionAttributeValues={":p": {"S": "audit-probe-"}},
            ):
                for item in page.get("Items", []):
                    targets.append(item["session_id"]["S"])

        dec_sessions = 0
        dec_grade = 0.0
        dec_cog = 0.0
        dec_kb = 0.0
        dec_off = 0
        dec_gen = 0.0

        for sid in targets:
            existing = ddb.get_item(TableName=ledger.table_name, Key={"session_id": {"S": sid}}).get("Item")
            if not existing:
                continue
            ddb.delete_item(TableName=ledger.table_name, Key={"session_id": {"S": sid}})
            deleted_ids.append(sid)
            dec_sessions += 1
            dec_grade += float(existing.get("grade_reduction", {}).get("N", 0))
            dec_cog += float(existing.get("cognitive_load_reduction_pct", {}).get("N", 0))
            dec_kb += float(existing.get("lab_size_kb", {}).get("N", 0))
            dec_off += 1 if existing.get("is_offline_ready", {}).get("BOOL", False) else 0
            dec_gen += float(existing.get("generation_time_sec", {}).get("N", 0))

        if dec_sessions > 0:
            agg_item = ddb.get_item(
                TableName=ledger.table_name, Key={"session_id": {"S": agg_sid}}
            ).get("Item")
            if agg_item:
                cur_total = int(float(agg_item.get("total_sessions", {}).get("N", 0)))
                if cur_total <= dec_sessions:
                    ddb.delete_item(TableName=ledger.table_name, Key={"session_id": {"S": agg_sid}})
                else:
                    ddb.update_item(
                        TableName=ledger.table_name,
                        Key={"session_id": {"S": agg_sid}},
                        UpdateExpression=(
                            "ADD total_sessions :n_one, "
                            "sum_grade_reduction :n_gr, "
                            "sum_cognitive_load_reduction_pct :n_clr, "
                            "sum_lab_size_kb :n_lkb, "
                            "total_offline_ready_labs :n_off, "
                            "sum_generation_time_sec :n_gt"
                        ),
                        ExpressionAttributeValues={
                            ":n_one": {"N": str(-dec_sessions)},
                            ":n_gr": {"N": str(-round(dec_grade, 6))},
                            ":n_clr": {"N": str(-round(dec_cog, 6))},
                            ":n_lkb": {"N": str(-round(dec_kb, 6))},
                            ":n_off": {"N": str(-dec_off)},
                            ":n_gt": {"N": str(-round(dec_gen, 6))},
                        },
                    )

        remaining_items = 0
        for page in ddb.get_paginator("scan").paginate(TableName=ledger.table_name, Select="COUNT"):
            remaining_items += int(page.get("Count", 0))

    stats_after = ledger.get_aggregate_stats()
    latency_ms = round((time.perf_counter() - t0) * 1000.0, 3)

    return _redact_sensitive({
        "deleted_session_ids": deleted_ids,
        "deleted_count": len(deleted_ids),
        "remaining_table_items": remaining_items,
        "stats_after": stats_after,
        "latency_ms": latency_ms,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    })


def _format_alarm_metrics(alarm: dict[str, Any]) -> str:
    """Format CloudWatch alarm metric name(s) cleanly without duplicating metric names."""
    metric_name = alarm.get("MetricName")
    if metric_name:
        return str(metric_name)

    metrics = alarm.get("Metrics") or []
    ops_by_metric: dict[str, list[str]] = {}
    metric_order: list[str] = []
    for entry in metrics:
        if not (isinstance(entry, dict) and "MetricStat" in entry):
            continue
        metric = entry["MetricStat"].get("Metric", {})
        mname = metric.get("MetricName")
        if not mname:
            continue
        if mname not in ops_by_metric:
            ops_by_metric[mname] = []
            metric_order.append(mname)
        for dim in metric.get("Dimensions", []):
            if dim.get("Name") == "Operation" and dim.get("Value"):
                op_val = str(dim["Value"])
                if op_val not in ops_by_metric[mname]:
                    ops_by_metric[mname].append(op_val)

    if not metric_order:
        return "Expression"

    formatted_parts = [
        f"{mname} ({', '.join(ops_by_metric[mname])})" if ops_by_metric[mname] else mname
        for mname in metric_order
    ]
    return ", ".join(formatted_parts)


@app.get("/api/audit/infrastructure")
async def audit_infrastructure() -> dict[str, Any]:
    """Inspect live CloudFormation stack, IAM policy (no Scan), LogGroup, SNS, and CloudWatch alarms."""
    config = get_config()
    stack_name = os.getenv("CFN_STACK_NAME", "LuminaLab-Swarm-Stack")
    t0 = time.perf_counter()

    if config.LUMINA_MOCK_MODE:
        return _redact_sensitive({
            "mock_mode": True,
            "region": config.AWS_REGION,
            "stack_name": stack_name,
            "stack_status": "MOCK_OFFLINE",
            "table_name": "mock_local_store",
            "iam_policy": {
                "policy_arn": "mock://LuminaLabSwarmPolicy",
                "dynamodb_actions": ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem"],
                "has_dynamodb_scan": False,
            },
            "log_group": {"name": f"/aws/luminalab/{stack_name}/application", "retention_in_days": 30},
            "sns_topic": {"arn": "mock://LuminaLabAlertsTopic", "kms_encrypted": True},
            "alarms": [],
            "latency_ms": round((time.perf_counter() - t0) * 1000.0, 3),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        })

    import boto3

    region = config.AWS_REGION
    cfn = boto3.client("cloudformation", region_name=region)
    iam = boto3.client("iam", region_name=region)
    cw = boto3.client("cloudwatch", region_name=region)
    logs_client = boto3.client("logs", region_name=region)
    sns_client = boto3.client("sns", region_name=region)

    try:
        stack_desc = cfn.describe_stacks(StackName=stack_name)["Stacks"][0]
        resources: list[dict[str, Any]] = []
        for page in cfn.get_paginator("list_stack_resources").paginate(StackName=stack_name):
            resources.extend(page.get("StackResourceSummaries", []))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Unable to query CloudFormation stack: {exc}") from exc

    policy_arn = ""
    sns_arn = ""
    log_group_name = ""
    alarm_names: list[str] = []
    for res in resources:
        rtype = res["ResourceType"]
        phys = res.get("PhysicalResourceId", "")
        if rtype == "AWS::IAM::ManagedPolicy" and res["LogicalResourceId"] == "LuminaLabSwarmPolicy":
            policy_arn = phys
        elif rtype == "AWS::SNS::Topic":
            sns_arn = phys
        elif rtype == "AWS::Logs::LogGroup":
            log_group_name = phys
        elif rtype == "AWS::CloudWatch::Alarm":
            alarm_names.append(phys)

    dynamo_actions: list[str] = []
    if policy_arn:
        default_ver = iam.get_policy(PolicyArn=policy_arn)["Policy"]["DefaultVersionId"]
        doc = iam.get_policy_version(PolicyArn=policy_arn, VersionId=default_ver)["PolicyVersion"]["Document"]
        for stmt in doc.get("Statement", []):
            acts = stmt.get("Action", [])
            if isinstance(acts, str):
                acts = [acts]
            for act in acts:
                if act.lower().startswith("dynamodb:"):
                    dynamo_actions.append(act)

    alarms_data: list[dict[str, Any]] = []
    if alarm_names:
        for alarm in cw.describe_alarms(AlarmNames=alarm_names).get("MetricAlarms", []):
            alarms_data.append({
                "name": alarm.get("AlarmName"),
                "state_value": alarm.get("StateValue"),
                "metric_name": _format_alarm_metrics(alarm),
                "threshold": alarm.get("Threshold"),
                "period": alarm.get("Period") or 60,
                "treat_missing_data": alarm.get("TreatMissingData"),
                "state_reason": alarm.get("StateReason"),
            })

    retention_days = None
    if log_group_name:
        lg_list = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name).get("logGroups", [])
        for lg in lg_list:
            if lg.get("logGroupName") == log_group_name:
                retention_days = lg.get("retentionInDays")
                break

    kms_encrypted = False
    if sns_arn:
        attrs = sns_client.get_topic_attributes(TopicArn=sns_arn).get("Attributes", {})
        kms_encrypted = bool(attrs.get("KmsMasterKeyId"))

    latency_ms = round((time.perf_counter() - t0) * 1000.0, 3)
    return _redact_sensitive({
        "mock_mode": False,
        "region": region,
        "stack_name": stack_name,
        "stack_status": stack_desc.get("StackStatus"),
        "table_name": config.DYNAMO_TABLE_NAME,
        "iam_policy": {
            "policy_arn": policy_arn,
            "dynamodb_actions": sorted(set(dynamo_actions)),
            "has_dynamodb_scan": "dynamodb:Scan" in dynamo_actions,
        },
        "log_group": {"name": log_group_name, "retention_in_days": retention_days},
        "sns_topic": {"arn": sns_arn, "kms_encrypted": kms_encrypted},
        "alarms": sorted(alarms_data, key=lambda x: str(x.get("name", ""))),
        "latency_ms": latency_ms,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
