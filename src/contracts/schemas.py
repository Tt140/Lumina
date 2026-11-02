"""LuminaLab Swarm - Core Contract Schemas (Pydantic Models)."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, field_validator, model_validator


class EngineType(str, Enum):
    """The four universal micro-lab engines."""
    SLIDER = "slider"
    STEPPER = "stepper"
    DIAGRAM = "diagram"
    BALANCE = "balance"


class LessonInput(BaseModel):
    """Student input representing the subject and topic to be deconstructed."""
    subject: str = Field(..., min_length=1, description="Subject name (e.g. Physics, Biology)")
    topic: str = Field(..., min_length=1, description="Topic name (e.g. Ohm's Law)")
    raw_text: str = Field(..., min_length=20, description="Raw textbook excerpt or concept explanation")
    student_grade: int = Field(..., ge=1, le=12, description="Target student grade (1-12)")
    language: str = Field(default="ar", description="Language of content ('ar' or 'en')")

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in ("ar", "en"):
            raise ValueError("language must be 'ar' or 'en'")
        return v


class DeconstructedConcept(BaseModel):
    """Output of Pair 1 (Agent 1A + 1B) - analyzed concept and recommended engine."""
    original_input: LessonInput
    core_concept: str = Field(..., min_length=5)
    target_equation_or_steps: str
    cognitive_bottleneck: str
    baseline_grade_level: float = Field(..., ge=1.0, le=12.0)
    simplified_explanation: str = Field(..., min_length=10)
    key_variables: list[dict[str, Any]] = Field(..., min_length=1)
    recommended_engine: EngineType
    engine_justification: str

    @field_validator("key_variables")
    @classmethod
    def validate_key_variables(cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not v:
            raise ValueError("key_variables must have at least one variable")
        required_keys = {"name", "symbol", "unit", "min_val", "max_val", "default_val"}
        for idx, var in enumerate(v):
            if not isinstance(var, dict):
                raise ValueError(f"Variable at index {idx} must be a dict")
            missing = required_keys - set(var.keys())
            if missing:
                raise ValueError(f"Variable at index {idx} missing keys: {missing}")
        return v


class SimulationSpec(BaseModel):
    """Mathematical and logical specification of the simulation - output of Agent 2A."""
    engine_type: EngineType
    title: str = Field(..., min_length=3)
    variables: list[dict[str, Any]] = Field(default_factory=list)
    formula_expression: str = Field(default="")
    result_symbol: str = Field(default="Result", description="Calculated dependent variable symbol, e.g. pH, F, V, P")
    result_unit: str = Field(default="", description="Physical unit of the calculated result, e.g. N, m, atm, m/s")
    result_min: float = Field(default=0.0, description="Authentic domain minimum bound for the calculated result")
    result_max: float = Field(default=100.0, description="Authentic domain maximum bound for the calculated result")
    is_logarithmic_output: bool = Field(default=False, description="True only if the output scale itself is logarithmic (e.g. dB), false for linear scales like pH")
    steps: list[dict[str, Any]] = Field(default_factory=list)
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    challenge_items: list[dict[str, Any]] = Field(default_factory=list)
    visual_archetype: str = Field(default="gauge", description="Visual archetype for STEM interactive lab")
    visual_svg: str = Field(default="", description="Generative SVG markup representing the physical phenomenon created by Agent 2A")
    svg_bindings: dict[str, Any] = Field(default_factory=dict, description="Declarative attribute bindings linking variables to SVG elements")
    constants: dict[str, float] = Field(default_factory=dict, description="Injected physical and scientific constants")
    size_kb: float = Field(default=0.0, ge=0.0)

    @model_validator(mode="after")
    def validate_engine_specs(self) -> "SimulationSpec":
        # Ensure result bounds are strictly valid
        if self.result_max <= self.result_min:
            self.result_max = self.result_min + (abs(self.result_min) if self.result_min != 0.0 else 10.0)

        if self.engine_type == EngineType.SLIDER:
            if len(self.variables) < 1 or not self.formula_expression.strip():
                raise ValueError("SLIDER engine requires at least one variable and non-empty formula_expression")
            if not self.visual_archetype or not self.visual_archetype.strip():
                raise ValueError("SLIDER engine requires a valid visual_archetype")
        elif self.engine_type == EngineType.STEPPER:
            if len(self.steps) < 1:
                raise ValueError("STEPPER engine requires at least one step")
        elif self.engine_type == EngineType.DIAGRAM:
            if len(self.nodes) < 2:
                raise ValueError("DIAGRAM engine requires at least two nodes")
        elif self.engine_type == EngineType.BALANCE:
            if len(self.challenge_items) < 2:
                raise ValueError("BALANCE engine requires at least two challenge items")
        return self


class VerifiedMicroLab(BaseModel):
    """Interactive micro-lab assembled by Agent 2B and verified by Sandbox Guard."""
    html_content: str = Field(..., min_length=50)
    engine_type: EngineType
    size_kb: float = Field(default=0.0, ge=0.0)
    passed_sandbox_guard: bool = Field(default=False)
    error_log: list[str] = Field(default_factory=list)
    repair_attempts: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def calculate_size_kb(self) -> "VerifiedMicroLab":
        if self.size_kb == 0.0:
            self.size_kb = len(self.html_content.encode("utf-8")) / 1024.0
        return self


class AccessibilityPack(BaseModel):
    """Neurodiversity and accessibility adaptations - output of Agent 3A."""
    adhd_steps: list[str]
    bionic_reading_html: str
    home_experiment: dict[str, Any]
    voice_script: str
    voice_audio_url: str = Field(default="")

    @field_validator("adhd_steps")
    @classmethod
    def validate_adhd_steps(cls, v: list[str]) -> list[str]:
        if len(v) != 3:
            raise ValueError("adhd_steps must contain exactly 3 items")
        return v

    @field_validator("home_experiment")
    @classmethod
    def validate_home_experiment(cls, v: dict[str, Any]) -> dict[str, Any]:
        required_keys = {"title", "materials", "steps", "safety_note"}
        missing = required_keys - set(v.keys())
        if missing:
            raise ValueError(f"home_experiment missing keys: {missing}")
        materials = v.get("materials")
        if not isinstance(materials, list) or len(materials) < 2:
            raise ValueError("home_experiment['materials'] must be a list with at least 2 items")
        steps = v.get("steps")
        if not isinstance(steps, list) or len(steps) < 2:
            raise ValueError("home_experiment['steps'] must be a list with at least 2 items")
        return v


class ImpactMetrics(BaseModel):
    """Deterministic societal impact metrics computed and recorded to DynamoDB."""
    baseline_grade_level: float = Field(..., ge=1.0, le=12.0)
    simplified_grade_level: float = Field(..., ge=1.0, le=12.0)
    grade_reduction: float = Field(default=0.0, ge=0.0)
    cognitive_load_reduction_pct: float = Field(..., ge=0.0, le=100.0)
    lab_size_kb: float = Field(..., ge=0.0)
    is_offline_ready: bool = Field(default=False)
    generation_time_sec: float = Field(..., ge=0.0)
    timestamp: str = Field(default="")

    @model_validator(mode="after")
    def compute_derived_fields(self) -> "ImpactMetrics":
        reduction = self.baseline_grade_level - self.simplified_grade_level
        self.grade_reduction = max(0.0, reduction)
        self.is_offline_ready = self.lab_size_kb < 200.0
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        return self


class LuminaResponse(BaseModel):
    """Complete aggregated output of the LuminaLab swarm."""
    lesson_input: LessonInput
    deconstructed: DeconstructedConcept
    simulation_spec: SimulationSpec
    verified_lab: VerifiedMicroLab
    accessibility: AccessibilityPack
    impact: ImpactMetrics
    swarm_trace: list[dict[str, Any]] = Field(default_factory=list)
    dynamo_receipt: dict[str, Any] = Field(default_factory=dict)
    s3_url: str = Field(default="")
    polly_audio_url: str = Field(default="")
