"""Phase 6 Test Suite: FastAPI Server, Endpoints, CORS, and Interactive UI."""

import os
import shutil
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

os.environ["LUMINA_MOCK_MODE"] = "true"

from src.api import server
from src.api.server import app


@pytest.fixture(autouse=True)
def cleanup_environment():
    """Ensure clean isolated state before and after each test."""
    if server.ledger:
        server.ledger.clear()
    if Path("_mock_storage").exists():
        shutil.rmtree("_mock_storage", ignore_errors=True)
    if Path("_mock_ledger.json").exists():
        Path("_mock_ledger.json").unlink(missing_ok=True)
    yield
    if server.ledger:
        server.ledger.clear()
    if Path("_mock_storage").exists():
        shutil.rmtree("_mock_storage", ignore_errors=True)
    if Path("_mock_ledger.json").exists():
        Path("_mock_ledger.json").unlink(missing_ok=True)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def valid_request_body() -> dict:
    return {
        "subject": "Physics",
        "topic": "Ohm's Law",
        "raw_text": (
            "Ohm's law states that the current through a conductor between two points "
            "is directly proportional to the voltage across the two points and inversely proportional to resistance. "
            "The formula is V = I * R where V is voltage, I is current, and R is resistance."
        ),
        "student_grade": 8,
        "language": "en",
    }


# ============================================================================
# 1. Health Check Tests
# ============================================================================

