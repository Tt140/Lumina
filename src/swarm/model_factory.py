"""LuminaLab Swarm - Model Factory and Local Mock Model for Strands SDK."""

import json
from typing import Any, AsyncGenerator
from strands.models.model import Model
from src.config import get_config


class MockModel(Model):
    """
    Local mock model for testing and offline execution.
    Compatible with the strands.Agent interface without requiring external API keys.
    """

    def __init__(self, **config_overrides: Any):
        self._config: dict[str, Any] = config_overrides

    def update_config(self, **model_config: Any) -> None:
        """Update model configuration."""
        self._config.update(model_config)

    def get_config(self) -> dict[str, Any]:
        """Return model configuration."""
        return self._config

    async def structured_output(self, output_model: Any, prompt: Any, system_prompt: str | None = None, **kwargs: Any) -> AsyncGenerator[dict[str, Any], None]:
        """Structured output fallback generator."""
        yield {"output": output_model()}

    def _extract_prompt_text(self, messages: Any) -> str:
        """Extract all textual content from incoming prompt messages."""
        if isinstance(messages, str):
            return messages

        text_parts = []
        if isinstance(messages, list):
            for msg in messages:
                if isinstance(msg, dict):
                    content = msg.get("content", "")
                    if isinstance(content, str):
                        text_parts.append(content)
                    elif isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and "text" in block:
                                text_parts.append(block["text"])
                            elif hasattr(block, "text"):
                                text_parts.append(getattr(block, "text"))
                elif hasattr(msg, "content"):
                    content = getattr(msg, "content")
                    if isinstance(content, str):
                        text_parts.append(content)
        return " ".join(text_parts)

    def _generate_response(self, text: str) -> str:
        """Generate structured JSON response based on prompt context."""
        import re
        text_lower = text.lower()

        # Isolate educational concept context from generic system prompt instructions
        # to prevent candidate archetypes listed in instructions ('spring', 'circuit', etc.) from hijacking concept matching
        context_split = text_lower.split("instructions:")[0].split("selection guidelines")[0].split("guidelines:")[0]

        def _match_words(patterns: list[str]) -> bool:
            for p in patterns:
                if re.search(r"\b" + re.escape(p) + r"\b", context_split, re.IGNORECASE):
                    return True
            return False

        is_lever = _match_words(["lever", "torque", "fulcrum", "seesaw", "arm", "رافعة", "عزم", "أرجوحة"])
        is_hooke = _match_words(["hooke", "spring", "elastic", "elasticity", "زنبرك", "نابض", "مرونة"])
        is_ph = _match_words(["ph scale", "ph value", "hydrogen ion", "acid", "acids", "alkaline", "titrat", "beaker", "حمض", "أحماض", "قاعدة كيميائية", "قلوي", "بي اتش"])
        is_ohm = (_match_words(["ohm", "ohms", "voltage", "current", "resistor", "resistance", "ampere", "volt", "أوم", "دائرة كهربائية", "جهد", "تيار", "مقاومة"]) or _match_words(["circuit"])) and not is_ph

        # 1. Agent 1A: Concept Extraction
        if any(k in text_lower for k in ["analyze this educational text", "extract the concept", "conceptextractor", "original_input"]):
            if is_lever:
                return json.dumps({
                    "core_concept": "Mechanical Equilibrium of Levers: Balance of Clockwise and Counterclockwise Torques",
                    "target_equation_or_steps": "Effort × Effort Arm = Load × Load Arm",
                    "cognitive_bottleneck": "Students confuse force with torque, missing that increasing the effort arm distance multiplies leverage.",
                    "baseline_grade_level": 6.0,
                    "simplified_explanation": "A lever acts like a playground seesaw: a smaller effort force far from the fulcrum balances a heavy load close to the fulcrum.",
                    "key_variables": [
                        {"name": "Effort Force", "symbol": "F_e", "unit": "N", "min_val": 1.0, "max_val": 100.0, "default_val": 10.0},
                        {"name": "Effort Arm", "symbol": "d_e", "unit": "m", "min_val": 0.5, "max_val": 5.0, "default_val": 2.0},
                        {"name": "Load Force", "symbol": "F_l", "unit": "N", "min_val": 1.0, "max_val": 200.0, "default_val": 20.0},
                        {"name": "Load Arm", "symbol": "d_l", "unit": "m", "min_val": 0.5, "max_val": 5.0, "default_val": 1.0}
                    ]
                }, ensure_ascii=False)

            if is_hooke:
                return json.dumps({
                    "core_concept": "Hooke's Law: Elastic Deformation of Springs",
                    "target_equation_or_steps": "F = k * x",
                    "cognitive_bottleneck": "Students forget that displacement is measured relative to equilibrium position.",
                    "baseline_grade_level": 7.0,
                    "simplified_explanation": "The more you pull or compress a spring, the harder it pulls back in direct proportion.",
                    "key_variables": [
                        {"name": "Spring Constant", "symbol": "k", "unit": "N/m", "min_val": 10.0, "max_val": 200.0, "default_val": 50.0},
                        {"name": "Displacement", "symbol": "x", "unit": "m", "min_val": 0.01, "max_val": 1.0, "default_val": 0.2}
                    ]
                }, ensure_ascii=False)

            if is_ph:
                return json.dumps({
                    "core_concept": "Acids, Bases and the Logarithmic pH Scale",
                    "target_equation_or_steps": "[H+] = pow(10, -pH)",
                    "cognitive_bottleneck": "Students miss that each single unit change in pH represents a tenfold change in hydrogen ion concentration.",
                    "baseline_grade_level": 8.0,
                    "simplified_explanation": "pH measures how acidic or basic a solution is on a scale from 0 to 14, where 7 is neutral water.",
                    "key_variables": [
                        {"name": "pH Value", "symbol": "pH", "unit": "", "min_val": 1.0, "max_val": 14.0, "default_val": 7.0},
                        {"name": "Hydrogen Ion Concentration", "symbol": "[H+]", "unit": "mol/L", "min_val": 1e-14, "max_val": 0.1, "default_val": 1e-7}
                    ]
                }, ensure_ascii=False)

            # Default: Ohm's Law
            return json.dumps({
                "core_concept": "Ohm's Law: Relationship between Voltage, Current, and Resistance",
                "target_equation_or_steps": "V = I * R",
                "cognitive_bottleneck": "Students struggle with the inverse relationship between resistance and current",
                "baseline_grade_level": 8.0,
                "simplified_explanation": "Voltage pushes electric current through a conductor, while resistance opposes it like a narrow pipe.",
                "key_variables": [
                    {"name": "Voltage", "symbol": "V", "unit": "Volt", "min_val": 0.0, "max_val": 220.0, "default_val": 12.0},
                    {"name": "Current", "symbol": "I", "unit": "Ampere", "min_val": 0.1, "max_val": 10.0, "default_val": 2.0},
                    {"name": "Resistance", "symbol": "R", "unit": "Ohm", "min_val": 1.0, "max_val": 100.0, "default_val": 6.0}
                ]
            }, ensure_ascii=False)

        # 2. Agent 1B: Archetype Routing
        if any(k in text_lower for k in ["choose the best engine", "archetyperouter", "recommended_engine", "best engine"]):
            if is_lever:
                return json.dumps({
                    "recommended_engine": "slider",
                    "engine_justification": "The lever concept is governed by rotational torque equilibrium around a central pivot fulcrum."
                }, ensure_ascii=False)

            return json.dumps({
                "recommended_engine": "slider",
                "engine_justification": "The concept involves continuous physical variables connected by a mathematical equation."
            }, ensure_ascii=False)

        # 3. Agent 2A: Simulation Math Architect
        if any(k in text_lower for k in ["create simulation parameters", "simulationmatharchitect", "formula_expression", "simulation specification"]):
            if is_hooke:
                return json.dumps({
                    "engine_type": "slider",
                    "title": "Hooke's Law & Spring Elasticity Lab",
                    "variables": [
                        {"name": "Spring Constant", "symbol": "k", "unit": "N/m", "min_val": 10.0, "max_val": 200.0, "default_val": 50.0},
                        {"name": "Displacement", "symbol": "x", "unit": "m", "min_val": 0.01, "max_val": 1.0, "default_val": 0.2}
                    ],
                    "formula_expression": "F = k * x",
                    "visual_archetype": "spring",
                    "visual_svg": "",
                    "svg_bindings": {}
                }, ensure_ascii=False)

            if is_lever:
                return json.dumps({
                    "engine_type": "slider",
                    "title": "Interactive Lever & Mechanical Equilibrium Lab",
                    "variables": [
                        {"name": "Effort Arm", "symbol": "d_e", "unit": "m", "min_val": 0.5, "max_val": 5.0, "default_val": 2.0},
                        {"name": "Load Force", "symbol": "F_l", "unit": "N", "min_val": 5.0, "max_val": 100.0, "default_val": 20.0},
                        {"name": "Load Arm", "symbol": "d_l", "unit": "m", "min_val": 0.5, "max_val": 5.0, "default_val": 1.0}
                    ],
                    "formula_expression": "Effort × Effort Arm = Load × Load Arm",
                    "visual_archetype": "lever",
                    "visual_svg": "",
                    "svg_bindings": {}
                }, ensure_ascii=False)

            if is_ph:
                return json.dumps({
                    "engine_type": "slider",
                    "title": "Acids, Bases & pH Scale Lab",
                    "variables": [
                        {"name": "pH Value", "symbol": "pH", "unit": "", "min_val": 1.0, "max_val": 14.0, "default_val": 7.0},
                        {"name": "Hydrogen Ion Concentration", "symbol": "[H+]", "unit": "mol/L", "min_val": 1e-14, "max_val": 0.1, "default_val": 1e-7}
                    ],
                    "formula_expression": "[H+] = pow(10, -pH)",
                    "visual_archetype": "beaker",
                    "visual_svg": "",
                    "svg_bindings": {}
                }, ensure_ascii=False)

            # Default: Electrical Circuits / Ohm's Law
            return json.dumps({
                "engine_type": "slider",
                "title": "Interactive Ohm's Law Lab",
                "variables": [
                    {"name": "Current", "symbol": "I", "unit": "A", "min_val": 0.1, "max_val": 10.0, "default_val": 2.0},
                    {"name": "Resistance", "symbol": "R", "unit": "Ω", "min_val": 1.0, "max_val": 100.0, "default_val": 10.0}
                ],
                "formula_expression": "V = I * R",
                "visual_archetype": "circuit",
                "visual_svg": "",
                "svg_bindings": {}
            }, ensure_ascii=False)

        # 4. Agent 2B: Visual Renderer & Guard / Repair
        if any(k in text_lower for k in ["failed verification", "suggest fixes", "visualrendererandguard"]):
            return json.dumps({
                "status": "repaired",
                "message": "HTML structure and interactivity verified."
            }, ensure_ascii=False)

        # 5. Agent 3A: Sensory Accessibility
        if any(k in text_lower for k in ["accessibility pack", "sensoryaccessibility", "adhd_steps", "bionic"]):
            if is_lever:
                return json.dumps({
                    "adhd_steps": [
                        "🔵 First: Locate the fulcrum pivot point in the center of the beam.",
                        "🟡 Second: Distance multiplies turning effect — longer arm means less effort needed.",
                        "🟢 Finally: Test equilibrium when Left Torque equals Right Torque."
                    ],
                    "bionic_reading_html": "<b>Lev</b>ers <b>bal</b>ance <b>thr</b>ough <b>for</b>ce <b>ti</b>mes <b>dist</b>ance.",
                    "home_experiment": {
                        "title": "Ruler and Coin Seesaw",
                        "materials": ["1 30cm plastic ruler", "1 triangular pencil (fulcrum)", "5 identical coins"],
                        "steps": [
                            "Place the pencil under the 15cm mark of the ruler.",
                            "Place 1 coin at 30cm and see how many coins placed at 20cm balance it."
                        ],
                        "safety_note": "Ensure safe placement on a flat table surface."
                    },
                    "voice_script": "Welcome to the lever lab! Balance torque by adjusting distance from the fulcrum. You're doing great!"
                }, ensure_ascii=False)

            if is_hooke:
                return json.dumps({
                    "adhd_steps": [
                        "🔵 First: Notice the equilibrium position of the spring at rest.",
                        "🟡 Second: Pull the spring down to increase displacement x.",
                        "🟢 Finally: Observe how the restoring force increases directly with extension."
                    ],
                    "bionic_reading_html": "<b>Spr</b>ing <b>for</b>ce <b>sca</b>les <b>dir</b>ectly <b>wi</b>th <b>exten</b>sion.",
                    "home_experiment": {
                        "title": "Rubber Band Scale",
                        "materials": ["1 rubber band", "1 paperclip", "small weights or coins in a cup"],
                        "steps": [
                            "Suspend the rubber band from a hook.",
                            "Add coins to the cup and measure the elongation with a ruler."
                        ],
                        "safety_note": "Avoid over-stretching the rubber band."
                    },
                    "voice_script": "Welcome to the elasticity lab! Stiffer springs resist pulling with greater force."
                }, ensure_ascii=False)

            if is_ph:
                return json.dumps({
                    "adhd_steps": [
                        "🔵 First: Pure water sits at neutral pH 7 with balanced ions.",
                        "🟡 Second: Adding acid lowers pH towards 0 with high H+ concentration.",
                        "🟢 Finally: Adding base raises pH towards 14 with low H+ concentration."
                    ],
                    "bionic_reading_html": "<b>pH</b> <b>mea</b>sures <b>hy</b>drogen <b>con</b>centration <b>on</b> <b>log</b> <b>sca</b>le.",
                    "home_experiment": {
                        "title": "Red Cabbage pH Indicator",
                        "materials": ["Red cabbage leaves", "Warm water", "Lemon juice", "Baking soda"],
                        "steps": [
                            "Soak red cabbage in warm water to extract purple indicator liquid.",
                            "Add lemon juice to see it turn red (acid), or baking soda to turn green (base)."
                        ],
                        "safety_note": "Do not taste the indicator solution."
                    },
                    "voice_script": "Welcome to the chemistry lab! Each unit on the pH scale represents a tenfold change in concentration."
                }, ensure_ascii=False)

            # Default: Ohm's Law
            return json.dumps({
                "adhd_steps": [
                    "🔵 First: Voltage acts as pressure pushing charges through the wire.",
                    "🟡 Second: Resistance acts like a narrow pipe reducing flow.",
                    "🟢 Finally: Current is the resulting amount of electricity flowing through."
                ],
                "bionic_reading_html": "<b>Vol</b>tage <b>pus</b>hes <b>cur</b>rent <b>thr</b>ough <b>resis</b>tance.",
                "home_experiment": {
                    "title": "Kitchen Battery Circuit",
                    "materials": ["1 AA battery", "Small flashlight bulb", "Aluminum foil strip"],
                    "steps": [
                        "Fold the aluminum foil into a narrow conducting strip.",
                        "Touch one end to the battery base and the other to the bulb tip to light it."
                    ],
                    "safety_note": "Handle batteries with care under adult supervision."
                },
                "voice_script": "Let's learn something new today! Voltage pushes current through a resistor. You did an amazing job exploring this!"
            }, ensure_ascii=False)

        # 6. Agent 3B: Mastery & Socratic Challenge
        if any(k in text_lower for k in ["socratic challenge", "masteryandimpact", "challenge_question"]):
            if is_lever:
                return json.dumps({
                    "challenge_question": "If you double the distance of your effort arm from the fulcrum, how much effort force do you need to balance the same load?",
                    "challenge_hint": "Remember the lever formula: Effort × Effort Arm = Load × Load Arm. If distance doubles, what happens to required force?",
                    "challenge_answer": "You need only half (50%) of the effort force because mechanical advantage is doubled.",
                    "learning_observation": "The learner demonstrated understanding of torque equilibrium and mechanical advantage."
                }, ensure_ascii=False)

            if is_hooke:
                return json.dumps({
                    "challenge_question": "If you double the displacement of a spring, what happens to the restoring force it exerts?",
                    "challenge_hint": "Remember Hooke's Law: F = k * x. Notice the direct linear proportionality between F and x.",
                    "challenge_answer": "The restoring force doubles because force is directly proportional to displacement.",
                    "learning_observation": "The learner understood linear spring elasticity."
                }, ensure_ascii=False)

            if is_ph:
                return json.dumps({
                    "challenge_question": "If a solution's pH decreases from 7 to 5, by what factor does the hydrogen ion concentration increase?",
                    "challenge_hint": "Remember that the pH scale is logarithmic: each single step represents a factor of 10.",
                    "challenge_answer": "The concentration increases by 100 times (10 to the power of 2) because each pH unit is a tenfold change.",
                    "learning_observation": "The learner mastered the logarithmic nature of the pH scale."
                }, ensure_ascii=False)

            # Default: Ohm's Law
            return json.dumps({
                "challenge_question": "What happens to the electric current if you double the resistance while keeping voltage unchanged?",
                "challenge_hint": "Remember Ohm's law: I = V / R. Notice how current changes when the denominator doubles.",
                "challenge_answer": "The current is halved (reduced by 50%) because current is inversely proportional to resistance.",
                "learning_observation": "The learner grasped the inverse relationship between resistance and current."
            }, ensure_ascii=False)

        # Default fallback
        return json.dumps({
            "status": "success",
            "output": "Mock model response"
        }, ensure_ascii=False)

    async def stream(self, messages: Any, *args: Any, **kwargs: Any) -> AsyncGenerator[dict[str, Any], None]:
        """Stream conversational response in chunks expected by strands.Agent."""
        prompt_text = self._extract_prompt_text(messages)
        response_text = self._generate_response(prompt_text)

        yield {"messageStart": {"role": "assistant"}}
        yield {"contentBlockDelta": {"delta": {"text": response_text}}}
        yield {"contentBlockStop": {}}
        yield {"messageStop": {"stopReason": "end_turn"}}
        yield {"metadata": {"usage": {"inputTokens": 10, "outputTokens": len(response_text) // 4, "totalTokens": 10 + len(response_text) // 4}}}

    def __call__(self, prompt: Any = None, *args: Any, **kwargs: Any) -> str:
        """Allow direct callable invocations for testing."""
        return self._generate_response(str(prompt or ""))


def get_model(model_id: str | None = None, api_key: str | None = None):
    """
    Returns a model object suitable for strands.Agent with universal provider support:

    1. Mock Mode (Local Deterministic Swarm):
       - If LUMINA_MOCK_MODE=True -> returns MockModel (zero internet, 100% offline).

    2. Universal OpenAI-Compatible API Key Mode:
       - Supports:
         a) AWS Bedrock Mantle Bearer Keys (with OPENAI_BASE_URL="https://bedrock-mantle.<region>.api.aws/v1")
         b) Native DeepSeek Platform Keys (sk-... with https://api.deepseek.com or custom base URL)
         c) Standard OpenAI Keys (sk-... with official OpenAI endpoint)
       - If LUMINA_MOCK_MODE=False and (api_key or config.BEDROCK_API_KEY):
         Uses strands.models.openai.OpenAIModel with dynamic client_args (base_url, api_key).

    3. Standard AWS IAM Credentials Mode:
       - If LUMINA_MOCK_MODE=False and no api_key:
         Standard SigV4 AWS IAM authentication via boto3.
    """
    config = get_config(reload=True)
    if config.LUMINA_MOCK_MODE:
        return MockModel()

    resolved_api_key = api_key or config.BEDROCK_API_KEY
    resolved_model_id = model_id or config.BEDROCK_MODEL_ID
    if resolved_model_id and resolved_model_id.startswith("bedrock:"):
        resolved_model_id = resolved_model_id.split("bedrock:", 1)[1]

    # Use OpenAIModel when an explicit base URL is configured or when using native platform keys (sk-*)
    use_openai = bool(config.LLM_BASE_URL or (resolved_api_key and resolved_api_key.startswith("sk-")))

    if use_openai and resolved_api_key:
        from strands.models.openai import OpenAIModel

        client_args: dict[str, Any] = {"api_key": resolved_api_key}
        if config.LLM_BASE_URL:
            client_args["base_url"] = config.LLM_BASE_URL

        return OpenAIModel(
            model_id=resolved_model_id,
            client_args=client_args,
        )
    else:
        from strands.models.bedrock import BedrockModel
        model_kwargs: dict[str, Any] = {
            "model_id": resolved_model_id,
            "region_name": config.AWS_REGION,
        }
        if resolved_api_key:
            model_kwargs["api_key"] = resolved_api_key
        return BedrockModel(**model_kwargs)

