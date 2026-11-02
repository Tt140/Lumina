"""Phase 1 Contract and Impact Calculator Test Suite."""

import pytest
from pydantic import ValidationError

from src.contracts.schemas import (
    EngineType,
    LessonInput,
    DeconstructedConcept,
    SimulationSpec,
    VerifiedMicroLab,
    AccessibilityPack,
    ImpactMetrics,
    LuminaResponse,
)
from src.tools.impact_calculator import (
    count_syllables_en,
    count_syllables_ar,
    count_words,
    count_sentences,
    calculate_grade_level,
    calculate_cognitive_load_reduction,
    calculate_lab_size_kb,
    build_impact_metrics,
)


# ============================================================================
# Schemas Tests
# ============================================================================

def test_engine_type_values():
    values = [e.value for e in EngineType]
    assert len(values) == 4
    assert set(values) == {"slider", "stepper", "diagram", "balance"}


def test_lesson_input_valid():
    inp = LessonInput(
        subject="Physics",
        topic="Ohm's Law",
        raw_text="Ohm's law states that current is directly proportional to voltage.",
        student_grade=8,
        language="en"
    )
    assert inp.subject == "Physics"
    assert inp.student_grade == 8
    assert inp.language == "en"


def test_lesson_input_invalid_grade():
    with pytest.raises(ValidationError):
        LessonInput(
            subject="Physics",
            topic="Ohm's Law",
            raw_text="Ohm's law states that current is directly proportional to voltage.",
            student_grade=15,
            language="en"
        )


def test_lesson_input_invalid_language():
    with pytest.raises(ValidationError):
        LessonInput(
            subject="Physics",
            topic="Ohm's Law",
            raw_text="Ohm's law states that current is directly proportional to voltage.",
            student_grade=8,
            language="fr"
        )


def test_lesson_input_short_text():
    with pytest.raises(ValidationError):
        LessonInput(
            subject="Physics",
            topic="Ohm's Law",
            raw_text="hi",
            student_grade=8,
            language="en"
        )


def test_deconstructed_concept_valid():
    inp = LessonInput(
        subject="Physics",
        topic="Ohm's Law",
        raw_text="Ohm's law states that current is directly proportional to voltage.",
        student_grade=8,
        language="en"
    )
    decon = DeconstructedConcept(
        original_input=inp,
        core_concept="Relation between V, I, and R",
        target_equation_or_steps="V = I * R",
        cognitive_bottleneck="Resistance inverse scaling",
        baseline_grade_level=8.5,
        simplified_explanation="Think of voltage like water pressure in pipes.",
        key_variables=[
            {
                "name": "Voltage",
                "symbol": "V",
                "unit": "Volt",
                "min_val": 0.0,
                "max_val": 220.0,
                "default_val": 12.0
            }
        ],
        recommended_engine=EngineType.SLIDER,
        engine_justification="Equation with continuous variables"
    )
    assert decon.core_concept == "Relation between V, I, and R"
    assert decon.recommended_engine == EngineType.SLIDER


def test_deconstructed_concept_invalid_variables():
    inp = LessonInput(
        subject="Physics",
        topic="Ohm's Law",
        raw_text="Ohm's law states that current is directly proportional to voltage.",
        student_grade=8,
        language="en"
    )
    with pytest.raises(ValidationError):
        DeconstructedConcept(
            original_input=inp,
            core_concept="Relation between V, I, and R",
            target_equation_or_steps="V = I * R",
            cognitive_bottleneck="Resistance inverse scaling",
            baseline_grade_level=8.5,
            simplified_explanation="Think of voltage like water pressure in pipes.",
            key_variables=[
                {
                    "name": "Voltage",
                    "symbol": "V"
                    # missing unit, min_val, max_val, default_val
                }
            ],
            recommended_engine=EngineType.SLIDER,
            engine_justification="Equation with continuous variables"
        )



def test_simulation_spec_slider_valid():
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Ohm's Law Lab",
        variables=[
            {"name": "Current", "symbol": "I", "unit": "A", "min_val": 0, "max_val": 10, "default_val": 2}
        ],
        formula_expression="V = I * R",
        visual_archetype="circuit"
    )
    assert spec.engine_type == EngineType.SLIDER
    assert spec.title == "Ohm's Law Lab"
    assert spec.visual_archetype == "circuit"


def test_simulation_spec_slider_default_archetype():
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Ohm's Law Lab",
        variables=[
            {"name": "Current", "symbol": "I", "unit": "A", "min_val": 0, "max_val": 10, "default_val": 2}
        ],
        formula_expression="V = I * R"
    )
    assert spec.visual_archetype == "gauge"


