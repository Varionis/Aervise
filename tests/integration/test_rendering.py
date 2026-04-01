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


class RenderingApiTests(unittest.TestCase):
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

    def test_render_endpoint_accepts_structured_decision_output(self) -> None:
        structured = self.client.post("/decision/evaluate", json=self._decision_input()).json()
        response = self.client.post("/decision/render", json=structured)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("headline", payload)
        self.assertIn("message", payload)
        self.assertIn("metadata", payload)

    def test_evaluate_rendered_endpoint_returns_structured_and_rendered(self) -> None:
        response = self.client.post("/decision/evaluate-rendered", json=self._decision_input())

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("structured", payload)
        self.assertIn("rendered", payload)
        self.assertEqual(payload["structured"]["decision"]["label"], "go_ahead")
        self.assertIn("headline", payload["rendered"])

    def test_evaluate_rendered_writes_logs_and_traces(self) -> None:
        log_path = self.settings.log_dir / "aervise.log"
        trace_path = self.settings.trace_dir / "aervise_trace.jsonl"
        before_log_size = log_path.stat().st_size if log_path.exists() else 0
        before_trace_size = trace_path.stat().st_size if trace_path.exists() else 0

        response = self.client.post(
            "/decision/evaluate-rendered",
            json=self._decision_input(),
            headers={"X-Trace-Id": "test-trace-rendering"},
        )

        self.assertEqual(response.status_code, 200)
        after_log_size = log_path.stat().st_size if log_path.exists() else 0
        after_trace_size = trace_path.stat().st_size if trace_path.exists() else 0
        self.assertGreater(after_log_size, before_log_size)
        self.assertGreater(after_trace_size, before_trace_size)

    def test_evaluate_rendered_future_day_request_returns_conservative_message(self) -> None:
        interaction = InteractionService(settings=self.settings).preview(
            {
                "user_id": "demo-user",
                "message": "does tomorrow look like a good day to go trecking? 2-3 hrs",
                "location": {"lat": 43.6532, "lon": -79.3832},
            }
        )
        environment_state = EnrichmentService(settings=self.settings).snapshot_to_environment_state(self.snapshot)
        decision_input = DecisionPayloadBuilder().build(
            entry_point=interaction["entry_point"],
            intent_recognition=interaction["intent_recognition"],
            environment_state=environment_state,
        )

        response = self.client.post("/decision/evaluate-rendered", json=decision_input)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["structured"]["decision"]["label"], "insufficient_confidence")
        self.assertIn("cannot yet assess", payload["rendered"]["message"].lower())

    def test_evaluate_rendered_unrealistic_duration_returns_supported_range_message(self) -> None:
        interaction = InteractionService(settings=self.settings).preview(
            {
                "user_id": "demo-user",
                "message": "Can I go for a run right now for 9 hrs?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            }
        )
        environment_state = EnrichmentService(settings=self.settings).snapshot_to_environment_state(self.snapshot)
        decision_input = DecisionPayloadBuilder().build(
            entry_point=interaction["entry_point"],
            intent_recognition=interaction["intent_recognition"],
            environment_state=environment_state,
        )

        response = self.client.post("/decision/evaluate-rendered", json=decision_input)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["structured"]["decision"]["label"], "insufficient_confidence")
        self.assertIn("supported range", payload["rendered"]["message"].lower())


if __name__ == "__main__":
    unittest.main()
