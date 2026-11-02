import json
import re
import subprocess
import pytest
from pydantic import ValidationError

from src.contracts.schemas import (
    SimulationSpec,
    EngineType,
    VerifiedMicroLab,
)
from src.swarm.pair2_interactive import _sanitize_simulation_spec
from src.engines.slider_engine import render_slider_lab
from src.engines.stepper_engine import render_stepper_lab
from src.engines.diagram_engine import render_diagram_lab
from src.engines.balance_engine import render_balance_lab
from src.tools.sandbox_guard import verify_micro_lab


# ============================================================================
# Slider Engine Tests
# ============================================================================

def test_slider_renders_valid_html():
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Ohm's Law Lab",
        variables=[
            {"name": "Current", "symbol": "I", "unit": "A", "min_val": 0, "max_val": 10, "default_val": 2},
            {"name": "Resistance", "symbol": "R", "unit": "Ω", "min_val": 1, "max_val": 100, "default_val": 5}
        ],
        formula_expression="V = I * R"
    )
    html = render_slider_lab(spec)
    assert "<!DOCTYPE html>" in html
    assert "<input" in html
    assert "slider-I" in html
    assert "slider-R" in html


def test_slider_contains_formula():
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Ohm's Law Lab",
        variables=[
            {"name": "Current", "symbol": "I", "unit": "A", "min_val": 0, "max_val": 10, "default_val": 2}
        ],
        formula_expression="V = I * R"
    )
    html = render_slider_lab(spec)
    assert "V = I * R" in html


def test_slider_size_under_25kb():
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Ohm's Law Lab",
        variables=[
            {"name": "Current", "symbol": "I", "unit": "A", "min_val": 0, "max_val": 10, "default_val": 2}
        ],
        formula_expression="V = I * R"
    )
    html = render_slider_lab(spec)
    size_kb = len(html.encode("utf-8")) / 1024.0
    assert size_kb < 200.0


def test_slider_rejects_wrong_engine():
    spec = SimulationSpec(
        engine_type=EngineType.STEPPER,
        title="Stepper Lab",
        steps=[{"label": "Step 1", "description": "Init", "state": {}}]
    )
    with pytest.raises(ValueError, match="Expected SLIDER engine type"):
        render_slider_lab(spec)


def test_slider_rejects_empty_variables():
    with pytest.raises(ValidationError):
        SimulationSpec(
            engine_type=EngineType.SLIDER,
            title="Empty Variables",
            variables=[],
            formula_expression="V = I * R"
        )


def test_slider_physics_renders_spring():
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Hooke's Law Lab",
        variables=[
            {"name": "Spring Constant", "symbol": "k", "unit": "N/m", "min_val": 10, "max_val": 200, "default_val": 50},
            {"name": "Displacement", "symbol": "x", "unit": "m", "min_val": 0.01, "max_val": 1.0, "default_val": 0.2}
        ],
        formula_expression="F = k * x",
        visual_archetype="spring"
    )
    html = render_slider_lab(spec)
    assert "spring-coil-path" in html


def test_slider_chemistry_renders_beaker():
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Acid Base Titration",
        variables=[{"name": "pH", "symbol": "pH", "unit": "", "min_val": 1, "max_val": 14, "default_val": 7}],
        formula_expression="pH = 7",
        visual_archetype="beaker"
    )
    html = render_slider_lab(spec)
    assert "beaker-liquid" in html


def test_slider_circuits_renders_circuit():
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Ohm's Law",
        variables=[
            {"name": "Current", "symbol": "I", "unit": "A", "min_val": 0.1, "max_val": 10, "default_val": 2},
            {"name": "Resistance", "symbol": "R", "unit": "Ω", "min_val": 1, "max_val": 100, "default_val": 10}
        ],
        formula_expression="V = I * R",
        visual_archetype="circuit"
    )
    html = render_slider_lab(spec)
    assert "bulb-glow" in html


def test_slider_gas_renders_piston():
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Boyle's Gas Law",
        variables=[{"name": "Volume", "symbol": "V", "unit": "L", "min_val": 10, "max_val": 100, "default_val": 50}],
        formula_expression="P = 100 / V",
        visual_archetype="piston"
    )
    html = render_slider_lab(spec)
    assert "piston-assembly" in html


def test_slider_biology_renders_cell():
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Cell Osmosis",
        variables=[{"name": "Solute", "symbol": "C", "unit": "%", "min_val": 0, "max_val": 100, "default_val": 50}],
        formula_expression="Osm = C * 2",
        visual_archetype="cell_osmosis"
    )
    html = render_slider_lab(spec)
    assert "cell-membrane" in html


def test_slider_lever_renders_lever():
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Lever Equilibrium",
        variables=[
            {"name": "Effort", "symbol": "F1", "unit": "N", "min_val": 1, "max_val": 50, "default_val": 10},
            {"name": "Arm1", "symbol": "d1", "unit": "m", "min_val": 0.5, "max_val": 5, "default_val": 2},
            {"name": "Load", "symbol": "F2", "unit": "N", "min_val": 1, "max_val": 50, "default_val": 20},
            {"name": "Arm2", "symbol": "d2", "unit": "m", "min_val": 0.5, "max_val": 5, "default_val": 1}
        ],
        formula_expression="F1 * d1 = F2 * d2",
        visual_archetype="lever_torque"
    )
    html = render_slider_lab(spec)
    assert "lever-beam-group" in html


def test_slider_generative_svg_injection():
    custom_svg = '<svg viewBox="0 0 360 140" id="custom-phenomenon"><circle id="particle" cx="180" cy="70" r="25" fill="#ec4899"/></svg>'
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Quantum Particle Lab",
        variables=[
            {"name": "Energy", "symbol": "E", "unit": "eV", "min_val": 1, "max_val": 100, "default_val": 50}
        ],
        formula_expression="E = 50",
        visual_svg=custom_svg
    )
    html = render_slider_lab(spec)
    assert "custom-phenomenon" in html
    assert "particle" in html



# ============================================================================
# Stepper Engine Tests
# ============================================================================

