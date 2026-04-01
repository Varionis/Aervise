from __future__ import annotations

import unittest

from config import get_settings
from pipeline.intent.parser import InteractionService


class IntentParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = InteractionService(settings=get_settings())

    def test_best_time_today_intent(self) -> None:
        result = self.service.preview(
            {
                "message": "What's the best time to go for a run today?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            }
        )["intent_recognition"]

        self.assertEqual(result["intent"], "best_time_today")
        self.assertEqual(result["activity"], "running")
        self.assertEqual(result["activity_profile"]["exertion_level"], "high")
        self.assertEqual(result["time_context"], "best_time_today")

    def test_when_is_a_good_time_maps_to_best_time_today(self) -> None:
        result = self.service.preview(
            {
                "message": "When is a good time to go for a run?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            }
        )["intent_recognition"]

        self.assertEqual(result["intent"], "best_time_today")
        self.assertEqual(result["activity"], "running")
        self.assertEqual(result["time_context"], "best_time_today")

    def test_compare_times_intent(self) -> None:
        result = self.service.preview(
            {
                "message": "Is evening better than now for a run?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            }
        )["intent_recognition"]

        self.assertEqual(result["intent"], "compare_times")
        self.assertEqual(result["comparison_target"], "now_vs_later")

    def test_duration_adjustment_intent(self) -> None:
        result = self.service.preview(
            {
                "message": "Can I go if I reduce my time to 20 minutes instead of an hour?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            }
        )["intent_recognition"]

        self.assertEqual(result["intent"], "duration_adjustment")
        self.assertEqual(result["adjustment_type"], "duration")
        self.assertEqual(result["duration_minutes"], 20)
        self.assertEqual(result["reference_duration_minutes"], 60)

    def test_route_mode_choice_intent(self) -> None:
        result = self.service.preview(
            {
                "message": "Should I drive instead of biking due to conditions?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            }
        )["intent_recognition"]

        self.assertEqual(result["intent"], "route_mode_choice")
        self.assertIn("drive", result["candidate_modes"])
        self.assertIn("bike", result["candidate_modes"])

    def test_should_avoid_intent(self) -> None:
        result = self.service.preview(
            {
                "message": "Should I avoid going outside for a walk right now?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            }
        )["intent_recognition"]

        self.assertEqual(result["intent"], "should_avoid")
        self.assertEqual(result["activity"], "walking")

    def test_duration_not_required_for_basic_activity_check(self) -> None:
        result = self.service.preview(
            {
                "message": "Should I go running?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            }
        )["intent_recognition"]

        self.assertEqual(result["intent"], "activity_check")
        self.assertEqual(result["activity"], "running")
        self.assertIsNone(result["duration_minutes"])
        self.assertNotIn("duration_minutes", result["unresolved_fields"])

    def test_tomorrow_query_does_not_collapse_to_now(self) -> None:
        result = self.service.preview(
            {
                "message": "I want to play basketball, how does tomorrow's weather look like? 40 mins",
                "location": {"lat": 43.6532, "lon": -79.3832},
            }
        )["intent_recognition"]

        self.assertEqual(result["activity"], "basketball")
        self.assertEqual(result["duration_minutes"], 40)
        self.assertEqual(result["time_horizon"], "tomorrow")
        self.assertNotEqual(result["time_context"], "now")

    def test_barbecue_maps_to_evening_window(self) -> None:
        result = self.service.preview(
            {
                "message": "Can I have a barbeque tomorrow? say after 5 pm?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            }
        )["intent_recognition"]

        self.assertEqual(result["activity"], "barbecue")
        self.assertEqual(result["activity_profile"]["motion_pattern"], "stationary")
        self.assertEqual(result["time_horizon"], "tomorrow")
        self.assertEqual(result["time_window"], "evening")

    def test_trekking_maps_to_hiking(self) -> None:
        result = self.service.preview(
            {
                "message": "Does tomorrow look like a good day to go trecking? 2 hrs?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            }
        )["intent_recognition"]

        self.assertEqual(result["activity"], "hiking")
        self.assertEqual(result["activity_profile"]["expected_duration_band"], "long")
        self.assertEqual(result["activity_profile"]["exposure_level"], "high")
        self.assertEqual(result["duration_minutes"], 120)
        self.assertEqual(result["time_horizon"], "tomorrow")

    def test_outdoor_wedding_maps_to_outdoor_gathering_profile(self) -> None:
        result = self.service.preview(
            {
                "message": "Does an outdoor wedding tomorrow evening look okay?",
                "location": {"lat": 43.6532, "lon": -79.3832},
            }
        )["intent_recognition"]

        self.assertEqual(result["activity"], "outdoor_gathering")
        self.assertEqual(result["activity_profile"]["exertion_level"], "low")
        self.assertEqual(result["activity_profile"]["expected_duration_band"], "long")


if __name__ == "__main__":
    unittest.main()