def test_simulation_spec_slider_missing_formula():
    with pytest.raises(ValidationError):
        SimulationSpec(
            engine_type=EngineType.SLIDER,
            title="Ohm's Law Lab",
            variables=[
                {"name": "Current", "symbol": "I", "unit": "A", "min_val": 0, "max_val": 10, "default_val": 2}
            ],
            formula_expression=""
        )


def test_simulation_spec_stepper_valid():
    spec = SimulationSpec(
        engine_type=EngineType.STEPPER,
        title="Binary Search Step-by-Step",
        steps=[
            {"label": "Step 1", "description": "Init pointers", "state": {"low": 0, "high": 5}}
        ]
    )
    assert len(spec.steps) == 1


def test_simulation_spec_diagram_needs_2_nodes():
    with pytest.raises(ValidationError):
        SimulationSpec(
            engine_type=EngineType.DIAGRAM,
            title="Circuit Diagram",
            nodes=[
                {"id": "battery", "label": "Battery 9V", "x": 0.0, "y": 0.0, "connections": []}
            ]
        )


def test_verified_micro_lab_auto_size():
    html = "<!DOCTYPE html><html><head><title>Test</title></head><body>Hello Lab</body></html>"
    lab = VerifiedMicroLab(
        html_content=html,
        engine_type=EngineType.SLIDER,
        passed_sandbox_guard=True
    )
    expected_size = len(html.encode("utf-8")) / 1024.0
    assert lab.size_kb == pytest.approx(expected_size, rel=1e-3)
    assert lab.size_kb > 0.0


def test_accessibility_pack_adhd_exactly_3():
    with pytest.raises(ValidationError):
        AccessibilityPack(
            adhd_steps=["Step 1", "Step 2"],  # only 2 items, requires 3
            bionic_reading_html="<b>Te</b>st",
            home_experiment={"title": "T", "materials": ["a", "b"], "steps": ["1", "2"], "safety_note": "Careful"},
            voice_script="Voice script here"
        )


def test_accessibility_pack_valid():
    pack = AccessibilityPack(
        adhd_steps=["Step 1", "Step 2", "Step 3"],
        bionic_reading_html="<b>Te</b>st <b>rea</b>ding",
        home_experiment={
            "title": "Kitchen Circuit",
            "materials": ["Battery", "Lemon"],
            "steps": ["Insert wire", "Measure voltage"],
            "safety_note": "Ask parents for help"
        },
        voice_script="Hello champions, let's explore!"
    )
    assert len(pack.adhd_steps) == 3
    assert len(pack.home_experiment["materials"]) >= 2


def test_impact_metrics_computed_fields():
    metrics = ImpactMetrics(
        baseline_grade_level=10.0,
        simplified_grade_level=4.0,
        cognitive_load_reduction_pct=60.0,
        lab_size_kb=18.5,
        generation_time_sec=2.5
    )
    assert metrics.grade_reduction == 6.0
    assert metrics.is_offline_ready is True


def test_impact_metrics_auto_timestamp():
    metrics = ImpactMetrics(
        baseline_grade_level=8.0,
        simplified_grade_level=5.0,
        cognitive_load_reduction_pct=37.5,
        lab_size_kb=250.0,
        generation_time_sec=1.8
    )
    assert metrics.timestamp != ""
    assert "T" in metrics.timestamp
    assert metrics.is_offline_ready is False


