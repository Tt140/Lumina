"""LuminaLab Swarm - Pair 2: Interactive Simulation Math & Quality Guard."""

import json
import re
import math
import itertools
from typing import Any
from strands import Agent, tool
from src.contracts.schemas import (
    DeconstructedConcept,
    SimulationSpec,
    VerifiedMicroLab,
    EngineType,
)
from src.swarm.pedagogical_calibration import parse_student_grade, get_pedagogical_directive
from src.swarm.terminal_stream import get_hackathon_callback_handler

# Complete Physics and Science Constants Registry
MATH_PHYSICS_CONSTANTS: dict[str, float] = {
    "G": 6.67430e-11,
    "g": 9.80665,
    "c": 299792458.0,
    "h": 6.62607015e-34,
    "hbar": 1.054571817e-34,
    "e": 1.602176634e-19,
    "k_e": 8.9875517923e9,
    "m_e": 9.1093837015e-31,
    "m_p": 1.67262192369e-27,
    "N_A": 6.02214076e23,
    "R": 8.314462618,
    "k_B": 1.380649e-23,
    "sigma": 5.670374419e-8,
    "epsilon_0": 8.8541878128e-12,
    "mu_0": 1.25663706212e-6,
    "F": 96485.33212,
    "pi": math.pi,
    "PI": math.pi,
    "h_rise": 3.4,
    "pitch": 34.0,
}

GREEK_MAP: dict[str, str] = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "Δ": "delta", "ε": "epsilon",
    "η": "eta", "θ": "theta", "Θ": "theta", "λ": "lambda", "μ": "mu", "ν": "nu",
    "π": "pi", "Π": "pi", "ρ": "rho", "σ": "sigma", "Σ": "sigma", "τ": "tau",
    "φ": "phi", "Φ": "phi", "ψ": "psi", "ω": "omega", "Ω": "omega",
}

SUPERSCRIPT_MAP: dict[str, str] = {
    "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
    "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
    "⁺": "+", "⁻": "-",
}


def _normalize_greek_math(text: str) -> str:
    """Stage 2: Transpiles Greek Unicode characters into ASCII math symbols."""
    if not text:
        return ""
    result = text
    for greek_char, ascii_name in GREEK_MAP.items():
        if greek_char in result:
            result = result.replace(greek_char, ascii_name)
    return result


def _transpile_superscripts(text: str) -> str:
    """Stage 3: Transpiles Unicode superscripts (e.g. r⁴, 10⁻⁵) into standard power notation (**N)."""
    if not text:
        return ""
    pattern = r"([a-zA-Z0-9_\.]+|(?:\([^\)]+\)))\s*([⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]+)"

    def _replace_super(match):
        base = match.group(1)
        supers = match.group(2)
        power_str = "".join(SUPERSCRIPT_MAP.get(c, c) for c in supers)
        return f"({base} ** ({power_str}))"

    result = re.sub(pattern, _replace_super, text)
    for s_char, digit in SUPERSCRIPT_MAP.items():
        if s_char in result:
            result = result.replace(s_char, digit)
    return result
from src.swarm.model_factory import get_model
from src.engines.slider_engine import render_slider_lab, _symbol_in_expr
from src.engines.stepper_engine import render_stepper_lab
from src.engines.diagram_engine import render_diagram_lab
from src.engines.balance_engine import render_balance_lab
from src.tools.sandbox_guard import verify_micro_lab


@tool
def render_lab(engine_type: str, spec_json: str) -> dict:
    """
    Renders an interactive lab from a SimulationSpec JSON string or dictionary.

    Args:
        engine_type: One of 'slider', 'stepper', 'diagram', 'balance'.
        spec_json: JSON string or dict of the SimulationSpec.

    Returns:
        {"html": str, "size_kb": float} or {"error": str}
    """
    try:
        engine = EngineType(engine_type.lower())
        spec_data = json.loads(spec_json) if isinstance(spec_json, str) else spec_json
        if not isinstance(spec_data, dict):
            return {"error": "spec_json must be a valid JSON dictionary"}
        spec_data["engine_type"] = engine
        if engine == EngineType.SLIDER:
            raw_arch = str(spec_data.get("visual_archetype", "")).strip().lower()
            if raw_arch not in VALID_ARCHETYPES:
                syms = [str(v.get("symbol", "")) for v in spec_data.get("variables", []) if isinstance(v, dict)]
                spec_data["visual_archetype"] = _infer_visual_archetype(
                    topic=str(spec_data.get("title", "")),
                    formula=str(spec_data.get("formula_expression", "")),
                    var_symbols=syms
                )
        spec = SimulationSpec(**spec_data)

        if engine == EngineType.SLIDER:
            html = render_slider_lab(spec)
        elif engine == EngineType.STEPPER:
            html = render_stepper_lab(spec)
        elif engine == EngineType.DIAGRAM:
            html = render_diagram_lab(spec)
        elif engine == EngineType.BALANCE:
            html = render_balance_lab(spec)
        else:
            return {"error": f"Unknown engine type: {engine_type}"}

        size_kb = len(html.encode("utf-8")) / 1024.0
        return {"html": html, "size_kb": round(size_kb, 2)}
    except Exception as exc:
        return {"error": str(exc)}


@tool
def verify_lab(html_content: str, engine_type: str) -> dict:
    """
    Verifies a rendered lab HTML using the Sandbox Guard.

    Args:
        html_content: The HTML code to verify.
        engine_type: The engine type used.

    Returns:
        {"passed": bool, "errors": list[str], "size_kb": float}
    """
    try:
        engine = EngineType(engine_type.lower())
        result = verify_micro_lab(html_content, engine)
        return {
            "passed": result.passed_sandbox_guard,
            "errors": result.error_log,
            "size_kb": result.size_kb,
        }
    except Exception as exc:
        return {"passed": False, "errors": [str(exc)], "size_kb": 0.0}


@tool
def fix_html(html_content: str, errors: str) -> dict:
    """
    Attempts basic automated fixes on HTML based on error messages.

    Args:
        html_content: The HTML to fix.
        errors: Comma-separated error descriptions.

    Returns:
        {"fixed_html": str, "fixes_applied": list[str]}
    """
    fixed = html_content
    fixes = []
    err_lower = errors.lower()

    if "doctype" in err_lower and "<!doctype" not in fixed.lower():
        fixed = "<!DOCTYPE html>\n" + fixed
        fixes.append("Added <!DOCTYPE html>")

    if "title" in err_lower and ("<title" not in fixed.lower() or "<title></title>" in fixed.lower()):
        if "<head>" in fixed.lower():
            fixed = re.sub(r"(<head[^>]*>)", r"\1\n    <title>Interactive Micro-Lab</title>", fixed, flags=re.IGNORECASE)
            fixes.append("Added <title> tag")

    return {"fixed_html": fixed, "fixes_applied": fixes}