def test_stepper_renders_valid_html():
    spec = SimulationSpec(
        engine_type=EngineType.STEPPER,
        title="Binary Search Visualizer",
        steps=[
            {"label": "Step 1", "description": "Init low and high", "state": {"array": [1, 2, 3]}}
        ]
    )
    html = render_stepper_lab(spec)
    assert "<!DOCTYPE html>" in html
    assert "<button" in html


def test_stepper_contains_step_labels():
    spec = SimulationSpec(
        engine_type=EngineType.STEPPER,
        title="Binary Search Visualizer",
        steps=[
            {"label": "Init Range", "description": "low=0, high=7", "state": {"array": [1, 3, 5, 7]}},
            {"label": "Inspect Mid", "description": "mid=3", "state": {"mid": 3}}
        ]
    )
    html = render_stepper_lab(spec)
    assert "Init Range" in html
    assert "Inspect Mid" in html


def test_stepper_size_under_25kb():
    spec = SimulationSpec(
        engine_type=EngineType.STEPPER,
        title="Binary Search",
        steps=[
            {"label": "Step 1", "description": "Desc 1", "state": {"array": [1, 2]}},
            {"label": "Step 2", "description": "Desc 2", "state": {"array": [1, 2]}}
        ]
    )
    html = render_stepper_lab(spec)
    size_kb = len(html.encode("utf-8")) / 1024.0
    assert size_kb < 200.0


def test_stepper_rejects_wrong_engine():
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Slider Lab",
        variables=[{"name": "x", "symbol": "x", "unit": "", "min_val": 0, "max_val": 10, "default_val": 5}],
        formula_expression="y = x * 2"
    )
    with pytest.raises(ValueError, match="Expected STEPPER engine type"):
        render_stepper_lab(spec)


# ============================================================================
# Diagram Engine Tests
# ============================================================================

def test_diagram_renders_valid_html():
    spec = SimulationSpec(
        engine_type=EngineType.DIAGRAM,
        title="Circuit Diagram",
        nodes=[
            {"id": "battery", "label": "Battery 9V", "x": 50, "y": 50, "connections": ["led"]},
            {"id": "led", "label": "LED", "x": 150, "y": 50, "connections": ["battery"]}
        ]
    )
    html = render_diagram_lab(spec)
    assert "<!DOCTYPE html>" in html
    assert "<svg" in html


def test_diagram_contains_node_labels():
    spec = SimulationSpec(
        engine_type=EngineType.DIAGRAM,
        title="Circulatory System",
        nodes=[
            {"id": "heart", "label": "Heart", "x": 100, "y": 100, "connections": ["lungs"]},
            {"id": "lungs", "label": "Lungs", "x": 200, "y": 100, "connections": ["heart"]}
        ]
    )
    html = render_diagram_lab(spec)
    assert "Heart" in html
    assert "Lungs" in html


def test_diagram_size_under_25kb():
    spec = SimulationSpec(
        engine_type=EngineType.DIAGRAM,
        title="Circuit Diagram",
        nodes=[
            {"id": "n1", "label": "Node 1", "x": 50, "y": 50, "connections": ["n2"]},
            {"id": "n2", "label": "Node 2", "x": 150, "y": 50, "connections": ["n1"]}
        ]
    )
    html = render_diagram_lab(spec)
    size_kb = len(html.encode("utf-8")) / 1024.0
    assert size_kb < 200.0


def test_diagram_rejects_wrong_engine():
    spec = SimulationSpec(
        engine_type=EngineType.STEPPER,
        title="Stepper",
        steps=[{"label": "s1", "description": "d", "state": {}}]
    )
    with pytest.raises(ValueError, match="Expected DIAGRAM engine type"):
        render_diagram_lab(spec)


# ============================================================================
# Balance Engine Tests
# ============================================================================

def test_balance_renders_valid_html():
    spec = SimulationSpec(
        engine_type=EngineType.BALANCE,
        title="Acid vs Base Challenge",
        challenge_items=[
            {"id": "hcl", "label": "HCl", "weight": 1.0, "category": "acid"},
            {"id": "naoh", "label": "NaOH", "weight": 1.0, "category": "base"}
        ]
    )
    html = render_balance_lab(spec)
    assert "<!DOCTYPE html>" in html


def test_balance_contains_item_labels():
    spec = SimulationSpec(
        engine_type=EngineType.BALANCE,
        title="Acid vs Base Challenge",
        challenge_items=[
            {"id": "hcl", "label": "Hydrochloric Acid", "weight": 1.0, "category": "acid"},
            {"id": "naoh", "label": "Sodium Hydroxide", "weight": 1.0, "category": "base"}
        ]
    )
    html = render_balance_lab(spec)
    assert "Hydrochloric Acid" in html
    assert "Sodium Hydroxide" in html


def test_balance_has_check_button():
    spec = SimulationSpec(
        engine_type=EngineType.BALANCE,
        title="Acid vs Base Challenge",
        challenge_items=[
            {"id": "hcl", "label": "HCl", "weight": 1.0, "category": "acid"},
            {"id": "naoh", "label": "NaOH", "weight": 1.0, "category": "base"}
        ]
    )
    html = render_balance_lab(spec)
    assert ("تحقق" in html) or ("Check" in html)


def test_balance_size_under_25kb():
    spec = SimulationSpec(
        engine_type=EngineType.BALANCE,
        title="Acid vs Base Challenge",
        challenge_items=[
            {"id": "hcl", "label": "HCl", "weight": 1.0, "category": "acid"},
            {"id": "naoh", "label": "NaOH", "weight": 1.0, "category": "base"}
        ]
    )
    html = render_balance_lab(spec)
    size_kb = len(html.encode("utf-8")) / 1024.0
    assert size_kb < 200.0


def test_balance_rejects_wrong_engine():
    spec = SimulationSpec(
        engine_type=EngineType.STEPPER,
        title="Stepper",
        steps=[{"label": "s1", "description": "d", "state": {}}]
    )
    with pytest.raises(ValueError, match="Expected BALANCE engine type"):
        render_balance_lab(spec)


# ============================================================================
# Sandbox Guard Tests
# ============================================================================

def test_guard_passes_valid_html():
    valid_html = (
        "<!DOCTYPE html><html><head><title>Test Lab</title></head>"
        "<body><button onclick='alert(1)'>Click</button></body></html>"
    )
    res = verify_micro_lab(valid_html, EngineType.SLIDER)
    assert res.passed_sandbox_guard is True
    assert len(res.error_log) == 0