def test_lumina_response_full_assembly():
    inp = LessonInput(
        subject="Physics",
        topic="Ohm's Law",
        raw_text="Ohm's law states that current is directly proportional to voltage.",
        student_grade=8,
        language="en"
    )
    decon = DeconstructedConcept(
        original_input=inp,
        core_concept="Relation between V, I, and R",
        target_equation_or_steps="V = I * R",
        cognitive_bottleneck="Resistance inverse scaling",
        baseline_grade_level=8.5,
        simplified_explanation="Think of voltage like water pressure in pipes.",
        key_variables=[
            {"name": "Voltage", "symbol": "V", "unit": "Volt", "min_val": 0.0, "max_val": 220.0, "default_val": 12.0}
        ],
        recommended_engine=EngineType.SLIDER,
        engine_justification="Equation with continuous variables"
    )
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Ohm Lab",
        variables=[
            {"name": "Voltage", "symbol": "V", "unit": "Volt", "min_val": 0.0, "max_val": 220.0, "default_val": 12.0}
        ],
        formula_expression="V = I * R"
    )
    lab = VerifiedMicroLab(
        html_content="<!DOCTYPE html><html><head><title>Ohm Lab</title></head><body><input type='range'></body></html>",
        engine_type=EngineType.SLIDER,
        passed_sandbox_guard=True
    )
    pack = AccessibilityPack(
        adhd_steps=["Step 1", "Step 2", "Step 3"],
        bionic_reading_html="<b>Te</b>st",
        home_experiment={
            "title": "Kitchen Circuit",
            "materials": ["Battery", "Lemon"],
            "steps": ["Step 1", "Step 2"],
            "safety_note": "Careful"
        },
        voice_script="Voice script here"
    )
    metrics = ImpactMetrics(
        baseline_grade_level=8.5,
        simplified_grade_level=4.0,
        cognitive_load_reduction_pct=52.9,
        lab_size_kb=lab.size_kb,
        generation_time_sec=2.1
    )
    response = LuminaResponse(
        lesson_input=inp,
        deconstructed=decon,
        simulation_spec=spec,
        verified_lab=lab,
        accessibility=pack,
        impact=metrics
    )
    dumped = response.model_dump()
    assert isinstance(dumped, dict)
    assert dumped["lesson_input"]["subject"] == "Physics"


def test_lumina_response_json_serializable():
    inp = LessonInput(
        subject="Physics",
        topic="Ohm's Law",
        raw_text="Ohm's law states that current is directly proportional to voltage.",
        student_grade=8,
        language="en"
    )
    decon = DeconstructedConcept(
        original_input=inp,
        core_concept="Relation between V, I, and R",
        target_equation_or_steps="V = I * R",
        cognitive_bottleneck="Resistance inverse scaling",
        baseline_grade_level=8.5,
        simplified_explanation="Think of voltage like water pressure in pipes.",
        key_variables=[
            {"name": "Voltage", "symbol": "V", "unit": "Volt", "min_val": 0.0, "max_val": 220.0, "default_val": 12.0}
        ],
        recommended_engine=EngineType.SLIDER,
        engine_justification="Equation with continuous variables"
    )
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Ohm Lab",
        variables=[
            {"name": "Voltage", "symbol": "V", "unit": "Volt", "min_val": 0.0, "max_val": 220.0, "default_val": 12.0}
        ],
        formula_expression="V = I * R"
    )
    lab = VerifiedMicroLab(
        html_content="<!DOCTYPE html><html><head><title>Ohm Lab</title></head><body><input type='range'></body></html>",
        engine_type=EngineType.SLIDER,
        passed_sandbox_guard=True
    )
    pack = AccessibilityPack(
        adhd_steps=["Step 1", "Step 2", "Step 3"],
        bionic_reading_html="<b>Te</b>st",
        home_experiment={
            "title": "Kitchen Circuit",
            "materials": ["Battery", "Lemon"],
            "steps": ["Step 1", "Step 2"],
            "safety_note": "Careful"
        },
        voice_script="Voice script here"
    )
    metrics = ImpactMetrics(
        baseline_grade_level=8.5,
        simplified_grade_level=4.0,
        cognitive_load_reduction_pct=52.9,
        lab_size_kb=lab.size_kb,
        generation_time_sec=2.1
    )
    response = LuminaResponse(
        lesson_input=inp,
        deconstructed=decon,
        simulation_spec=spec,
        verified_lab=lab,
        accessibility=pack,
        impact=metrics
    )
    json_str = response.model_dump_json()
    assert isinstance(json_str, str)
    assert len(json_str) > 0


# ============================================================================
# Impact Calculator Tests
# ============================================================================

def test_count_syllables_en():
    assert count_syllables_en("hello") == 2
    assert count_syllables_en("world") == 1
    assert count_syllables_en("beautiful") == 3


def test_count_syllables_ar():
    assert count_syllables_ar("مدرسة") >= 2
    assert count_syllables_ar("كتاب") == 2


def test_count_words_en():
    assert count_words("Hello world foo") == 3


def test_count_words_ar():
    assert count_words("مرحبا بالعالم") == 2


def test_count_sentences():
    assert count_sentences("Hello. World! How?") == 3


def test_count_sentences_arabic():
    assert count_sentences("مرحبا بالعالم. كيف حالك؟") == 2


def test_count_sentences_no_punctuation():
    assert count_sentences("Hello world") == 1


def test_grade_level_en_simple():
    text = "The cat sat on the mat. It was a sunny day. The dog ran in the park."
    grade = calculate_grade_level(text, language="en")
    assert 1.0 <= grade <= 5.0