VALID_ARCHETYPES = {
    "circuit",
    "piston",
    "beaker",
    "spectrophotometer",
    "optics_bench",
    "refraction",
    "spring",
    "kinematics_block",
    "pendulum",
    "projectile",
    "gravity_orbit",
    "wave_oscillator",
    "cell_osmosis",
    "dna_pcr",
    "lever_torque",
    "gauge",
    "ph_titration",
    "cell_division",
    "enzyme_kinetics",
    "thermo_calorimeter",
}


def _matches_any(text: str, patterns: list[str]) -> bool:
    """Helper to match keywords respecting word boundaries for alphanumeric terms."""
    for p in patterns:
        p_strip = p.strip()
        if not p_strip:
            continue
        if re.match(r"^[a-zA-Z0-9_]+$", p_strip):
            if re.search(r"\b" + re.escape(p_strip) + r"(?:s|es)?\b", text, re.IGNORECASE):
                return True
        else:
            if p_strip.lower() in text.lower():
                return True
    return False


def _sanitize_svg(raw_svg: str | None) -> str:
    """
    Sanitizes generative SVG markup from Agent 2A.
    Ensures safe, inline SVG without scripts, external links, or dangerous attributes.
    """
    if not raw_svg or not isinstance(raw_svg, str):
        return ""
    svg_clean = raw_svg.strip()
    if "<svg" not in svg_clean.lower() or "</svg>" not in svg_clean.lower():
        return ""
    start = svg_clean.lower().find("<svg")
    end = svg_clean.lower().rfind("</svg>")
    svg_clean = svg_clean[start : end + 6]
    lower = svg_clean.lower()
    if any(bad in lower for bad in ["<script", "javascript:", "onload=", "onerror=", "onclick=", "xlink:href=", "http://", "https://"]):
        return ""
    return svg_clean


