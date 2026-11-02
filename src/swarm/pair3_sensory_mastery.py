"""LuminaLab Swarm - Pair 3: Sensory Accessibility Adaptation and Socratic Mastery."""

import json
import re
from typing import Any
from strands import Agent, tool
from src.contracts.schemas import DeconstructedConcept, AccessibilityPack
from src.swarm.model_factory import get_model
from src.tools.accessibility_tools import (
    bionic_reading_format,
    adhd_micro_chunk,
    generate_home_experiment_template,
    generate_voice_script,
)
from src.swarm.pedagogical_calibration import parse_student_grade, get_pedagogical_directive
from src.swarm.terminal_stream import get_hackathon_callback_handler



@tool
def format_bionic_reading(text: str) -> dict:
    """Formats text in Bionic Reading style for dyslexia accessibility."""
    return {"bionic_html": bionic_reading_format(text)}


@tool
def chunk_for_adhd(explanation: str, language: str = "ar") -> dict:
    """Splits explanation into 3 focused ADHD-friendly steps."""
    return {"steps": adhd_micro_chunk(explanation, num_steps=3, language=language)}


@tool
def create_voice_script(simplified_explanation: str, step1: str, step2: str, step3: str, language: str = "ar") -> dict:
    """Creates a voice-over script for audio synthesis."""
    steps = [step1, step2, step3]
    return {"script": generate_voice_script(simplified_explanation, steps, language=language)}


def create_agent_3a(model=None) -> Agent:
    """
    Creates Agent 3A (SensoryAccessibilityAdapter).
    Generates ADHD-focused steps, bionic reading, home experiment, and voice script.
    """
    system_prompt = (
        "You are an expert sensory accessibility and neurodiversity learning designer.\n"
        "Your task is to adapt educational concepts into an engaging multi-sensory accessibility package:\n"
        "1. ADHD MICRO-CHUNKED DOPAMINE LOOP: Exactly 3 concise, action-oriented micro-steps with visual icons (🔵, 🟡, 🟢) directly linked to the interactive simulation:\n"
        "   - 🔵 Step 1 (Predict & Move): Direct the student to manipulate a specific slider variable and actively watch the corresponding moving element in the visual 2D simulation.\n"
        "   - 🟡 Step 2 (Spot the Pattern): Direct the student to correlate the visual movement/change directly to the numerical result or meter (instant cause-and-effect).\n"
        "   - 🟢 Step 3 (The 'Aha!' Takeaway): The unforgettable conceptual core takeaway summarized in one crisp sentence.\n"
        "2. Dyslexia: Bionic reading format with whole-word or stem eye-fixation anchors.\n"
        "3. Free home experiment: Using only kitchen/household items (minimum 2 materials, minimum 2 steps, and a safety note).\n"
        "CRITICAL VOICE SCRIPT DIRECTIVE (DYNAMIC GRADE-ADAPTIVE PEDAGOGICAL CAPSULE):\n"
        "For 'voice_script', write an engaging, audio-narrated learning capsule strictly tailored to the Student's Grade Level and Cognitive Maturity:\n"
        "1. FOR HIGH SCHOOL SENIORS (Grades 10, 11, 12 — e.g. Pre-University, Senior Chemistry/Physics):\n"
        "   - TONE: Address the student respectfully as an aspiring young scientist or engineer. Engaging, direct, punchy, and intellectually stimulating.\n"
        "   - FORBIDDEN: NEVER use juvenile baby-talk like 'Hey champion!', 'champ', 'superhero flavor squad', or childish cartoon analogies! Treat them as 17-18 year olds.\n"
        "   - CONTENT: Provide intuitive physical intuition and real-world mechanisms (e.g. human blood pH buffer regulation, circuit surge protection, bridge structural elasticity). Demystify the governing equation (e.g. Henderson-Hasselbalch, Ohm's law) with clear cause-and-effect, and guide them to interact with the simulation parameters.\n"
        "2. FOR MIDDLE SCHOOL (Grades 7, 8, 9 — Ages 12-14):\n"
        "   - TONE: Energetic, curious, relatable mentor with interactive challenge tone.\n"
        "   - CONTENT: Tangible analogies from daily life, sports, and sensory reactions. Clear cause-and-effect without heavy jargon.\n"
        "3. FOR ELEMENTARY (Grades 1, 2, 3, 4, 5, 6 — Ages 6-11):\n"
        "   - TONE: Warm, playful, encouraging mentor ('Hey explorer!' / 'يا بطل').\n"
        "   - CONTENT: Fun story-driven physical metaphors.\n"
        "4. FOR ALL GRADES:\n"
        "   - Avoid dry, monotonous textbook recitation.\n"
        "   - Keep length between 40 to 80 words (around 20-30 seconds of high-impact spoken audio).\n"
        "   - Accurately reflect authentic science (e.g. never confuse chemical buffer equilibrium with sweetness!).\n"
        "   - If Language is 'ar', use clear, friendly, accessible Egyptian/Modern Arabic (لهجة بيضاء راقية ومحترمة) tailored to the grade level.\n\n"
        "Output strictly valid JSON:\n"
        "{\n"
        '  "adhd_steps": ["🔵 First: ...", "🟡 Second: ...", "🟢 Finally: ..."],\n'
        '  "bionic_reading_html": "...",\n'
        '  "home_experiment": {\n'
        '    "title": "...",\n'
        '    "materials": ["item1", "item2"],\n'
        '    "steps": ["step1", "step2"],\n'
        '    "safety_note": "..."\n'
        '  },\n'
        '  "voice_script": "..."\n'
        "}\n"
        "Ensure adhd_steps contains exactly 3 items, and materials and steps in home_experiment have at least 2 items each.\n"
        "CRITICAL LANGUAGE ENFORCEMENT:\n"
        "If Language is 'ar', all outputs (adhd_steps, bionic_reading_html, home_experiment, voice_script) MUST be written in accessible Egyptian-friendly Arabic (المصرية البيضاء الواضحة والممتعة للطفل العربي).\n"
        "Format Arabic adhd_steps strictly with Arabic ordinal prefixes: ['🔵 أولاً: ...', '🟡 ثانياً: ...', '🟢 أخيراً: ...'].\n"
        "Never output English words or steps when Language is 'ar'.\n"
        "If Language is 'en', format adhd_steps with ['🔵 First: ...', '🟡 Then: ...', '🟢 Finally: ...'].\n"
        "If Language is 'en', output strictly in fluent English without any Arabic keys or text."
    )
    return Agent(
        model=model or get_model(),
        system_prompt=system_prompt,
        tools=[format_bionic_reading, chunk_for_adhd, create_voice_script],
        callback_handler=get_hackathon_callback_handler("Agent 3A: SensoryAdapter")
    )


