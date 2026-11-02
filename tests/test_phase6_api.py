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
