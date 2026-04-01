from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from config import get_settings
from core import RequestFeasibilityEvaluator, DecisionLayer2Evaluator, DecisionLayer3Policy
from pipeline.enrichment.service import EnrichmentService
from pipeline.intent.parser import InteractionService
from pipeline.payload_builder.builder import DecisionPayloadBuilder


class DecisionLayer3PolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        snapshot_path = Path(__file__).resolve().parents[2] / "logs" / "latest_environment.json"
        self.snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        self.settings = get_settings()
        self.payload_builder = DecisionPayloadBuilder()
        self.interaction_service = InteractionService(settings=self.settings)
        self.feasibility_evaluator = RequestFeasibilityEvaluator()
        self.layer2_evaluator = DecisionLayer2Evaluator()
        self.layer3_policy = DecisionLayer3Policy()

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

    def test_outputs_go_ahead_for_clean_cool_run(self) -> None:
        decision_input = self._decision_input(self.snapshot, "Can I go for a run right now for 45 minutes?")
        layer2 = self.layer2_evaluator.evaluate(self.feasibility_evaluator.evaluate(decision_input))
        layer3 = self.layer3_policy.evaluate(layer2)

        self.assertEqual(layer3["decision"]["label"], "go_ahead")
        self.assertTrue(layer3["recommendation"]["allowed"])
        self.assertIn("policy_trace", layer3)

    def test_hard_constraint_blocks_extreme_pm25_for_high_intensity(self) -> None:
        snapshot = copy.deepcopy(self.snapshot)
        snapshot["environment"]["air"]["pm25"]["value"] = 180.0

        decision_input = self._decision_input(snapshot, "Can I go for a run right now for 30 minutes?")
        layer2 = self.layer2_evaluator.evaluate(self.feasibility_evaluator.evaluate(decision_input))
        layer3 = self.layer3_policy.evaluate(layer2)

        self.assertEqual(layer3["decision"]["label"], "avoid_for_now")
        self.assertTrue(layer3["policy_trace"]["hard_constraints_triggered"])

    def test_missing_core_inputs_returns_insufficient_confidence(self) -> None:
        snapshot = copy.deepcopy(self.snapshot)
        snapshot["environment"]["weather"]["temperature_c"] = None

        decision_input = self._decision_input(snapshot, "Can I go for a walk right now for 20 minutes?")
        layer2 = self.layer2_evaluator.evaluate(self.feasibility_evaluator.evaluate(decision_input))
        layer3 = self.layer3_policy.evaluate(layer2)

        self.assertEqual(layer3["decision"]["label"], "insufficient_confidence")
        self.assertFalse(layer3["recommendation"]["allowed"])

    def test_duration_adjustment_prefers_shorten_or_modify(self) -> None:
        decision_input = self._decision_input(self.snapshot, "Can I still go for a run if I reduce my time to 20 minutes instead of an hour?")
        layer2 = self.layer2_evaluator.evaluate(self.feasibility_evaluator.evaluate(decision_input))
        layer3 = self.layer3_policy.evaluate(layer2)

        self.assertIn(layer3["decision"]["label"], {"go_ahead", "shorten_or_modify"})
        self.assertEqual(layer3["request"]["intent"]["source_intent"], "duration_adjustment")
        if layer3["decision"]["label"] == "shorten_or_modify":
            self.assertIn("shorter", layer3["recommendation"]["message"].lower())

    def test_route_mode_choice_sets_preferred_mode(self) -> None:
        snapshot = copy.deepcopy(self.snapshot)
        snapshot["environment"]["air"]["pm25"]["value"] = 120.0
        decision_input = self._decision_input(snapshot, "Should I drive instead of biking due to conditions?")
        layer2 = self.layer2_evaluator.evaluate(self.feasibility_evaluator.evaluate(decision_input))
        layer3 = self.layer3_policy.evaluate(layer2)

        self.assertEqual(layer3["request"]["intent"]["source_intent"], "route_mode_choice")
        self.assertIn("preferred_mode", layer3["policy_trace"])
        self.assertIn(layer3["policy_trace"]["preferred_mode"], {"drive", "transit", "bike"})

    def test_should_avoid_uses_binary_advisory_tone(self) -> None:
        snapshot = copy.deepcopy(self.snapshot)
        snapshot["environment"]["air"]["pm25"]["value"] = 90.0
        decision_input = self._decision_input(snapshot, "Should I avoid going outside for a walk right now?")
        layer2 = self.layer2_evaluator.evaluate(self.feasibility_evaluator.evaluate(decision_input))
        layer3 = self.layer3_policy.evaluate(layer2)

        self.assertEqual(layer3["request"]["intent"]["source_intent"], "should_avoid")
        self.assertIn("safer", layer3["recommendation"]["message"].lower())

    def test_future_day_request_returns_insufficient_confidence(self) -> None:
        decision_input = self._decision_input(self.snapshot, "does tomorrow look like a good day to go trecking? 2-3 hrs")
        layer2 = self.layer2_evaluator.evaluate(self.feasibility_evaluator.evaluate(decision_input))
        layer3 = self.layer3_policy.evaluate(layer2)

        self.assertEqual(layer3["request"]["intent"]["time_horizon"], "tomorrow")
        self.assertEqual(layer3["decision"]["label"], "insufficient_confidence")
        self.assertIn("cannot yet assess", layer3["recommendation"]["message"].lower())

    def test_unrealistic_run_duration_is_blocked_by_feasibility(self) -> None:
        decision_input = self._decision_input(self.snapshot, "Can I go for a run right now for 9 hrs?")
        layer2 = self.layer2_evaluator.evaluate(self.feasibility_evaluator.evaluate(decision_input))
        layer3 = self.layer3_policy.evaluate(layer2)

        self.assertEqual(layer3["decision"]["label"], "insufficient_confidence")
        self.assertFalse(layer3["recommendation"]["allowed"])
        self.assertIn("outside the supported range", layer3["recommendation"]["message"].lower())

    def test_stale_saved_snapshot_blocks_same_day_planning(self) -> None:
        decision_input = self._decision_input(self.snapshot, "What's the best time to go for a run today?")
        decision_input["environment_state"]["time_context"]["data_origin"] = "saved_snapshot_fallback"
        decision_input["environment_state"]["time_context"]["snapshot_age_minutes"] = 500.0
        layer2 = self.layer2_evaluator.evaluate(self.feasibility_evaluator.evaluate(decision_input))
        layer3 = self.layer3_policy.evaluate(layer2)

        self.assertEqual(layer3["decision"]["label"], "insufficient_confidence")
        self.assertTrue(layer3["policy_trace"]["hard_constraints_triggered"])
        self.assertIn("fallback snapshot", layer3["reasoning"][0].lower())


if __name__ == "__main__":
    unittest.main()
