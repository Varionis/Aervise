from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from config import Settings
from pipeline.enrichment.http import HttpClient


@dataclass
class OpenWeatherProvider:
    settings: Settings
    http_client: HttpClient

    def fetch_current(self, *, lat: float, lon: float) -> dict[str, Any]:
        if not self.settings.openweather_api_key:
            raise ValueError("OPENWEATHER_API_KEY is required")

        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.settings.openweather_api_key,
            "units": self.settings.openweather_units,
        }
        payload = self.http_client.get(f"{self.settings.openweather_api_url}/weather", params=params)
        main = payload.get("main", {})
        wind = payload.get("wind", {})

        return {
            "weather": {
                "temperature_c": main.get("temp"),
                "humidity": main.get("humidity"),
                "wind_speed": wind.get("speed"),
                "measured_at_utc": self._format_timestamp(payload.get("dt")),
                "source": "openweather",
            },
            "forecast": [],
            "meta": {
                "source": "openweather",
                "timezone_offset_seconds": payload.get("timezone"),
                "location_name": payload.get("name"),
                "data_confidence": 1.0,
                "units": self.settings.openweather_units,
            },
        }

    @staticmethod
    def _format_timestamp(value: int | None) -> str | None:
        if value is None:
            return None
        from datetime import UTC, datetime

        return datetime.fromtimestamp(value, UTC).isoformat()
