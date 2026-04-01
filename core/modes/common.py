from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from core import RequestFeasibilityEvaluator, DecisionLayer2Evaluator, DecisionLayer3Policy, DecisionLayer4Explainer


@dataclass
class ModeEvaluationHelper:
    def evaluate_single(self, decision_input: dict[str, Any]) -> dict[str, Any]:
        feasibility = RequestFeasibilityEvaluator().evaluate(decision_input)
        layer2 = DecisionLayer2Evaluator().evaluate(feasibility)
        layer3 = DecisionLayer3Policy().evaluate(layer2)
        return DecisionLayer4Explainer().explain(layer3)

    def build_weather_variant(
        self,
        *,
        decision_input: dict[str, Any],
        selected_hour: dict[str, Any],
        selection_mode: str,
        confidence_penalty: float,
        decision_archetype: str | None = None,
        timing_mode: str = "specific_hour",
    ) -> dict[str, Any]:
        alternative_input = deepcopy(decision_input)
        if decision_archetype is not None:
            alternative_input["request"]["intent"]["decision_archetype"] = decision_archetype
        alternative_input["request"]["intent"]["timing_mode"] = timing_mode
        alternative_input["request"]["intent"]["requested_time"] = selected_hour.get("time")
        alternative_input["environment_state"]["weather"] = {
            **alternative_input["environment_state"]["weather"],
            "temperature_c": selected_hour.get("temperature_c"),
            "humidity": selected_hour.get("humidity"),
            "wind_speed": selected_hour.get("wind_speed"),
            "measured_at_utc": selected_hour.get("time"),
            "source": f"{alternative_input['environment_state']['weather'].get('source')}_{selection_mode}",
        }
        alternative_input["environment_state"]["time_context"] = {
            **alternative_input["environment_state"].get("time_context", {}),
            "weather_selection_mode": selection_mode,
            "selected_weather_window_available": True,
            "selected_weather_time_utc": selected_hour.get("time"),
        }
        quality = dict(alternative_input["environment_state"].get("data_quality") or {})
        overall = quality.get("overall_confidence")
        if overall is not None:
            quality["overall_confidence"] = round(max(0.0, overall - confidence_penalty), 3)
        alternative_input["environment_state"]["data_quality"] = quality
        return alternative_input

    @staticmethod
    def matches_window(hour: int, requested_window: str) -> bool:
        if requested_window == "early_morning":
            return 5 <= hour < 8
        if requested_window == "morning":
            return 8 <= hour < 12
        if requested_window == "midday":
            return 12 <= hour < 14
        if requested_window == "afternoon":
            return 14 <= hour < 18
        if requested_window == "evening":
            return 18 <= hour < 22
        if requested_window == "night":
            return hour >= 22 or hour < 5
        if requested_window == "rush_hour":
            return 7 <= hour < 10 or 16 <= hour < 19
        return True

    @staticmethod
    def display_time(timestamp: str | None) -> str | None:
        if not timestamp:
            return None
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return parsed.strftime("%I %p").lstrip("0")
