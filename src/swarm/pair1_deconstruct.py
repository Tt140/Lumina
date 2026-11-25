"""LuminaLab Swarm - Pair 1: Concept Deconstruction and Archetype Routing."""

import json
import logging
import math
import re
from typing import Any
from strands import Agent, tool
from src.contracts.schemas import LessonInput, DeconstructedConcept, EngineType
from src.swarm.json_utils import (
    extract_agent_response_text as _get_agent_response_text,
    extract_json_dict as _extract_json_dict,
    invoke_agent_for_json,
    is_non_retryable_provider_error,
)
from src.swarm.model_factory import get_model
from src.tools.impact_calculator import calculate_grade_level


from src.swarm.pedagogical_calibration import parse_student_grade, get_pedagogical_directive
from src.swarm.terminal_stream import get_hackathon_callback_handler

logger = logging.getLogger("luminalab.pair1")


@tool
def assess_readability(text: str, language: str = "en") -> dict:
    """Calculates the readability grade level of an educational text (1.0 to 12.0)."""
    grade = calculate_grade_level(text, language=language)
    return {"grade_level": grade}


def create_agent_1a(model=None) -> Agent:
    """
    Creates Agent 1A (ConceptExtractor).
    Analyzes student lesson input to extract the core scientific concept,
    cognitive bottleneck, simplified explanation, and key variables.
    """
    system_prompt = (
        "You are an expert pedagogical analyst specializing in adaptive STEM education.\n"
        "Your task is to analyze the provided textbook excerpt and extract its core scientific concept.\n"
        "You MUST return ONLY a valid JSON object matching this exact structure:\n"
        "{\n"
        '  "core_concept": "Concise definition of the main concept",\n'
        '  "target_equation_or_steps": "Target mathematical equation or procedural steps",\n'
        '  "cognitive_bottleneck": "The specific misconception or intuition gap students face",\n'
        '  "baseline_grade_level": 8.0,\n'
        '  "simplified_explanation": "A crystal-clear, age-calibrated intuition capsule tailored to the student\'s cognitive stage",\n'
        '  "key_variables": [\n'
        '    {"name": "VarName", "symbol": "V", "unit": "Unit", "min_val": 0.0, "max_val": 100.0, "default_val": 10.0}\n'
        "  ]\n"
        "}\n"
        "Ensure each variable in key_variables contains all 6 required fields: name, symbol, unit, min_val, max_val, default_val.\n"
        "CRITICAL PEDAGOGY DIRECTIVE (AGE-CALIBRATED INTUITION CAPSULE):\n"
        "Never output dry, bureaucratic, or circular textbook jargon. Write with high cognitive empathy for hospital students and neurodiverse learners (ADHD, Dyslexia):\n"
        "- 'simplified_explanation' must be a punchy, crystal-clear 'capsule' in 2-3 lively sentences explaining the direct physical cause-and-effect.\n"
        "- For Elementary (Grades 1-6): Use concrete tangible physical metaphors, warm encouraging tone, and short sentences (<12 words).\n"
        "- For Middle School (Grades 7-9): Use smart mentor tone, focus on direct cause-and-effect ('when X doubles, Y drops by half'), zero baby-talk.\n"
        "- For High School (Grades 10-12): 'Executive Scientific Capsule (الزتونة العلمية المركزة)' — Highly respectful, sharp physical intuition. Demystify the governing mechanism in 2-3 punchy sentences linking formulas directly to reality. NEVER use baby-talk ('يا بطل') or childish cartoons!\n"
        "LANGUAGE ENFORCEMENT:\n"
        "If the input indicates Language 'ar', write 'core_concept', 'cognitive_bottleneck', 'simplified_explanation', and variable names in natural, accessible Arabic (المصرية البيضاء الراقية أو الفصحى الميسرة) calibrated to the grade maturity.\n"
        "If Language is 'en', output in English.\n"
        "Do not include any conversational preamble or markdown outside the JSON."
    )

    return Agent(
        model=model or get_model(),
        system_prompt=system_prompt,
        tools=[assess_readability],
        callback_handler=get_hackathon_callback_handler("Agent 1A: ConceptExtractor")
    )


