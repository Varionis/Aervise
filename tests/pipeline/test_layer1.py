from __future__ import annotations

import json
import unittest
from pathlib import Path

from config import get_settings
from pipeline.enrichment.service import EnrichmentService
from pipeline.intent.parser import InteractionService
from pipeline.payload_builder.builder import DecisionPayloadBuilder


class DecisionPayloadBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        snapshot_path = Path(__file__).resolve().parents[2] / "logs" / "latest_environment.json"
        self.snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        self.settings = get_settings()
        self.builder = DecisionPayloadBuilder()
        self.interaction_service = InteractionService(settings=self.settings)
        self.environment_state = EnrichmentService(settings=self.settings).snapshot_to_environment_state(self.snapshot)

    def test_builds_running_now_request(self) -> None:
        interaction = self.interaction_service.preview(
            {
                "message": "Can I go for a run right now for 45 minutes?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            }
        )
        payload = self.builder.build(
            entry_point=interaction["entry_point"],
            intent_recognition=interaction["intent_recognition"],
            environment_state=self.environment_state,
        )

        self.assertEqual(payload["request"]["intent"]["activity"], "running")
        self.assertEqual(payload["request"]["intent"]["activity_profile"]["exertion_level"], "high")
        self.assertEqual(payload["request"]["intent"]["decision_archetype"], "NOW_CHECK")
        self.assertEqual(payload["request"]["intent"]["activity_archetype"], "outdoor_high_exertion")
        self.assertTrue(payload["environment_state"]["time_context"]["forecast_window_available"])
        self.assertEqual(payload["environment_state"]["air_quality"]["pm25"]["value"], 12.0)

    def test_uses_specific_hour_when_timing_parser_detects_named_period(self) -> None:
        interaction = self.interaction_service.preview(
            {
                "message": "Can I go for a walk this afternoon for 20 minutes?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            }
        )
        payload = self.builder.build(
            entry_point=interaction["entry_point"],
            intent_recognition=interaction["intent_recognition"],
            environment_state=self.environment_state,
        )

        self.assertEqual(payload["request"]["intent"]["timing_mode"], "specific_hour")
        self.assertEqual(payload["request"]["intent"]["decision_archetype"], "COMPARE_NOW_LATER")
        self.assertEqual(payload["request"]["intent"]["activity_profile"]["expected_duration_band"], "medium")
        self.assertEqual(payload["request"]["intent"]["duration_band"], "medium")

    def test_builds_best_time_payload_with_default_duration(self) -> None:
        interaction = self.interaction_service.preview(
            {
                "message": "What's the best time to go for a run today?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            }
        )
        payload = self.builder.build(
            entry_point=interaction["entry_point"],
            intent_recognition=interaction["intent_recognition"],
            environment_state=self.environment_state,
        )

        self.assertEqual(payload["request"]["intent"]["source_intent"], "best_time_today")
        self.assertEqual(payload["request"]["intent"]["decision_archetype"], "BEST_TIME_TODAY")
        self.assertEqual(payload["request"]["intent"]["duration_min"], 45)

    def test_builds_what_if_duration_payload_with_reference_duration(self) -> None:
        interaction = self.interaction_service.preview(
            {
                "message": "Can I still go for a run if I reduce my time to 20 minutes instead of an hour?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            }
        )
        payload = self.builder.build(
            entry_point=interaction["entry_point"],
            intent_recognition=interaction["intent_recognition"],
            environment_state=self.environment_state,
        )

        self.assertEqual(payload["request"]["intent"]["source_intent"], "duration_adjustment")
        self.assertEqual(payload["request"]["intent"]["decision_archetype"], "WHAT_IF")
        self.assertEqual(payload["request"]["intent"]["duration_min"], 20)
        self.assertEqual(payload["request"]["intent"]["reference_duration_min"], 60)

    def test_activity_check_without_duration_uses_activity_default(self) -> None:
        interaction = self.interaction_service.preview(
            {
                "message": "Should I go running?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            }
        )
        payload = self.builder.build(
            entry_point=interaction["entry_point"],
            intent_recognition=interaction["intent_recognition"],
            environment_state=self.environment_state,
        )

        self.assertEqual(payload["request"]["intent"]["activity"], "running")
        self.assertEqual(payload["request"]["intent"]["duration_min"], 45)
        self.assertEqual(payload["request"]["intent"]["duration_band"], "medium")

    def test_future_day_request_carries_temporal_fields(self) -> None:
        interaction = self.interaction_service.preview(
            {
                "message": "does tomorrow look like a good day to go trecking?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            }
        )
        payload = self.builder.build(
            entry_point=interaction["entry_point"],
            intent_recognition=interaction["intent_recognition"],
            environment_state=self.environment_state,
        )

        self.assertEqual(payload["request"]["intent"]["activity"], "hiking")
        self.assertEqual(payload["request"]["intent"]["activity_profile"]["expected_duration_band"], "long")
        self.assertEqual(payload["request"]["intent"]["time_horizon"], "tomorrow")
        self.assertEqual(payload["request"]["intent"]["decision_archetype"], "FUTURE_LOOKAHEAD")

    def test_outdoor_wedding_uses_profile_driven_defaults(self) -> None:
        interaction = self.interaction_service.preview(
            {
                "message": "Does an outdoor wedding tomorrow evening look okay?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            }
        )
        payload = self.builder.build(
            entry_point=interaction["entry_point"],
            intent_recognition=interaction["intent_recognition"],
            environment_state=self.environment_state,
        )

        self.assertEqual(payload["request"]["intent"]["activity_profile"]["motion_pattern"], "stationary")
        self.assertEqual(payload["request"]["intent"]["duration_min"], 120)
        self.assertEqual(payload["request"]["intent"]["activity_group"], "light_outdoor_activity")

    def test_builds_route_mode_payload_with_candidate_modes(self) -> None:
        interaction = self.interaction_service.preview(
            {
                "message": "Should I drive instead of biking due to conditions?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            }
        )
        payload = self.builder.build(
            entry_point=interaction["entry_point"],
            intent_recognition=interaction["intent_recognition"],
            environment_state=self.environment_state,
        )

        self.assertEqual(payload["request"]["intent"]["source_intent"], "route_mode_choice")
        self.assertIn("drive", payload["request"]["intent"]["candidate_modes"])
        self.assertIn("bike", payload["request"]["intent"]["candidate_modes"])


if __name__ == "__main__":
    unittest.main()