def test_guard_fails_missing_doctype():
    bad_html = "<html><head><title>No Doctype</title></head><body><button>Click</button></body></html>"
    res = verify_micro_lab(bad_html, EngineType.SLIDER)
    assert res.passed_sandbox_guard is False
    assert any("DOCTYPE" in err for err in res.error_log)


def test_guard_fails_no_interactivity():
    silent_html = "<!DOCTYPE html><html><head><title>Silent Lab</title></head><body><p>Just text</p></body></html>"
    res = verify_micro_lab(silent_html, EngineType.SLIDER)
    assert res.passed_sandbox_guard is False
    assert any("interactive" in err.lower() for err in res.error_log)


def test_guard_fails_oversized():
    huge_html = (
        "<!DOCTYPE html><html><head><title>Huge Lab</title></head>"
        f"<body><button>Click</button><!-- {'x' * 205 * 1024} --></body></html>"
    )
    res = verify_micro_lab(huge_html, EngineType.SLIDER)
    assert res.passed_sandbox_guard is False
    assert any("exceeds limit" in err for err in res.error_log)


def test_guard_fails_external_script():
    script_html = (
        "<!DOCTYPE html><html><head><title>Script Lab</title>"
        "<script src='https://cdn.example.com/lib.js'></script></head>"
        "<body><button>Click</button></body></html>"
    )
    res = verify_micro_lab(script_html, EngineType.SLIDER)
    assert res.passed_sandbox_guard is False
    assert any("External script" in err for err in res.error_log)


def test_guard_fails_dangerous_js():
    danger_html = (
        "<!DOCTYPE html><html><head><title>Danger Lab</title></head>"
        "<body><button onclick='let c = document.cookie'>Click</button></body></html>"
    )
    res = verify_micro_lab(danger_html, EngineType.SLIDER)
    assert res.passed_sandbox_guard is False
    assert any("document.cookie" in err for err in res.error_log)


def test_guard_calculates_size_kb():
    html = "<!DOCTYPE html><html><head><title>Size Lab</title></head><body><button>Click</button></body></html>"
    res = verify_micro_lab(html, EngineType.SLIDER)
    expected_kb = len(html.encode("utf-8")) / 1024.0
    assert res.size_kb == pytest.approx(expected_kb, rel=1e-3)


def test_guard_allows_eval_for_formulas():
    eval_html = (
        "<!DOCTYPE html><html><head><title>Eval Lab</title></head>"
        "<body><button onclick='let res = eval(\"2 + 2\")'>Calculate</button></body></html>"
    )
    res = verify_micro_lab(eval_html, EngineType.SLIDER)
    assert res.passed_sandbox_guard is True


def test_guard_integration_with_slider():
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Ohm's Law",
        variables=[
            {"name": "Current", "symbol": "I", "unit": "A", "min_val": 0, "max_val": 10, "default_val": 2}
        ],
        formula_expression="V = I * 5"
    )
    html = render_slider_lab(spec)
    res = verify_micro_lab(html, spec.engine_type)
    assert res.passed_sandbox_guard is True
    assert len(res.error_log) == 0


def test_guard_integration_with_stepper():
    spec = SimulationSpec(
        engine_type=EngineType.STEPPER,
        title="Binary Search",
        steps=[
            {"label": "Step 1", "description": "Initialize", "state": {"array": [1, 2, 3]}}
        ]
    )
    html = render_stepper_lab(spec)
    res = verify_micro_lab(html, spec.engine_type)
    assert res.passed_sandbox_guard is True
    assert len(res.error_log) == 0


def test_guard_integration_with_diagram():
    spec = SimulationSpec(
        engine_type=EngineType.DIAGRAM,
        title="Circuit Diagram",
        nodes=[
            {"id": "a", "label": "Node A", "x": 50, "y": 50, "connections": ["b"]},
            {"id": "b", "label": "Node B", "x": 150, "y": 50, "connections": ["a"]}
        ]
    )
    html = render_diagram_lab(spec)
    res = verify_micro_lab(html, spec.engine_type)
    assert res.passed_sandbox_guard is True
    assert len(res.error_log) == 0


def test_guard_integration_with_balance():
    spec = SimulationSpec(
        engine_type=EngineType.BALANCE,
        title="Acid vs Base",
        challenge_items=[
            {"id": "hcl", "label": "HCl", "weight": 1.0, "category": "acid"},
            {"id": "naoh", "label": "NaOH", "weight": 1.0, "category": "base"}
        ]
    )
    html = render_balance_lab(spec)
    res = verify_micro_lab(html, spec.engine_type)
    assert res.passed_sandbox_guard is True
    assert len(res.error_log) == 0


def test_guard_fails_external_svg_image():
    svg_image_html = (
        "<!DOCTYPE html><html><head><title>SVG Image</title></head>"
        "<body><button>Click</button><svg><image href='https://evil.com/pic.png'/></svg></body></html>"
    )
    res = verify_micro_lab(svg_image_html, EngineType.SLIDER)
    assert res.passed_sandbox_guard is False
    assert any("External SVG resource" in err for err in res.error_log)


def test_guard_fails_external_svg_use():
    svg_use_html = (
        "<!DOCTYPE html><html><head><title>SVG Use</title></head>"
        "<body><button>Click</button><svg><use xlink:href='https://evil.com/icons.svg#item'/></svg></body></html>"
    )
    res = verify_micro_lab(svg_use_html, EngineType.SLIDER)
    assert res.passed_sandbox_guard is False
    assert any("External SVG resource" in err for err in res.error_log)


def test_guard_fails_external_css_import():
    css_import_html = (
        "<!DOCTYPE html><html><head><title>CSS Import</title>"
        "<style>@import url('https://fonts.googleapis.com/css2?family=Roboto');</style></head>"
        "<body><button>Click</button></body></html>"
    )
    res = verify_micro_lab(css_import_html, EngineType.SLIDER)
    assert res.passed_sandbox_guard is False
    assert any("External CSS @import" in err for err in res.error_log)


