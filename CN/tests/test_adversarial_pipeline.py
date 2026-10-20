"""
test_adversarial_pipeline.py
-----------------------------
Unit and integration tests for Phase 6: Adversarial Bot (Tier 4) and Evasion Benchmark.
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock

from bots.tier4_adversarial import sample_human_delay, generate_padded_query
from ai.adversarial_eval import (
    generate_adversarial_sessions,
    evaluate_adversarial,
    OUTPUT_JSON_PATH,
)
from CN.agent.ai_bridge import REQUIRED_FEATURES
from CN.web.backend_server import app


class TestTier4BotGenerator:
    """Tests for Tier 4 Adversarial Bot components."""

    def test_sample_human_delay_bounds(self):
        """Ensure sampled delays stay within plausible positive bounds."""
        for _ in range(50):
            d = sample_human_delay()
            assert isinstance(d, float)
            assert 0.1 <= d <= 10.0

    def test_generate_padded_query_structure(self):
        """Ensure padded query generates valid query parameters with padding."""
        query = generate_padded_query()
        assert "q=" in query
        assert "&pad=" in query
        assert len(query) > 20


class TestAdversarialEvaluation:
    """Tests for adversarial evaluation and synthetic session generator."""

    def test_generate_adversarial_sessions_conforms_to_contract(self):
        """Verify generated adversarial sessions include all required features."""
        sessions = generate_adversarial_sessions(n_samples=5, mode="full_feature_mimicry")
        assert len(sessions) == 5
        for s in sessions:
            for feat in REQUIRED_FEATURES:
                assert feat in s, f"Missing contract feature {feat}"
            assert s["label"] == "bot_adversarial"
            assert s["bot_tier"] == "tier4"
            assert s["provenance"] == "simulated"

    def test_adversarial_benchmark_execution(self):
        """Verify adversarial benchmark produces complete results file."""
        res = evaluate_adversarial(n_samples=10)
        assert res["status"] == "success"
        assert "scenarios" in res
        assert "delay_mimicry_only" in res["scenarios"]
        assert "full_feature_mimicry" in res["scenarios"]
        assert os.path.exists(OUTPUT_JSON_PATH)


class TestAdversarialEndpoint:
    """Tests for GET /api/adversarial web backend endpoint."""

    @pytest.fixture
    def client(self):
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    def test_get_adversarial_endpoint_success(self, client):
        """Verify endpoint returns 200 and valid JSON when results exist."""
        res = client.get("/api/adversarial")
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "success"
        assert "scenarios" in data
        assert "vulnerability_analysis" in data
        assert "recommended_countermeasures" in data
        assert len(data["recommended_countermeasures"]) >= 3