def test_grade_level_en_complex():
    text = (
        "Electrochemical impedance spectroscopy represents a sophisticated non-destructive analytical "
        "methodology utilized extensively for investigating intricate interfacial phenomena occurring "
        "within heterogeneous electrochemical systems."
    )
    grade = calculate_grade_level(text, language="en")
    assert 8.0 <= grade <= 12.0


def test_grade_level_ar_simple():
    text = "أنا أحب أمي وأبي. نحن في بيت جميل. هذا يوم سعيد."
    grade = calculate_grade_level(text, language="ar")
    assert 1.0 <= grade <= 5.0


def test_grade_level_ar_complex():
    text = (
        "تعتبر التفاعلات الكهروكيميائية ظاهرة معقدة تتطلب تحليلاً دقيقاً للمتغيرات الفيزيائية المختلفة، "
        "وتستند هذه التحليلات النظرية والتجريبية إلى مبادئ الديناميكا الحرارية التطبيقية والمعادلات "
        "التفاضلية المتقدمة المرتبطة بالكهرومغناطيسية."
    )
    grade = calculate_grade_level(text, language="ar")
    assert 8.0 <= grade <= 12.0


def test_grade_level_clamped():
    super_simple = "A. B. C."
    grade_low = calculate_grade_level(super_simple, language="en")
    assert grade_low >= 1.0

    super_complex = "Supercalifragilisticexpialidocious " * 30
    grade_high = calculate_grade_level(super_complex, language="en")
    assert grade_high <= 12.0


def test_cognitive_load_reduction():
    assert calculate_cognitive_load_reduction(10.0, 4.0) == 60.0


def test_cognitive_load_reduction_same():
    assert calculate_cognitive_load_reduction(5.0, 5.0) == 0.0


def test_cognitive_load_reduction_zero_baseline():
    assert calculate_cognitive_load_reduction(0.0, 0.0) == 0.0


def test_lab_size_kb():
    content = "a" * 1024
    assert calculate_lab_size_kb(content) == 1.0


def test_lab_size_kb_unicode():
    arabic_text = "مرحبا بالعالم التفاعلي"
    size_kb = calculate_lab_size_kb(arabic_text)
    # in UTF-8, each Arabic char is 2 bytes, so byte length > char length
    assert len(arabic_text.encode("utf-8")) > len(arabic_text)
    assert size_kb == pytest.approx(len(arabic_text.encode("utf-8")) / 1024.0, rel=1e-3)


def test_build_impact_metrics_integration():
    original = (
        "Electrochemical impedance spectroscopy represents a sophisticated non-destructive analytical "
        "methodology utilized extensively for investigating intricate interfacial phenomena occurring "
        "within heterogeneous electrochemical systems."
    )
    simplified = "Batteries make toys run. We can turn them on and off."
    html = "<!DOCTYPE html><html><body><h1>Lab</h1></body></html>"

    metrics = build_impact_metrics(
        original_text=original,
        simplified_text=simplified,
        html_content=html,
        language="en",
        generation_time_sec=3.2
    )
    assert isinstance(metrics, ImpactMetrics)
    assert metrics.baseline_grade_level > metrics.simplified_grade_level
    assert metrics.grade_reduction > 0.0
    assert metrics.cognitive_load_reduction_pct > 0.0
    assert metrics.is_offline_ready is True
    assert metrics.generation_time_sec == 3.2


def test_simulation_spec_result_bounds_contract():
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Chemistry Buffer Lab",
        variables=[
            {"name": "pKa", "symbol": "pKa", "unit": "", "min_val": 1.0, "max_val": 14.0, "default_val": 4.76},
            {"name": "Acid", "symbol": "HA", "unit": "M", "min_val": 0.01, "max_val": 1.0, "default_val": 0.1}
        ],
        formula_expression="pH = pKa + log10(0.1 / HA)",
        result_symbol="pH",
        result_min=0.0,
        result_max=14.0,
        is_logarithmic_output=False
    )
    assert spec.result_symbol == "pH"
    assert spec.result_min == 0.0
    assert spec.result_max == 14.0
    assert spec.is_logarithmic_output is False

    # Test auto-healing when result_max <= result_min
    invalid_bounds_spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Healed Bounds Lab",
        variables=[
            {"name": "x", "symbol": "x", "unit": "m", "min_val": 0.0, "max_val": 10.0, "default_val": 5.0}
        ],
        formula_expression="y = 2 * x",
        result_min=10.0,
        result_max=5.0
    )
    assert invalid_bounds_spec.result_max > invalid_bounds_spec.result_min