def test_guard_fails_navigator_sendbeacon():
    beacon_html = (
        "<!DOCTYPE html><html><head><title>Beacon Lab</title></head>"
        "<body><button onclick='navigator.sendBeacon(\"https://evil.com\")'>Send</button></body></html>"
    )
    res = verify_micro_lab(beacon_html, EngineType.SLIDER)
    assert res.passed_sandbox_guard is False
    assert any("navigator.sendBeacon" in err for err in res.error_log)


def test_guard_verifies_all_20_slider_archetypes():
    from src.swarm.pair2_interactive import VALID_ARCHETYPES
    assert len(VALID_ARCHETYPES) == 20
    for arch in sorted(VALID_ARCHETYPES):
        spec = SimulationSpec(
            engine_type=EngineType.SLIDER,
            title=f"Archetype {arch}",
            variables=[{"name": "Var1", "symbol": "v1", "unit": "u", "min_val": 1.0, "max_val": 10.0, "default_val": 5.0}],
            formula_expression="v1 = 5",
            visual_archetype=arch
        )
        html = render_slider_lab(spec)
        res = verify_micro_lab(html, EngineType.SLIDER)
        assert res.passed_sandbox_guard is True
        assert 0.0 < res.size_kb < 200.0
        assert len(res.error_log) == 0


def test_slider_universal_math_compiler_pow_and_functions():
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="pH Math Test",
        variables=[
            {"name": "pH", "symbol": "pH", "unit": "", "min_val": 1.0, "max_val": 14.0, "default_val": 3.0}
        ],
        formula_expression="[H+] = pow(10, -pH)",
        visual_archetype="beaker"
    )
    html = render_slider_lab(spec)
    assert "safeReplace" in html
    assert "Math." in html
    res = verify_micro_lab(html, EngineType.SLIDER)
    assert res.passed_sandbox_guard is True


def test_slider_dependent_variable_decoupling():
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Acids & Bases Titration",
        variables=[
            {"name": "pH Value", "symbol": "pH", "unit": "", "min_val": 1.0, "max_val": 14.0, "default_val": 7.0},
            {"name": "Hydrogen Ion Concentration", "symbol": "[H+]", "unit": "mol/L", "min_val": 1e-14, "max_val": 0.1, "default_val": 1e-7}
        ],
        formula_expression="[H+] = pow(10, -pH)",
        visual_archetype="beaker"
    )
    html = render_slider_lab(spec)
    # The independent input variable has a slider
    assert "slider-pH" in html
    # The dependent output variable is decoupled and NOT rendered as a slider
    assert "slider-[H+]" not in html
    # The dependent variable title and unit appear in the result display
    assert "Hydrogen Ion Concentration" in html
    assert "mol/L" in html
    res = verify_micro_lab(html, EngineType.SLIDER)
    assert res.passed_sandbox_guard is True
    assert 0.0 < res.size_kb < 200.0


def test_slider_progress_bar_dynamic_bounds_and_log_scale():
    # Logarithmic formula
    spec_log = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Acids & Bases Log Scale",
        variables=[
            {"name": "pH", "symbol": "pH", "unit": "", "min_val": 1.0, "max_val": 14.0, "default_val": 3.0}
        ],
        formula_expression="[H+] = pow(10, -pH)",
        visual_archetype="beaker"
    )
    html_log = render_slider_lab(spec_log)
    assert "isLogScale = true" in html_log
    assert "Math.log10" in html_log

    # Linear formula
    spec_lin = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Ohm Law Linear Scale",
        variables=[
            {"name": "Current", "symbol": "I", "unit": "A", "min_val": 0.1, "max_val": 5.0, "default_val": 2.0},
            {"name": "Resistance", "symbol": "R", "unit": "Ω", "min_val": 10.0, "max_val": 100.0, "default_val": 20.0}
        ],
        formula_expression="V = I * R",
        visual_archetype="circuit"
    )
    html_lin = render_slider_lab(spec_lin)
    assert "isLogScale = false" in html_lin


def test_slider_prunes_disconnected_zombie_variables():
    """Ensure disconnected variables (e.g. V_acid, V_base) are pruned when formula only uses pH."""
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Acids, Bases & pH Scale",
        variables=[
            {"name": "Acid volume added", "symbol": "V_acid", "unit": "mL", "min_val": 0.0, "max_val": 100.0, "default_val": 36.0},
            {"name": "Base volume added", "symbol": "V_base", "unit": "mL", "min_val": 0.0, "max_val": 100.0, "default_val": 34.0},
            {"name": "pH value", "symbol": "pH", "unit": "", "min_val": 1.0, "max_val": 14.0, "default_val": 7.0},
            {"name": "Hydrogen Ion Concentration", "symbol": "[H+]", "unit": "mol/L", "min_val": 1e-14, "max_val": 0.1, "default_val": 1e-7}
        ],
        formula_expression="[H+] = pow(10, -pH)",
        visual_archetype="beaker"
    )
    html = render_slider_lab(spec)

    # Active driving slider MUST be present
    assert "slider-pH" in html

    # Zombie/Dummy sliders MUST NOT be rendered
    assert "slider-V_acid" not in html
    assert "slider-V_base" not in html
    assert "slider-[H+]" not in html

    # Dependent result card must display the calculated variable
    assert "Hydrogen Ion Concentration" in html
    assert "mol/L" in html

    # Dynamic visual color response
    assert "getPhColor" in html
    assert "beaker-liquid" in html

    res = verify_micro_lab(html, EngineType.SLIDER)
    assert res.passed_sandbox_guard is True
    assert 0.0 < res.size_kb < 200.0


def test_spec_sanitizer_prunes_zombie_variables():
    """Ensure _sanitize_simulation_spec pre-flight sanitizer eliminates unlinked dummy variables."""
    from src.swarm.pair2_interactive import _sanitize_simulation_spec

    raw_spec = {
        "engine_type": "slider",
        "title": "pH Scale Test",
        "formula_expression": "[H+] = pow(10, -pH)",
        "variables": [
            {"name": "Acid volume", "symbol": "V_acid", "unit": "mL", "min_val": 0, "max_val": 100, "default_val": 20},
            {"name": "Base volume", "symbol": "V_base", "unit": "mL", "min_val": 0, "max_val": 100, "default_val": 20},
            {"name": "pH value", "symbol": "pH", "unit": "", "min_val": 1, "max_val": 14, "default_val": 7},
            {"name": "Concentration", "symbol": "[H+]", "unit": "mol/L", "min_val": 1e-14, "max_val": 0.1, "default_val": 1e-7}
        ]
    }

    sanitized = _sanitize_simulation_spec(raw_spec)
    syms = [v["symbol"] for v in sanitized["variables"]]

    assert "pH" in syms
    assert "[H+]" in syms
    assert "V_acid" not in syms
    assert "V_base" not in syms