def test_health_check(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_health_check_mock_mode(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["mock_mode"] is True


# ============================================================================
# 2. UI Serving Tests
# ============================================================================

def test_serve_ui(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "LuminaLab" in response.text
    assert "<title id=\"page-title\">LuminaLab Swarm | Interactive STEM Micro-Labs</title>" in response.text
    assert "Enterprise" not in response.text.split("</title>")[0]


def test_ui_has_form_elements(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert "<input" in html
    assert "<textarea" in html
    assert "<button" in html
    assert "<select" in html


def test_ui_has_api_call(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert "/api/generate" in html
    assert "fetch" in html


def test_ui_has_offline_download_button(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert "Download Offline Lab" in html or "btn-download-lab" in html
    assert "lab-frame" in html


def test_cors_headers(client: TestClient):
    response = client.options(
        "/api/generate",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    # FastAPI CORS middleware returns 200 on allowed preflight
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


# ============================================================================
# 3. Generate Endpoint Tests
# ============================================================================

def test_generate_success(client: TestClient, valid_request_body: dict):
    response = client.post("/api/generate", json=valid_request_body)
    assert response.status_code == 200
    data = response.json()
    assert "lesson_input" in data
    assert "deconstructed" in data
    assert "simulation_spec" in data


def test_generate_returns_verified_lab(client: TestClient, valid_request_body: dict):
    response = client.post("/api/generate", json=valid_request_body)
    assert response.status_code == 200
    data = response.json()
    assert "verified_lab" in data
    assert "html_content" in data["verified_lab"]
    assert len(data["verified_lab"]["html_content"]) > 50
    assert data["verified_lab"]["passed_sandbox_guard"] is True


def test_generate_returns_accessibility(client: TestClient, valid_request_body: dict):
    response = client.post("/api/generate", json=valid_request_body)
    assert response.status_code == 200
    data = response.json()
    assert "accessibility" in data
    access = data["accessibility"]
    assert "adhd_steps" in access
    assert len(access["adhd_steps"]) == 3
    assert "<b>" in access["bionic_reading_html"]
    assert "home_experiment" in access
    assert len(access["home_experiment"]["materials"]) >= 2


def test_generate_returns_impact(client: TestClient, valid_request_body: dict):
    response = client.post("/api/generate", json=valid_request_body)
    assert response.status_code == 200
    data = response.json()
    assert "impact" in data
    impact = data["impact"]
    assert impact["baseline_grade_level"] >= 1.0
    assert impact["simplified_grade_level"] >= 1.0
    assert impact["lab_size_kb"] > 0.0
    assert impact["is_offline_ready"] is True


def test_generate_returns_swarm_trace(client: TestClient, valid_request_body: dict):
    response = client.post("/api/generate", json=valid_request_body)
    assert response.status_code == 200
    data = response.json()
    assert "swarm_trace" in data
    assert isinstance(data["swarm_trace"], list)
    assert len(data["swarm_trace"]) >= 6


def test_generate_returns_s3_url(client: TestClient, valid_request_body: dict):
    response = client.post("/api/generate", json=valid_request_body)
    assert response.status_code == 200
    data = response.json()
    assert "s3_url" in data
    assert data["s3_url"] != ""


def test_generate_returns_dynamo_receipt(client: TestClient, valid_request_body: dict):
    response = client.post("/api/generate", json=valid_request_body)
    assert response.status_code == 200
    data = response.json()
    assert "dynamo_receipt" in data
    assert data["dynamo_receipt"].get("status") == "recorded"
    assert "session_id" in data["dynamo_receipt"]


def test_generate_invalid_grade(client: TestClient, valid_request_body: dict):
    bad_body = dict(valid_request_body)
    bad_body["student_grade"] = 15  # Out of range (1-12)
    response = client.post("/api/generate", json=bad_body)
    assert response.status_code == 422


def test_generate_missing_field(client: TestClient, valid_request_body: dict):
    bad_body = dict(valid_request_body)
    del bad_body["raw_text"]
    response = client.post("/api/generate", json=bad_body)
    assert response.status_code == 422


def test_generate_short_text(client: TestClient, valid_request_body: dict):
    bad_body = dict(valid_request_body)
    bad_body["raw_text"] = "hi"
    response = client.post("/api/generate", json=bad_body)
    assert response.status_code == 422


# ============================================================================
# 4. Stats Endpoint Tests
# ============================================================================

def test_stats_empty(client: TestClient):
    response = client.get("/api/stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_sessions"] == 0
    assert stats["avg_grade_reduction"] == 0.0
    assert stats["avg_cognitive_load_reduction_pct"] == 0.0


def test_stats_after_generate(client: TestClient, valid_request_body: dict):
    # Execute generation
    gen_resp = client.post("/api/generate", json=valid_request_body)
    assert gen_resp.status_code == 200

    # Retrieve stats
    stats_resp = client.get("/api/stats")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_sessions"] >= 1
    assert stats["avg_lab_size_kb"] > 0.0


# ============================================================================
# 5. Full End-to-End (E2E) Test
# ============================================================================

def test_e2e_generate_and_verify(client: TestClient, valid_request_body: dict):
    response = client.post("/api/generate", json=valid_request_body)
    assert response.status_code == 200
    data = response.json()

    # Contract verifications
    assert data["verified_lab"]["passed_sandbox_guard"] is True
    assert data["impact"]["is_offline_ready"] is True
    assert data["s3_url"] != ""
    assert data["polly_audio_url"] != ""
    assert "challenge" in data
    assert "challenge_question" in data["challenge"]


def test_audio_stream_endpoint(client: TestClient):
    """Test audio streaming route delivers audio/mpeg with range headers."""
    from pathlib import Path
    audio_dir = Path("_mock_storage") / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    test_mp3 = audio_dir / "test_api_stream.mp3"
    test_mp3.write_bytes(b"TEST_MP3_STREAM_PAYLOAD")

    resp = client.get("/api/audio/test_api_stream.mp3")
    assert resp.status_code == 200
    assert "audio/mpeg" in resp.headers.get("Content-Type", "")
    assert resp.content == b"TEST_MP3_STREAM_PAYLOAD"


def test_audio_stream_not_found(client: TestClient):
    """Test non-existent audio file returns 404."""
    resp = client.get("/api/audio/non_existent_file_9999.mp3")
    assert resp.status_code == 404


# ============================================================================
# 6. Audit Reliability Inspector (/audit & /api/audit/*) Tests
# ============================================================================

def test_serve_audit_ui(client: TestClient):
    """Verify GET /audit renders the Ledger Reliability Inspector HTML."""
    resp = client.get("/audit")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    assert "Ledger Reliability Inspector" in resp.text
    assert "/static/js/audit.js" in resp.text
    assert "/static/css/audit.css" in resp.text


def test_audit_benchmarks_endpoint(client: TestClient):
    """Verify /api/audit/benchmarks loads measured JSON snapshots and computes deltas."""
    resp = client.get("/api/audit/benchmarks")
    assert resp.status_code == 200
    data = resp.json()
    assert "before" in data
    assert "after" in data
    assert "comparison" in data
    if data["before"] and data["after"]:
        comp = data["comparison"]
        assert comp["rcu_reduction_pct"] > 90.0
        assert comp["read_p50_speedup"] > 1.0


def test_audit_stats_and_idempotency_and_cleanup_probes(client: TestClient):
    """Verify /api/audit live probe workflow: stats-probe -> idempotency-probe -> cleanup-probe."""
    stats_resp = client.get("/api/audit/stats-probe")
    assert stats_resp.status_code == 200
    s_data = stats_resp.json()
    assert s_data["stats"]["total_sessions"] == 0
    assert s_data["latency_ms"] >= 0.0

    idem_resp = client.post("/api/audit/idempotency-probe", json={})
    assert idem_resp.status_code == 200
    idem = idem_resp.json()
    assert idem["session_id"].startswith("audit-probe-")
    assert idem["delta_first"] == 1
    assert idem["delta_second"] == 0
    assert idem["idempotency_verified"] is True

    # Guardrail: arbitrary non-probe IDs must be rejected
    bad_clean = client.post("/api/audit/cleanup-probe", json={"session_ids": ["prod-session-1"]})
    assert bad_clean.status_code == 400

    clean_resp = client.post("/api/audit/cleanup-probe", json={"session_ids": [idem["session_id"]]})
    assert clean_resp.status_code == 200
    c_data = clean_resp.json()
    assert c_data["deleted_count"] == 1
    assert c_data["remaining_table_items"] == 0
    assert c_data["stats_after"]["total_sessions"] == 0


def test_audit_infrastructure_endpoint_mock(client: TestClient):
    """Verify /api/audit/infrastructure responds cleanly with IAM no-Scan status in mock mode."""
    resp = client.get("/api/audit/infrastructure")
    assert resp.status_code == 200
    data = resp.json()
    assert data["iam_policy"]["has_dynamodb_scan"] is False
    assert "dynamodb:Scan" not in data["iam_policy"]["dynamodb_actions"]


def test_format_alarm_metrics_deduplicates_system_errors():
    """Verify composite MetricMath alarm metrics list SystemErrors once with Operation dimensions."""
    composite_alarm = {
        "Metrics": [
            {
                "Id": "m1",
                "MetricStat": {
                    "Metric": {
                        "MetricName": "SystemErrors",
                        "Dimensions": [
                            {"Name": "TableName", "Value": "tbl"},
                            {"Name": "Operation", "Value": "TransactWriteItems"},
                        ],
                    }
                },
            },
            {
                "Id": "m2",
                "MetricStat": {
                    "Metric": {
                        "MetricName": "SystemErrors",
                        "Dimensions": [
                            {"Name": "TableName", "Value": "tbl"},
                            {"Name": "Operation", "Value": "GetItem"},
                        ],
                    }
                },
            },
        ]
    }
    throttle_alarm = {
        "Metrics": [
            {"Id": "m1", "MetricStat": {"Metric": {"MetricName": "ReadThrottleEvents", "Dimensions": []}}},
            {"Id": "m2", "MetricStat": {"Metric": {"MetricName": "WriteThrottleEvents", "Dimensions": []}}},
        ]
    }
    assert server._format_alarm_metrics(composite_alarm) == "SystemErrors (TransactWriteItems, GetItem)"
    assert server._format_alarm_metrics(throttle_alarm) == "ReadThrottleEvents, WriteThrottleEvents"
    assert server._format_alarm_metrics({"MetricName": "DynamoFallbackCount"}) == "DynamoFallbackCount"
