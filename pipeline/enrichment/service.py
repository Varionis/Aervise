from __future__ import annotations

from dataclasses import dataclass

from config import Settings
from pipeline.enrichment.air_provider import OpenAQProvider
from pipeline.enrichment.http import HttpClient
from pipeline.enrichment.normalization import EnvironmentAggregator
from pipeline.enrichment.openmeteo_provider import OpenMeteoProvider
from pipeline.enrichment.weather_provider import OpenWeatherProvider
from pipeline.enrichment.weather_service import WeatherService


@dataclass
class EnrichmentService:
    settings: Settings

    def enrich(self, *, lat: float, lon: float) -> dict:
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
        return self._to_environment_state(snapshot)

    @staticmethod
    def _to_environment_state(snapshot: dict) -> dict:
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

        return {
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