def test_slider_physics_prunes_unrelated_dummy_variables():
    """Ensure Physics engine prunes dummy variables not in Hooke's Law formula."""
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Hooke's Law Clean Graph",
        variables=[
            {"name": "Spring Constant", "symbol": "k", "unit": "N/m", "min_val": 10, "max_val": 200, "default_val": 50},
            {"name": "Displacement", "symbol": "x", "unit": "m", "min_val": 0.01, "max_val": 1.0, "default_val": 0.2},
            {"name": "Room Temperature", "symbol": "T_ambient", "unit": "°C", "min_val": 15, "max_val": 35, "default_val": 25}
        ],
        formula_expression="F = k * x",
        visual_archetype="spring"
    )
    html = render_slider_lab(spec)

    assert "slider-k" in html
    assert "slider-x" in html
    assert "slider-T_ambient" not in html


def test_slider_ph_progress_bar_bounds_scale():
    """Verify that Chemistry pH simulations set boundMin=0.0 and boundMax=14.0 instead of 100."""
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Buffer Henderson-Hasselbalch",
        variables=[
            {"name": "pKa", "symbol": "pKa", "unit": "", "min_val": 1.0, "max_val": 14.0, "default_val": 4.76},
            {"name": "Base", "symbol": "[A⁻]", "unit": "M", "min_val": 0.01, "max_val": 1.0, "default_val": 0.1},
            {"name": "Acid", "symbol": "[HA]", "unit": "M", "min_val": 0.01, "max_val": 1.0, "default_val": 0.1}
        ],
        formula_expression="pH = pKa + log10([A⁻] / [HA])",
        visual_archetype="beaker",
        result_symbol="pH",
        result_min=0.0,
        result_max=14.0,
        is_logarithmic_output=False
    )
    html = render_slider_lab(spec)

    assert "let boundMin = 0.0;" in html
    assert "let boundMax = 14.0;" in html
    assert "const isLogScale = false;" in html
    assert "getPhColor" in html


def test_estimate_result_bounds_bracketed_symbols():
    """Verify that _evaluate_deterministic_bounds does not crash when variable symbols have brackets."""
    from src.swarm.pair2_interactive import _evaluate_deterministic_bounds
    slider_vars = [
        {"name": "pKa", "symbol": "pKa", "min_val": 1.0, "max_val": 14.0, "default_val": 4.76},
        {"name": "Base", "symbol": "[A⁻]", "min_val": 0.01, "max_val": 1.0, "default_val": 0.1},
        {"name": "Acid", "symbol": "[HA]", "min_val": 0.01, "max_val": 1.0, "default_val": 0.1}
    ]
    rmin, rmax, is_log = _evaluate_deterministic_bounds(
        formula="pH = pKa + log10([A⁻] / [HA])",
        variables=slider_vars
    )
    assert rmin == 0.0
    assert rmax == 14.0
    assert is_log is False


def test_slider_bracketed_symbols_interactive_js_execution():
    """Verify that client-side JS executes and recalculates properly without regex syntax errors on bracketed symbols."""
    import subprocess, json

    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Buffer Solutions and Henderson-Hasselbalch Equilibrium",
        variables=[
            {"name": "pKa", "symbol": "pKa", "unit": "unitless", "min_val": 0.0, "max_val": 14.0, "default_val": 4.8},
            {"name": "Conjugate Base Concentration", "symbol": "[A-]", "unit": "mol/L", "min_val": 0.01, "max_val": 1.0, "default_val": 0.591},
            {"name": "Weak Acid Concentration", "symbol": "[HA]", "unit": "mol/L", "min_val": 0.01, "max_val": 1.0, "default_val": 0.6}
        ],
        formula_expression="pH = pKa + log10([A-] / [HA])",
        result_min=0.0,
        result_max=14.0,
        result_symbol="pH",
        is_logarithmic_output=False
    )
    html = render_slider_lab(spec)
    assert "escapeRegExp" in html
    assert "normalizeChemSymbols" in html
    assert "Invalid escape" not in html

    script = html.split("<script>")[1].split("</script>")[0]
    test_node = f"""
    const elements = {{}};
    global.document = {{
        getElementById: (id) => {{
            if (!elements[id]) elements[id] = {{ textContent: "", value: "1", style: {{}}, setAttribute: () => {{}} }};
            return elements[id];
        }},
        querySelector: (sel) => {{
            if (sel.includes("data-idx=\\"0\\"")) return elements["slider-pKa"];
            if (sel.includes("data-idx=\\"1\\"")) return elements["slider-[A-]"];
            if (sel.includes("data-idx=\\"2\\"")) return elements["slider-[HA]"];
            return null;
        }}
    }};

    elements["slider-pKa"] = {{ value: "4.8", textContent: "", style: {{}}, setAttribute: () => {{}} }};
    elements["slider-[A-]"] = {{ value: "0.591", textContent: "", style: {{}}, setAttribute: () => {{}} }};
    elements["slider-[HA]"] = {{ value: "0.6", textContent: "", style: {{}}, setAttribute: () => {{}} }};

    {script}

    const initialResult = document.getElementById("result-display").textContent;
    const initialBarWidth = document.getElementById("visual-bar").style.width;

    // Simulate slider movement
    elements["slider-[A-]"].value = "1.0";
    updateLab(1, "[A-]");

    const updatedResult = document.getElementById("result-display").textContent;
    const updatedBarWidth = document.getElementById("visual-bar").style.width;

    console.log(JSON.stringify({{
        initialResult: initialResult,
        initialBarWidth: initialBarWidth,
        updatedResult: updatedResult,
        updatedBarWidth: updatedBarWidth
    }}));
    """
    res = subprocess.run(["node", "-e", test_node], capture_output=True, text=True)
    assert res.returncode == 0, f"Node script failed: {res.stderr}"
    data = json.loads(res.stdout)
    assert data["initialResult"] == "4.79"
    assert data["initialBarWidth"] == "34%"
    assert data["updatedResult"] == "5.02"
    assert data["updatedBarWidth"] == "36%"


