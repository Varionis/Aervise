from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any


@dataclass
class WeatherWindowSelector:
    def select(self, *, environment_state: dict[str, Any], intent_recognition: dict[str, Any]) -> dict[str, Any]:
        time_horizon = str(intent_recognition.get("time_horizon") or "unspecified")
        time_window = str(intent_recognition.get("time_window") or "unspecified")

        if time_horizon not in {"tomorrow", "this_weekend", "future_day"}:
            environment_state["time_context"] = {
                **environment_state.get("time_context", {}),
                "requested_horizon": time_horizon,
                "requested_window": time_window,
                "weather_selection_mode": "current",
                "selected_weather_window_available": False,
            }
            return environment_state

        selected = self._select_forecast_hour(
            forecast_hours=environment_state.get("forecast_hours") or [],
            time_horizon=time_horizon,
            time_window=time_window,
        )
        if not selected:
            environment_state["time_context"] = {
                **environment_state.get("time_context", {}),
                "requested_horizon": time_horizon,
                "requested_window": time_window,
                "weather_selection_mode": "current_fallback",
                "selected_weather_window_available": False,
            }
            return environment_state

        environment_state["weather"] = {
            **environment_state["weather"],
            "temperature_c": selected.get("temperature_c"),
            "humidity": selected.get("humidity"),
            "wind_speed": selected.get("wind_speed"),
            "measured_at_utc": selected.get("time"),
            "source": f"{environment_state['weather'].get('source')}_forecast_window",
        }
        environment_state["time_context"] = {
            **environment_state.get("time_context", {}),
            "requested_horizon": time_horizon,
            "requested_window": time_window,
            "weather_selection_mode": "forecast_window",
            "selected_weather_window_available": True,
            "selected_weather_time_utc": selected.get("time"),
        }
        return environment_state

    def _select_forecast_hour(
        self,
        *,
        forecast_hours: list[dict[str, Any]],
        time_horizon: str,
        time_window: str,
    ) -> dict[str, Any] | None:
        candidates: list[tuple[datetime, dict[str, Any]]] = []
        for item in forecast_hours:
            timestamp = item.get("time")
            if not timestamp:
                continue
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).astimezone(UTC)
            if self._matches_horizon(parsed, time_horizon) and self._matches_window(parsed, time_window):
                candidates.append((parsed, item))

        if not candidates:
            return None
        candidates.sort(key=lambda pair: pair[0])
        return candidates[0][1]

    @staticmethod
    def _matches_horizon(timestamp: datetime, time_horizon: str) -> bool:
        now = datetime.now(UTC)
        today = now.date()
        day = timestamp.date()
        if time_horizon == "tomorrow":
            return day == today + timedelta(days=1)
        if time_horizon == "future_day":
            return day >= today + timedelta(days=1)
        if time_horizon == "this_weekend":
            return timestamp.weekday() in {5, 6}
        return True

    @staticmethod
    def _matches_window(timestamp: datetime, time_window: str) -> bool:
        hour = timestamp.hour
        if time_window == "unspecified":
            return True
        if time_window == "early_morning":
            return 5 <= hour < 8
        if time_window == "morning":
            return 8 <= hour < 12
        if time_window == "midday":
            return 12 <= hour < 14
        if time_window == "afternoon":
            return 14 <= hour < 18
        if time_window == "evening":
            return 18 <= hour < 22
        if time_window == "night":
            return hour >= 22 or hour < 5
        if time_window == "rush_hour":
            return 7 <= hour < 10 or 16 <= hour < 19
        return True
