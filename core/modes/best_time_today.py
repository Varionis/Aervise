from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from core.modes.common import ModeEvaluationHelper


@dataclass
class BestTimeTodayEngine:
    helper: ModeEvaluationHelper = field(default_factory=ModeEvaluationHelper)

    def evaluate(self, decision_input: dict[str, Any]) -> dict[str, Any]:
        baseline_result = self.helper.evaluate_single(decision_input)
        candidates = self._select_candidate_hours(decision_input)
        if not candidates:
            return self._fallback_to_baseline(baseline_result)

        evaluated = []
        for candidate in candidates:
            variant_input = self.helper.build_weather_variant(
                decision_input=decision_input,
                selected_hour=candidate,
                selection_mode="best_time_window",
                confidence_penalty=0.12,
                decision_archetype="NOW_CHECK",
            )
            result = self.helper.evaluate_single(variant_input)
            evaluated.append((candidate, result))

        best_candidate, best_result = min(
            evaluated,
            key=lambda item: (item[1]["decision"]["score"], -item[1]["decision"]["confidence"], item[0].get("time") or ""),
        )
        return self._merge_best_time_result(
            baseline_result=baseline_result,
            best_result=best_result,
            best_candidate=best_candidate,
            evaluated=evaluated,
        )

    def _select_candidate_hours(self, decision_input: dict[str, Any]) -> list[dict[str, Any]]:
        environment_state = decision_input["environment_state"]
        forecast_hours = environment_state.get("forecast_hours") or []
        time_context = environment_state.get("time_context") or {}
        current_timestamp = time_context.get("snapshot_timestamp_utc")
        requested_window = decision_input["request"]["intent"].get("time_window")
        if not current_timestamp:
            return []

        current_dt = datetime.fromisoformat(current_timestamp.replace("Z", "+00:00"))
        candidates: list[dict[str, Any]] = []
        for hour in forecast_hours:
            timestamp = hour.get("time")
            if not timestamp:
                continue
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if parsed.date() != current_dt.date() or parsed <= current_dt:
                continue
            if requested_window and requested_window != "unspecified" and not self.helper.matches_window(parsed.hour, requested_window):
                continue
            candidates.append(hour)
        return candidates

    def _merge_best_time_result(
        self,
        *,
        baseline_result: dict[str, Any],
        best_result: dict[str, Any],
        best_candidate: dict[str, Any],
        evaluated: list[tuple[dict[str, Any], dict[str, Any]]],
    ) -> dict[str, Any]:
        display_time = self.helper.display_time(best_candidate.get("time"))
        best_score = best_result["decision"]["score"]
        baseline_score = baseline_result["decision"]["score"]
        improved = best_score < baseline_score - 0.03
        activity = best_result["request"]["intent"]["activity"].replace("_", " ")

        best_result["recommendation"]["message"] = (
            f"The best weather-supported window today looks closest to {display_time} for {activity}."
            if improved
            else f"The best-time-today check suggests current conditions are already as good as the later weather-supported windows evaluated for {activity}."
        )
        best_result["explanation"]["summary"] = (
            f"The best weather-supported time today for {activity} looks closest to {display_time}."
            if improved
            else f"Current conditions look as good as the later weather-supported windows evaluated for {activity}."
        )
        lead_reason = (
            f"Among the evaluated same-day forecast windows, {display_time} produced the lowest weather-led risk score."
            if improved
            else "None of the evaluated later same-day weather windows scored better than current conditions."
        )
        best_result["explanation"]["reasons"] = [lead_reason] + [
            reason for reason in best_result["explanation"]["reasons"] if reason != lead_reason
        ]

        best_result["mode_result"] = {
            "mode": "best_time_today",
            "comparison": None,
            "best_time": {
                "selected_time": best_candidate.get("time"),
                "display_time": display_time,
                "basis": "weather_only",
                "evaluated_candidates_count": len(evaluated),
                "candidates": [
                    {
                        "time": candidate.get("time"),
                        "display_time": self.helper.display_time(candidate.get("time")),
                        "decision_label": result["decision"]["label"],
                        "score": result["decision"]["score"],
                        "confidence": result["decision"]["confidence"],
                        "weather_basis": "forecast_weather_only",
                    }
                    for candidate, result in evaluated
                ],
            },
        }
        best_result["policy_trace"]["best_time_mode"] = True
        best_result["policy_trace"]["best_time_selected_time"] = best_candidate.get("time")
        best_result["policy_trace"]["best_time_evaluated_candidates"] = len(evaluated)
        return best_result

    @staticmethod
    def _fallback_to_baseline(baseline_result: dict[str, Any]) -> dict[str, Any]:
        baseline_result["recommendation"]["message"] = (
            "A best-time-today forecast window could not be selected from the available same-day weather forecast, so this result is based on current conditions only."
        )
        baseline_result["explanation"]["reasons"] = [
            "A same-day weather forecast window was not available for best-time ranking."
        ] + baseline_result["explanation"]["reasons"]
        baseline_result["mode_result"] = {
            "mode": "best_time_today",
            "comparison": None,
            "best_time": None,
        }
        return baseline_result