def _infer_visual_archetype(
    archetype: str | None = None,
    topic: str = "",
    formula: str = "",
    var_symbols: list[str] | None = None,
    subject: str = "",
    concept: str = "",
    variables: list[dict[str, Any]] | None = None,
) -> str:
    """
    Deterministically classifies a STEM topic/formula into one of the 20 Master SVG Archetypes.
    Guarantees that every scientific simulation maps to an authentic, interactive SVG apparatus.
    Applies a strict mutually exclusive priority tree from most specific to most general.
    Defaults to 'gauge' if no specific archetype matches.
    """
    # 0. Handle explicit archetype hint with alias resolution and domain guards
    if archetype:
        arch_clean = str(archetype).strip().lower()
        alias_map = {
            "lever": "lever_torque",
            "torque": "lever_torque",
            "cell": "cell_osmosis",
            "osmosis": "cell_osmosis",
            "wave": "wave_oscillator",
            "oscillator": "wave_oscillator",
            "kinematics": "kinematics_block",
            "block": "kinematics_block",
            "gravity": "gravity_orbit",
            "orbit": "gravity_orbit",
            "dna": "dna_pcr",
            "pcr": "dna_pcr",
            "optics": "optics_bench",
            "lens": "optics_bench",
            "titration": "ph_titration",
            "ph": "ph_titration",
            "poh": "ph_titration",
            "buffer": "ph_titration",
            "fission": "cell_division",
            "mitosis": "cell_division",
            "bacteria": "cell_division",
            "colony": "cell_division",
            "enzyme": "enzyme_kinetics",
            "michaelis": "enzyme_kinetics",
            "menten": "enzyme_kinetics",
            "calorimeter": "thermo_calorimeter",
            "calorimetry": "thermo_calorimeter",
            "thermo": "thermo_calorimeter",
        }
        arch_clean = alias_map.get(arch_clean, arch_clean)

        # Domain Guard: Chemistry should never use lever/torque/spring
        if subject.lower() == "chemistry" and arch_clean in ("lever_torque", "circuit", "spring"):
            arch_clean = "beaker"

        if arch_clean in VALID_ARCHETYPES:
            return arch_clean

    if variables and not var_symbols:
        var_symbols = [str(v.get("symbol", "")) for v in variables if isinstance(v, dict)]

    syms = [s.strip().lower() for s in (var_symbols or []) if s]
    combined = f"{subject} {topic} {concept} {formula}".lower()

    # 1. THERMO CALORIMETER (Thermochemistry, Calorimetry, Specific Heat Capacity q = m*c*dT)
    if _matches_any(combined, [
        "calorimeter", "calorimetry", "specific heat", "heat capacity", "enthalpy",
        "endothermic", "exothermic", "bomb calorimeter", "heat exchange",
        "مسعر", "سعرة", "حرارة نوعية", "إنثالبيا", "كيمياء حرارية", "طارد للحرارة", "ماص للحرارة"
    ]) or ("q" in syms and "c" in syms and ("t" in syms or "dt" in syms or "δt" in syms)) or any(k in formula.lower().replace(" ", "") for k in ["m*c*d", "m*c*t", "m*c*δt", "q=m*c"]):
        return "thermo_calorimeter"

    # 2. PH TITRATION (Acids, Bases, Titration, Buffer, Henderson-Hasselbalch, pH / pOH)
    if _matches_any(combined, [
        "acid", "base", "ph", "poh", "titrat", "buffer", "henderson", "hasselbalch", "neutralization",
        "ka", "kb", "pka", "pkb", "alkali", "equivalence point", "burette", "indicator",
        "حمض", "قاعدة", "معايرة", "أس هيدروجيني", "حمضي", "قاعدي", "منظم", "نقطة التكافؤ", "سحاحة"
    ]) or any(s in syms for s in ["ph", "poh", "[h+]", "[oh-]", "ka", "kb", "pka", "pkb"]) or any(k in formula.lower().replace(" ", "") for k in ["10^-ph", "pow(10,-ph", "pka+", "pka-"]):
        return "ph_titration"

    # 3. ENZYME KINETICS (Michaelis-Menten, Vmax, Km, Active Site Cleft, Catalysis)
    if _matches_any(combined, [
        "michaelis", "menten", "vmax", "km", "enzyme", "substrate", "active site",
        "catalysis", "allosteric", "enzyme kinetics",
        "إنزيم", "ركيزة", "ميكايليس", "سرعة التفاعل الإنزيمي", "الموقع النشط", "تثبيط"
    ]) or any(s in syms for s in ["vmax", "km", "[s]"]) or ("enzyme" in combined and any(s in syms for s in ["v", "s"])):
        return "enzyme_kinetics"

    # 4. CELL DIVISION (Bacterial Binary Fission, Mitosis, Colony Growth, Generation Doubling)
    if _matches_any(combined, [
        "binary fission", "fission", "bacteria", "bacterial growth", "mitosis", "colony",
        "generation", "doubling time", "petri", "culture",
        "انشطار", "انشطار ثنائي", "بكتيريا", "انقسام خلوي", "ميتوزي", "مستعمرة", "أجيال", "تضاعف بكتيري"
    ]) or (("bacteria" in combined or "fission" in combined or "mitosis" in combined) and any(s in syms for s in ["g", "gen", "n", "t"])):
        return "cell_division"

    # 5. DNA PCR (Molecular Biology, PCR Amplification, DNA Helix, Primers, Taq Polymerase)
    if _matches_any(combined, [
        "pcr", "amplification", "polymerase", "helix", "gene", "nucleotide", "primer", "taq",
        "تفاعل البوليميراز", "حلزون", "جين", "بادئ", "تضاعف الـ dna"
    ]) or ("pcr" in combined or ("dna" in combined and any(k in combined for k in ["cycle", "primer", "taq", "amplif"]))):
        return "dna_pcr"

    # 6. CELL OSMOSIS (Cell Biology, Osmosis, Tonicity, Semipermeable Membrane, Turgor)
    if _matches_any(combined, [
        "osmosis", "tonicity", "hypertonic", "hypotonic", "isotonic", "membrane",
        "plasmolysis", "turgor", "water potential",
        "أسموزي", "خاصية أسموزية", "غشاء خلوي", "بلزمة", "امتلاء", "ضغط أسموزي"
    ]) or ("v_cell" in syms or "osmosis" in combined or "tonicity" in combined):
        return "cell_osmosis"

    # 7. BEAKER (General Chemistry, Molarity, Concentration, Dilution, Density, Solutions M = n/V)
    if _matches_any(combined, [
        "molar", "molarity", "concentration", "dilution", "solution", "solute", "solvent", "density", "beaker",
        "محلول", "تركيز", "مولارية", "تخفيف", "مذاب", "مذيب", "كثافة", "وعاء كيميائي"
    ]) or (any(s in syms for s in ["m", "c", "molarity"]) and any(s in syms for s in ["v", "vol", "v1", "v2"])) or ("n/v" in formula.lower().replace(" ", "") or "c1*v1" in formula.lower().replace(" ", "")):
        return "beaker"

    # 8. CIRCUIT (Electricity, Ohm's law, resistors, voltage, current)
    if _matches_any(combined, [
        "circuit", "ohm", "resistor", "resistance", "current", "voltage", "kirchhoff",
        "capacitor", "capacitance", "electric", "battery", "series", "parallel", "ammeter", "voltmeter",
        "دائرة", "أوم", "مقاومة", "تيار", "جهد", "كهرباء", "بطارية", "مكثف"
    ]) or (all(s in syms for s in ["v", "i"]) or all(s in syms for s in ["i", "r"])):
        return "circuit"

    # 9. PISTON (Gases, Boyle's, Charles's, Gay-Lussac, Ideal Gas, thermodynamics PV=nRT)
    if _matches_any(combined, [
        "piston", "boyle", "charles", "gas", "gases", "pressure", "volume", "thermodynamic",
        "isothermal", "isobaric", "cylinder", "mole",
        "مكبس", "غاز", "غازات", "ضغط", "حجم", "ديناميكا حرارية", "بويل", "شارل"
    ]) or (all(s in syms for s in ["p", "v"]) or "p*v" in formula.replace(" ", "") or "n*r*t" in formula.replace(" ", "")):
        return "piston"

    # 10. SPECTROPHOTOMETER (Beer-Lambert Law, Absorbance, Transmittance)
    if _matches_any(combined, [
        "beer", "lambert", "spectrophotometr", "absorbance", "transmittance", "cuvette",
        "extinction", "molar absorptivity", "path length", "attenuation",
        "بير لامبرت", "امتصاص", "مطياف", "نفاذية", "امتصاصية"
    ]) or ("a" in syms and "c" in syms and any(k in formula.lower() for k in ["epsilon", "eps", "ε", "* c", "* l"])):
        return "spectrophotometer"

    # 11. REFRACTION (Snell's Law, Index of Refraction, Total Internal Reflection)
    if _matches_any(combined, [
        "snell", "refraction", "refractive", "incident", "prism", "critical angle",
        "انكسار", "معامل انكسار", "زاوية السقوط", "زاوية الانكسار", "منشور"
    ]) or any(s in syms for s in ["n1", "n2", "theta1", "theta2", "theta_1", "theta_2"]):
        return "refraction"

    # 12. OPTICS BENCH (Lenses, Mirrors, Focal Length, Magnification)
    if _matches_any(combined, [
        "lens", "mirror", "focal", "optics bench", "magnification", "convex", "concave",
        "عدسة", "مرآة", "بؤري", "تكبير", "محدبة", "مقعرة"
    ]) or (any(s in syms for s in ["f", "do", "di"]) and any(k in combined for k in ["lens", "mirror", "focal", "عدسة", "مرآة"])):
        return "optics_bench"

    # 13. SPRING (Hooke's Law, Elasticity, Simple Harmonic Motion)
    if _matches_any(combined, [
        "spring", "hooke", "elastic", "elasticity", "oscillator", "stiffness",
        "نابض", "زنبرك", "مرونة", "استطالة"
    ]) or (all(s in syms for s in ["k", "x"]) and not any(k in combined for k in ["wave", "circuit"])):
        return "spring"

    # 14. PENDULUM (Simple Pendulum, Period, Length, Gravity)
    if _matches_any(combined, [
        "pendulum", "bob", "period of pendulum",
        "بندول", "رقاص", "بندول بسيط"
    ]) or (any(s in syms for s in ["l", "length"]) and any(k in combined for k in ["pendulum", "بندول"])):
        return "pendulum"

    # 15. PROJECTILE (2D Kinematics, Launch Angle, Trajectory, Range)
    if _matches_any(combined, [
        "projectile", "trajectory", "launch angle", "range", "ballistic",
        "مقذوف", "مقذوفات", "مسار المقذوف", "زاوية الإطلاق", "المدى الأفقي"
    ]) or any(k in combined for k in ["projectile", "مقذوف"]):
        return "projectile"

    # 16. GRAVITY ORBIT (Newton's Gravitation, Orbital Mechanics, Kepler)
    if _matches_any(combined, [
        "orbit", "orbital", "gravitation", "kepler", "celestial", "planet", "satellite",
        "جاذبية كوكبية", "مدار", "كبلر", "قمر صناعي", "كوكب"
    ]) or ("g" in formula and any(s in syms for s in ["m1", "m2", "r"])):
        return "gravity_orbit"

    # 17. WAVE OSCILLATOR (Frequency, Wavelength, Sound, Wave Speed)
    if _matches_any(combined, [
        "wave", "waves", "wavelength", "frequency", "sound", "acoustic", "hertz", "standing wave",
        "موجة", "أمواج", "طول موجي", "تردد", "صوت", "اهتزاز"
    ]) or any(s in syms for s in ["lambda", "λ", "freq"]):
        return "wave_oscillator"

    # 18. LEVER TORQUE (Moments, Mechanical Advantage, Fulcrum, Balance)
    if _matches_any(combined, [
        "lever", "torque", "fulcrum", "moment", "effort", "load", "mechanical advantage",
        "رافعة", "عزم", "نقطة ارتكاز", "ذراع القوة", "ذراع المقاومة"
    ]) or any(k in combined for k in ["torque", "lever", "fulcrum", "عزم", "رافعة"]):
        return "lever_torque"

    # 19. KINEMATICS BLOCK (Newton's Laws, Acceleration, Friction, Velocity, Momentum)
    if _matches_any(combined, [
        "newton", "force", "mass", "acceleration", "friction", "kinematics", "momentum", "velocity",
        "نيوتن", "تسارع", "احتكاك", "كتلة", "كمية حركة", "سرعة"
    ]) or (all(s in syms for s in ["m", "a"]) or all(s in syms for s in ["f", "m"])):
        return "kinematics_block"

    # 20. GAUGE (Universal scientific meter / dial fallback)
    return "gauge"



