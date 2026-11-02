"""Phase 3 Test Suite: Strands Swarm Pairs 1 & 2."""

import json
import os
import pytest
from strands import Agent

# Force mock mode for all tests
os.environ["LUMINA_MOCK_MODE"] = "true"

from src.contracts.schemas import (
    LessonInput,
    DeconstructedConcept,
    SimulationSpec,
    VerifiedMicroLab,
    EngineType,
)
from src.swarm.model_factory import get_model, MockModel
from src.swarm.pair1_deconstruct import (
    create_agent_1a,
    create_agent_1b,
    run_pair1,
)
from src.swarm.pair2_interactive import (
    create_agent_2a,
    create_agent_2b,
    run_pair2,
    render_lab,
    verify_lab,
)


@pytest.fixture
def sample_lesson_input() -> LessonInput:
    return LessonInput(
        subject="Physics",
        topic="Ohm's Law",
        raw_text=(
            "Ohm's law states that the current through a conductor between two points "
            "is directly proportional to the voltage across the two points. "
            "Mathematically, V = I × R, where V is voltage in volts, I is current in amperes, "
            "and R is resistance in ohms."
        ),
        student_grade=8,
        language="en",
    )


# ============================================================================
# Model Factory Tests
# ============================================================================

def test_mock_model_creation():
    model = get_model()
    assert isinstance(model, MockModel)


def test_mock_model_callable():
    model = MockModel()
    resp = model("Test prompt")
    assert isinstance(resp, str)
    assert len(resp) > 0


def test_get_model_bedrock_api_key_mode(monkeypatch):
    """Verify that get_model correctly initializes BedrockModel with Bearer API Key without IAM."""
    monkeypatch.setenv("LUMINA_MOCK_MODE", "false")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "bedrock-api-key-test-token")
    monkeypatch.setenv("DEEPSEEK_PRO_MODEL", "bedrock:deepseek.v3.2")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("DEEPSEEK_BASE_URL", raising=False)
    from src.config import get_config
    get_config(reload=True)

    from strands.models.bedrock import BedrockModel
    model = get_model()
    assert isinstance(model, BedrockModel)
    assert model.config["model_id"] == "deepseek.v3.2"

    # Reset environment back to mock mode
    monkeypatch.setenv("LUMINA_MOCK_MODE", "true")
    get_config(reload=True)


def test_get_model_openai_mantle_mode(monkeypatch):
    """Verify that get_model correctly initializes OpenAIModel when OPENAI_BASE_URL is provided."""
    monkeypatch.setenv("LUMINA_MOCK_MODE", "false")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "bedrock-api-key-test-token")
    monkeypatch.setenv("DEEPSEEK_PRO_MODEL", "deepseek.v3.2")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://bedrock-mantle.us-east-1.api.aws/v1")
    from src.config import get_config
    get_config(reload=True)

    from strands.models.openai import OpenAIModel
    model = get_model()
    assert isinstance(model, OpenAIModel)
    assert model.config["model_id"] == "deepseek.v3.2"
    assert model.client_args.get("base_url") == "https://bedrock-mantle.us-east-1.api.aws/v1"

    # Reset environment back to mock mode
    monkeypatch.setenv("LUMINA_MOCK_MODE", "true")
    get_config(reload=True)


def test_get_model_deepseek_platform_mode(monkeypatch):
    """Verify that get_model correctly initializes OpenAIModel for native DeepSeek sk-* keys."""
    monkeypatch.setenv("LUMINA_MOCK_MODE", "false")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-mock-testing-key-placeholder-00000000")
    monkeypatch.setenv("DEEPSEEK_PRO_MODEL", "deepseek-chat")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    from src.config import get_config
    get_config(reload=True)

    from strands.models.openai import OpenAIModel
    model = get_model()
    assert isinstance(model, OpenAIModel)
    assert model.config["model_id"] == "deepseek-chat"
    assert model.client_args.get("base_url") == "https://api.deepseek.com"

    # Reset environment back to mock mode
    monkeypatch.setenv("LUMINA_MOCK_MODE", "true")
    get_config(reload=True)




# ============================================================================
# Pair 1 Tests
# ============================================================================

def test_create_agent_1a():
    agent = create_agent_1a()
    assert isinstance(agent, Agent)


def test_create_agent_1b():
    agent = create_agent_1b()
    assert isinstance(agent, Agent)


def test_run_pair1_returns_deconstructed(sample_lesson_input):
    decon = run_pair1(sample_lesson_input)
    assert isinstance(decon, DeconstructedConcept)


def test_run_pair1_has_engine(sample_lesson_input):
    decon = run_pair1(sample_lesson_input)
    assert isinstance(decon.recommended_engine, EngineType)