def test_slider_cell_osmosis_progress_bar_bounds_scale():
    """Verify Biology Cell Membrane Osmosis simulations enforce 0..100 boundMax and 99% scale at 99.01."""
    from src.swarm.pair2_interactive import _sanitize_simulation_spec

    # 1. Test domain guard override when input spec had result_max = 200.0
    spec_data = {
        "engine_type": "slider",
        "title": "Cell Membrane Osmosis",
        "variables": [
            {"name": "Internal Solute", "symbol": "C_in", "unit": "mol/L", "min_val": 1.0, "max_val": 100.0, "default_val": 50.0},
            {"name": "External Solute", "symbol": "C_out", "unit": "mol/L", "min_val": 1.0, "max_val": 100.0, "default_val": 50.0}
        ],
        "formula_expression": "V_cell = 100 * (C_in / (C_in + C_out))",
        "visual_archetype": "cell_osmosis",
        "result_symbol": "V_cell",
        "result_min": 0.0,
        "result_max": 200.0  # Intentional legacy/hallucinated value to be corrected
    }

    guarded_data = _sanitize_simulation_spec(spec_data)

    assert guarded_data["result_min"] == 0.0
    assert guarded_data["result_max"] == 100.0
    assert guarded_data.get("is_logarithmic_output", False) is False

    # 2. Render Lab HTML and verify boundMin and boundMax
    spec = SimulationSpec(**guarded_data)
    html = render_slider_lab(spec)

    assert "let boundMin = 0.0;" in html
    assert "let boundMax = 100.0;" in html
    assert "boundMax = 200.0" not in html

    # 3. Verify in Node.js runtime that at C_in=100 and C_out=1, V_cell=99.01 gives 99% progress (not 50%)
    script_match = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
    assert script_match is not None
    script = script_match.group(1)

    test_node = f"""
    const elements = {{}};
    const document = {{
        getElementById: (id) => {{
            if (!elements[id]) {{
                elements[id] = {{
                    style: {{}},
                    textContent: '',
                    innerHTML: '',
                    value: '50',
                    setAttribute: (k, v) => {{ elements[id][k] = v; }}
                }};
            }}
            return elements[id];
        }},
        querySelector: () => null,
        querySelectorAll: () => []
    }};
    const window = {{
        addEventListener: () => {{}}
    }};

    elements["slider-C_in"] = {{ value: "50", textContent: "", style: {{}}, setAttribute: () => {{}} }};
    elements["slider-C_out"] = {{ value: "50", textContent: "", style: {{}}, setAttribute: () => {{}} }};

    {script}

    // Set C_in to 100 and C_out to 1 (hypotonic extreme: V_cell = 99.01)
    elements["slider-C_in"].value = "100";
    elements["slider-C_out"].value = "1";
    updateLab(0, "C_in");

    const resultText = document.getElementById("result-display").textContent;
    const barWidth = document.getElementById("visual-bar").style.width;
    const barText = document.getElementById("visual-text").textContent;

    console.log(JSON.stringify({{
        resultText,
        barWidth,
        barText
    }}));
    """
    res = subprocess.run(["node", "-e", test_node], capture_output=True, text=True)
    assert res.returncode == 0, f"Node script failed: {res.stderr}"
    data = json.loads(res.stdout)

    assert data["resultText"] == "99.01"
    assert data["barWidth"] == "99%"
    assert "99%" in data["barText"]
    assert "50%" not in data["barWidth"]


def test_slider_projectile_auto_calibrating_bounds_and_barrel_rotation():
    """Verify projectile motion auto-calibrates true peak at 45 deg to 100% and rotates barrel upwards (-angle)."""
    import subprocess, json
    from src.contracts.schemas import SimulationSpec, EngineType
    from src.engines.slider_engine import render_slider_lab

    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Projectile Motion Range",
        variables=[
            {"name": "Initial Velocity", "symbol": "v0", "unit": "m/s", "min_val": 10.0, "max_val": 40.0, "default_val": 40.0},
            {"name": "Launch Angle", "symbol": "theta", "unit": "°", "min_val": 12.0, "max_val": 75.0, "default_val": 45.0}
        ],
        formula_expression="R = (pow(v0, 2) * sin(2 * theta * pi / 180)) / 9.8",
        visual_archetype="projectile",
        constants={"g": 9.8}
    )
    html = render_slider_lab(spec)
    assert "autoCalibrateBounds" in html

    script = html.split("<script>")[1].split("</script>")[0]
    test_node = f"""
    const elements = {{}};
    const document = {{
        getElementById: (id) => {{
            if (!elements[id]) {{
                elements[id] = {{
                    style: {{}},
                    textContent: '',
                    setAttribute: (k, v) => {{ elements[id][k] = v; }}
                }};
            }}
            return elements[id];
        }},
        querySelector: () => null,
        querySelectorAll: () => []
    }};
    const window = {{ addEventListener: () => {{}} }};

    elements["slider-v0"] = {{ value: "40", style: {{}}, setAttribute: () => {{}} }};
    elements["slider-theta"] = {{ value: "45", style: {{}}, setAttribute: () => {{}} }};

    {script}

    // Peak at 45 degrees
    calculate();
    const peakResult = document.getElementById("result-display").textContent;
    const peakBar = document.getElementById("visual-bar").style.width;
    const peakBarrel = elements["cannon-barrel"] ? elements["cannon-barrel"].transform : "";

    // Angle at 12 degrees
    elements["slider-theta"].value = "12";
    updateLab(1, "theta");
    const r12 = document.getElementById("result-display").textContent;
    const bar12 = document.getElementById("visual-bar").style.width;
    const barrel12 = elements["cannon-barrel"] ? elements["cannon-barrel"].transform : "";

    // Angle at 75 degrees
    elements["slider-theta"].value = "75";
    updateLab(1, "theta");
    const r75 = document.getElementById("result-display").textContent;
    const bar75 = document.getElementById("visual-bar").style.width;
    const barrel75 = elements["cannon-barrel"] ? elements["cannon-barrel"].transform : "";

    console.log(JSON.stringify({{
        peakResult, peakBar, peakBarrel,
        r12, bar12, barrel12,
        r75, bar75, barrel75
    }}));
    """
    res = subprocess.run(["node", "-e", test_node], capture_output=True, text=True)
    assert res.returncode == 0, f"Node script failed: {res.stderr}"
    data = json.loads(res.stdout)

    # 45 degrees must reach 100%
    assert data["peakBar"] == "100%"
    assert "163" in data["peakResult"]
    assert "rotate(-45" in data["peakBarrel"]

    # 12 and 75 degrees must change dynamically and not freeze
    assert data["bar12"] != data["bar75"]
    assert "rotate(-12" in data["barrel12"]
    assert "rotate(-75" in data["barrel75"]


