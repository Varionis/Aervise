from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from config import Settings
from pipeline.enrichment.air_provider import OpenAQProvider
from pipeline.enrichment.http import HttpClient
from pipeline.enrichment.normalization import EnvironmentAggregator
from pipeline.enrichment.openmeteo_provider import OpenMeteoProvider
from pipeline.enrichment.weather_provider import OpenWeatherProvider
from pipeline.enrichment.weather_service import WeatherService
from pipeline.enrichment.window_selector import WeatherWindowSelector


@dataclass
class EnrichmentService:
    settings: Settings

    def enrich(self, *, lat: float, lon: float, intent_recognition: dict | None = None) -> dict:
        http_client = HttpClient()
        aggregator = EnvironmentAggregator(
            settings=self.settings,
            air_provider=OpenAQProvider(settings=self.settings, http_client=http_client),
            weather_service=WeatherService(
                settings=self.settings,
                openweather_provider=OpenWeatherProvider(settings=self.settings, http_client=http_client),
                openmeteo_provider=OpenMeteoProvider(settings=self.settings, http_client=http_client),
            ),
        )
        snapshot = aggregator.fetch_snapshot(lat=lat, lon=lon)
        return self.snapshot_to_environment_state(snapshot, intent_recognition=intent_recognition)

    def enrich_with_fallback(self, *, lat: float, lon: float, intent_recognition: dict | None = None) -> dict:
        try:
            return self.enrich(lat=lat, lon=lon, intent_recognition=intent_recognition)
        except Exception:
            snapshot = self._load_saved_snapshot()
            if snapshot is None:
                raise
            return self.snapshot_to_environment_state(snapshot, intent_recognition=intent_recognition)

    @staticmethod
    def snapshot_to_environment_state(snapshot: dict, intent_recognition: dict | None = None) -> dict:
        air = snapshot.get("environment", {}).get("air", {})
        weather = snapshot.get("environment", {}).get("weather", {})
        source_meta = (snapshot.get("meta") or {}).get("sources") or {}

        missing_fields = []
        for field_name, value in {
            "pm25": air.get("pm25", {}).get("value") if air.get("pm25") else None,
            "temperature_c": weather.get("temperature_c"),
            "humidity": weather.get("humidity"),
            "wind_speed": weather.get("wind_speed"),
        }.items():
            if value is None:
                missing_fields.append(field_name)

        environment_state = {
            "air_quality": {
                "pm25": EnrichmentService._pollutant(air.get("pm25")),
                "no2": EnrichmentService._pollutant(air.get("no2")),
                "o3": EnrichmentService._pollutant(air.get("o3")),
                "confidence": (source_meta.get("air") or {}).get("data_confidence"),
                "staleness_minutes": (source_meta.get("air") or {}).get("staleness_minutes"),
            },
            "weather": {
                "temperature_c": weather.get("temperature_c"),
                "humidity": weather.get("humidity"),
                "wind_speed": weather.get("wind_speed"),
                "measured_at_utc": weather.get("measured_at_utc"),
                "source": weather.get("source"),
                "confidence": (source_meta.get("weather") or {}).get("data_confidence"),
            },
            "forecast_hours": [
                {
                    "time": item.get("timestamp_utc"),
                    "temperature_c": (item.get("weather") or {}).get("temperature_c"),
                    "humidity": (item.get("weather") or {}).get("humidity"),
                    "wind_speed": (item.get("weather") or {}).get("wind_speed"),
                }
                for item in (snapshot.get("forecast") or [])
            ],
            "time_context": {
                "snapshot_timestamp_utc": snapshot.get("timestamp_utc"),
                "forecast_window_available": bool(snapshot.get("forecast")),
            },
            "forecast_capabilities": {
                "supports_air_forecast": False,
                "supports_weather_forecast": bool(snapshot.get("forecast")),
                "supports_same_day_timing": "partial" if snapshot.get("forecast") else "none",
            },
            "data_quality": {
                "overall_confidence": (snapshot.get("meta") or {}).get("data_confidence"),
                "aq_source_confidence": (source_meta.get("air") or {}).get("data_confidence"),
                "weather_source_confidence": (source_meta.get("weather") or {}).get("data_confidence"),
                "missing_fields": missing_fields,
            },
            "location": (snapshot.get("meta") or {}).get("location"),
        }
        if intent_recognition:
            environment_state = WeatherWindowSelector().select(
                environment_state=environment_state,
                intent_recognition=intent_recognition,
            )
            environment_state["data_quality"] = EnrichmentService._adjust_quality_for_selected_window(
                data_quality=environment_state["data_quality"],
                forecast_capabilities=environment_state["forecast_capabilities"],
                time_context=environment_state["time_context"],
            )
        return environment_state

    @staticmethod
    def _pollutant(payload: dict | None) -> dict | None:
        if not payload:
            return None
        return {
            "value": payload.get("value"),
            "unit": payload.get("unit"),
            "measured_at_utc": payload.get("measured_at_utc"),
            "source": payload.get("source"),
        }

    @staticmethod
    def _load_saved_snapshot() -> dict | None:
        snapshot_path = Path("logs/latest_environment.json")
        if not snapshot_path.exists():
            return None
        return json.loads(snapshot_path.read_text(encoding="utf-8"))

    @staticmethod
    def _adjust_quality_for_selected_window(
        *,
        data_quality: dict,
        forecast_capabilities: dict,
        time_context: dict,
    ) -> dict:
        if time_context.get("weather_selection_mode") != "forecast_window":
            return data_quality
        adjusted = dict(data_quality)
        overall = adjusted.get("overall_confidence")
        if overall is not None and not forecast_capabilities.get("supports_air_forecast"):
            adjusted["overall_confidence"] = round(max(0.0, overall - 0.18), 3)
        return adjusted
