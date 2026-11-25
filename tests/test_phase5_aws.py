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


# ============================================================================
# 5. F-05 Architectural Remediation Tests (Timeouts, O(1) Atomic Stats, Degraded Trace)
# ============================================================================

@pytest.fixture
def live_config_mode(monkeypatch):
    """Temporarily enable non-mock config mode and cleanly restore singleton afterward."""
    monkeypatch.setenv("LUMINA_MOCK_MODE", "false")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("DYNAMO_TABLE_NAME", "test-impact-table")
    monkeypatch.setenv("CLOUDWATCH_METRICS_ENABLED", "false")
    get_config(reload=True)
    yield
    monkeypatch.setenv("LUMINA_MOCK_MODE", "true")
    monkeypatch.setenv("CLOUDWATCH_METRICS_ENABLED", "false")
    get_config(reload=True)


def test_dynamo_client_uses_production_timeouts_and_retries(live_config_mode):
    """Verify F-05A: boto3 client config uses 2.0s connect, 5.0s read, standard retries=3."""
    ledger = DynamoImpactLedger()
    assert ledger.mock_mode is False
    cfg = ledger.client.meta.config
    assert cfg.connect_timeout == 2.0
    assert cfg.read_timeout == 5.0
    assert cfg.retries.get("mode") == "standard"
    assert cfg.retries.get("total_max_attempts") == 3


def test_record_impact_uses_idempotent_transact_write_and_prevents_double_count(
    live_config_mode, sample_metrics, caplog
):
    """Verify F-05B: record_impact issues TransactWriteItems and avoids double-counting duplicates."""
    from unittest.mock import MagicMock
    from botocore.exceptions import ClientError

    mock_client = MagicMock()
    ledger = DynamoImpactLedger()
    ledger.client = mock_client

    receipt1 = ledger.record_impact(sample_metrics, session_id="idem-sess-001")
    assert receipt1["status"] == "recorded"
    assert mock_client.transact_write_items.call_count == 1
    mock_client.put_item.assert_not_called()

    tx_items = mock_client.transact_write_items.call_args.kwargs["TransactItems"]
    assert len(tx_items) == 2
    assert tx_items[0]["Put"]["ConditionExpression"] == "attribute_not_exists(session_id)"
    assert tx_items[1]["Update"]["Key"] == {"session_id": {"S": DynamoImpactLedger.AGGREGATE_SESSION_ID}}
    assert "ADD total_sessions :one" in tx_items[1]["Update"]["UpdateExpression"]

    # Simulate duplicate retry returning TransactionCanceledException(ConditionalCheckFailed)
    mock_client.transact_write_items.side_effect = ClientError(
        {
            "Error": {"Code": "TransactionCanceledException", "Message": "ConditionalCheckFailed"},
            "CancellationReasons": [{"Code": "ConditionalCheckFailed"}, {"Code": "None"}],
        },
        "TransactWriteItems",
    )
    with caplog.at_level("INFO", logger="luminalab.dynamo_ledger"):
        receipt2 = ledger.record_impact(sample_metrics, session_id="idem-sess-001")

    assert receipt2["status"] == "recorded"
    assert receipt2.get("idempotent_duplicate") is True
    assert "idem-sess-001" not in ledger._local_store
    assert any("dynamo_idempotent_duplicate" in r.message for r in caplog.records)


def test_record_impact_retries_transient_transaction_conflict(live_config_mode, sample_metrics, monkeypatch):
    """Verify F-05B: TransactionConflict triggers bounded retry and succeeds cleanly."""
    from unittest.mock import MagicMock
    from botocore.exceptions import ClientError

    monkeypatch.setattr("src.aws.dynamo_ledger.time.sleep", lambda _s: None)
    mock_client = MagicMock()
    conflict_err = ClientError(
        {
            "Error": {"Code": "TransactionCanceledException", "Message": "Conflict"},
            "CancellationReasons": [{"Code": "None"}, {"Code": "TransactionConflict"}],
        },
        "TransactWriteItems",
    )
    mock_client.transact_write_items.side_effect = [conflict_err, {}]

    ledger = DynamoImpactLedger()
    ledger.client = mock_client
    receipt = ledger.record_impact(sample_metrics, session_id="conflict-sess-01")
    assert receipt["status"] == "recorded"
    assert mock_client.transact_write_items.call_count == 2


def test_record_impact_mock_mode_is_idempotent(sample_metrics):
    """Verify mock mode avoids double-counting duplicate session_ids."""
    ledger = DynamoImpactLedger()
    ledger.record_impact(sample_metrics, session_id="dup-mock-1")
    dup_receipt = ledger.record_impact(sample_metrics, session_id="dup-mock-1")
    assert dup_receipt["status"] == "recorded"
    assert dup_receipt.get("idempotent_duplicate") is True
    assert ledger.get_aggregate_stats()["total_sessions"] == 1


