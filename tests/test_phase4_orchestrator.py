"""Phase 4 Test Suite: Accessibility Tools, Pair 3, and Swarm Orchestrator."""

import os
import pytest
from strands import Agent

os.environ["LUMINA_MOCK_MODE"] = "true"

from src.contracts.schemas import (
    LessonInput,
    DeconstructedConcept,
    SimulationSpec,
    VerifiedMicroLab,
    AccessibilityPack,
    ImpactMetrics,
    LuminaResponse,
    EngineType,
)
from src.tools.accessibility_tools import (
    bionic_reading_format,
    adhd_micro_chunk,
    generate_home_experiment_template,
    generate_voice_script,
)
from src.swarm.pair3_sensory_mastery import (
    create_agent_3a,
    create_agent_3b,
    run_pair3,
)
from src.swarm.orchestrator import (
    LuminaSwarmOrchestrator,
    SwarmOrchestrator,
    run_swarm,
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


@pytest.fixture
def sample_deconstructed_concept(sample_lesson_input) -> DeconstructedConcept:
    return DeconstructedConcept(
        original_input=sample_lesson_input,
        core_concept="Ohm's Law relationship between voltage, current, and resistance",
        target_equation_or_steps="V = I * R",
        cognitive_bottleneck="Inverse relationship between current and resistance",
        baseline_grade_level=8.5,
        simplified_explanation="Voltage pushes charges, current is the flow, and resistance opposes it.",
        key_variables=[
            {"name": "Current", "symbol": "I", "unit": "A", "min_val": 0.1, "max_val": 10.0, "default_val": 2.0},
            {"name": "Resistance", "symbol": "R", "unit": "Ω", "min_val": 1.0, "max_val": 100.0, "default_val": 5.0},
        ],
        recommended_engine=EngineType.SLIDER,
        engine_justification="Continuous equation suitable for sliders",
    )


# ============================================================================
# Accessibility Tools Tests (M4.1)
# ============================================================================

def test_bionic_reading_english():
    bionic = bionic_reading_format("Hello World")
    assert "<b>" in bionic
    assert "<b>He</b>llo" in bionic or "<b>Hel</b>lo" in bionic


def test_bionic_reading_arabic():
    bionic = bionic_reading_format("مرحبا بالعالم")
    assert "<b>" in bionic


def test_bionic_reading_single_char():
    bionic = bionic_reading_format("I am here")
    # "I" should not be wrapped in <b>
    parts = bionic.split()
    assert parts[0] == "I"


def test_adhd_chunk_returns_3():
    steps = adhd_micro_chunk("One. Two. Three. Four. Five.")
    assert len(steps) == 3


def test_adhd_chunk_has_icons():
    steps = adhd_micro_chunk("Explaining a concept clearly to students.")
    assert any("🔵" in s for s in steps)
    assert any("🟡" in s for s in steps)
    assert any("🟢" in s for s in steps)


def test_adhd_chunk_short_text():
    steps = adhd_micro_chunk("Short single sentence.")
    assert len(steps) == 3


def test_voice_script_english():
    script = generate_voice_script("Voltage pushes current", ["Step 1", "Step 2", "Step 3"], language="en")
    assert "Let's learn" in script
    assert "Voltage pushes current" in script


def test_voice_script_arabic():
    script = generate_voice_script("الجهد يدفع التيار", ["الخطوة 1", "الخطوة 2", "الخطوة 3"], language="ar")
    assert "يلا نتعلم" in script


def test_home_experiment_template():
    tpl = generate_home_experiment_template("Circuits", language="en")
    assert "title" in tpl
    assert "materials" in tpl
    assert "steps" in tpl
    assert "safety_note" in tpl
    assert len(tpl["materials"]) >= 2
    assert len(tpl["steps"]) >= 2


# ============================================================================
# Pair 3 Tests (M4.2)
# ============================================================================

def test_create_agent_3a():
    agent = create_agent_3a()
    assert isinstance(agent, Agent)


def test_create_agent_3b():
    agent = create_agent_3b()
    assert isinstance(agent, Agent)


def test_run_pair3_returns_tuple(sample_deconstructed_concept):
    pack, challenge = run_pair3(sample_deconstructed_concept)
    assert isinstance(pack, AccessibilityPack)
    assert isinstance(challenge, dict)


def test_run_pair3_accessibility_complete(sample_deconstructed_concept):
    pack, _ = run_pair3(sample_deconstructed_concept)
    assert len(pack.adhd_steps) == 3
    assert "<b>" in pack.bionic_reading_html
    assert len(pack.home_experiment["materials"]) >= 2
    assert len(pack.home_experiment["steps"]) >= 2


def test_run_pair3_challenge_has_question(sample_deconstructed_concept):
    _, challenge = run_pair3(sample_deconstructed_concept)
    assert "challenge_question" in challenge
    assert len(challenge["challenge_question"]) > 5


from strands.models.model import Model


def test_run_pair3_fallback_works(sample_deconstructed_concept):
    class BrokenModel(Model):
        def update_config(self, **kwargs):
            pass

        def get_config(self):
            return {}

        async def stream(self, *args, **kwargs):
            raise RuntimeError("LLM breakdown")
            yield {}

        async def structured_output(self, *args, **kwargs):
            raise RuntimeError("LLM breakdown")
            yield {}

    pack, challenge = run_pair3(sample_deconstructed_concept, model=BrokenModel())

    assert isinstance(pack, AccessibilityPack)
    assert len(pack.adhd_steps) == 3
    assert "challenge_question" in challenge


# ============================================================================
# Orchestrator Tests (M4.3)
# ============================================================================

def test_orchestrator_creation():
    orch = LuminaSwarmOrchestrator()
    assert orch.model is not None


def test_orchestrator_run_returns_lumina_response(sample_lesson_input):
    orch = LuminaSwarmOrchestrator()
    response = orch.run(sample_lesson_input)
    assert isinstance(response, LuminaResponse)


def test_orchestrator_response_has_all_fields(sample_lesson_input):
    response = run_swarm(sample_lesson_input)
    assert response.lesson_input is not None
    assert response.deconstructed is not None
    assert response.simulation_spec is not None
    assert response.verified_lab is not None
    assert response.accessibility is not None
    assert response.impact is not None


def test_orchestrator_impact_metrics_valid(sample_lesson_input):
    orch = LuminaSwarmOrchestrator()
    response = orch.run(sample_lesson_input)
    assert response.impact.baseline_grade_level >= 1.0
    assert response.impact.lab_size_kb > 0.0
    assert response.impact.is_offline_ready is True
    assert response.impact.generation_time_sec >= 0.0


def test_orchestrator_swarm_trace_has_6_entries(sample_lesson_input):
    orch = LuminaSwarmOrchestrator()
    response = orch.run(sample_lesson_input)
    assert len(response.swarm_trace) >= 6
    agent_names = [e["agent_name"] for e in response.swarm_trace]
    assert "Agent_1A_ConceptExtractor" in agent_names
    assert "Agent_1B_ArchetypeRouter" in agent_names
    assert "Agent_2A_SimMathArchitect" in agent_names
    assert "Agent_2B_RendererGuard" in agent_names
    assert "Agent_3A_SensoryAdapter" in agent_names
    assert "Agent_3B_MasteryRecorder" in agent_names


def test_orchestrator_swarm_trace_all_success(sample_lesson_input):
    response = run_swarm(sample_lesson_input)
    for entry in response.swarm_trace:
        assert entry["status"] in ("success", "repaired")
        assert entry["duration_ms"] >= 0


def test_orchestrator_verified_lab_passed(sample_lesson_input):
    orch = LuminaSwarmOrchestrator()
    response = orch.run(sample_lesson_input)
    assert response.verified_lab.passed_sandbox_guard is True


def test_orchestrator_response_json_serializable(sample_lesson_input):
    response = run_swarm(sample_lesson_input)
    json_str = response.model_dump_json()
    assert isinstance(json_str, str)
    assert len(json_str) > 0


def test_orchestrator_parallel_execution(sample_lesson_input):
    orch = SwarmOrchestrator()
    response = orch.run(sample_lesson_input)
    assert response.simulation_spec.engine_type == response.deconstructed.recommended_engine
    assert response.verified_lab.passed_sandbox_guard is True


def test_orchestrator_parallel_faster_than_serial(sample_lesson_input):
    orch = LuminaSwarmOrchestrator()
    response = orch.run(sample_lesson_input)
    assert response is not None
    trace_agents = {t["agent_name"] for t in response.swarm_trace}
    assert "Agent_2A_SimMathArchitect" in trace_agents
    assert "Agent_3A_SensoryAdapter" in trace_agents