def _evaluate_deterministic_bounds(
    formula: str,
    variables: list[dict[str, Any]],
    constants: dict[str, float] | None = None,
) -> tuple[float, float, bool]:
    """
    Computes mathematically truthful result bounds (result_min, result_max) by evaluating
    the formula expression over the Cartesian product of extreme slider boundaries.
    Eliminates heuristic LLM guessing and ensures dynamic progress bar travel between 0% and 100%.
    """
    if not formula:
        return 0.0, 100.0, False

    clean_formula = str(formula).strip().replace("==", "=")
    lhs = ""
    rhs = clean_formula
    if "=" in clean_formula:
        parts = clean_formula.split("=", 1)
        lhs = parts[0].strip()
        rhs = parts[1].strip()

    # Exact scientific scales
    lhs_clean = lhs.lower().strip("[]")
    if lhs_clean in ("ph", "poh") or ("ph" in clean_formula.lower() and "log10" in clean_formula.lower()):
        return 0.0, 14.0, False
    if lhs in ("[H+]", "H+", "[OH-]", "OH-") or any(k in clean_formula.lower() for k in ["pow(10, -ph)", "10^-ph", "10**-ph"]):
        return 1e-14, 0.1, True
    if lhs_clean in ("v_cell", "balance") or any(k in clean_formula.lower() for k in ["osmosis", "diffusion", "v_cell", "f1 * d1", "f2 * d2", "torque", "lever"]):
        return 0.0, 100.0, False

    slider_vars = []
    for v in variables:
        if not isinstance(v, dict):
            continue
        sym = str(v.get("symbol", "")).strip()
        if not sym:
            continue
        if lhs and (sym == lhs or sym.strip("[]") == lhs.strip("[]")):
            continue
        slider_vars.append(v)

    if not slider_vars:
        return 0.0, 100.0, False

    safe_env: dict[str, Any] = {
        "pow": math.pow,
        "sqrt": math.sqrt,
        "log10": math.log10,
        "log2": math.log2,
        "log": math.log,
        "ln": math.log,
        "exp": math.exp,
        "abs": abs,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "pi": math.pi,
        "PI": math.pi,
        "min": min,
        "max": max,
        "round": round,
    }
    safe_env.update(MATH_PHYSICS_CONSTANTS)
    if constants:
        safe_env.update(constants)

    clean_expr = _normalize_greek_math(rhs)
    clean_expr = _transpile_superscripts(clean_expr)
    clean_expr = clean_expr.replace("^", "**").replace("×", "*").replace("÷", "/").replace("·", "*").replace("−", "-")
    clean_expr = re.sub(r'\*\*\s*-\s*([0-9.]+)', r'** (-\1)', clean_expr)
    clean_expr = re.sub(r'\b10\s*\*\*\s*-\s*([a-zA-Z_]\w*)', r'pow(10, -\1)', clean_expr)

    sorted_vars = sorted(slider_vars, key=lambda v: len(str(v.get("symbol", ""))), reverse=True)
    sym_map: dict[str, str] = {}
    for idx, v in enumerate(sorted_vars):
        sym = str(v.get("symbol", "")).strip()
        if sym:
            safe_id = f"__v_{idx}"
            sym_map[sym] = safe_id
            clean_expr = re.sub(r'\b' + re.escape(sym) + r'\b', safe_id, clean_expr)

    # Generate Cartesian product across slider boundaries
    ids = [sym_map[str(v.get("symbol", "")).strip()] for v in sorted_vars if str(v.get("symbol", "")).strip() in sym_map]
    var_bounds = []
    for v in sorted_vars:
        if str(v.get("symbol", "")).strip() not in sym_map:
            continue
        try:
            mn = float(v.get("min_val", 0.0))
            mx = float(v.get("max_val", 100.0))
            df = float(v.get("default_val", (mn + mx) / 2.0))
        except (ValueError, TypeError):
            mn, mx, df = 0.0, 100.0, 50.0
        if mn >= mx:
            mx = mn + 10.0
        step = (mx - mn) / 4.0
        var_bounds.append([mn, mn + step, mn + 2.0 * step, mn + 3.0 * step, mx])

    points: list[dict[str, float]] = []
    active_bounds = var_bounds[:4]
    active_ids = ids[:4]
    for combo in itertools.product(*active_bounds):
        points.append(dict(zip(active_ids, combo)))

    sampled_vals: list[float] = []
    for pt in points:
        try:
            eval_env = dict(safe_env)
            eval_env.update(pt)
            val = eval(clean_expr, {"__builtins__": {}}, eval_env)
            if isinstance(val, (int, float)) and math.isfinite(val):
                sampled_vals.append(float(val))
        except Exception:
            pass

    if not sampled_vals:
        return 0.0, 100.0, False

    raw_min = min(sampled_vals)
    raw_max = max(sampled_vals)

    if raw_max < raw_min:
        raw_min, raw_max = raw_max, raw_min
    if raw_max == raw_min:
        raw_max = raw_min + (abs(raw_min) if raw_min != 0 else 10.0)

    # Truthful mathematical bounds: exactly the minimum and maximum of the Cartesian product (no arbitrary padding)
    final_min = float(raw_min)
    final_max = float(raw_max)

    is_log = False
    ratio = (final_max / max(final_min, 1e-9)) if final_max > 0 and final_min >= 0 else 1.0
    if ("pow(" in clean_expr.lower() or "**" in clean_expr or "^" in clean_expr) and ratio > 1e4 and final_min > 0:
        is_log = True
    elif ratio > 1e6 and final_min > 0:
        is_log = True

    return final_min, final_max, is_log


