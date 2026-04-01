from __future__ import annotations

import json
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from config import get_settings
from interfaces.api.main import app
from pipeline.enrichment.service import EnrichmentService
from pipeline.intent.parser import InteractionService
from pipeline.payload_builder.builder import DecisionPayloadBuilder


class WhatIfModeApiTests(unittest.TestCase):
    def setUp(self) -> None:
        snapshot_path = Path(__file__).resolve().parents[2] / "logs" / "latest_environment.json"
        self.snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        self.client = TestClient(app)
        self.settings = get_settings()

    def _decision_input(self, message: str) -> dict:
        interaction = InteractionService(settings=self.settings).preview(
            {
                "user_id": "demo-user",
                "message": message,
                "location": {"lat": 43.6532, "lon": -79.3832},
            }
        )
        environment_state = EnrichmentService(settings=self.settings).snapshot_to_environment_state(
            self.snapshot,
            intent_recognition=interaction["intent_recognition"],
        )
        return DecisionPayloadBuilder().build(
            entry_point=interaction["entry_point"],
            intent_recognition=interaction["intent_recognition"],
            environment_state=environment_state,
        )

    def test_timing_what_if_returns_mode_result(self) -> None:
        response = self.client.post("/decision/evaluate", json=self._decision_input("What if I go later for a run?"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["mode_result"]["mode"], "what_if")
        self.assertEqual(payload["mode_result"]["what_if"]["scenario_type"], "timing")

    def test_duration_what_if_returns_mode_result(self) -> None:
        response = self.client.post(
            "/decision/evaluate",
            json=self._decision_input("Can I still go for a run if I reduce my time to 20 minutes instead of an hour?"),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["mode_result"]["mode"], "what_if")
        self.assertEqual(payload["mode_result"]["what_if"]["scenario_type"], "duration")
        self.assertEqual(payload["mode_result"]["what_if"]["baseline"]["duration_min"], 60)
        self.assertEqual(payload["mode_result"]["what_if"]["scenario"]["duration_min"], 20)

    def test_rendered_duration_what_if_mentions_shorter_or_reduce(self) -> None:
        response = self.client.post(
            "/decision/evaluate-rendered",
            json=self._decision_input("Can I still go for a run if I reduce my time to 20 minutes instead of an hour?"),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["structured"]["mode_result"]["mode"], "what_if")
        self.assertTrue(
            "shorter" in payload["rendered"]["message"].lower() or "reduce" in payload["rendered"]["message"].lower()
        )


if __name__ == "__main__":
    unittest.main()