def create_agent_1b(model=None) -> Agent:
    """
    Creates Agent 1B (ArchetypeRouter).
    Selects the most suitable interactive micro-lab archetype engine based on concept characteristics.
    """
    system_prompt = (
        "You are an expert interactive curriculum designer specializing in selecting interactive simulation archetypes.\n"
        "The available engines are:\n"
        "1. SLIDER - For continuous variables governed by mathematical formulas (e.g. V=IR, F=ma, fractions).\n"
        "2. STEPPER - For sequential, multi-step algorithms, chronological histories, or discrete biological stages without mathematical equations.\n"
        "3. DIAGRAM - For interconnected systems with nodes and relationships (circuits, anatomy, networks, trees).\n"
        "4. BALANCE - For categorization, sorting, or balance challenges (acid vs base, balancing equations).\n\n"
        "CRITICAL ROUTING PRIORITY (NEUTRALIZE STEPPER TRAP & QUANTITATIVE FORMULA PRIORITY):\n"
        "- DO NOT route to 'stepper' simply because the text mentions words like 'cycles', 'steps', 'stages', or 'phases' if there is an underlying mathematical equation or variables that can be manipulated (e.g. PCR amplification cycles N = N0 * 2^cycles, reaction kinetics steps, gas expansion cycles).\n"
        "- Whenever a mathematical formula or quantitative relationship with variables exists, you MUST select 'slider', because the 2D interactive canvas runtime simulates continuous and discrete equations dynamically.\n"
        "- 'stepper' is strictly reserved for purely descriptive, qualitative chronological procedures (like historical milestones or laboratory dissection protocols) that lack mathematical equations.\n\n"
        "Analyze the provided concept and return ONLY a valid JSON object:\n"
        "{\n"
        '  "recommended_engine": "slider" | "stepper" | "diagram" | "balance",\n'
        '  "engine_justification": "Clear educational reason why this engine archetype was chosen."\n'
        "}\n"
        "Do not include any conversational preamble or markdown outside the JSON."
    )

    return Agent(
        model=model or get_model(),
        system_prompt=system_prompt,
        callback_handler=get_hackathon_callback_handler("Agent 1B: ArchetypeRouter")
    )


def _coerce_finite_float(val: Any, default: float) -> float:
    """Safely convert numeric or string values (including scientific notation) into a finite float."""
    if isinstance(val, bool):
        return default
    if isinstance(val, (int, float)):
        f = float(val)
        return f if math.isfinite(f) else default
    if isinstance(val, str):
        cleaned = val.strip().replace(",", "")
        match = re.search(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", cleaned)
        if match:
            try:
                f = float(match.group(0))
                if math.isfinite(f):
                    return f
            except ValueError:
                pass
    return default


def _sanitize_key_variables(raw_vars: Any, lesson_input: LessonInput) -> list[dict[str, Any]]:
    """Normalize, deduplicate, and enforce numeric/schema bounds on key_variables."""
    sanitized: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str]] = set()

    if isinstance(raw_vars, list):
        for idx, item in enumerate(raw_vars):
            if isinstance(item, str) and item.strip():
                sym = f"x_{idx + 1}"
                name = item.strip()
                item_dict: dict[str, Any] = {"name": name, "symbol": sym, "unit": ""}
            elif isinstance(item, dict):
                item_dict = dict(item)
            else:
                continue

            name = str(item_dict.get("name") or item_dict.get("symbol") or f"Variable {idx + 1}").strip()
            symbol = str(item_dict.get("symbol") or f"v{idx + 1}").strip()
            unit = str(item_dict.get("unit") or "").strip()

            dedup_key = (symbol.lower(), name.lower())
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)

            min_val = _coerce_finite_float(item_dict.get("min_val", item_dict.get("min")), 0.0)
            max_val = _coerce_finite_float(item_dict.get("max_val", item_dict.get("max")), min_val + 100.0)
            if min_val >= max_val:
                max_val = min_val + (abs(min_val) if min_val != 0.0 else 10.0)

            default_val = _coerce_finite_float(
                item_dict.get("default_val", item_dict.get("default")),
                (min_val + max_val) / 2.0,
            )
            if default_val < min_val or default_val > max_val:
                default_val = (min_val + max_val) / 2.0

            sanitized.append({
                "name": name,
                "symbol": symbol,
                "unit": unit,
                "min_val": min_val,
                "max_val": max_val,
                "default_val": default_val,
            })

    if not sanitized:
        default_name = "تقدم المفهوم" if lesson_input.language == "ar" else "Concept Progression"
        sanitized.append({
            "name": default_name,
            "symbol": "x",
            "unit": "step",
            "min_val": 1.0,
            "max_val": 10.0,
            "default_val": 1.0,
        })

    return sanitized


