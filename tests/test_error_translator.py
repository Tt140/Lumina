"""Tests for Transparent Error Translation and SimulationSpec Auto-Healing."""

import pytest
from pydantic import ValidationError

from src.contracts.schemas import EngineType, LessonInput, DeconstructedConcept, SimulationSpec
from src.swarm.error_translator import sanitize_error_text, translate_swarm_error
from src.swarm.pair2_interactive import _sanitize_simulation_spec, run_pair2


class TestErrorSanitization:
    def test_strip_api_keys(self):
        err = "Failed request with sk-1234567890abcdef1234567890"
        scrubbed = sanitize_error_text(err)
        assert "sk-1234567890" not in scrubbed
        assert "[REDACTED_API_KEY]" in scrubbed

    def test_strip_aws_credentials(self):
        err = "AWS Error: AKIAIOSFODNN7EXAMPLE using SessionToken=AQoDYXdzEJr1111111111111111"
        scrubbed = sanitize_error_text(err)
        assert "AKIAIOSFODNN7EXAMPLE" not in scrubbed
        assert "[REDACTED_AWS_KEY]" in scrubbed
        assert "AQoDYXdz" not in scrubbed

    def test_strip_bearer_token(self):
        err = "Authorization: Bearer secret_token_1234567890_value"
        scrubbed = sanitize_error_text(err)
        assert "secret_token_1234567890" not in scrubbed
        assert "[REDACTED_TOKEN]" in scrubbed or "[REDACTED]" in scrubbed


class TestErrorClassification:
    def test_auth_token_expired(self):
        exc = Exception("The security token included in the request is expired.")
        res = translate_swarm_error(exc)
        assert res["error_code"] == "AUTH_TOKEN_EXPIRED"
        assert "صلاحية" in res["title_ar"]
        assert "DEEPSEEK_API_KEY" in res["hint_ar"]

    def test_auth_missing_key(self):
        exc = Exception("DEEPSEEK_API_KEY is not set in environment.")
        res = translate_swarm_error(exc)
        assert res["error_code"] == "AUTH_KEY_MISSING"
        assert "غير متوفر" in res["title_ar"]
        assert ".env" in res["hint"]

    def test_rate_limit(self):
        exc = Exception("429 Too Many Requests: RateLimitError")
        res = translate_swarm_error(exc)
        assert res["error_code"] == "RATE_LIMIT_EXCEEDED"
        assert "الطلبات" in res["title_ar"]

    def test_schema_validation_error(self):
        exc = Exception("8 validation errors for SimulationSpec\nsteps.0\n  Input should be a valid dictionary")
        res = translate_swarm_error(exc)
        assert res["error_code"] == "SCHEMA_VALIDATION_ERROR"
        assert "steps.0" in res["message"] or "parameters" in res["message"]


class TestSimulationSpecAutoHealing:
    def test_auto_heal_string_steps_and_challenges(self):
        raw_data = {
            "title": "Buffer Equilibrium",
            "formula_expression": "pH = pKa + log10(A / HA)",
            "variables": [
                {"name": "pKa", "symbol": "pKa", "unit": "", "min_val": 1.0, "max_val": 14.0, "default_val": 4.76},
                {"name": "Base", "symbol": "A", "unit": "M", "min_val": 0.01, "max_val": 2.0, "default_val": 0.1},
                {"name": "Acid", "symbol": "HA", "unit": "M", "min_val": 0.01, "max_val": 2.0, "default_val": 0.1},
            ],
            # String items instead of dicts:
            "steps": [
                "Adjust pKa to explore different buffer systems.",
                "Vary the acid concentration relative to base."
            ],
            "challenge_items": [
                "Set [A⁻] = [HA] and observe pH.",
                "Calculate pH when ratio is 10:1."
            ],
            "nodes": [
                "pKa Node",
                "pH Node"
            ]
        }
        sanitized = _sanitize_simulation_spec(raw_data)
        sanitized["engine_type"] = EngineType.SLIDER

        # Must construct without ValidationError:
        spec = SimulationSpec(**sanitized)
        assert len(spec.steps) == 2
        assert isinstance(spec.steps[0], dict)
        assert spec.steps[0]["step_number"] == 1
        assert "Adjust pKa" in spec.steps[0]["description"]

        assert len(spec.challenge_items) == 2
        assert isinstance(spec.challenge_items[0], dict)
        assert "Set [A⁻]" in spec.challenge_items[0]["question"]

        assert len(spec.nodes) == 2
        assert isinstance(spec.nodes[0], dict)
        assert spec.nodes[0]["label"] == "pKa Node"


class TestDomainGuards:
    def test_domain_guards_chemistry_ph_bounds(self):
        from src.swarm.pair2_interactive import _sanitize_simulation_spec
        spec_data = {
            "title": "Buffer Solutions Lab",
            "formula_expression": "pH = pKa + log10([A⁻] / [HA])",
            "variables": [
                {"name": "pKa", "symbol": "pKa", "min_val": 1.0, "max_val": 14.0, "default_val": 4.76}
            ],
            "visual_archetype": "beaker"
        }
        guarded = _sanitize_simulation_spec(spec_data)
        assert guarded["result_symbol"] == "pH"
        assert guarded["result_min"] == 0.0
        assert guarded["result_max"] == 14.0
        assert guarded.get("is_logarithmic_output", False) is False

    def test_domain_guards_lever_balance_bounds(self):
        from src.swarm.pair2_interactive import _sanitize_simulation_spec
        spec_data = {
            "title": "Lever Seesaw Equilibrium",
            "formula_expression": "F1 * d1 = F2 * d2",
            "variables": [],
            "visual_archetype": "lever_torque"
        }
        guarded = _sanitize_simulation_spec(spec_data)
        assert guarded["result_symbol"] == "Balance"
        assert guarded["result_min"] == 0.0
        assert guarded["result_max"] == 100.0
        assert guarded.get("is_logarithmic_output", False) is False