def test_run_pair1_has_variables(sample_lesson_input):
    decon = run_pair1(sample_lesson_input)
    assert isinstance(decon.key_variables, list)
    assert len(decon.key_variables) >= 1
    assert "name" in decon.key_variables[0]


def test_run_pair1_has_baseline_grade(sample_lesson_input):
    decon = run_pair1(sample_lesson_input)
    assert 1.0 <= decon.baseline_grade_level <= 12.0


# ============================================================================
# Pair 2 Tests
# ============================================================================

def test_create_agent_2a():
    agent = create_agent_2a()
    assert isinstance(agent, Agent)


def test_create_agent_2b():
    agent = create_agent_2b()
    assert isinstance(agent, Agent)


def test_run_pair2_returns_tuple(sample_lesson_input):
    decon = run_pair1(sample_lesson_input)
    spec, lab = run_pair2(decon)
    assert isinstance(spec, SimulationSpec)
    assert isinstance(lab, VerifiedMicroLab)


def test_run_pair2_lab_passes_guard(sample_lesson_input):
    decon = run_pair1(sample_lesson_input)
    _, lab = run_pair2(decon)
    assert lab.passed_sandbox_guard is True
    assert len(lab.error_log) == 0


def test_run_pair2_lab_size_valid(sample_lesson_input):
    decon = run_pair1(sample_lesson_input)
    _, lab = run_pair2(decon)
    assert 0.0 < lab.size_kb < 200.0


def test_run_pair2_html_is_complete(sample_lesson_input):
    decon = run_pair1(sample_lesson_input)
    _, lab = run_pair2(decon)
    assert "<!DOCTYPE html>" in lab.html_content
    assert "</html>" in lab.html_content


# ============================================================================
# Pair 2 Tools Tests
# ============================================================================

def test_render_lab_tool_slider():
    spec_data = {
        "engine_type": "slider",
        "title": "Ohm Lab",
        "variables": [
            {"name": "Current", "symbol": "I", "unit": "A", "min_val": 0, "max_val": 10, "default_val": 2}
        ],
        "formula_expression": "V = I * 5",
    }
    result = render_lab(engine_type="slider", spec_json=json.dumps(spec_data))
    assert "html" in result
    assert "<!DOCTYPE html>" in result["html"]


def test_render_lab_tool_invalid():
    result = render_lab(engine_type="invalid_engine", spec_json="{}")
    assert "error" in result


def test_verify_lab_tool_valid():
    valid_html = (
        "<!DOCTYPE html><html><head><title>Test Lab</title></head>"
        "<body><button>Click</button></body></html>"
    )
    result = verify_lab(html_content=valid_html, engine_type="slider")
    assert result["passed"] is True
    assert len(result["errors"]) == 0


def test_verify_lab_tool_invalid():
    bad_html = "<html><body>No doctype, no title, no interaction</body></html>"
    result = verify_lab(html_content=bad_html, engine_type="slider")
    assert result["passed"] is False
    assert len(result["errors"]) > 0


# ============================================================================
# Full Integration Test (Pair 1 -> Pair 2)
# ============================================================================

def test_pair1_then_pair2_integration(sample_lesson_input):
    decon = run_pair1(sample_lesson_input)
    spec, lab = run_pair2(decon)

    assert spec.engine_type == decon.recommended_engine
    assert lab.passed_sandbox_guard is True
    assert lab.size_kb < 200.0
    assert len(lab.html_content) > 100


# ============================================================================
# Phase 2 Adaptive Visual Archetype & Agent 2A Tests
# ============================================================================

def test_agent_2a_system_prompt_visual_archetypes():
    agent = create_agent_2a()
    prompt = agent.system_prompt
    for arch in ["spring", "circuit", "beaker", "piston", "gauge", "ph_titration", "cell_division", "enzyme_kinetics", "thermo_calorimeter"]:
        assert arch in prompt


def test_infer_visual_archetype():
    from src.swarm.pair2_interactive import _infer_visual_archetype

    assert _infer_visual_archetype("spring") == "spring"
    assert _infer_visual_archetype("BEAKER") == "beaker"
    assert _infer_visual_archetype(None, subject="Physics", topic="Ohm's Law", formula="V = I * R") == "circuit"
    assert _infer_visual_archetype(None, subject="Physics", topic="Mechanical Levers", formula="F1 * d1 = F2 * d2") == "lever_torque"
    assert _infer_visual_archetype(None, subject="Chemistry", topic="Acid Base Titration and pH") == "ph_titration"
    assert _infer_visual_archetype(None, subject="Chemistry", topic="Solution Molarity and Dilution", formula="M = n / V") == "beaker"
    assert _infer_visual_archetype(None, subject="Chemistry", topic="Thermochemistry Bomb Calorimeter", formula="q = m * c * dT") == "thermo_calorimeter"
    assert _infer_visual_archetype(None, subject="Biology", topic="Michaelis-Menten Enzyme Kinetics", formula="v = (Vmax * S) / (Km + S)") == "enzyme_kinetics"
    assert _infer_visual_archetype(None, subject="Biology", topic="Bacterial Binary Fission in Colony", formula="N = N0 * pow(2, n)") == "cell_division"
    assert _infer_visual_archetype(None, subject="Biology", topic="PCR Amplification DNA Helix", formula="N = pow(2, cycle)") == "dna_pcr"
    assert _infer_visual_archetype(None, subject="Physics", topic="Boyle's Law of Ideal Gases", formula="P * V = const") == "piston"
    assert _infer_visual_archetype(None, subject="Biology", topic="Cell Membrane Osmosis") == "cell_osmosis"
    assert _infer_visual_archetype(None, subject="Math", topic="Linear Functions") == "gauge"


