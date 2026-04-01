from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from core.modes.common import ModeEvaluationHelper


@dataclass
class CompareNowLaterEngine:
    helper: ModeEvaluationHelper = field(default_factory=ModeEvaluationHelper)

    def evaluate(self, decision_input: dict[str, Any]) -> dict[str, Any]:
        current_result = self.helper.evaluate_single(decision_input)
        alternative_input, selected_hour = self._build_alternative_input(decision_input)
        if not alternative_input or not selected_hour:
            return self._fallback_to_current(current_result)

        later_result = self.helper.evaluate_single(alternative_input)
        enriched = self._merge_compare_result(
            current_result=current_result,
            later_result=later_result,
            selected_hour=selected_hour,
        )
        return enriched

    def _build_alternative_input(self, decision_input: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        environment_state = decision_input["environment_state"]
        time_context = environment_state.get("time_context") or {}
        current_timestamp = time_context.get("snapshot_timestamp_utc")
        forecast_hours = environment_state.get("forecast_hours") or []
        intent = decision_input["request"]["intent"]
        selected_hour = self._select_later_hour(
            current_timestamp=current_timestamp,
            forecast_hours=forecast_hours,
            requested_window=intent.get("time_window"),
        )
        if not selected_hour:
            return None, None

        alternative_input = self.helper.build_weather_variant(
            decision_input=decision_input,
            selected_hour=selected_hour,
            selection_mode="compare_window",
            confidence_penalty=0.12,
            decision_archetype="NOW_CHECK",
        )
        return alternative_input, selected_hour

    def _merge_compare_result(
        self,
        *,
        current_result: dict[str, Any],
        later_result: dict[str, Any],
        selected_hour: dict[str, Any],
    ) -> dict[str, Any]:
        current_score = current_result["decision"]["score"]
        later_score = later_result["decision"]["score"]
        choose_later = later_score < current_score - 0.03
        choose_current = current_score < later_score - 0.03

        selected_option = "later" if choose_later else "current"
        if choose_current:
            selected_option = "current"

        display_time = self._display_time(selected_hour.get("time"))
        if choose_later:
            current_result["recommendation"]["message"] = (
                f"Later looks better than now. The weather-supported option around {display_time} appears safer than going now."
            )
            current_result["explanation"]["summary"] = (
                f"Later looks better than now for {current_result['request']['intent']['activity'].replace('_', ' ')}."
            )
            current_result["explanation"]["reasons"] = [
                f"The later weather window around {display_time} scores better than current conditions."
            ] + current_result["explanation"]["reasons"]
        else:
            current_result["recommendation"]["message"] = (
                f"Current conditions look as good as or better than the later weather-supported option around {display_time}."
            )
            current_result["explanation"]["summary"] = (
                f"Now looks as good as or better than later for {current_result['request']['intent']['activity'].replace('_', ' ')}."
            )
            current_result["explanation"]["reasons"] = [
                f"The later weather window around {display_time} does not score better than current conditions."
            ] + current_result["explanation"]["reasons"]

        current_result["mode_result"] = {
            "mode": "compare_now_later",
            "comparison": {
                "selected_option": selected_option,
                "basis": "weather_only",
                "candidates": [
                    {
                        "label": "current",
                        "time": current_result["environment_state"]["weather"].get("measured_at_utc"),
                        "display_time": "now",
                        "decision_label": current_result["decision"]["label"],
                        "score": current_score,
                        "confidence": current_result["decision"]["confidence"],
                        "weather_basis": "current",
                    },
                    {
                        "label": "later",
                        "time": selected_hour.get("time"),
                        "display_time": display_time,
                        "decision_label": later_result["decision"]["label"],
                        "score": later_score,
                        "confidence": later_result["decision"]["confidence"],
                        "weather_basis": "forecast_weather_only",
                    },
                ],
            },
        }
        current_result["policy_trace"]["comparison_mode"] = True
        current_result["policy_trace"]["comparison_selected_option"] = selected_option
        return current_result

    @staticmethod
    def _fallback_to_current(current_result: dict[str, Any]) -> dict[str, Any]:
        current_result["mode_result"] = {"mode": "compare_now_later", "comparison": None}
        current_result["recommendation"]["message"] = (
            "A later comparison window could not be selected from the available same-day weather forecast, so this is based on current conditions only."
        )
        current_result["explanation"]["reasons"] = [
            "A later same-day weather comparison window was not available."
        ] + current_result["explanation"]["reasons"]
        return current_result

    def _select_later_hour(
        self,
        *,
        current_timestamp: str | None,
        forecast_hours: list[dict[str, Any]],
        requested_window: str | None,
    ) -> dict[str, Any] | None:
        if not current_timestamp:
            return None
        current_dt = datetime.fromisoformat(current_timestamp.replace("Z", "+00:00"))
        same_day: list[dict[str, Any]] = []
        for hour in forecast_hours:
            timestamp = hour.get("time")
            if not timestamp:
                continue
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if parsed.date() != current_dt.date() or parsed <= current_dt:
                continue
            if requested_window and requested_window != "unspecified" and not self.helper.matches_window(parsed.hour, requested_window):
                continue
            same_day.append(hour)
        if not same_day:
            return None
        return min(same_day, key=lambda item: (item.get("temperature_c") is None, item.get("temperature_c", 999), item.get("time")))

    @staticmethod
    def _display_time(timestamp: str | None) -> str | None:
        return ModeEvaluationHelper.display_time(timestamp)
