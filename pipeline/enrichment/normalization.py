from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from config import Settings
from pipeline.enrichment.air_provider import OpenAQProvider
from pipeline.enrichment.weather_service import WeatherService


@dataclass
class EnvironmentAggregator:
    settings: Settings
    air_provider: OpenAQProvider
    weather_service: WeatherService

    def fetch_snapshot(self, *, lat: float, lon: float) -> dict[str, Any]:
        air_payload = self.air_provider.fetch_current(lat=lat, lon=lon)
        weather_payload = self.weather_service.fetch_current(lat=lat, lon=lon)

        air_confidence = air_payload["meta"]["data_confidence"]
        weather_confidence = weather_payload["meta"]["data_confidence"]

        return {
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "environment": {
                "air": air_payload["air"],
                "weather": weather_payload["weather"],
            },
            "forecast": weather_payload["forecast"],
            "meta": {
                "location": {"lat": lat, "lon": lon},
                "data_confidence": round((air_confidence + weather_confidence) / 2, 3),
                "sources": {
                    "air": air_payload["meta"],
                    "weather": weather_payload["meta"],
                },
            },
        }