def _sanitize_formula(data: dict[str, Any]) -> dict[str, Any]:
    """Normalizes mathematical formula expression and computes deterministic result bounds."""
    formula = str(data.get("formula_expression", "")).strip()
    if formula:
        formula = formula.replace("==", "=").replace("×", "*").replace("·", "*").replace("÷", "/").replace("−", "-")
        formula = re.sub(r'\b10\s*\^\s*-\s*([a-zA-Z_]\w*)', r'pow(10, -\1)', formula)
        formula = re.sub(r'\b10\s*\^\s*([a-zA-Z0-9_().-]+)', r'pow(10, \1)', formula)
        data["formula_expression"] = formula

    if "result_symbol" in data and data["result_symbol"]:
        data["result_symbol"] = str(data["result_symbol"]).strip()
    else:
        f_expr = str(data.get("formula_expression", "")).strip()
        if "=" in f_expr:
            lhs = f_expr.split("=")[0].strip()
            if any(op in lhs for op in ["*", "+", "-", "/"]):
                data["result_symbol"] = "Balance"
            else:
                data["result_symbol"] = lhs
        else:
            data["result_symbol"] = "Result"

    det_min, det_max, is_log = _evaluate_deterministic_bounds(
        data.get("formula_expression", ""),
        data.get("variables", []),
        data.get("constants", {})
    )
    data["result_min"] = det_min
    data["result_max"] = det_max
    data["is_logarithmic_output"] = bool(is_log)

    return data


def _sanitize_variables(data: dict[str, Any], grade: int = 8) -> dict[str, Any]:
    """Sanitizes variable bounds, heals inversions, applies denominator guards, protects constants, prunes zombie variables."""
    formula = str(data.get("formula_expression", "")).strip()
    title = str(data.get("title", "")).strip()
    archetype = str(data.get("visual_archetype", "")).strip().lower()
    combined = f"{title} {formula} {archetype}".lower()
    raw_vars = data.get("variables", [])
    if not isinstance(raw_vars, list):
        return data

    is_electric = any(k in combined for k in [
        "circuit", "ohm", "resistor", "resistance", "current", "voltage", "kirchhoff",
        "v = i", "i * r", "دائرة", "أوم", "مقاومة", "تيار", "جهد"
    ])
    is_osmosis_or_gas = any(k in combined for k in [
        "osmosis", "tonicity", "pi =", "π =", "m * r * t", "p * v", "pv =", "n * r * t",
        "gas", "boyle", "charles", "piston", "أسموز", "ضغط أسموزي", "غازات", "مكبس"
    ]) or archetype in ("cell_osmosis", "cell", "piston")
    is_gravity_context = any(k in combined for k in [
        "projectile", "pendulum", "gravity", "free fall", "orbit", "مقذوف", "بندول", "سقوط", "جاذبية"
    ]) or archetype in ("projectile", "pendulum", "gravity_orbit")

    # Protect and extract Universal Physical Constants
    filtered_raw_vars = []
    for v in raw_vars:
        if not isinstance(v, dict):
            continue
        sym = str(v.get("symbol", "")).strip()
        v_name = str(v.get("name", "")).strip().lower()
        unit_str = str(v.get("unit", "")).strip().lower()
        try:
            raw_def = float(v.get("default_val", 0.0))
        except (ValueError, TypeError):
            raw_def = 0.0

        # Symbol already registered in constants
        if sym in data.get("constants", {}):
            continue

        # 1. Universal Gravitational Constant G = 6.67430e-11
        if sym == "G" or "gravitational constant" in v_name or "ثابت الجذب" in v_name or (0 < abs(raw_def) < 1e-9 and ("g" in sym.lower() or "grav" in v_name)):
            data.setdefault("constants", {})["G"] = 6.67430e-11
            continue

        # 2. Universal Gas Constant R (in gas / osmosis context, NOT in electric circuits)
        if not is_electric and (sym in ("R", "r") or "gas constant" in v_name or "ثابت الغاز" in v_name):
            if is_osmosis_or_gas or any(k in formula.lower() for k in ["* r *", "*r*", "/ r", "/r", "n*r*t", "n * r * t", "m*r*t", "m * r * t"]):
                r_val = 8.314 if ("j" in unit_str or "kpa" in combined or "pa" in combined) else 0.0821
                data.setdefault("constants", {})["R"] = r_val
                if len(raw_vars) > 1:
                    continue

        # 3. Gravitational acceleration g (in projectile / pendulum / gravity)
        if sym == "g" or "gravity" in v_name or "جاذبية" in v_name or "acceleration due to gravity" in v_name:
            if is_gravity_context or any(k in formula.lower() for k in ["/ g", "/g", "* g", "*g"]):
                other_vars = [o for o in raw_vars if isinstance(o, dict) and str(o.get("symbol", "")).strip() != "g" and "gravity" not in str(o.get("name", "")).lower() and "جاذبية" not in str(o.get("name", "")).lower()]
                if len(other_vars) >= 2:
                    data.setdefault("constants", {})["g"] = 9.8
                    continue
                else:
                    v = dict(v)
                    v["min_val"] = 1.6
                    v["max_val"] = 25.0
                    v["default_val"] = 9.8
                    v["unit"] = "m/s²"

        # 4. Speed of light c = 299792458.0
        if sym == "c" and ("speed of light" in v_name or "سرعة الضوء" in v_name or raw_def >= 1e7 or "c**2" in formula or "c^2" in formula):
            data.setdefault("constants", {})["c"] = 299792458.0
            continue

        # 5. Planck's constant h / hbar
        if sym in ("h", "hbar") and ("planck" in v_name or "بلانك" in v_name or (0 < raw_def < 1e-15)):
            val = 1.054571817e-34 if "bar" in sym else 6.62607015e-34
            data.setdefault("constants", {})[sym] = val
            continue

        # 6. Coulomb constant k_e or k (when Coulomb force, not spring stiffness)
        if sym == "k_e" or (sym == "k" and ("coulomb" in v_name or "كولوم" in v_name or "coulomb" in combined)):
            data.setdefault("constants", {})[sym] = 8.9875517923e9
            continue

        # 7. Avogadro's number N_A
        if sym in ("N_A", "Na", "NA") or "avogadro" in v_name or "أفوجادرو" in v_name:
            data.setdefault("constants", {})[sym] = 6.02214076e23
            continue

        # 8. Stefan-Boltzmann constant sigma
        if (sym in ("sigma", "σ") or "stefan" in v_name or "ستيفان" in v_name) and ("stefan" in v_name or "ستيفان" in v_name or 0 < raw_def < 1e-5):
            data.setdefault("constants", {})[sym] = 5.670374419e-8
            continue

        # 9. Boltzmann constant k_B
        if (sym in ("k_B", "kB") or "boltzmann" in v_name or "بولتزمان" in v_name) and ("boltzmann" in v_name or "بولتزمان" in v_name or 0 < raw_def < 1e-15):
            data.setdefault("constants", {})[sym] = 1.380649e-23
            continue

        # 10. Elementary charge e
        if (sym == "e" or "elementary charge" in v_name or "شحنة الإلكترون" in v_name) and ("elementary" in v_name or "شحنة" in v_name or 0 < raw_def < 1e-15):
            data.setdefault("constants", {})["e"] = 1.602176634e-19
            continue

        # 11. Mathematical pi
        if sym in ("pi", "PI", "π"):
            data.setdefault("constants", {})["pi"] = math.pi
            data.setdefault("constants", {})["PI"] = math.pi
            data.setdefault("constants", {})["π"] = math.pi
            continue

        filtered_raw_vars.append(v)

    raw_vars = filtered_raw_vars if filtered_raw_vars else raw_vars

    sanitized_vars = []
    for v in raw_vars:
        if not isinstance(v, dict):
            continue
        v_clean = dict(v)
        sym = str(v_clean.get("symbol", "")).strip()
        name = str(v_clean.get("name", sym or "Variable")).strip()
        unit = str(v_clean.get("unit", "")).strip()

        try:
            min_v = float(v_clean.get("min_val", 0.0))
        except (ValueError, TypeError):
            min_v = 0.0
        try:
            max_v = float(v_clean.get("max_val", 100.0))
        except (ValueError, TypeError):
            max_v = 100.0

        if min_v >= max_v:
            max_v = min_v + (abs(min_v) if min_v != 0 else 10.0)

        try:
            def_v = float(v_clean.get("default_val", (min_v + max_v) / 2.0))
        except (ValueError, TypeError):
            def_v = (min_v + max_v) / 2.0

        if def_v < min_v or def_v > max_v:
            def_v = (min_v + max_v) / 2.0

        def _clean_var_num(val: float) -> float:
            if val == 0.0:
                return 0.0
            abs_v = abs(val)
            if abs_v < 1e-3 or abs_v > 1e5:
                return float(f"{val:.4g}")
            return round(val, 4)

        min_v = _clean_var_num(min_v)
        max_v = _clean_var_num(max_v)
        def_v = _clean_var_num(def_v)

        # Denominator & physical slider guard: tame denominator blowup and prevent division by zero
        if formula and sym:
            denom_pattern = r'/\s*\(?[^/)]*\b' + re.escape(sym) + r'\b'
            if re.search(denom_pattern, formula):
                if max_v >= 10.0 and min_v < max_v * 0.05:
                    min_floor = 1.0 if max_v >= 20.0 else round(max_v * 0.05, 2)
                    min_v = max(min_v, min_floor)
                else:
                    positive_floor = 0.05 if max_v <= 5.0 else 0.1
                    if min_v < positive_floor:
                        min_v = positive_floor
                if def_v < min_v:
                    def_v = min_v

        # Elementary tier (grades 1-6): prefer friendly integers for non-microscopic variables
        if grade <= 6:
            if abs(min_v - round(min_v)) < 0.05 and min_v >= 0:
                min_v = float(round(min_v))
            if abs(max_v - round(max_v)) < 0.05:
                max_v = float(round(max_v))
            if abs(def_v - round(def_v)) < 0.05:
                def_v = float(round(def_v))

        v_clean.update({"symbol": sym, "name": name, "unit": unit,
                        "min_val": min_v, "max_val": max_v, "default_val": def_v})
        sanitized_vars.append(v_clean)

    # Prune disconnected zombie variables
    if formula and sanitized_vars:
        bindings = data.get("svg_bindings") or {}
        is_eq = False
        result_sym = ""
        rhs_expr = formula
        lhs_expr = ""

        if "=" in formula:
            parts = formula.split("=", 1)
            lhs_cand = parts[0].strip()
            rhs_cand = parts[1].strip()
            if any(k in formula.lower() for k in ["d1", "d2", "arm", "fulcrum", "torque", "عزم", "effort", "load"]):
                is_eq = True
                lhs_expr = lhs_cand
                rhs_expr = rhs_cand
            else:
                result_sym = lhs_cand
                rhs_expr = rhs_cand

        active_vars = []
        for v in sanitized_vars:
            sym = v.get("symbol", "")
            name = v.get("name", "")
            if not sym:
                continue
            if not is_eq and (sym == result_sym or sym.strip("[]") == result_sym.strip("[]")):
                active_vars.append(v)
                continue
            active_target = (lhs_expr + " " + rhs_expr) if is_eq else rhs_expr
            if _symbol_in_expr(sym, active_target):
                active_vars.append(v)
                continue
            if is_eq and name and name.lower() in active_target.lower():
                active_vars.append(v)
                continue
            if isinstance(bindings, dict) and sym in bindings:
                active_vars.append(v)
                continue

        data["variables"] = active_vars if active_vars else sanitized_vars
    else:
        data["variables"] = sanitized_vars

    return data