def create_agent_3b(model=None) -> Agent:
    """
    Creates Agent 3B (MasteryAndImpactRecorder).
    Designs a Socratic challenge question, hint, and model answer.
    """
    system_prompt = (
        "You are a Socratic tutor and learning mastery evaluator.\n"
        "Design a single thought-provoking conceptual challenge question based on the interactive lab, strictly calibrated to the student's cognitive maturity:\n"
        "- For High School (10-12): Deep conceptual mechanism question testing underlying physical intuition without rote calculation.\n"
        "- For Middle School (7-9): Direct cause-and-effect inquiry ('What happens to Y when you double X?').\n"
        "- For Elementary (1-6): Wonder-sparking, encouraging question based on the visual simulation.\n"
        "Include a helpful hint and a clear model answer.\n"
        "Output strictly valid JSON:\n"
        "{\n"
        '  "challenge_question": "...",\n'
        '  "challenge_hint": "...",\n'
        '  "challenge_answer": "...",\n'
        '  "learning_observation": "..."\n'
        "}\n"
        "If Language is 'en', output all fields strictly in English without non-English characters."
    )
    return Agent(
        model=model or get_model(),
        system_prompt=system_prompt,
        callback_handler=get_hackathon_callback_handler("Agent 3B: SocraticTutor")
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


def run_pair3(
    deconstructed: DeconstructedConcept,
    model=None
) -> tuple[AccessibilityPack, dict]:
    """
    Executes Pair 3: Agent 3A (Sensory Accessibility) and Agent 3B (Socratic Challenge).

    Parameters:
        deconstructed: Concept output from Pair 1.
        model: Optional language model override.

    Returns:
        tuple[AccessibilityPack, dict]
    """
    lang = deconstructed.original_input.language
    expl = deconstructed.simplified_explanation

    # 1. Run Agent 3A
    agent_3a = create_agent_3a(model=model)
    lang_instruction = (
        "CRITICAL: Output all fields (adhd_steps, bionic_reading_html, home_experiment, voice_script) in 100% Modern Standard Arabic (العربية الفصحى). Format adhd_steps with ['🔵 أولاً: ...', '🟡 ثانياً: ...', '🟢 أخيراً: ...']. No English words permitted."
        if lang == "ar"
        else "Output all fields in English."
    )
    grade = parse_student_grade(deconstructed.original_input.student_grade)
    ped_directive = get_pedagogical_directive(grade, lang)

    prompt_3a = (
        f"Create an accessibility pack for this concept:\n"
        f"Subject: {deconstructed.original_input.subject}\n"
        f"Topic: {deconstructed.original_input.topic}\n"
        f"Simplified Explanation: {expl}\n"
        f"Language: {lang}\n"
        f"Student Grade: {grade} ({ped_directive['tier_label']})\n"
        f"Core Concept: {deconstructed.core_concept}\n"
        f"Target Equation/Steps: {deconstructed.target_equation_or_steps}\n"
        f"Simulation Variables: {json.dumps(deconstructed.key_variables, ensure_ascii=False)}\n\n"
        f"{ped_directive['adhd_guidance']}\n\n"
        f"Directive: {lang_instruction}\n"
        f"Return everything as JSON."
    )

    try:
        res_3a = agent_3a(prompt_3a)
        text_3a = _get_agent_response_text(res_3a)
        data_3a = _extract_json_dict(text_3a)
    except Exception:
        # Fallback to deterministic tools
        data_3a = {}

    # Safe defaults from deterministic tools if anything is missing
    adhd_steps = data_3a.get("adhd_steps")
    if not isinstance(adhd_steps, list) or len(adhd_steps) != 3:
        adhd_steps = adhd_micro_chunk(expl, num_steps=3, language=lang)

    bionic_html = data_3a.get("bionic_reading_html")
    if not bionic_html or "<b>" not in bionic_html:
        bionic_html = bionic_reading_format(expl)

    home_exp = data_3a.get("home_experiment")
    if (
        not isinstance(home_exp, dict)
        or not all(k in home_exp for k in ["title", "materials", "steps", "safety_note"])
        or len(home_exp.get("materials", [])) < 2
        or len(home_exp.get("steps", [])) < 2
    ):
        home_exp = generate_home_experiment_template(deconstructed.core_concept, language=lang)

    voice_script = data_3a.get("voice_script")
    if not voice_script:
        voice_script = generate_voice_script(expl, adhd_steps, language=lang, grade=grade)

    pack = AccessibilityPack(
        adhd_steps=adhd_steps,
        bionic_reading_html=bionic_html,
        home_experiment=home_exp,
        voice_script=voice_script,
        voice_audio_url=""
    )

    # 2. Run Agent 3B
    agent_3b = create_agent_3b(model=model)
    lang_instruction_3b = (
        "CRITICAL: Output challenge_question, challenge_hint, and challenge_answer entirely in Modern Standard Arabic (العربية الفصحى)."
        if lang == "ar"
        else "Output in English."
    )
    prompt_3b = (
        f"Design a Socratic challenge question for this concept:\n"
        f"Core Concept: {deconstructed.core_concept}\n"
        f"Equation/Steps: {deconstructed.target_equation_or_steps}\n"
        f"Simplified Explanation: {expl}\n"
        f"Student Grade: {grade} ({ped_directive['tier_label']})\n"
        f"Language: {lang}\n"
        f"{ped_directive['concept_guidance']}\n\n"
        f"Directive: {lang_instruction_3b}\n"
        f"Return as JSON."
    )

    try:
        res_3b = agent_3b(prompt_3b)
        text_3b = _get_agent_response_text(res_3b)
        data_3b = _extract_json_dict(text_3b)
    except Exception:
        data_3b = {}

    challenge_dict = {
        "challenge_question": data_3b.get("challenge_question")
        or (f"ما هو المفهوم الأساسي في {deconstructed.core_concept}؟" if lang == "ar" else f"What is the key takeaway in {deconstructed.core_concept}?"),
        "challenge_hint": data_3b.get("challenge_hint")
        or ("راجع الشرح المبسط أعلاه وتأمل العلاقة." if lang == "ar" else "Review the simplified explanation and check the equation relationship."),
        "challenge_answer": data_3b.get("challenge_answer") or expl,
        "partial_metrics": {
            "baseline_grade_level": deconstructed.baseline_grade_level,
            "learning_observation": data_3b.get("learning_observation", "Concept mastered.")
        }
    }

    return pack, challenge_dict