def test_sanitize_svg():
    from src.swarm.pair2_interactive import _sanitize_svg

    # Valid SVG
    valid = '<svg viewBox="0 0 360 140"><circle id="c1" cx="50" cy="50" r="20" fill="red"/></svg>'
    assert _sanitize_svg(valid) == valid

    # SVG with dangerous script
    malicious = '<svg viewBox="0 0 360 140"><script>alert("hack")</script></svg>'
    assert _sanitize_svg(malicious) == ""

    # SVG with event handlers
    with_events = '<svg viewBox="0 0 360 140" onload="doEvil()"><rect/></svg>'
    assert _sanitize_svg(with_events) == ""

    # Non-SVG string
    assert _sanitize_svg("<div>Not an SVG</div>") == ""
    assert _sanitize_svg("") == ""


def test_run_pair2_sets_visual_archetype(sample_lesson_input):
    from src.swarm.pair2_interactive import VALID_ARCHETYPES
    decon = run_pair1(sample_lesson_input)
    spec, lab = run_pair2(decon)
    assert spec.visual_archetype in VALID_ARCHETYPES
    assert spec.visual_archetype == "circuit"
    assert '<svg' in lab.html_content


def test_sanitize_simulation_spec_cleans_float_noise_and_formula():
    from src.swarm.pair2_interactive import _sanitize_simulation_spec

    raw_spec = {
        "title": "Acids & Bases",
        "formula_expression": "10^-pH",
        "variables": [
            {"name": "pH", "symbol": "pH", "unit": "", "min_val": 10.0, "max_val": 2.0, "default_val": 0.9000000000000001}
        ]
    }
    cleaned = _sanitize_simulation_spec(raw_spec)
    # Formula normalized to pow(10, -pH)
    assert "pow(10, -pH)" in cleaned["formula_expression"]
    # Inverted bounds healed
    var = cleaned["variables"][0]
    assert var["min_val"] < var["max_val"]
    # Float noise cleaned
    assert var["default_val"] == 0.9 or var["default_val"] > var["min_val"]


def test_sandbox_guard_rejects_nan_and_degenerate_ranges():
    from src.tools.sandbox_guard import verify_micro_lab

    # HTML with rendered NaN
    html_with_nan = """<!DOCTYPE html><html><head><title>Test</title></head><body>
    <button onclick="calc()">Run</button>
    <span>NaN</span>
    </body></html>"""
    res1 = verify_micro_lab(html_with_nan, EngineType.SLIDER)
    assert res1.passed_sandbox_guard is False
    assert any("Invalid numerical artifact" in err for err in res1.error_log)

    # HTML with degenerate range input (min >= max)
    html_with_bad_slider = """<!DOCTYPE html><html><head><title>Test</title></head><body>
    <input type="range" min="10" max="2" value="5">
    </body></html>"""
    res2 = verify_micro_lab(html_with_bad_slider, EngineType.SLIDER)
    assert res2.passed_sandbox_guard is False
    assert any("Degenerate slider range" in err for err in res2.error_log)


def test_pair2_chemistry_ph_end_to_end_mock():
    chem_input = LessonInput(
        subject="Chemistry",
        topic="Acids and Bases pH scale",
        raw_text="The pH scale measures how acidic or basic a water-based solution is. Acidic solutions have higher hydrogen ion concentration [H+] = 10^-pH.",
        student_grade=9,
        language="en"
    )
    decon = run_pair1(chem_input)
    spec, verified_lab = run_pair2(decon)
    assert spec.visual_archetype == "beaker"
    assert '<rect id="beaker-liquid"' in verified_lab.html_content
    assert verified_lab.passed_sandbox_guard is True
    # Verify dependent variable is decoupled and progress bar is log-scale
    assert "slider-[H+]" not in verified_lab.html_content
    assert "isLogScale = true" in verified_lab.html_content


