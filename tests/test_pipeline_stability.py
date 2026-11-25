"""Comprehensive Pipeline Stability Tests across ALL Scenarios, Engines, and Failure Modes."""

import json
import os
from typing import Any, AsyncGenerator

import pytest
from strands.models.model import Model

os.environ["LUMINA_MOCK_MODE"] = "true"

from src.contracts.schemas import (
    DeconstructedConcept,
    EngineType,
    LessonInput,
    LuminaResponse,
    SimulationSpec,
    VerifiedMicroLab,
)
from src.swarm.json_utils import (
    extract_agent_response_text,
    extract_json_dict,
    invoke_agent_for_json,
    is_non_retryable_provider_error,
)
from src.swarm.orchestrator import LuminaSwarmOrchestrator
from src.swarm.pair1_deconstruct import _sanitize_deconstructed_data, run_pair1
from src.swarm.pair2_interactive import run_pair2
from src.swarm.pair3_sensory_mastery import run_pair3


class ScriptedSequenceModel(Model):
    """Test double that yields scripted outputs on successive turns and records incoming prompts."""

    def __init__(self, responses: list[str | Exception]):
        self._responses = list(responses)
        self.calls: list[str] = []
        self._idx = 0

    def update_config(self, **kwargs: Any) -> None:
        pass

    def get_config(self) -> dict[str, Any]:
        return {}

    async def structured_output(self, output_model: Any, prompt: Any, system_prompt: str | None = None, **kwargs: Any) -> AsyncGenerator[dict[str, Any], None]:
        yield {"output": output_model()}

    async def stream(self, messages: Any, *args: Any, **kwargs: Any) -> AsyncGenerator[dict[str, Any], None]:
        prompt_str = json.dumps(messages, ensure_ascii=False, default=str)
        self.calls.append(prompt_str)
        item = self._responses[min(self._idx, len(self._responses) - 1)]
        self._idx += 1
        if isinstance(item, Exception):
            raise item
        yield {"messageStart": {"role": "assistant"}}
        yield {"contentBlockDelta": {"delta": {"text": item}}}
        yield {"contentBlockStop": {}}
        yield {"messageStop": {"stopReason": "end_turn"}}


# ============================================================================
# 1. Resilient JSON Extraction & Repair
# ============================================================================

def test_extract_json_heals_exact_live_acid_dissociation_glitch():
    """Reproduces exact malformed JSON seen in live server logs (dangling quote + duplicated object)."""
    raw = '''```json
{
  "core_concept": "Acid Dissociation Equilibrium and pH",
  "target_equation_or_steps": "pH = pKa + log10([A-]/[HA])",
  "cognitive_bottleneck": "Students confuse weak acid strength Ka with total concentration.",
  "baseline_grade_level": 11.0,
  "simplified_explanation": "Weak acids partially ionize according to Ka, shifting equilibrium.",
  "key_variables": [
    {
      "name": "Acid Dissociation Constant",
      "symbol": "Ka",
      "unit": "(mol/L)",
      "min_val": 1e-10,
      "max_val": 10.0,
      "default_val":66",
      "name": "Acid Dissociation Constant",
      "symbol": "Ka",
      "unit": "Dimensionless",
      "min_val": 1e-10,
      "max_val": 100.0,
      "default_val": 1e-5
    }
  ]
}
```'''
    parsed = extract_json_dict(raw)
    assert parsed["core_concept"] == "Acid Dissociation Equilibrium and pH"
    assert len(parsed["key_variables"]) == 1
    assert parsed["key_variables"][0]["symbol"] == "Ka"
    assert parsed["key_variables"][0]["default_val"] == pytest.approx(1e-5)


