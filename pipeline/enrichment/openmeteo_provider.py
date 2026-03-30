from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from config import Settings
from pipeline.enrichment.http import HttpClient


@dataclass
class OpenMeteoProvider:
    settings: Settings
    http_client: HttpClient

    def fetch_current(self, *, lat: float, lon: float) -> dict[str, Any]:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
            "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m",
            "forecast_hours": 12,
            "timezone": "GMT",
            "wind_speed_unit": "ms",
        }
        payload = self.http_client.get(f"{self.settings.openmeteo_api_url}/forecast", params=params)
        current = payload.get("current", {})
        hourly = payload.get("hourly", {})

        times = hourly.get("time", [])
        temperatures = hourly.get("temperature_2m", [])
        humidities = hourly.get("relative_humidity_2m", [])
        wind_speeds = hourly.get("wind_speed_10m", [])

        forecast = []
        for index, timestamp in enumerate(times[:12]):
            forecast.append(
                {
                    "timestamp_utc": self._to_iso_utc(timestamp),
                    "weather": {
                        "temperature_c": self._safe_index(temperatures, index),
                        "humidity": self._safe_index(humidities, index),
                        "wind_speed": self._safe_index(wind_speeds, index),
                    },
                }
            )

        return {
            "weather": {
                "temperature_c": current.get("temperature_2m"),
                "humidity": current.get("relative_humidity_2m"),
                "wind_speed": current.get("wind_speed_10m"),
                "measured_at_utc": self._to_iso_utc(current.get("time")),
                "source": "openmeteo",
            },
            "forecast": forecast,
            "meta": {
                "source": "openmeteo",
                "timezone": payload.get("timezone"),
                "timezone_abbreviation": payload.get("timezone_abbreviation"),
                "data_confidence": 0.95,
            },
        }

    @staticmethod
    def _safe_index(items: list[Any], index: int) -> Any:
        if index >= len(items):
            return None
        return items[index]

    @staticmethod
    def _to_iso_utc(value: str | None) -> str | None:
        if not value:
            return None
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC).isoformat()