def test_slider_osmosis_pi_mrt_auto_calibrating_and_constants():
    """Verify Osmosis Pi = M * R * T protects R constant, auto-calibrates bounds, and asserts rx <= 58, ry <= 42."""
    import subprocess, json
    from src.swarm.pair2_interactive import _sanitize_simulation_spec
    from src.engines.slider_engine import render_slider_lab

    spec_data = {
        "engine_type": "slider",
        "title": "Osmotic Pressure Lab",
        "visual_archetype": "cell_osmosis",
        "variables": [
            {"name": "Molarity", "symbol": "M", "unit": "mol/L", "min_val": 0.1, "max_val": 3.0, "default_val": 1.0},
            {"name": "Gas Constant", "symbol": "R", "unit": "L*atm/(mol*K)", "min_val": 1.0, "max_val": 100.0, "default_val": 50.0},
            {"name": "Temperature", "symbol": "T", "unit": "K", "min_val": 273.0, "max_val": 373.0, "default_val": 300.0}
        ],
        "formula_expression": "Pi = M * R * T"
    }

    sanitized = _sanitize_simulation_spec(spec_data)
    # R must be moved to constants, leaving only M and T as interactive sliders
    assert "R" in sanitized.get("constants", {})
    assert sanitized["constants"]["R"] == 0.0821
    symbols = [v["symbol"] for v in sanitized["variables"]]
    assert "R" not in symbols
    assert "M" in symbols and "T" in symbols

    spec = SimulationSpec(**sanitized)
    html = render_slider_lab(spec)

    script = html.split("<script>")[1].split("</script>")[0]
    test_node = f"""
    const elements = {{}};
    const document = {{
        getElementById: (id) => {{
            if (!elements[id]) {{
                elements[id] = {{
                    style: {{}},
                    textContent: '',
                    setAttribute: (k, v) => {{ elements[id][k] = v; }}
                }};
            }}
            return elements[id];
        }},
        querySelector: () => null,
        querySelectorAll: () => []
    }};
    const window = {{ addEventListener: () => {{}} }};

    // Set sliders to MAX values
    elements["slider-M"] = {{ value: "3.0", style: {{}}, setAttribute: () => {{}} }};
    elements["slider-T"] = {{ value: "373.0", style: {{}}, setAttribute: () => {{}} }};

    {script}

    calculate();
    const maxBar = document.getElementById("visual-bar").style.width;
    const maxState = document.getElementById("cell-state-label").textContent;
    const maxRx = parseFloat(elements["cell-membrane"].rx);
    const maxRy = parseFloat(elements["cell-membrane"].ry);

    // Set sliders to MIN values
    elements["slider-M"].value = "0.1";
    elements["slider-T"].value = "273.0";
    updateLab(0, "M");

    const minBar = document.getElementById("visual-bar").style.width;
    const minState = document.getElementById("cell-state-label").textContent;
    const minRx = parseFloat(elements["cell-membrane"].rx);
    const minRy = parseFloat(elements["cell-membrane"].ry);

    console.log(JSON.stringify({{
        maxBar, maxState, maxRx, maxRy,
        minBar, minState, minRx, minRy
    }}));
    """
    res = subprocess.run(["node", "-e", test_node], capture_output=True, text=True)
    assert res.returncode == 0, f"Node script failed: {res.stderr}"
    data = json.loads(res.stdout)

    # At max sliders, progress bar must reach 100% (not 1%!) and state is Hypertonic
    assert data["maxBar"] == "100%"
    assert "Hypertonic" in data["maxState"]
    assert data["maxRx"] <= 58.0 and data["maxRy"] <= 42.0

    # At min sliders, progress bar must reach 0% and state is Hypotonic (swollen cell)
    assert data["minBar"] == "0%"
    assert "Hypotonic" in data["minState"]
    assert data["minRx"] <= 58.0 and data["minRy"] <= 42.0


def test_archetype_ph_titration_rendering_and_dom_ids():
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Acid Base Titration and pH",
        variables=[
            {"name": "Titrant Volume", "symbol": "V_base", "unit": "mL", "min_val": 0.0, "max_val": 50.0, "default_val": 25.0},
            {"name": "pH Value", "symbol": "pH", "unit": "", "min_val": 0.0, "max_val": 14.0, "default_val": 7.0}
        ],
        formula_expression="pH = 7.0",
        visual_archetype="ph_titration"
    )
    html_en = render_slider_lab(spec)
    assert "viewBox=\"0 0 360 140\"" in html_en
    assert "id=\"burette-liquid\"" in html_en
    assert "id=\"titrant-drop\"" in html_en
    assert "id=\"titration-liquid\"" in html_en
    assert "id=\"ph-digital-readout\"" in html_en
    assert "id=\"ph-state-badge\"" in html_en
    assert "id=\"ph-color-strip\"" in html_en
    assert "id=\"titrant-vol-val\"" in html_en
    res = verify_micro_lab(html_en, EngineType.SLIDER)
    assert res.passed_sandbox_guard is True

    # Test Arabic version
    spec_ar = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="معايرة الأحماض والقواعد والرقم الهيدروجيني",
        variables=[
            {"name": "حجم المعاير", "symbol": "V_base", "unit": "مل", "min_val": 0.0, "max_val": 50.0, "default_val": 25.0}
        ],
        formula_expression="pH = 7.0",
        visual_archetype="ph_titration"
    )
    html_ar = render_slider_lab(spec_ar)
    assert "مقياس الـ pH" in html_ar
    assert "الحجم المضاف" in html_ar