def _sanitize_deconstructed_data(data: dict[str, Any], lesson_input: LessonInput) -> dict[str, Any]:
    """Normalize Agent 1A JSON payload so any lesson/subject satisfies DeconstructedConcept cleanly."""
    clean = dict(data) if isinstance(data, dict) else {}

    core = str(clean.get("core_concept") or "").strip()
    if len(core) < 5:
        core = f"{lesson_input.subject}: {lesson_input.topic}".strip()
        if len(core) < 5:
            core = f"{core} Concept".strip()
    clean["core_concept"] = core

    raw_eq = clean.get("target_equation_or_steps")
    if isinstance(raw_eq, list):
        eq_str = "; ".join(str(x).strip() for x in raw_eq if str(x).strip())
    else:
        eq_str = str(raw_eq or "").strip()
    clean["target_equation_or_steps"] = eq_str or core

    bottleneck = str(clean.get("cognitive_bottleneck") or "").strip()
    if not bottleneck:
        bottleneck = (
            f"فهم العلاقة السببية الأساسية خلف {lesson_input.topic} بدلاً من الحفظ المجرد."
            if lesson_input.language == "ar"
            else f"Connecting the underlying cause-and-effect mechanism behind {lesson_input.topic} rather than memorizing formulas."
        )
    clean["cognitive_bottleneck"] = bottleneck

    expl = str(clean.get("simplified_explanation") or "").strip()
    if len(expl) < 10:
        excerpt = " ".join(lesson_input.raw_text.strip().split())
        expl = excerpt[:240] if len(excerpt) >= 10 else f"{core}: {excerpt}"
    clean["simplified_explanation"] = expl

    baseline = _coerce_finite_float(clean.get("baseline_grade_level"), 0.0)
    if baseline <= 0.0:
        baseline = calculate_grade_level(lesson_input.raw_text, language=lesson_input.language)
    clean["baseline_grade_level"] = min(12.0, max(1.0, baseline))

    raw_vars = clean.get("key_variables") if clean.get("key_variables") is not None else clean.get("variables")
    clean["key_variables"] = _sanitize_key_variables(raw_vars, lesson_input)
    return clean


