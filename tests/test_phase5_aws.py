"""Phase 5 Test Suite: AWS Cloud Persistence & Voice Services (DynamoDB, S3, Polly)."""

import os
import shutil
import uuid
from pathlib import Path
import pytest

os.environ["LUMINA_MOCK_MODE"] = "true"

from src.config import get_config
from src.contracts.schemas import LessonInput, ImpactMetrics, LuminaResponse
from src.aws.dynamo_ledger import DynamoImpactLedger
from src.aws.s3_polly_service import S3PollyService
from scripts.aws_setup import run_setup, create_dynamo_table, create_s3_bucket
from src.swarm.orchestrator import LuminaSwarmOrchestrator


@pytest.fixture(autouse=True)
def cleanup_mock_storage():
    """Ensure clean storage before and after each test."""
    yield
    if Path("_mock_storage").exists():
        shutil.rmtree("_mock_storage", ignore_errors=True)
    if Path("_mock_ledger.json").exists():
        Path("_mock_ledger.json").unlink(missing_ok=True)


@pytest.fixture
def sample_metrics() -> ImpactMetrics:
    return ImpactMetrics(
        baseline_grade_level=10.0,
        simplified_grade_level=4.0,
        cognitive_load_reduction_pct=60.0,
        lab_size_kb=15.0,
        generation_time_sec=2.5,
    )


@pytest.fixture
def sample_lesson_input() -> LessonInput:
    return LessonInput(
        subject="Physics",
        topic="Electric Current",
        raw_text="Electric current is the rate of flow of electric charges in a conductor.",
        student_grade=7,
        language="en",
    )


# ============================================================================
# 1. DynamoDB Ledger Tests
# ============================================================================

def test_ledger_creation_mock():
    ledger = DynamoImpactLedger()
    assert ledger.mock_mode is True
    assert ledger.client is None
    assert ledger.table_name == "mock_local_store"


def test_record_impact_returns_receipt(sample_metrics):
    ledger = DynamoImpactLedger()
    receipt = ledger.record_impact(sample_metrics)
    assert isinstance(receipt, dict)
    assert "session_id" in receipt
    assert receipt["status"] == "recorded"
    assert receipt["table_name"] == "mock_local_store"


def test_record_impact_with_custom_session_id(sample_metrics):
    ledger = DynamoImpactLedger()
    receipt = ledger.record_impact(sample_metrics, session_id="custom-123")
    assert receipt["session_id"] == "custom-123"
    assert receipt["status"] == "recorded"


def test_record_impact_auto_generates_session_id(sample_metrics):
    ledger = DynamoImpactLedger()
    receipt = ledger.record_impact(sample_metrics)
    # Validate UUID format
    val = uuid.UUID(receipt["session_id"])
    assert str(val) == receipt["session_id"]


def test_get_session_returns_data(sample_metrics):
    ledger = DynamoImpactLedger()
    receipt = ledger.record_impact(sample_metrics, session_id="sess-abc")
    data = ledger.get_session("sess-abc")
    assert data is not None
    assert data["session_id"] == "sess-abc"
    assert data["baseline_grade_level"] == 10.0
    assert data["simplified_grade_level"] == 4.0


def test_get_session_not_found():
    ledger = DynamoImpactLedger()
    data = ledger.get_session("nonexistent-sess")
    assert data is None


def test_aggregate_stats_empty():
    ledger = DynamoImpactLedger()
    stats = ledger.get_aggregate_stats()
    assert stats["total_sessions"] == 0
    assert stats["avg_grade_reduction"] == 0.0
    assert stats["avg_cognitive_load_reduction_pct"] == 0.0
    assert stats["avg_lab_size_kb"] == 0.0
    assert stats["total_offline_ready_labs"] == 0
    assert stats["avg_generation_time_sec"] == 0.0


