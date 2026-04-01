from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from config import get_settings
from core import RequestFeasibilityEvaluator, DecisionLayer2Evaluator, DecisionLayer3Policy, DecisionLayer4Explainer
from pipeline.enrichment.service import EnrichmentService
from pipeline.intent.parser import InteractionService
from pipeline.payload_builder.builder import DecisionPayloadBuilder


class DecisionLayer4ExplainerTests(unittest.TestCase):
    def setUp(self) -> None:
        snapshot_path = Path(__file__).resolve().parents[2] / "logs" / "latest_environment.json"
        self.snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        self.settings = get_settings()
        self.payload_builder = DecisionPayloadBuilder()
        self.interaction_service = InteractionService(settings=self.settings)
        self.feasibility_evaluator = RequestFeasibilityEvaluator()
        self.layer2_evaluator = DecisionLayer2Evaluator()
        self.layer3_policy = DecisionLayer3Policy()
        self.layer4_explainer = DecisionLayer4Explainer()

    def _decision_input(self, snapshot: dict, message: str) -> dict:
        interaction = self.interaction_service.preview(
            {"message": message, "location": {"lat": 43.6532, "lon": -79.3832}}
        )
        environment_state = EnrichmentService(settings=self.settings).snapshot_to_environment_state(snapshot)
        return self.payload_builder.build(
            entry_point=interaction["entry_point"],
            intent_recognition=interaction["intent_recognition"],
            environment_state=environment_state,
        )

    def test_explanation_for_go_ahead_contains_summary_and_assumptions(self) -> None:
        decision_input = self._decision_input(self.snapshot, "Can I go for a run right now for 45 minutes?")
        layer4 = self.layer4_explainer.explain(
            self.layer3_policy.evaluate(self.layer2_evaluator.evaluate(self.feasibility_evaluator.evaluate(decision_input)))
        )

        self.assertIn("explanation", layer4)
        self.assertIn("summary", layer4["explanation"])
        self.assertIn("No same-day air-quality forecast is available yet.", layer4["explanation"]["assumptions"])
        self.assertFalse(layer4["safe_alternative_available"])

    def test_weather_only_timing_guidance_is_explicit_for_modify_decision(self) -> None:
        snapshot = copy.deepcopy(self.snapshot)
        snapshot["environment"]["weather"]["temperature_c"] = 32.0
        snapshot["environment"]["weather"]["humidity"] = 70

        decision_input = self._decision_input(snapshot, "Can I go for a run right now for 60 minutes?")
        layer4 = self.layer4_explainer.explain(
            self.layer3_policy.evaluate(self.layer2_evaluator.evaluate(self.feasibility_evaluator.evaluate(decision_input)))
        )

        self.assertIn(layer4["decision"]["label"], {"shorten_or_modify", "avoid_for_now"})
        self.assertIsNotNone(layer4["alternative_recommendation"])
        self.assertEqual(layer4["alternative_recommendation"]["basis"], "weather_only")
        self.assertIn("air-quality forecast is not available", " ".join(layer4["explanation"]["assumptions"]))

    def test_best_time_requests_get_best_time_summary(self) -> None:
        decision_input = self._decision_input(self.snapshot, "What's the best time to go for a run today?")
        layer4 = self.layer4_explainer.explain(
            self.layer3_policy.evaluate(self.layer2_evaluator.evaluate(self.feasibility_evaluator.evaluate(decision_input)))
        )

        self.assertEqual(layer4["request"]["intent"]["source_intent"], "best_time_today")
        self.assertIn("best-time-today", layer4["explanation"]["summary"].lower())

    def test_compare_times_requests_get_comparison_summary(self) -> None:
        decision_input = self._decision_input(self.snapshot, "Is evening better than now for a run?")
        layer4 = self.layer4_explainer.explain(
            self.layer3_policy.evaluate(self.layer2_evaluator.evaluate(self.feasibility_evaluator.evaluate(decision_input)))
        )

        self.assertEqual(layer4["request"]["intent"]["source_intent"], "compare_times")
        self.assertIn("same-day comparison", layer4["explanation"]["summary"].lower())

    def test_future_day_request_does_not_get_same_day_timing_guidance(self) -> None:
        decision_input = self._decision_input(self.snapshot, "does tomorrow look like a good day to go trecking? 2-3 hrs")
        layer4 = self.layer4_explainer.explain(
            self.layer3_policy.evaluate(self.layer2_evaluator.evaluate(self.feasibility_evaluator.evaluate(decision_input)))
        )

        self.assertEqual(layer4["decision"]["label"], "insufficient_confidence")
        self.assertIn("future-window request", layer4["explanation"]["summary"].lower())
        self.assertIsNone(layer4["explanation"]["timing_guidance"]["message"])
        self.assertIn("future-day timing guidance is disabled", " ".join(layer4["explanation"]["assumptions"]).lower())


if __name__ == "__main__":
    unittest.main()
