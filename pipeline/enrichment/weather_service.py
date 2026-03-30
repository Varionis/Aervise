from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from config import Settings
from pipeline.enrichment.openmeteo_provider import OpenMeteoProvider
from pipeline.enrichment.weather_provider import OpenWeatherProvider


@dataclass
class WeatherService:
    settings: Settings
    openweather_provider: OpenWeatherProvider
    openmeteo_provider: OpenMeteoProvider

    def fetch_current(self, *, lat: float, lon: float) -> dict[str, Any]:
        failures: list[dict[str, str]] = []

        for provider_name in self.settings.weather_provider_priority:
            try:
                if provider_name == "openweather":
                    payload = self.openweather_provider.fetch_current(lat=lat, lon=lon)
                elif provider_name == "openmeteo":
                    payload = self.openmeteo_provider.fetch_current(lat=lat, lon=lon)
                else:
                    failures.append({"provider": provider_name, "error": "Unsupported provider"})
                    continue

                payload["meta"]["fallback_chain"] = failures
                payload["meta"]["selected_provider"] = provider_name
                return payload
            except Exception as exc:
                failures.append({"provider": provider_name, "error": str(exc)})

        raise RuntimeError(f"All weather providers failed: {failures}")