def test_aggregate_stats_single_session(sample_metrics):
    ledger = DynamoImpactLedger()
    ledger.record_impact(sample_metrics)
    stats = ledger.get_aggregate_stats()
    assert stats["total_sessions"] == 1
    assert stats["avg_grade_reduction"] == sample_metrics.grade_reduction
    assert stats["avg_cognitive_load_reduction_pct"] == sample_metrics.cognitive_load_reduction_pct
    assert stats["avg_lab_size_kb"] == sample_metrics.lab_size_kb
    assert stats["total_offline_ready_labs"] == 1
    assert stats["avg_generation_time_sec"] == sample_metrics.generation_time_sec


def test_aggregate_stats_multiple_sessions():
    ledger = DynamoImpactLedger()
    m1 = ImpactMetrics(baseline_grade_level=10.0, simplified_grade_level=4.0, cognitive_load_reduction_pct=60.0, lab_size_kb=12.0, generation_time_sec=2.0)
    m2 = ImpactMetrics(baseline_grade_level=8.0, simplified_grade_level=4.0, cognitive_load_reduction_pct=50.0, lab_size_kb=18.0, generation_time_sec=4.0)
    m3 = ImpactMetrics(baseline_grade_level=9.0, simplified_grade_level=3.0, cognitive_load_reduction_pct=66.6, lab_size_kb=15.0, generation_time_sec=3.0)

    ledger.record_impact(m1)
    ledger.record_impact(m2)
    ledger.record_impact(m3)

    stats = ledger.get_aggregate_stats()
    assert stats["total_sessions"] == 3
    # (6.0 + 4.0 + 6.0) / 3 = 16.0 / 3 = 5.33
    assert stats["avg_grade_reduction"] == round((6.0 + 4.0 + 6.0) / 3.0, 2)
    assert stats["avg_lab_size_kb"] == 15.0
    assert stats["avg_generation_time_sec"] == 3.0


def test_aggregate_stats_offline_ready_count():
    ledger = DynamoImpactLedger()
    # 2 offline ready (<200KB), 1 not ready (>=200KB)
    m1 = ImpactMetrics(baseline_grade_level=8.0, simplified_grade_level=4.0, cognitive_load_reduction_pct=50.0, lab_size_kb=10.0, generation_time_sec=1.0)
    m2 = ImpactMetrics(baseline_grade_level=8.0, simplified_grade_level=4.0, cognitive_load_reduction_pct=50.0, lab_size_kb=20.0, generation_time_sec=1.0)
    m3 = ImpactMetrics(baseline_grade_level=8.0, simplified_grade_level=4.0, cognitive_load_reduction_pct=50.0, lab_size_kb=250.0, generation_time_sec=1.0)

    ledger.record_impact(m1)
    ledger.record_impact(m2)
    ledger.record_impact(m3)

    stats = ledger.get_aggregate_stats()
    assert stats["total_sessions"] == 3
    assert stats["total_offline_ready_labs"] == 2


# ============================================================================
# 2. S3 + Polly Service Tests
# ============================================================================

def test_s3_polly_creation_mock():
    svc = S3PollyService()
    assert svc.mock_mode is True
    assert svc.s3_client is None
    assert svc.polly_client is None
    assert Path("_mock_storage").exists()
    assert Path("_mock_storage/labs").exists()
    assert Path("_mock_storage/audio").exists()


def test_upload_lab_creates_file():
    svc = S3PollyService()
    html = "<html><body><h1>Simulation</h1></body></html>"
    svc.upload_lab_to_s3(html, "test-id-100")
    expected_file = Path("_mock_storage/labs/test-id-100.html")
    assert expected_file.exists()
    assert expected_file.read_text(encoding="utf-8") == html


def test_upload_lab_returns_url():
    svc = S3PollyService()
    res = svc.upload_lab_to_s3("<html></html>", "sess-special-99")
    assert "s3_url" in res
    assert "sess-special-99" in res["s3_url"]
    assert res["status"] == "uploaded"


def test_upload_lab_correct_size():
    svc = S3PollyService()
    content = "A" * 1024  # exactly 1 KB
    res = svc.upload_lab_to_s3(content, "size-test")
    assert res["size_kb"] == 1.0


