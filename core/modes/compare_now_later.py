from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.modes.common import ModeEvaluationHelper


@dataclass
class CompareNowLaterEngine:
    helper: ModeEvaluationHelper = field(default_factory=ModeEvaluationHelper)

    def evaluate(self, decision_input: dict[str, Any]) -> dict[str, Any]:
        current_result = self.helper.evaluate_single(decision_input)
        selected_hour, later_result = self._evaluate_best_later_candidate(decision_input)
        if not selected_hour or not later_result:
            return self._fallback_to_current(current_result)
        enriched = self._merge_compare_result(
            current_result=current_result,
            later_result=later_result,
            selected_hour=selected_hour,
        )
        return enriched

    def _evaluate_best_later_candidate(
        self,
        decision_input: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        candidates = self.helper.collect_same_day_candidates(
            decision_input=decision_input,
            requested_window=decision_input["request"]["intent"].get("time_window"),
        )
        evaluated = self.helper.evaluate_weather_candidates(
            decision_input=decision_input,
            selection_mode="compare_window",
            confidence_penalty=0.12,
            candidates=candidates,
        )
        return self.helper.select_best_evaluated_candidate(evaluated)

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

    @staticmethod
    def _display_time(timestamp: str | None) -> str | None:
        return ModeEvaluationHelper.display_time(timestamp)