def test_get_aggregate_stats_uses_get_item_only_and_handles_cold_start(live_config_mode):
    """Verify F-05B: get_aggregate_stats uses O(1) GetItem, never calls scan(), and handles empty table."""
    from unittest.mock import MagicMock

    mock_client = MagicMock()
    mock_client.scan.side_effect = AssertionError("Scan must never be called in get_aggregate_stats()")
    mock_client.get_item.return_value = {}

    ledger = DynamoImpactLedger()
    ledger.client = mock_client

    # Cold start: empty table with no AGGREGATE#GLOBAL item yet
    cold_stats = ledger.get_aggregate_stats()
    assert cold_stats == {
        "total_sessions": 0,
        "avg_grade_reduction": 0.0,
        "avg_cognitive_load_reduction_pct": 0.0,
        "avg_lab_size_kb": 0.0,
        "total_offline_ready_labs": 0,
        "avg_generation_time_sec": 0.0,
    }
    mock_client.get_item.assert_called_once_with(
        TableName="test-impact-table",
        Key={"session_id": {"S": "AGGREGATE#GLOBAL"}},
    )
    mock_client.scan.assert_not_called()

    # Populated AGGREGATE#GLOBAL item returns exact computed averages in O(1)
    mock_client.get_item.return_value = {
        "Item": {
            "session_id": {"S": "AGGREGATE#GLOBAL"},
            "total_sessions": {"N": "4"},
            "sum_grade_reduction": {"N": "18.0"},
            "sum_cognitive_load_reduction_pct": {"N": "220.0"},
            "sum_lab_size_kb": {"N": "100.0"},
            "total_offline_ready_labs": {"N": "3"},
            "sum_generation_time_sec": {"N": "10.0"},
        }
    }
    stats = ledger.get_aggregate_stats()
    assert stats == {
        "total_sessions": 4,
        "avg_grade_reduction": 4.5,
        "avg_cognitive_load_reduction_pct": 55.0,
        "avg_lab_size_kb": 25.0,
        "total_offline_ready_labs": 3,
        "avg_generation_time_sec": 2.5,
    }
    mock_client.scan.assert_not_called()


def test_orchestrator_marks_dynamo_fallback_as_degraded_and_emits_metric(
    live_config_mode, sample_lesson_input, caplog
):
    """Verify F-05A: local fallback never logs 'success'; marks 'degraded', logs warning, and emits metric."""
    from unittest.mock import MagicMock
    from botocore.exceptions import ReadTimeoutError
    from src.swarm.model_factory import MockModel

    mock_ddb = MagicMock()
    mock_ddb.transact_write_items.side_effect = ReadTimeoutError(
        endpoint_url="https://dynamodb.us-east-1.amazonaws.com/",
        error=TimeoutError("Read timeout simulated"),
    )
    mock_cw = MagicMock()

    orch = LuminaSwarmOrchestrator(
        model=MockModel(),
        cloudwatch_client=mock_cw,
        emit_cloudwatch_metrics=True,
    )
    orch.dynamo_ledger.client = mock_ddb
    orch.s3_polly_service.mock_mode = True
    orch.s3_polly_service.bucket_name = "mock_local"

    with caplog.at_level("WARNING", logger="luminalab.orchestrator"):
        response = orch.run(sample_lesson_input, include_aws=True)

    # Pipeline still succeeds for student while accurately reporting DynamoDB degradation
    assert response.verified_lab.passed_sandbox_guard is True
    assert response.dynamo_receipt["status"] == "recorded_local_fallback"

    dynamo_trace = next(e for e in response.swarm_trace if e["agent_name"] == "AWS_DynamoDB")
    assert dynamo_trace["status"] == "degraded"
    assert dynamo_trace["status"] != "success"

    assert any("dynamo_persistence_degraded" in r.message for r in caplog.records)
    mock_cw.put_metric_data.assert_called_once()
    cw_kwargs = mock_cw.put_metric_data.call_args.kwargs
    assert cw_kwargs["Namespace"] == "LuminaLab/Swarm"
    assert cw_kwargs["MetricData"][0]["MetricName"] == "DynamoFallbackCount"

    # Also verify CloudWatch failure never breaks student response
    mock_cw.put_metric_data.side_effect = RuntimeError("CloudWatch unreachable")
    response2 = orch.run(sample_lesson_input, include_aws=True)
    dynamo_trace2 = next(e for e in response2.swarm_trace if e["agent_name"] == "AWS_DynamoDB")
    assert dynamo_trace2["status"] == "degraded"