def test_synthesize_speech_arabic():
    svc = S3PollyService()
    res = svc.synthesize_speech("مرحبا بكم في لومينا لاب", "ar")
    assert res["voice_id"] == get_config().POLLY_VOICE_AR
    assert res["status"] == "synthesized"
    assert "audio_url" in res


def test_synthesize_speech_english():
    svc = S3PollyService()
    res = svc.synthesize_speech("Welcome to LuminaLab", "en")
    assert res["voice_id"] == "Joanna"
    assert res["status"] == "synthesized"
    assert "audio_url" in res


def test_synthesize_speech_creates_file():
    svc = S3PollyService()
    res = svc.synthesize_speech("Testing voice creation", "en", session_id="voice-test-55")
    assert Path("_mock_storage/audio/voice-test-55.mp3").exists()
    assert "voice-test-55.mp3" in res["audio_url"]


def test_offline_package_complete():
    svc = S3PollyService()
    html = "<!DOCTYPE html><html><body><p>Lab</p></body></html>"
    pkg = svc.create_offline_package(html, "Audio explanation", "session-pack-1", "en")
    assert "s3_lab" in pkg
    assert "polly_audio" in pkg
    assert "total_size_kb" in pkg
    assert "is_offline_ready" in pkg
    assert pkg["s3_lab"]["status"] == "uploaded"
    assert pkg["polly_audio"]["status"] == "synthesized"


def test_offline_package_small_lab_is_ready():
    svc = S3PollyService()
    small_html = "<html><body>Small Lab</body></html>"
    pkg = svc.create_offline_package(small_html, "Voice text", "ready-sess", "en")
    assert pkg["is_offline_ready"] is True


# ============================================================================
# 3. AWS Setup Script Tests
# ============================================================================

def test_setup_mock_mode():
    result = run_setup()
    assert result["mock_mode"] is True
    assert result["dynamo"]["status"] == "mock_skipped"
    assert result["s3"]["status"] == "mock_skipped"


def test_create_dynamo_table_mock():
    res = create_dynamo_table()
    assert res["status"] == "mock_skipped"
    assert res["table_name"] == get_config().DYNAMO_TABLE_NAME


def test_create_s3_bucket_mock():
    res = create_s3_bucket()
    assert res["status"] == "mock_skipped"
    assert res["bucket_name"] == get_config().S3_BUCKET_NAME


# ============================================================================
# 4. Orchestrator AWS Integration Tests
# ============================================================================

def test_orchestrator_has_dynamo_receipt(sample_lesson_input):
    orch = LuminaSwarmOrchestrator()
    response = orch.run(sample_lesson_input)
    assert response.dynamo_receipt is not None
    assert len(response.dynamo_receipt) > 0
    assert response.dynamo_receipt.get("status") == "recorded"
    assert "session_id" in response.dynamo_receipt


def test_orchestrator_has_s3_url(sample_lesson_input):
    orch = LuminaSwarmOrchestrator()
    response = orch.run(sample_lesson_input)
    assert response.s3_url != ""
    assert "labs" in response.s3_url


def test_orchestrator_has_polly_url(sample_lesson_input):
    orch = LuminaSwarmOrchestrator()
    response = orch.run(sample_lesson_input)
    assert response.polly_audio_url != ""
    assert "audio" in response.polly_audio_url
    assert response.accessibility.voice_audio_url == response.polly_audio_url


def test_orchestrator_trace_includes_aws(sample_lesson_input):
    orch = LuminaSwarmOrchestrator()
    response = orch.run(sample_lesson_input)
    agent_names = [e["agent_name"] for e in response.swarm_trace]
    assert "AWS_DynamoDB" in agent_names
    assert "AWS_S3_Polly" in agent_names

    dynamo_trace = next(e for e in response.swarm_trace if e["agent_name"] == "AWS_DynamoDB")
    s3_trace = next(e for e in response.swarm_trace if e["agent_name"] == "AWS_S3_Polly")
    assert dynamo_trace["status"] == "success"
    assert s3_trace["status"] == "success"
    assert dynamo_trace["duration_ms"] >= 1
    assert s3_trace["duration_ms"] >= 1