def test_extract_json_handles_unclosed_fence_trailing_commas_and_prose():
    raw = '''Sure! Here is the extracted analysis:
```json
{
  "core_concept": "Kinetic Energy",
  "target_equation_or_steps": "KE = 0.5 * m * v**2",
  "cognitive_bottleneck": "Velocity is squared, quadrupling kinetic energy when speed doubles.",
  "baseline_grade_level": 9.0,
  "simplified_explanation": "Speed matters twice as much as mass because velocity is squared.",
  "key_variables": [
    {"name": "Mass", "symbol": "m", "unit": "kg", "min_val": 1.0, "max_val": 50.0, "default_val": 5.0,},
  ],
'''
    parsed = extract_json_dict(raw)
    assert parsed["core_concept"] == "Kinetic Energy"
    assert len(parsed["key_variables"]) == 1


def test_extract_json_never_masks_inner_error_with_char0_backtick():
    broken = '```json\n{\n  "a": [unquoted_broken_token,\n}\n```'
    with pytest.raises(ValueError) as exc_info:
        extract_json_dict(broken)
    msg = str(exc_info.value)
    assert "char 0" not in msg.lower()
    assert "line 2" in msg.lower() or "unquoted_broken_token" in msg


def test_extract_agent_response_text_collects_all_text_blocks_across_tool_calls():
    class FakeResult:
        message = {
            "role": "assistant",
            "content": [
                {"toolUse": {"name": "assess_readability", "input": {"text": "sample"}}},
                {"text": "Readability checked."},
                {"text": '{"recommended_engine": "slider", "engine_justification": "Continuous law"}'},
            ],
        }

    text = extract_agent_response_text(FakeResult())
    parsed = extract_json_dict(text)
    assert parsed["recommended_engine"] == "slider"


# ============================================================================
# 2. Self-Healing Retry Loop & Auth Fast-Fail
# ============================================================================

def test_pair1_self_heals_on_second_attempt_with_error_feedback():
    lesson = LessonInput(
        subject="Chemistry",
        topic="Acids and Ka",
        raw_text="Weak acids dissociate partially in water according to their acid dissociation constant Ka and pH equilibrium.",
        student_grade=11,
        language="en",
    )
    valid_1a = json.dumps({
        "core_concept": "Weak Acid Dissociation",
        "target_equation_or_steps": "Ka = ([H+] * [A-]) / [HA]",
        "cognitive_bottleneck": "Equilibrium concentration differs from initial acid concentration.",
        "baseline_grade_level": 11.0,
        "simplified_explanation": "Only a small fraction of weak acid molecules donate protons at equilibrium.",
        "key_variables": [
            {"name": "Acid Constant", "symbol": "Ka", "unit": "mol/L", "min_val": 1e-10, "max_val": 1.0, "default_val": 1e-5}
        ],
    })
    valid_1b = json.dumps({"recommended_engine": "slider", "engine_justification": "Formula driven."})

    # Turn 1 (Agent 1A): complete syntax corruption -> Turn 2 (Agent 1A retry): valid JSON -> Turn 3 (Agent 1B): valid
    model = ScriptedSequenceModel(["NOT_JSON_AT_ALL {{{ broken", valid_1a, valid_1b])
    decon = run_pair1(lesson, model=model)
    assert decon.core_concept == "Weak Acid Dissociation"
    assert decon.recommended_engine == EngineType.SLIDER
    # Retry prompt included error diagnostics
    assert len(model.calls) == 3
    assert "Fix the syntax/schema error" in model.calls[1]


def test_auth_error_fails_fast_without_masking_or_retry():
    assert is_non_retryable_provider_error(RuntimeError("ExpiredToken: The security token included in the request is expired"))
    lesson = LessonInput(
        subject="Physics",
        topic="Force",
        raw_text="Newton second law relates force, mass, and acceleration quantitatively as F = m * a.",
        student_grade=9,
        language="en",
    )
    model = ScriptedSequenceModel([RuntimeError("401 AuthenticationError: No API key provided")])
    with pytest.raises(RuntimeError, match="401"):
        run_pair1(lesson, model=model)
    assert len(model.calls) == 1


# ============================================================================
# 3. Exhausted Retry Deterministic Recovery + All 4 Engines + Qualitative Lessons
# ============================================================================

