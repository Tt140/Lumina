"""LuminaLab Swarm - Main Swarm Orchestrator (Concurrent Multi-Agent Pipeline)."""

import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from src.contracts.schemas import LessonInput, LuminaResponse
from src.swarm.model_factory import get_model
from src.swarm.pair1_deconstruct import run_pair1
from src.swarm.pair2_interactive import run_pair2
from src.swarm.pair3_sensory_mastery import run_pair3
from src.tools.impact_calculator import build_impact_metrics
from src.aws.dynamo_ledger import DynamoImpactLedger
from src.aws.s3_polly_service import S3PollyService

logger = logging.getLogger("luminalab.orchestrator")
logger.setLevel(logging.INFO)


class LuminaSwarmOrchestrator:
    """
    Main swarm orchestrator coordinating all 6 specialized agents across 3 pairs.
    Executes Pair 1 sequentially, then runs Pair 2 and Pair 3 concurrently.
    Finally persists artifacts to AWS DynamoDB & S3/Polly (or local mock fallback).
    """

    def __init__(self, model=None):
        self.model = model or get_model()
        self.dynamo_ledger = DynamoImpactLedger()
        self.s3_polly_service = S3PollyService()

    def _run_parallel_pairs(self, deconstructed):
        """Executes Pair 2 and Pair 3 concurrently using ThreadPoolExecutor."""
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_pair2 = executor.submit(run_pair2, deconstructed, self.model)
            future_pair3 = executor.submit(run_pair3, deconstructed, self.model)
            pair2_res = future_pair2.result()
            pair3_res = future_pair3.result()
        return pair2_res, pair3_res

    def _build_swarm_trace(self, timings: dict[str, float]) -> list[dict[str, Any]]:
        """Constructs audit trace entries for all 6 agents."""
        t_pair1 = timings.get("t_pair1", 0.0)
        t_pair2 = timings.get("t_pair2", 0.0)
        t_pair3 = timings.get("t_pair3", 0.0)

        t_1a = int((t_pair1 / 2.0) * 1000)
        t_1b = int((t_pair1 / 2.0) * 1000)
        t_2a = int((t_pair2 / 2.0) * 1000)
        t_2b = int((t_pair2 / 2.0) * 1000)
        t_3a = int((t_pair3 / 2.0) * 1000)
        t_3b = int((t_pair3 / 2.0) * 1000)

        return [
            {"agent_name": "Agent_1A_ConceptExtractor", "action": "extract_concept", "duration_ms": max(1, t_1a), "status": "success"},
            {"agent_name": "Agent_1B_ArchetypeRouter", "action": "select_engine", "duration_ms": max(1, t_1b), "status": "success"},
            {"agent_name": "Agent_2A_SimMathArchitect", "action": "generate_spec", "duration_ms": max(1, t_2a), "status": "success"},
            {"agent_name": "Agent_2B_RendererGuard", "action": "render_and_verify", "duration_ms": max(1, t_2b), "status": "success"},
            {"agent_name": "Agent_3A_SensoryAdapter", "action": "create_accessibility", "duration_ms": max(1, t_3a), "status": "success"},
            {"agent_name": "Agent_3B_MasteryRecorder", "action": "design_challenge", "duration_ms": max(1, t_3b), "status": "success"},
        ]

    def run(self, lesson_input: LessonInput, include_aws: bool = True) -> LuminaResponse:
        """
        Executes the complete swarm pipeline:
        1. Pair 1 (sequential): Concept analysis and engine selection.
        2. Pair 2 & 3 (concurrent): Interactive lab generation & accessibility package.
        3. Impact calculation: Deterministic societal metrics.
        4. Assembly: Final LuminaResponse object.
        5. AWS Cloud Persistence: Record in DynamoDB and upload offline package to S3/Polly.
        """
        t_start = time.time()
        logger.info(
            f"[Swarm Orchestrator] Starting multi-agent pipeline: Topic='{lesson_input.topic}' "
            f"| Subject={lesson_input.subject} | Grade={lesson_input.student_grade} | Lang={lesson_input.language}"
        )

        # Step 1: Run Pair 1 sequentially
        t_p1_start = time.time()
        deconstructed = run_pair1(lesson_input, model=self.model)
        t_pair1 = time.time() - t_p1_start
        logger.info(
            f"[Swarm Orchestrator] Agent 1A (ConceptExtractor) -> Concept: '{deconstructed.core_concept}'"
        )
        logger.info(
            f"[Swarm Orchestrator] Agent 1B (ArchetypeRouter) -> Selected Engine: '{deconstructed.recommended_engine.value.upper()}' ({int(t_pair1 * 1000)}ms)"
        )

        # Step 2: Run Pair 2 and Pair 3 concurrently
        logger.info("[Swarm Orchestrator] Launching Pair 2 (Simulation & Guard) and Pair 3 (Sensory & Mastery) concurrently...")
        t_par_start = time.time()
        pair2_result, pair3_result = self._run_parallel_pairs(deconstructed)
        t_parallel = time.time() - t_par_start

        sim_spec, verified_lab = pair2_result
        accessibility_pack, challenge_data = pair3_result
        self.last_challenge = challenge_data

        logger.info(
            f"[Swarm Orchestrator] Agent 2A & 2B -> Engine: '{sim_spec.engine_type.value}', "
            f"Sandbox Guard: {'PASSED' if verified_lab.passed_sandbox_guard else 'REPAIRED'}, Size: {verified_lab.size_kb} KB, Variables: {len(sim_spec.variables)}"
        )
        logger.info(
            f"[Swarm Orchestrator] Agent 3A & 3B -> Accessibility Suite generated (Voice script, Bionic reading, ADHD steps, Socratic challenge) in {int(t_parallel * 1000)}ms"
        )

        # Step 3: Compute deterministic impact metrics
        t_total = time.time() - t_start
        impact = build_impact_metrics(
            original_text=lesson_input.raw_text,
            simplified_text=deconstructed.simplified_explanation,
            html_content=verified_lab.html_content,
            language=lesson_input.language,
            generation_time_sec=round(t_total, 3)
        )
        logger.info(
            f"[Swarm Orchestrator] Impact Metrics -> Baseline grade: {impact.baseline_grade_level} -> Simplified: {impact.simplified_grade_level} "
            f"(-{impact.cognitive_load_reduction_pct}% cognitive load), Lab size: {impact.lab_size_kb} KB"
        )

        # Step 4: Assemble complete LuminaResponse
        timings = {
            "t_pair1": t_pair1,
            "t_pair2": t_parallel,
            "t_pair3": t_parallel,
        }
        swarm_trace = self._build_swarm_trace(timings)

        response = LuminaResponse(
            lesson_input=lesson_input,
            deconstructed=deconstructed,
            simulation_spec=sim_spec,
            verified_lab=verified_lab,
            accessibility=accessibility_pack,
            impact=impact,
            swarm_trace=swarm_trace,
            dynamo_receipt={},
            s3_url="",
            polly_audio_url=""
        )

        # Step 5: AWS Cloud Persistence (Non-critical path, wrapped in try/except)
        if include_aws:
            session_id = str(uuid.uuid4())

            def _record_dynamo():
                t0 = time.time()
                status = "success"
                receipt = {}
                try:
                    receipt = self.dynamo_ledger.record_impact(response.impact, session_id=session_id)
                    if receipt.get("status") not in ("recorded", "recorded_local_fallback"):
                        status = "failed"
                except Exception:
                    status = "failed"
                dur = max(1, int((time.time() - t0) * 1000))
                return receipt, status, dur

            def _record_s3():
                t0 = time.time()
                status = "success"
                s3_url = ""
                audio_url = ""
                try:
                    offline_pkg = self.s3_polly_service.create_offline_package(
                        html_content=response.verified_lab.html_content,
                        voice_script=response.accessibility.voice_script,
                        session_id=session_id,
                        language=response.lesson_input.language,
                    )
                    s3_url = offline_pkg.get("s3_lab", {}).get("s3_url", "")
                    audio_url = offline_pkg.get("polly_audio", {}).get("audio_url", "")
                except Exception:
                    status = "failed"
                dur = max(1, int((time.time() - t0) * 1000))
                return s3_url, audio_url, status, dur

            with ThreadPoolExecutor(max_workers=2) as executor:
                f_dynamo = executor.submit(_record_dynamo)
                f_s3 = executor.submit(_record_s3)
                receipt, dynamo_status, t_dynamo_ms = f_dynamo.result()
                s3_url, audio_url, s3_status, t_s3_ms = f_s3.result()

            response.dynamo_receipt = receipt
            response.s3_url = s3_url
            response.polly_audio_url = audio_url
            if audio_url:
                response.accessibility.voice_audio_url = audio_url

            response.swarm_trace.append({
                "agent_name": "AWS_DynamoDB",
                "action": "record_impact",
                "duration_ms": t_dynamo_ms,
                "status": dynamo_status,
            })
            response.swarm_trace.append({
                "agent_name": "AWS_S3_Polly",
                "action": "create_offline_package",
                "duration_ms": t_s3_ms,
                "status": s3_status,
            })

            logger.info(
                f"[AWS Persistence] DynamoDB: {dynamo_status} ({t_dynamo_ms}ms) | S3/Polly: {s3_status} ({t_s3_ms}ms)"
            )

        logger.info(
            f"[Swarm Orchestrator] Pipeline finished successfully in {round(time.time() - t_start, 2)}s"
        )
        return response



# Aliases for compatibility
SwarmOrchestrator = LuminaSwarmOrchestrator


def run_swarm(lesson_input: LessonInput, model=None) -> LuminaResponse:
    """Convenience functional interface to execute the swarm."""
    orchestrator = LuminaSwarmOrchestrator(model=model)
    return orchestrator.run(lesson_input)
