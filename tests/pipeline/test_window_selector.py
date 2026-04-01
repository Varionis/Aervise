from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta

from pipeline.enrichment.service import EnrichmentService
from pipeline.enrichment.window_selector import WeatherWindowSelector


class WeatherWindowSelectorTests(unittest.TestCase):
    def _base_environment_state(self) -> dict:
        now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        tomorrow_evening = now + timedelta(days=1)
        tomorrow_evening = tomorrow_evening.replace(hour=19)
        tomorrow_morning = now + timedelta(days=1)
        tomorrow_morning = tomorrow_morning.replace(hour=9)
        return {
            "air_quality": {
                "pm25": {"value": 12.0},
                "no2": {"value": 0.008},
                "o3": {"value": 0.043},
                "confidence": 0.71,
                "staleness_minutes": 30.0,
            },
            "weather": {
                "temperature_c": 8.0,
                "humidity": 50,
                "wind_speed": 2.0,
                "measured_at_utc": now.isoformat(),
                "source": "openmeteo",
                "confidence": 0.95,
            },
            "forecast_hours": [
                {
                    "time": tomorrow_morning.isoformat(),
                    "temperature_c": 6.0,
                    "humidity": 55,
                    "wind_speed": 2.1,
                },
                {
                    "time": tomorrow_evening.isoformat(),
                    "temperature_c": 12.0,
                    "humidity": 40,
                    "wind_speed": 3.0,
                },
            ],
            "time_context": {
                "snapshot_timestamp_utc": now.isoformat(),
                "forecast_window_available": True,
            },
            "forecast_capabilities": {
                "supports_air_forecast": False,
                "supports_weather_forecast": True,
                "supports_same_day_timing": "partial",
            },
            "data_quality": {
                "overall_confidence": 0.83,
                "aq_source_confidence": 0.71,
                "weather_source_confidence": 0.95,
                "missing_fields": [],
            },
            "location": {"lat": 43.6532, "lon": -79.3832},
        }

    def test_selects_tomorrow_evening_weather_window(self) -> None:
        selector = WeatherWindowSelector()
        state = selector.select(
            environment_state=self._base_environment_state(),
            intent_recognition={"time_horizon": "tomorrow", "time_window": "evening"},
        )

        self.assertTrue(state["time_context"]["selected_weather_window_available"])
        self.assertEqual(state["time_context"]["weather_selection_mode"], "forecast_window")
        self.assertEqual(state["weather"]["temperature_c"], 12.0)

    def test_snapshot_to_environment_state_applies_window_selection_and_confidence_adjustment(self) -> None:
        now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        tomorrow_evening = (now + timedelta(days=1)).replace(hour=19)
        snapshot = {
            "timestamp_utc": now.isoformat(),
            "environment": {
                "air": {
                    "pm25": {"value": 12.0, "unit": "ug/m3", "measured_at_utc": now.isoformat(), "source": "openaq"},
                    "no2": {"value": 0.008, "unit": "ppm", "measured_at_utc": now.isoformat(), "source": "openaq"},
                    "o3": {"value": 0.043, "unit": "ppm", "measured_at_utc": now.isoformat(), "source": "openaq"},
                },
                "weather": {
                    "temperature_c": 8.0,
                    "humidity": 50,
                    "wind_speed": 2.0,
                    "measured_at_utc": now.isoformat(),
                    "source": "openmeteo",
                },
            },
            "forecast": [
                {
                    "timestamp_utc": tomorrow_evening.isoformat(),
                    "weather": {"temperature_c": 12.0, "humidity": 40, "wind_speed": 3.0},
                }
            ],
            "meta": {
                "location": {"lat": 43.6532, "lon": -79.3832},
                "data_confidence": 0.83,
                "sources": {
                    "air": {"data_confidence": 0.71, "staleness_minutes": 30.0},
                    "weather": {"data_confidence": 0.95},
                },
            },
        }
        state = EnrichmentService.snapshot_to_environment_state(
            snapshot,
            intent_recognition={"time_horizon": "tomorrow", "time_window": "evening"},
        )

        self.assertEqual(state["weather"]["temperature_c"], 12.0)
        self.assertEqual(state["time_context"]["weather_selection_mode"], "forecast_window")
        self.assertLess(state["data_quality"]["overall_confidence"], 0.83)

    def test_snapshot_to_environment_state_records_data_origin_and_snapshot_age(self) -> None:
        now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        snapshot = {
            "timestamp_utc": now.isoformat(),
            "environment": {
                "air": {"pm25": {"value": 12.0, "unit": "ug/m3", "measured_at_utc": now.isoformat(), "source": "openaq"}},
                "weather": {
                    "temperature_c": 8.0,
                    "humidity": 50,
                    "wind_speed": 2.0,
                    "measured_at_utc": now.isoformat(),
                    "source": "openmeteo",
                },
            },
            "forecast": [],
            "meta": {
                "location": {"lat": 43.6532, "lon": -79.3832},
                "data_confidence": 0.83,
                "sources": {"air": {"data_confidence": 0.71}, "weather": {"data_confidence": 0.95}},
            },
        }

        state = EnrichmentService.snapshot_to_environment_state(snapshot, data_origin="saved_snapshot_fallback")

        self.assertEqual(state["time_context"]["data_origin"], "saved_snapshot_fallback")
        self.assertIsNotNone(state["time_context"]["snapshot_age_minutes"])


if __name__ == "__main__":
    unittest.main()