@pytest.mark.parametrize("engine", [EngineType.SLIDER, EngineType.STEPPER, EngineType.DIAGRAM, EngineType.BALANCE])
def test_pair2_guarantees_valid_lab_for_all_4_engines_when_agent2a_returns_incomplete_or_corrupt_json(engine):
    lesson = LessonInput(
        subject="Biology" if engine != EngineType.SLIDER else "Physics",
        topic="Cell Mitosis" if engine != EngineType.SLIDER else "Wave Speed",
        raw_text="Prophase, metaphase, anaphase, and telophase organize chromosome division into two daughter cells.",
        student_grade=7,
        language="ar",
    )
    decon = DeconstructedConcept(
        original_input=lesson,
        core_concept="مراحل الانقسام المتساوي للخلية",
        target_equation_or_steps="التمهيدي -> الاستوائي -> الانفصالي -> النهائي",
        cognitive_bottleneck="ترتيب اصطفاف الكروموسومات قبل الانفصال",
        baseline_grade_level=7.0,
        simplified_explanation="تمر الخلية بأربع مراحل مرتبة لتوزيع المادة الوراثية بالتساوي.",
        key_variables=[
            {"name": "الطور التمهيدي", "symbol": "P1", "unit": "phase", "min_val": 1.0, "max_val": 4.0, "default_val": 1.0},
            {"name": "الطور الاستوائي", "symbol": "P2", "unit": "phase", "min_val": 1.0, "max_val": 4.0, "default_val": 2.0},
        ],
        recommended_engine=engine,
        engine_justification="Match requested engine.",
    )
    # Agent 2A emits broken JSON on every attempt -> Pair 2 self-heals via deterministic engine completeness fallback
    model = ScriptedSequenceModel(["{{{ broken json", "still broken", "no json"])
    spec, lab = run_pair2(decon, model=model)
    assert isinstance(spec, SimulationSpec)
    assert spec.engine_type == engine
    assert isinstance(lab, VerifiedMicroLab)
    assert lab.passed_sandbox_guard is True
    assert "<!DOCTYPE html>" in lab.html_content


def test_full_pipeline_end_to_end_survives_adversarial_qualitative_arabic_lesson():
    """Tests an Arabic non-STEM qualitative lesson when live LLM outputs broken/empty structures across all pairs."""
    lesson = LessonInput(
        subject="التاريخ",
        topic="طرق التجارة القديمة",
        raw_text="ازدهرت طرق القوافل التجارية القديمة وربطت المدن والموانئ لنقل التوابل والحرير عبر القارات.",
        student_grade=4,
        language="ar",
    )
    # Minimal valid JSON lacking key_variables + malformed types for Pair 3
    agent1a_minimal = json.dumps({
        "core_concept": "شبكة القوافل التجارية القديمة",
        "target_equation_or_steps": "تجهيز القافلة -> عبور المحطات -> التبادل التجاري",
        "cognitive_bottleneck": "",
        "baseline_grade_level": "Grade 4",
        "simplified_explanation": "نقلت القوافل البضائع بين المدن عبر محطات منظمة.",
        "key_variables": [],
    }, ensure_ascii=False)
    agent1b_synonym = json.dumps({"recommended_engine": "timeline", "engine_justification": "مراحل متسلسلة"})
    bad_json = "{{{ corrupt output"

    model = ScriptedSequenceModel([
        agent1a_minimal,
        agent1b_synonym,
        bad_json, bad_json, bad_json,  # Agent 2A broken x3 -> deterministic fallback
        bad_json, bad_json,            # Agent 3A broken x2 -> deterministic fallback
        bad_json, bad_json,            # Agent 3B broken x2 -> deterministic fallback
    ])
    orch = LuminaSwarmOrchestrator(model=model)
    response = orch.run(lesson, include_aws=False)
    assert isinstance(response, LuminaResponse)
    assert response.verified_lab.passed_sandbox_guard is True
    assert len(response.accessibility.adhd_steps) == 3
    assert "<b>" in response.accessibility.bionic_reading_html