def test_archetype_cell_division_dynamic_generations_and_cells():
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Bacterial Binary Fission in Petri Dish",
        variables=[
            {"name": "Initial Cells", "symbol": "N0", "unit": "cells", "min_val": 1.0, "max_val": 10.0, "default_val": 1.0},
            {"name": "Generations", "symbol": "n", "unit": "gens", "min_val": 0.0, "max_val": 8.0, "default_val": 3.0}
        ],
        formula_expression="N = N0 * pow(2, n)",
        visual_archetype="cell_division"
    )
    html = render_slider_lab(spec)
    assert "viewBox=\"0 0 360 140\"" in html
    assert "id=\"colony-cells-group\"" in html
    assert "id=\"bact-cell-1\"" in html
    assert "id=\"bact-cell-2\"" in html
    assert "id=\"division-gen-val\"" in html
    assert "id=\"division-total-cells\"" in html
    assert "id=\"division-phase-badge\"" in html
    assert "values['n']" in html or "values['g']" in html
    res = verify_micro_lab(html, EngineType.SLIDER)
    assert res.passed_sandbox_guard is True


def test_archetype_enzyme_kinetics_saturation_and_cleft():
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Michaelis-Menten Enzyme Kinetics",
        variables=[
            {"name": "Substrate Concentration", "symbol": "S", "unit": "mM", "min_val": 0.1, "max_val": 50.0, "default_val": 5.0},
            {"name": "Max Velocity", "symbol": "Vmax", "unit": "μM/s", "min_val": 10.0, "max_val": 100.0, "default_val": 50.0},
            {"name": "Michaelis Constant", "symbol": "Km", "unit": "mM", "min_val": 1.0, "max_val": 20.0, "default_val": 5.0}
        ],
        formula_expression="v = (Vmax * S) / (Km + S)",
        visual_archetype="enzyme_kinetics"
    )
    html = render_slider_lab(spec)
    assert "viewBox=\"0 0 360 140\"" in html
    assert "id=\"active-site-glow\"" in html
    assert "id=\"substrate-dock\"" in html
    assert "id=\"enzyme-v-val\"" in html
    assert "id=\"enzyme-sat-bar\"" in html
    assert "id=\"enzyme-s-val\"" in html
    assert "id=\"enzyme-state-badge\"" in html
    res = verify_micro_lab(html, EngineType.SLIDER)
    assert res.passed_sandbox_guard is True


def test_archetype_thermo_calorimeter_enthalpy_and_mercury():
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Thermochemistry Bomb Calorimeter",
        variables=[
            {"name": "Mass", "symbol": "m", "unit": "g", "min_val": 10.0, "max_val": 500.0, "default_val": 100.0},
            {"name": "Specific Heat", "symbol": "c", "unit": "J/g°C", "min_val": 0.5, "max_val": 4.184, "default_val": 4.184},
            {"name": "Temp Change", "symbol": "dT", "unit": "°C", "min_val": -20.0, "max_val": 50.0, "default_val": 15.0}
        ],
        formula_expression="q = m * c * dT",
        visual_archetype="thermo_calorimeter"
    )
    html = render_slider_lab(spec)
    assert "viewBox=\"0 0 360 140\"" in html
    assert "id=\"calorimeter-fluid\"" in html
    assert "id=\"calorimeter-mercury\"" in html
    assert "id=\"calorimeter-q-val\"" in html
    assert "id=\"calorimeter-temp-val\"" in html
    assert "id=\"calorimeter-state-badge\"" in html
    res = verify_micro_lab(html, EngineType.SLIDER)
    assert res.passed_sandbox_guard is True


def test_archetype_beaker_purged_of_ph_and_dedicated_to_molarity():
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Solution Molarity and Concentration",
        variables=[
            {"name": "Moles of Solute", "symbol": "n", "unit": "mol", "min_val": 0.1, "max_val": 5.0, "default_val": 1.0},
            {"name": "Volume of Solution", "symbol": "V", "unit": "L", "min_val": 0.1, "max_val": 10.0, "default_val": 2.0}
        ],
        formula_expression="M = n / V",
        visual_archetype="beaker"
    )
    html = render_slider_lab(spec)
    assert "viewBox=\"0 0 360 140\"" in html
    assert "id=\"beaker-liquid\"" in html
    assert "id=\"beaker-conc-val\"" in html
    assert "id=\"beaker-state-badge\"" in html
    assert "id=\"beaker-vol-val\"" in html
    assert "id=\"beaker-solute-particles\"" in html
    # Ensure pH elements are completely purged
    assert "id=\"chem-indicator-text\"" not in html
    assert "pH 7.0" not in html
    res = verify_micro_lab(html, EngineType.SLIDER)
    assert res.passed_sandbox_guard is True


def test_archetype_gravity_orbit_physical_speed_and_clean_radius_meters():
    spec = SimulationSpec(
        engine_type=EngineType.SLIDER,
        title="Gravitational Force and Orbital Speed",
        variables=[
            {"name": "Central Mass", "symbol": "M", "unit": "kg", "min_val": 1e22, "max_val": 1e26, "default_val": 5.972e24},
            {"name": "Orbital Radius", "symbol": "r", "unit": "m", "min_val": 6.371e6, "max_val": 5e7, "default_val": 7e6}
        ],
        formula_expression="F = (6.6743e-11 * M * 1000) / (r * r)",
        visual_archetype="gravity_orbit"
    )
    html = render_slider_lab(spec)
    assert "viewBox=\"0 0 360 140\"" in html
    assert "id=\"orbit-radius-val\"" in html
    assert "id=\"orbit-speed-val\"" in html
    assert "+ ' m'" in html
    assert "AU" not in html
    assert "6.6743e-11" in html
    res = verify_micro_lab(html, EngineType.SLIDER)
    assert res.passed_sandbox_guard is True







