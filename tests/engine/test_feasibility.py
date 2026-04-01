from __future__ import annotations

import json
import unittest
from pathlib import Path

from config import get_settings
from core import RequestFeasibilityEvaluator
from pipeline.enrichment.service import EnrichmentService
from pipeline.intent.parser import InteractionService
from pipeline.payload_builder.builder import DecisionPayloadBuilder


class RequestFeasibilityEvaluatorTests(unittest.TestCase):
    def setUp(self) -> None:
        snapshot_path = Path(__file__).resolve().parents[2] / "logs" / "latest_environment.json"
        self.snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        self.settings = get_settings()
        self.payload_builder = DecisionPayloadBuilder()
        self.interaction_service = InteractionService(settings=self.settings)
        self.environment_state = EnrichmentService(settings=self.settings).snapshot_to_environment_state(self.snapshot)
        self.evaluator = RequestFeasibilityEvaluator()

    def _decision_input(self, message: str) -> dict:
        interaction = self.interaction_service.preview(
            {"message": message, "location": {"lat": 43.6532, "lon": -79.3832}}
        )
        return self.payload_builder.build(
            entry_point=interaction["entry_point"],
            intent_recognition=interaction["intent_recognition"],
            environment_state=self.environment_state,
        )

    def test_running_nine_hours_exceeds_hard_upper(self) -> None:
        payload = self.evaluator.evaluate(self._decision_input("Can I go for a run right now for 9 hrs?"))

        self.assertEqual(payload["request_feasibility"]["status"], "exceeds_hard_upper")
        self.assertEqual(payload["request_feasibility"]["hard_upper_duration_min"], 240)

    def test_barbecue_five_hours_can_exceed_typical_without_exceeding_hard_upper(self) -> None:
        payload = self.evaluator.evaluate(self._decision_input("Can I have a barbeque for 5 hours?"))

        self.assertEqual(payload["request_feasibility"]["status"], "exceeds_typical")
        self.assertEqual(payload["request_feasibility"]["hard_upper_duration_min"], 540)


if __name__ == "__main__":
    unittest.main()