def _sanitize_ancillary(data: dict[str, Any]) -> dict[str, Any]:
    """Normalizes steps, challenge_items, nodes, and constants."""
    raw_steps = data.get("steps")
    if isinstance(raw_steps, list):
        sanitized_steps = []
        for idx, s in enumerate(raw_steps):
            if isinstance(s, dict):
                sanitized_steps.append(s)
            elif isinstance(s, str) and s.strip():
                sanitized_steps.append({
                    "step_number": idx + 1, "title": f"Step {idx + 1}",
                    "description": s.strip(), "text": s.strip()
                })
        data["steps"] = sanitized_steps

    raw_challenges = data.get("challenge_items")
    if isinstance(raw_challenges, list):
        sanitized_challenges = []
        for idx, c in enumerate(raw_challenges):
            if isinstance(c, dict):
                sanitized_challenges.append(c)
            elif isinstance(c, str) and c.strip():
                sanitized_challenges.append({"question": c.strip(), "answer": "", "hint": ""})
        data["challenge_items"] = sanitized_challenges

    raw_nodes = data.get("nodes")
    if isinstance(raw_nodes, list):
        sanitized_nodes = []
        for idx, n in enumerate(raw_nodes):
            if isinstance(n, dict):
                sanitized_nodes.append(n)
            elif isinstance(n, str) and n.strip():
                sanitized_nodes.append({"id": f"node_{idx + 1}", "label": n.strip()})
        data["nodes"] = sanitized_nodes

    raw_consts = data.get("constants")
    if isinstance(raw_consts, dict):
        clean_consts = {}
        for k, v in raw_consts.items():
            try:
                clean_consts[str(k)] = float(v)
            except (ValueError, TypeError):
                pass
        data["constants"] = clean_consts

    # Sanitize visual_archetype to guarantee one of the 16 Master SVG Archetypes
    raw_arch = str(data.get("visual_archetype", "")).strip().lower()
    if raw_arch not in VALID_ARCHETYPES:
        symbols = [str(v.get("symbol", "")) for v in data.get("variables", []) if isinstance(v, dict)]
        data["visual_archetype"] = _infer_visual_archetype(
            topic=str(data.get("title", "")),
            formula=str(data.get("formula_expression", "")),
            var_symbols=symbols
        )
    else:
        data["visual_archetype"] = raw_arch

    data.pop("scenegraph_2d", None)
    return data


