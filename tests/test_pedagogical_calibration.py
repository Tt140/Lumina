"""Tests for Age-Calibrated Pedagogical and Neuro-Adaptive Engine."""

import pytest
from src.contracts.schemas import LessonInput, EngineType
from src.swarm.pedagogical_calibration import (
    parse_student_grade,
    get_pedagogical_tier,
    get_pedagogical_directive,
)
from src.swarm.pair1_deconstruct import run_pair1
from src.swarm.pair2_interactive import run_pair2, _sanitize_variables
from src.swarm.pair3_sensory_mastery import run_pair3
from src.engines.slider_engine import render_slider_lab
from src.contracts.schemas import SimulationSpec


def test_parse_student_grade_various_inputs():
    """Verify grade parsing handles integers, floats, strings, and edge cases."""
    assert parse_student_grade(5) == 5
    assert parse_student_grade(12) == 12
    assert parse_student_grade(8.0) == 8
    assert parse_student_grade("Grade 11 — High School") == 11
    assert parse_student_grade("Grade 4 (Elementary)") == 4
    assert parse_student_grade("7th Grade") == 7
    assert parse_student_grade("High School") == 11
    assert parse_student_grade("Primary") == 5
    assert parse_student_grade("Prep / إعدادي") == 8
    assert parse_student_grade(None) == 8
    assert parse_student_grade("Invalid") == 8
    # Clamping
    assert parse_student_grade(0) == 1
    assert parse_student_grade(15) == 12


def test_get_pedagogical_tier():
    """Verify accurate 3-tier cognitive classification."""
    assert get_pedagogical_tier(1) == "elementary"
    assert get_pedagogical_tier(4) == "elementary"
    assert get_pedagogical_tier(6) == "elementary"
    assert get_pedagogical_tier(7) == "middle"
    assert get_pedagogical_tier(8) == "middle"
    assert get_pedagogical_tier(9) == "middle"
    assert get_pedagogical_tier(10) == "high"
    assert get_pedagogical_tier(11) == "high"
    assert get_pedagogical_tier(12) == "high"


def test_pedagogical_directive_elementary_ar():
    """Verify elementary directive has warm, tangible metaphors and ADHD 3-step loop."""
    res = get_pedagogical_directive(5, language="ar")
    assert res["tier"] == "elementary"
    assert "المرحلة الابتدائية" in res["tier_label"]
    assert "تشبيهات بصرية ملموسة" in res["concept_guidance"]
    assert "أرقام صحيحة بسيطة" in res["math_guidance"]
    assert "🔵 أولاً" in res["adhd_guidance"]
    assert "🟡 ثانياً" in res["adhd_guidance"]
    assert "🟢 أخيراً" in res["adhd_guidance"]


def test_pedagogical_directive_high_school_ar():
    """Verify high school directive enforces 'الزتونة' and strictly forbids kid talk."""
    res = get_pedagogical_directive("Grade 11 — High School", language="ar")
    assert res["tier"] == "high"
    assert "المرحلة الثانوية" in res["tier_label"]
    assert "الزتونة العلمية المركزة" in res["concept_guidance"]
    assert "ممنوع منعاً باتاً لغة الأطفال" in res["concept_guidance"]
    assert "يا بطل" in res["concept_guidance"]  # Mentioned in forbidden list
    assert "وحدات SI المعيارية" in res["math_guidance"]
    assert "حرّك الآلية الفيزيائية" in res["adhd_guidance"]


def test_pedagogical_directive_english():
    """Verify English output produces correct executive and cause-and-effect directives."""
    res_elem = get_pedagogical_directive(4, language="en")
    assert "Concrete operational" in res_elem["concept_guidance"]
    assert "friendly integer bounds" in res_elem["math_guidance"]

    res_high = get_pedagogical_directive(12, language="en")
    assert "Executive Scientific Capsule" in res_high["concept_guidance"]
    assert "NEVER use baby talk" in res_high["concept_guidance"]


def test_sanitize_variables_elementary_integer_preference():
    """Verify that elementary tier rounds near-integer bounds to clean integers."""
    raw_data = {
        "title": "Friction Lab",
        "formula_expression": "F = m * a",
        "variables": [
            {"name": "Mass", "symbol": "m", "unit": "kg", "min_val": 1.002, "max_val": 10.01, "default_val": 2.001},
            {"name": "Acceleration", "symbol": "a", "unit": "m/s²", "min_val": 0.0, "max_val": 20.0, "default_val": 5.0}
        ]
    }
    cleaned = _sanitize_variables(raw_data, grade=4)
    v0 = cleaned["variables"][0]
    assert v0["min_val"] == 1.0
    assert v0["max_val"] == 10.0
    assert v0["default_val"] == 2.0


def test_slider_engine_dyslexia_typography():
    """Verify slider_engine HTML incorporates dyslexia-friendly typography and contrast."""
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Ohm's Law Lab",
        variables=[
            {"name": "Current", "symbol": "I", "unit": "A", "min_val": 0.1, "max_val": 10.0, "default_val": 2.0},
            {"name": "Resistance", "symbol": "R", "unit": "Ω", "min_val": 1.0, "max_val": 100.0, "default_val": 5.0}
        ],
        formula_expression="V = I * R",
        visual_archetype="circuit"
    )
    html = render_slider_lab(spec)
    assert "letter-spacing:0.015em;" in html or "letter-spacing: 0.015em;" in html
    assert "line-height:1.55;" in html or "line-height: 1.55;" in html
    assert "--muted: #475569;" in html
    assert "Noto Sans Arabic" in html
    # Ensure no clutter cards were added
    assert "balance-bar-container" in html
    assert len(html.encode("utf-8")) / 1024.0 < 50.0  # Kept lightweight and clean


def test_swarm_integration_grade_adaptation():
    """Verify Pair 1, 2, 3 run cleanly with age calibration."""
    elem_input = LessonInput(
        subject="Physics",
        topic="Levers and Seesaws",
        raw_text="A lever is a simple machine that allows a small effort to lift a heavy load using a pivot fulcrum.",
        student_grade=5,
        language="ar"
    )
    decon = run_pair1(elem_input)
    assert decon.core_concept
    assert decon.simplified_explanation

    spec, verified_lab = run_pair2(decon)
    assert verified_lab.passed_sandbox_guard

    acc_pack, challenge = run_pair3(decon)
    assert len(acc_pack.adhd_steps) == 3
    assert any("🔵" in s for s in acc_pack.adhd_steps)
    assert any("🟡" in s for s in acc_pack.adhd_steps)
    assert any("🟢" in s for s in acc_pack.adhd_steps)
    assert challenge["challenge_question"]
