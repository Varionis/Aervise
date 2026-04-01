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


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        snapshot_path = Path(__file__).resolve().parents[2] / "logs" / "latest_environment.json"
        self.snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        self.client = TestClient(app)
        self.settings = get_settings()

    def _decision_input(self) -> dict:
        interaction = InteractionService(settings=self.settings).preview(
            {
                "user_id": "demo-user",
                "message": "Can I go for a run right now for 45 minutes?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            }
        )
        environment_state = EnrichmentService(settings=self.settings).snapshot_to_environment_state(self.snapshot)
        return DecisionPayloadBuilder().build(
            entry_point=interaction["entry_point"],
            intent_recognition=interaction["intent_recognition"],
            environment_state=environment_state,
        )

    def test_health_endpoint(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["service"], "aervise-api")

    def test_landing_page_renders(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Interaction Flow Demo", response.text)
        self.assertIn("User message", response.text)
        self.assertIn("Chat View", response.text)
        self.assertIn("Run Flow", response.text)
        self.assertIn("Rendered Output", response.text)
        self.assertIn("Copy Trace", response.text)
        self.assertIn("Stage 0 + 1", response.text)
        self.assertIn("Stage 2", response.text)
        self.assertIn("Stage 3", response.text)
        self.assertIn("Decision Core Output", response.text)

    def test_decision_endpoint_with_inline_snapshot(self) -> None:
        response = self.client.post("/decision/evaluate", json=self._decision_input())

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["decision"]["label"], "go_ahead")
        self.assertIn("explanation", payload)

    def test_debug_layers_endpoint(self) -> None:
        response = self.client.post("/decision/debug/layers", json=self._decision_input())

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("decision_input", payload)
        self.assertIn("layer2", payload)
        self.assertIn("layer3", payload)
        self.assertIn("layer4", payload)

    def test_interaction_preview_endpoint(self) -> None:
        response = self.client.post(
            "/interaction/preview",
            json={
                "user_id": "demo-user",
                "message": "Can I go for a run right now for 30 minutes?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("entry_point", payload)
        self.assertIn("intent_recognition", payload)
        self.assertEqual(payload["intent_recognition"]["activity"], "running")

    def test_interaction_preview_supports_best_time_today(self) -> None:
        response = self.client.post(
            "/interaction/preview",
            json={
                "user_id": "demo-user",
                "message": "What's the best time to go for a run today?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["intent_recognition"]["intent"], "best_time_today")
        self.assertEqual(payload["intent_recognition"]["time_context"], "best_time_today")

    def test_enrichment_preview_endpoint(self) -> None:
        response = self.client.post(
            "/interaction/enrichment-preview",
            json={
                "user_id": "demo-user",
                "message": "Can I go for a run right now for 30 minutes?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ready_to_fetch")
        self.assertEqual(payload["next_stage"], "context_enrichment")

    def test_enrich_endpoint(self) -> None:
        response = self.client.post(
            "/interaction/enrich",
            json={
                "user_id": "demo-user",
                "message": "Can I go for a run right now for 30 minutes?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("entry_point", payload)
        self.assertIn("intent_recognition", payload)
        self.assertIn("environment_state", payload)
        self.assertIn("weather", payload["environment_state"])

    def test_build_payload_endpoint(self) -> None:
        response = self.client.post(
            "/interaction/build-payload",
            json={
                "user_id": "demo-user",
                "message": "Can I go for a run right now for 30 minutes?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("request", payload)
        self.assertIn("environment_state", payload)
        self.assertEqual(payload["request"]["intent"]["activity"], "running")


if __name__ == "__main__":
    unittest.main()
