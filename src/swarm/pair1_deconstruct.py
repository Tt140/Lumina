"""LuminaLab Swarm - Pair 1: Concept Deconstruction and Archetype Routing."""

import json
import re
from typing import Any
from strands import Agent, tool
from src.contracts.schemas import LessonInput, DeconstructedConcept, EngineType
from src.swarm.model_factory import get_model
from src.tools.impact_calculator import calculate_grade_level


from src.swarm.pedagogical_calibration import parse_student_grade, get_pedagogical_directive
from src.swarm.terminal_stream import get_hackathon_callback_handler


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


def run_pair1(lesson_input: LessonInput, model=None) -> DeconstructedConcept:
    """
    Executes Pair 1 sequentially: Agent 1A (ConceptExtractor) then Agent 1B (ArchetypeRouter).

    Parameters:
        lesson_input: Validated student input.
        model: Optional language model override.

    Returns:
        DeconstructedConcept containing analyzed concept, key variables, and recommended engine.

    Raises:
        ValueError: If agent output cannot be parsed or validated against schemas.
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

    try:
        res_1a = agent_1a(prompt_1a)
        text_1a = _get_agent_response_text(res_1a)
        data_1a = _extract_json_dict(text_1a)
    except Exception as exc:
        raise ValueError(f"Failed to parse Agent 1A response: {exc}") from exc

    # Ensure baseline grade level is present and computed
    baseline_grade = data_1a.get("baseline_grade_level")
    if baseline_grade is None or baseline_grade <= 0.0:
        data_1a["baseline_grade_level"] = calculate_grade_level(lesson_input.raw_text, language=lesson_input.language)

    # 2. Run Agent 1B
    prompt_1b = (
        f"Choose the best engine for this concept:\n"
        f"{json.dumps(data_1a, ensure_ascii=False)}"
    )

    try:
        res_1b = agent_1b(prompt_1b)
        text_1b = _get_agent_response_text(res_1b)
        data_1b = _extract_json_dict(text_1b)
    except Exception as exc:
        raise ValueError(f"Failed to parse Agent 1B response: {exc}") from exc

    engine_str = data_1b.get("recommended_engine", "slider").lower()
    try:
        recommended_engine = EngineType(engine_str)
    except ValueError as exc:
        raise ValueError(f"Invalid recommended_engine returned by Agent 1B: {engine_str}") from exc

        # Deterministic safeguard: If target_equation_or_steps contains an algebraic equation ('=')
    # and key_variables has at least one variable, it is fundamentally quantitative and should run in the slider engine.
    target_eq = str(data_1a.get("target_equation_or_steps", ""))
    key_vars = data_1a.get("key_variables", [])
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
