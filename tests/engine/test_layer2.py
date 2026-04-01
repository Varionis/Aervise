from __future__ import annotations

import json
import unittest
from pathlib import Path

from config import get_settings
from core import RequestFeasibilityEvaluator, DecisionLayer2Evaluator
from pipeline.enrichment.service import EnrichmentService
from pipeline.intent.parser import InteractionService
from pipeline.payload_builder.builder import DecisionPayloadBuilder


class DecisionLayer2EvaluatorTests(unittest.TestCase):
    def setUp(self) -> None:
        snapshot_path = Path(__file__).resolve().parents[2] / "logs" / "latest_environment.json"
        self.snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        self.settings = get_settings()
        self.payload_builder = DecisionPayloadBuilder()
        self.interaction_service = InteractionService(settings=self.settings)
        self.environment_state = EnrichmentService(settings=self.settings).snapshot_to_environment_state(self.snapshot)
        self.feasibility_evaluator = RequestFeasibilityEvaluator()
        self.layer2_evaluator = DecisionLayer2Evaluator()

    def test_evaluates_factors_for_outdoor_run(self) -> None:
        interaction = self.interaction_service.preview(
            {"message": "Can I go for a run right now for 45 minutes?", "location": {"lat": 43.6532, "lon": -79.3832}}
        )
        decision_input = self.payload_builder.build(
            entry_point=interaction["entry_point"],
            intent_recognition=interaction["intent_recognition"],
            environment_state=self.environment_state,
        )
        layer2 = self.layer2_evaluator.evaluate(self.feasibility_evaluator.evaluate(decision_input))

        self.assertIn("risk_factors", layer2)
        self.assertIn("air_burden", layer2["risk_factors"])
        self.assertEqual(layer2["risk_factors"]["air_burden"]["level"], "low")
        self.assertLess(layer2["risk_factors"]["heat_burden"]["score"], 0.3)
        self.assertGreater(layer2["risk_factors"]["confidence_penalty"]["score"], 0.0)

    def test_sensitive_user_increases_air_burden(self) -> None:
        interaction = self.interaction_service.preview(
            {"message": "Can I go for a walk right now for 30 minutes?", "location": {"lat": 43.6532, "lon": -79.3832}}
        )
        base_decision_input = self.payload_builder.build(
            entry_point=interaction["entry_point"],
            intent_recognition=interaction["intent_recognition"],
            environment_state=self.environment_state,
        )
        sensitive_decision_input = self.payload_builder.build(
            entry_point=interaction["entry_point"],
            intent_recognition=interaction["intent_recognition"],
            environment_state=self.environment_state,
            user_context={"sensitive_group": True},
        )

        base_score = self.layer2_evaluator.evaluate(self.feasibility_evaluator.evaluate(base_decision_input))["risk_factors"]["air_burden"]["score"]
        sensitive_score = self.layer2_evaluator.evaluate(self.feasibility_evaluator.evaluate(sensitive_decision_input))["risk_factors"]["air_burden"]["score"]

        self.assertGreater(sensitive_score, base_score)


if __name__ == "__main__":
    unittest.main()