def _build_fallback_deconstructed_data(lesson_input: LessonInput) -> dict[str, Any]:
    """Deterministic Pair 1 fallback used only after all non-auth JSON/schema retries are exhausted."""
    eq_match = re.search(r"([A-Za-z\[\]\u0621-\u064A_]{1,12}\s*=\s*[^.\n;،]{2,60})", lesson_input.raw_text)
    target_eq = eq_match.group(1).strip() if eq_match else lesson_input.topic

    # Extract ASCII variable tokens from detected equation when available
    var_candidates: list[dict[str, Any]] = []
    if eq_match and "=" in target_eq:
        rhs = target_eq.split("=", 1)[1]
        tokens = re.findall(r"\b([A-Za-z][A-Za-z0-9_]{0,4})\b", rhs)
        skip = {"pow", "sqrt", "log", "log10", "sin", "cos", "tan", "exp", "abs", "min", "max"}
        seen: set[str] = set()
        for tok in tokens:
            if tok.lower() in skip or tok in seen:
                continue
            seen.add(tok)
            var_candidates.append({
                "name": tok,
                "symbol": tok,
                "unit": "",
                "min_val": 1.0,
                "max_val": 20.0,
                "default_val": 5.0,
            })

    return _sanitize_deconstructed_data(
        {
            "core_concept": f"{lesson_input.topic} ({lesson_input.subject})",
            "target_equation_or_steps": target_eq,
            "cognitive_bottleneck": (
                f"ربط المتغيرات الأساسية عملياً في درس {lesson_input.topic}."
                if lesson_input.language == "ar"
                else f"Visualizing how key variables interact in {lesson_input.topic}."
            ),
            "baseline_grade_level": calculate_grade_level(lesson_input.raw_text, language=lesson_input.language),
            "simplified_explanation": " ".join(lesson_input.raw_text.strip().split())[:260],
            "key_variables": var_candidates,
        },
        lesson_input,
    )


def _normalize_engine_type(raw_engine: Any, target_eq: str, key_vars: list[dict[str, Any]]) -> EngineType:
    """Resolve Agent 1B engine selection with synonym normalization and safe routing fallback."""
    token = str(raw_engine or "").strip().lower()
    aliases = {
        "slider": EngineType.SLIDER,
        "sliders": EngineType.SLIDER,
        "simulation": EngineType.SLIDER,
        "stepper": EngineType.STEPPER,
        "step": EngineType.STEPPER,
        "steps": EngineType.STEPPER,
        "timeline": EngineType.STEPPER,
        "diagram": EngineType.DIAGRAM,
        "graph": EngineType.DIAGRAM,
        "network": EngineType.DIAGRAM,
        "flowchart": EngineType.DIAGRAM,
        "balance": EngineType.BALANCE,
        "scale": EngineType.BALANCE,
        "sort": EngineType.BALANCE,
        "quiz": EngineType.BALANCE,
    }
    if token in aliases:
        return aliases[token]
    for eng in EngineType:
        if eng.value in token:
            return eng
    return EngineType.SLIDER if ("=" in target_eq and len(key_vars) >= 1) else EngineType.STEPPER


def _validate_agent_1a_schema(data: dict[str, Any], lesson_input: LessonInput) -> None:
    """Verify sanitized Agent 1A dictionary constructs DeconstructedConcept cleanly before continuing."""
    DeconstructedConcept(
        original_input=lesson_input,
        core_concept=data["core_concept"],
        target_equation_or_steps=data["target_equation_or_steps"],
        cognitive_bottleneck=data["cognitive_bottleneck"],
        baseline_grade_level=float(data["baseline_grade_level"]),
        simplified_explanation=data["simplified_explanation"],
        key_variables=data["key_variables"],
        recommended_engine=EngineType.SLIDER,
        engine_justification="Schema validation check.",
    )