def _sanitize_simulation_spec(spec_data: dict[str, Any], grade: int = 8) -> dict[str, Any]:
    """
    Sanitizes and normalizes SimulationSpec data from LLM.
    Delegates to focused sub-functions for formula, variables, and ancillary data.
    """
    data = dict(spec_data)
    data = _sanitize_ancillary(data)
    data = _sanitize_variables(data, grade=grade)
    data = _sanitize_formula(data)
    if not data.get("result_unit"):
        res_sym = str(data.get("result_symbol", "")).strip()
        for v in data.get("variables", []):
            if isinstance(v, dict) and str(v.get("symbol", "")).strip() == res_sym:
                data["result_unit"] = v.get("unit", "")
                break
        if not data.get("result_unit"):
            sym_l = res_sym.lower()
            if sym_l in ("f", "fg", "fe", "force"):
                data["result_unit"] = "N"
            elif sym_l in ("v", "speed", "velocity"):
                data["result_unit"] = "m/s"
            elif sym_l in ("a", "acc", "acceleration"):
                data["result_unit"] = "m/s²"
            elif sym_l in ("p", "pressure"):
                data["result_unit"] = "atm" if data.get("visual_archetype") == "piston" else "Pa"
            elif sym_l in ("l", "λ", "lambda", "wavelength", "r", "d", "x"):
                data["result_unit"] = "m"
            elif sym_l in ("t", "period", "time"):
                data["result_unit"] = "s"
    return data


def create_agent_2a(model=None) -> Agent:
    """
    Creates Agent 2A (SimulationMathArchitect).
    Translates concept specifications into rigorous mathematical parameters and
    authentic STEM Master SVG Archetypes.
    """
    system_prompt = (
        "You are an expert scientific simulation mathematician for LuminaLab.\n"
        "Your task is to convert educational concepts across Physics, Chemistry, and Biology into rigorous mathematical specifications.\n\n"
        "IMPORTANT: Select the most authentic 'visual_archetype' from the 20 approved STEM Master SVG Archetypes:\n"
        "- Physics: 'circuit', 'piston', 'spring', 'kinematics_block', 'pendulum', 'projectile', 'gravity_orbit', 'wave_oscillator', 'optics_bench', 'refraction', 'lever_torque'\n"
        "- Chemistry: 'ph_titration', 'beaker', 'thermo_calorimeter', 'spectrophotometer', 'piston'\n"
        "- Biology: 'cell_division', 'enzyme_kinetics', 'cell_osmosis', 'dna_pcr'\n"
        "- Universal Fallback: 'gauge'\n"
        "Focus on mathematical precision: formula_expression (LHS = RHS), variables with physical bounds, and selecting the exact visual_archetype.\n\n"
        "### OUTPUT FORMAT:\n"
        "Output ONLY valid JSON:\n"
        "{\n"
        '  "engine_type": "slider" | "stepper" | "diagram" | "balance",\n'
        '  "title": "Clear educational lab title in requested language",\n'
        '  "visual_archetype": "circuit" | "piston" | "beaker" | "spectrophotometer" | "optics_bench" | "refraction" | "spring" | "kinematics_block" | "pendulum" | "projectile" | "gravity_orbit" | "wave_oscillator" | "cell_osmosis" | "dna_pcr" | "lever_torque" | "gauge" | "ph_titration" | "cell_division" | "enzyme_kinetics" | "thermo_calorimeter",\n'
        '  "variables": [\n'
        '    {"name": "Variable Name", "symbol": "x", "unit": "unit", "min_val": 0.0, "max_val": 100.0, "default_val": 10.0}\n'
        '  ],\n'
        '  "formula_expression": "Mathematical relationship (e.g. F = k * x or V = I * R or [H+] = pow(10, -pH))",\n'
        '  "result_symbol": "Calculated variable symbol (e.g. pH or F or V)",\n'
        '  "constants": {},\n'
        '  "steps": [...],\n'
        '  "nodes": [...],\n'
        '  "challenge_items": [...]\n'
        "}\n\n"
        "### MATHEMATICAL & SCIENTIFIC MODELING RULES:\n"
        "1. FORMULA FORMULATION (LHS = RHS):\n"
        "   - Isolate the dependent calculated variable on the left side of the '=' sign (e.g. '[H+] = pow(10, -pH)' or 'F = k * x' or 'V = I * R').\n"
        "   - Use clean, standard mathematical notation: '+', '-', '*', '/', '**' or 'pow(base, exp)', 'sqrt()', 'log10()'.\n"
        "2. ZERO DEAD SLIDERS:\n"
        "   - Ensure EVERY variable in 'variables' appears in the formula expression.\n"
        "3. REALISTIC PHYSICAL BOUNDS:\n"
        "   - min_val MUST be strictly less than max_val.\n"
        "   - In denominators, min_val must be strictly positive (> 0) to avoid division by zero.\n"
        "4. AGE-CALIBRATED COGNITIVE CALIBRATION:\n"
        "   - For Elementary (Grades 1-6): Use clean, friendly integer bounds (e.g. 1 to 10 or 1 to 20) with simple whole-number defaults (e.g. 2, 5, 10). Use intuitive variable names alongside symbols so the child never faces intimidating decimals or scientific notation unless unavoidable.\n"
        "   - For Middle School (Grades 7-9): Use clean standard SI units and relatable real-world ranges.\n"
        "   - For High School (Grades 10-12): Use authentic curriculum-accurate physical/chemical bounds, precise SI units, and exact scientific terminology matching their grade curriculum.\n\n"
        "Return strictly valid JSON without any markdown formatting or commentary."
    )
    return Agent(
        model=model or get_model(),
        system_prompt=system_prompt,
        callback_handler=get_hackathon_callback_handler("Agent 2A: SimMathArchitect")
    )


def create_agent_2b(model=None) -> Agent:
    """
    Creates Agent 2B (VisualRendererAndGuard).
    Responsible for rendering, quality verification, and self-healing fixes.
    """
    system_prompt = (
        "You are an interactive lab assembler and quality auditor.\n"
        "You render labs from SimulationSpec parameters, verify them with Sandbox Guard, and repair any errors.\n"
        "Use your tools (render_lab, verify_lab, fix_html) to ensure self-contained, clean, interactive labs."
    )
    return Agent(
        model=model or get_model(),
        system_prompt=system_prompt,
        tools=[render_lab, verify_lab, fix_html],
        callback_handler=get_hackathon_callback_handler("Agent 2B: RendererGuard")
    )


def _extract_json_dict(text: str) -> dict:
    """Helper to parse a JSON dictionary from raw agent output with high resilience."""
    clean_text = text.strip()

    # 1. Search for fenced code blocks containing a JSON object
    json_block = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", clean_text, flags=re.IGNORECASE)
    if json_block:
        candidate = json_block.group(1).strip()
        try:
            return json.loads(candidate)
        except Exception:
            try:
                cleaned = re.sub(r",\s*([}\]])", r"\1", candidate)
                return json.loads(cleaned)
            except Exception:
                pass

    # 2. Search for outermost curly braces
    start = clean_text.find("{")
    end = clean_text.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = clean_text[start : end + 1]
        try:
            return json.loads(snippet)
        except Exception:
            try:
                cleaned = re.sub(r",\s*([}\]])", r"\1", snippet)
                return json.loads(cleaned)
            except Exception:
                pass

    # 3. Direct load attempt with trailing comma cleanup
    try:
        return json.loads(clean_text)
    except Exception:
        cleaned = re.sub(r",\s*([}\]])", r"\1", clean_text)
        return json.loads(cleaned)


