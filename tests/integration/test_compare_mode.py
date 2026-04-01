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


class CompareModeApiTests(unittest.TestCase):
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

    def test_compare_now_later_returns_mode_result(self) -> None:
        response = self.client.post("/decision/evaluate", json=self._decision_input("Is later better than now for a run?"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["mode_result"]["mode"], "compare_now_later")
        self.assertIsNotNone(payload["mode_result"]["comparison"])
        self.assertEqual(len(payload["mode_result"]["comparison"]["candidates"]), 2)

    def test_compare_now_later_rendered_message_mentions_later_or_current(self) -> None:
        response = self.client.post("/decision/evaluate-rendered", json=self._decision_input("Is later better than now for a run?"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["structured"]["mode_result"]["mode"], "compare_now_later")
        self.assertTrue(
            "later" in payload["rendered"]["message"].lower() or "current" in payload["rendered"]["message"].lower()
        )


if __name__ == "__main__":
    unittest.main()