def run_pair1(lesson_input: LessonInput, model=None) -> DeconstructedConcept:
    """
    Executes Pair 1 sequentially: Agent 1A (ConceptExtractor) then Agent 1B (ArchetypeRouter).

    Parameters:
        lesson_input: Validated student input.
        model: Optional language model override.

    Returns:
        DeconstructedConcept containing analyzed concept, key variables, and recommended engine.

    Raises:
        ValueError: If authentication fails or final contract assembly fails.
    """
    agent_1a = create_agent_1a(model=model)
    agent_1b = create_agent_1b(model=model)

    ped_directive = get_pedagogical_directive(lesson_input.student_grade, lesson_input.language)

    lang_directive = (
        "CRITICAL: The target language is Arabic (العربية). You MUST write simplified_explanation, core_concept, and cognitive_bottleneck entirely in Modern Standard Arabic (العربية الفصحى)."
        if lesson_input.language == "ar"
        else "The target language is English. Write all fields in English."
    )

    prompt_1a = (
        f"Analyze this educational text and extract the concept.\n"
        f"Subject: {lesson_input.subject}\n"
        f"Topic: {lesson_input.topic}\n"
        f"Student Grade: {lesson_input.student_grade} ({ped_directive['tier_label']})\n"
        f"Language: {lesson_input.language}\n"
        f"Directive: {lang_directive}\n\n"
        f"{ped_directive['concept_guidance']}\n\n"
        f"Text:\n{lesson_input.raw_text}"
    )

    def _normalize_and_check_1a(raw_dict: dict[str, Any]) -> dict[str, Any]:
        cleaned = _sanitize_deconstructed_data(raw_dict, lesson_input)
        _validate_agent_1a_schema(cleaned, lesson_input)
        return cleaned

    try:
        data_1a = invoke_agent_for_json(
            agent_1a,
            prompt_1a,
            max_json_attempts=3,
            normalizer=_normalize_and_check_1a,
            required_hint=(
                "JSON object with keys: core_concept, target_equation_or_steps, cognitive_bottleneck, "
                "baseline_grade_level, simplified_explanation, key_variables "
                "(non-empty list of objects with name, symbol, unit, min_val, max_val, default_val)."
            ),
            agent_label="Agent 1A: ConceptExtractor",
        )
    except Exception as exc:
        if is_non_retryable_provider_error(exc):
            raise
        logger.warning(f"[Pair 1] Agent 1A exhausted retries ({exc}); engaging deterministic concept fallback.")
        data_1a = _build_fallback_deconstructed_data(lesson_input)

    # 2. Run Agent 1B
    prompt_1b = (
        f"Choose the best engine for this concept:\n"
        f"{json.dumps(data_1a, ensure_ascii=False)}"
    )

    try:
        data_1b = invoke_agent_for_json(
            agent_1b,
            prompt_1b,
            max_json_attempts=2,
            required_hint='JSON object with keys "recommended_engine" ("slider"|"stepper"|"diagram"|"balance") and "engine_justification".',
            agent_label="Agent 1B: ArchetypeRouter",
        )
    except Exception as exc:
        if is_non_retryable_provider_error(exc):
            raise
        logger.warning(f"[Pair 1] Agent 1B exhausted retries ({exc}); engaging deterministic routing fallback.")
        data_1b = {}

    target_eq = str(data_1a.get("target_equation_or_steps", ""))
    key_vars = data_1a.get("key_variables", [])
    recommended_engine = _normalize_engine_type(data_1b.get("recommended_engine"), target_eq, key_vars)

    # Deterministic safeguard: If target_equation_or_steps contains an algebraic equation ('=')
    # and key_variables has at least one variable, it is fundamentally quantitative and should run in the slider engine.
    if recommended_engine == EngineType.STEPPER and "=" in target_eq and len(key_vars) >= 1:
        recommended_engine = EngineType.SLIDER
        data_1b["engine_justification"] = (
            f"Promoted to SLIDER engine because concept contains a quantitative equation ({target_eq}) "
            f"with {len(key_vars)} manipulable variable(s) suitable for 2D dynamic simulation."
        )

    # 3. Assemble and validate DeconstructedConcept
    try:
        deconstructed = DeconstructedConcept(
            original_input=lesson_input,
            core_concept=data_1a["core_concept"],
            target_equation_or_steps=data_1a["target_equation_or_steps"],
            cognitive_bottleneck=data_1a["cognitive_bottleneck"],
            baseline_grade_level=float(data_1a["baseline_grade_level"]),
            simplified_explanation=data_1a["simplified_explanation"],
            key_variables=data_1a["key_variables"],
            recommended_engine=recommended_engine,
            engine_justification=data_1b.get("engine_justification", "Best fit for interactive learning.")
        )
    except Exception as exc:
        raise ValueError(f"Failed to construct DeconstructedConcept: {exc}") from exc

    return deconstructed


# Alias for compatibility with prompt phrasing
run_pair1_deconstruct = run_pair1