def _get_agent_response_text(res: Any) -> str:
    """Helper to extract text content from an AgentResult."""
    if hasattr(res, "message") and isinstance(res.message, dict):
        content = res.message.get("content", [])
        if isinstance(content, list) and len(content) > 0:
            first = content[0]
            if isinstance(first, dict) and "text" in first:
                return first["text"]
            elif hasattr(first, "text"):
                return getattr(first, "text")
        elif isinstance(content, str):
            return content
    return str(res)


def run_pair2(
    deconstructed: DeconstructedConcept,
    model=None,
    max_repair_attempts: int = 3
) -> tuple[SimulationSpec, VerifiedMicroLab]:
    """
    Executes Pair 2: Agent 2A creates simulation parameters, the engine renders HTML,
    and Sandbox Guard verifies with a self-healing loop.

    Parameters:
        deconstructed: Output from Pair 1.
        model: Optional language model override.
        max_repair_attempts: Max automated self-healing iterations.

    Returns:
        tuple[SimulationSpec, VerifiedMicroLab]

    Raises:
        RuntimeError: If lab verification fails after max_repair_attempts.
    """
    agent_2a = create_agent_2a(model=model)

    grade = parse_student_grade(deconstructed.original_input.student_grade)
    ped_directive = get_pedagogical_directive(grade, deconstructed.original_input.language)

    # 1. Run Agent 2A to generate SimulationSpec parameters
    prompt_2a = (
        f"Design an adaptive scientific simulation specification for this concept:\n"
        f"Subject: {deconstructed.original_input.subject}\n"
        f"Topic: {deconstructed.original_input.topic}\n"
        f"Grade Level: {grade} ({ped_directive['tier_label']})\n"
        f"Recommended Engine: {deconstructed.recommended_engine.value}\n"
        f"Core Concept: {deconstructed.core_concept}\n"
        f"Target Equation/Steps: {deconstructed.target_equation_or_steps}\n"
        f"Simplified Explanation: {deconstructed.simplified_explanation}\n"
        f"Cognitive Bottleneck: {deconstructed.cognitive_bottleneck}\n"
        f"Key Variables: {json.dumps(deconstructed.key_variables, ensure_ascii=False)}\n"
        f"Title Language: {deconstructed.original_input.language}\n\n"
        f"{ped_directive['math_guidance']}\n\n"
        f"Instructions:\n"
        f"1. Select the most authentic 'visual_archetype' from the 20 approved STEM Master SVG Archetypes: circuit, piston, beaker, spectrophotometer, optics_bench, refraction, spring, kinematics_block, pendulum, projectile, gravity_orbit, wave_oscillator, cell_osmosis, dna_pcr, lever_torque, gauge, ph_titration, cell_division, enzyme_kinetics, thermo_calorimeter.\n"
        f"2. Formulate target equation with calculated dependent variable on LHS (e.g. '[H+] = pow(10, -pH)' or 'F = k * x').\n"
        f"3. ZERO DEAD SLIDERS: Ensure EVERY variable in 'variables' appears in the formula expression. Do NOT pass unused variables!\n"
        f"4. Provide realistic physical bounds (min_val < max_val) and authentic units.\n"
        f"5. Return strictly valid JSON matching SimulationSpec schema."
    )

    try:
        res_2a = agent_2a(prompt_2a)
        text_2a = _get_agent_response_text(res_2a)
        spec_data = _extract_json_dict(text_2a)
    except Exception as exc:
        raise ValueError(f"Failed to parse Agent 2A output: {exc}") from exc

    # Sanitize and normalize spec parameters
    spec_data = _sanitize_simulation_spec(spec_data, grade=grade)

    # Ensure engine type aligns with recommendation
    spec_data["engine_type"] = deconstructed.recommended_engine
    if "title" not in spec_data or not str(spec_data["title"]).strip():
        spec_data["title"] = deconstructed.core_concept[:60]

    # Guarantee variables and formula fallback for SLIDER and all engines
    if not spec_data.get("variables"):
        spec_data["variables"] = deconstructed.key_variables
    if not spec_data.get("formula_expression") or not str(spec_data.get("formula_expression")).strip():
        spec_data["formula_expression"] = deconstructed.target_equation_or_steps

    # Verify and set visual_archetype deterministically
    raw_arch = str(spec_data.get("visual_archetype", "")).strip().lower()
    if raw_arch not in VALID_ARCHETYPES:
        syms = [str(v.get("symbol", "")) for v in spec_data.get("variables", []) if isinstance(v, dict)]
        spec_data["visual_archetype"] = _infer_visual_archetype(
            topic=f"{deconstructed.original_input.subject} {deconstructed.original_input.topic} {deconstructed.core_concept}",
            formula=spec_data.get("formula_expression", deconstructed.target_equation_or_steps),
            var_symbols=syms
        )
    else:
        spec_data["visual_archetype"] = raw_arch

    spec_data.pop("scenegraph_2d", None)

    spec = SimulationSpec(**spec_data)

    # 2. Render Lab directly via deterministic engine
    if spec.engine_type == EngineType.SLIDER:
        html_content = render_slider_lab(spec)
    elif spec.engine_type == EngineType.STEPPER:
        html_content = render_stepper_lab(spec)
    elif spec.engine_type == EngineType.DIAGRAM:
        html_content = render_diagram_lab(spec)
    elif spec.engine_type == EngineType.BALANCE:
        html_content = render_balance_lab(spec)
    else:
        raise ValueError(f"Unsupported engine type: {spec.engine_type}")

    # 3. Initial Sandbox Guard check
    verified_lab = verify_micro_lab(html_content, spec.engine_type)
    if verified_lab.passed_sandbox_guard:
        return spec, verified_lab

    # 4. Self-Healing Loop if verification fails
    attempt = 0
    agent_2b = create_agent_2b(model=model)

    while attempt < max_repair_attempts and not verified_lab.passed_sandbox_guard:
        attempt += 1
        errors_str = ", ".join(verified_lab.error_log)

        # Call fix_html tool for standard structural errors
        fix_result = fix_html(html_content, errors_str)
        html_content = fix_result.get("fixed_html", html_content)

        # Re-verify
        verified_lab = verify_micro_lab(html_content, spec.engine_type)
        verified_lab.repair_attempts = attempt
        if verified_lab.passed_sandbox_guard:
            break

        # Ask Agent 2B for targeted repairs if still failing
        prompt_2b = (
            f"The lab failed verification with errors: {errors_str}.\n"
            f"Current HTML (first 500 chars):\n{html_content[:500]}\n"
            f"Suggest fixes or return corrected HTML."
        )
        try:
            agent_2b(prompt_2b)
        except Exception:
            pass

    if not verified_lab.passed_sandbox_guard:
        raise RuntimeError(
            f"Lab verification failed after {max_repair_attempts} attempts: {verified_lab.error_log}"
        )

    return spec, verified_lab
