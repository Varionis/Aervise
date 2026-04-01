from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from core.modes.common import ModeEvaluationHelper


@dataclass
class WhatIfEngine:
    helper: ModeEvaluationHelper = field(default_factory=ModeEvaluationHelper)

    def evaluate(self, decision_input: dict[str, Any]) -> dict[str, Any]:
        intent = decision_input["request"]["intent"]
        adjustment_type = intent.get("adjustment_type")
        if adjustment_type == "duration" or intent.get("source_intent") == "duration_adjustment":
            return self._evaluate_duration_scenario(decision_input)
        return self._evaluate_timing_scenario(decision_input)

    def _evaluate_duration_scenario(self, decision_input: dict[str, Any]) -> dict[str, Any]:
        scenario_result = self.helper.evaluate_single(decision_input)
        baseline_input, baseline_assumption = self._build_duration_baseline(decision_input)
        baseline_result = self.helper.evaluate_single(baseline_input)

        scenario_duration = decision_input["request"]["intent"]["duration_min"]
        baseline_duration = baseline_input["request"]["intent"]["duration_min"]
        improvement = scenario_result["decision"]["score"] < baseline_result["decision"]["score"] - 0.03
        activity = scenario_result["request"]["intent"]["activity"].replace("_", " ")

        if improvement:
            scenario_result["recommendation"]["message"] = (
                f"A shorter {scenario_duration}-minute version looks better than the baseline {baseline_duration}-minute plan for {activity}."
            )
            summary = f"A shorter what-if version of {activity} looks better than the longer baseline plan."
            lead_reason = f"Reducing the duration to {scenario_duration} minutes lowers total exposure compared with the {baseline_duration}-minute baseline."
        else:
            scenario_result["recommendation"]["message"] = (
                f"Reducing this to {scenario_duration} minutes does not materially improve the result over the baseline {baseline_duration}-minute plan for {activity}."
            )
            summary = f"The shorter what-if version of {activity} does not materially outperform the baseline plan."
            lead_reason = f"The shorter {scenario_duration}-minute scenario does not score meaningfully better than the {baseline_duration}-minute baseline."

        scenario_result["explanation"]["summary"] = summary
        scenario_result["explanation"]["reasons"] = [lead_reason] + [
            reason for reason in scenario_result["explanation"]["reasons"] if reason != lead_reason
        ]
        scenario_result["mode_result"] = {
            "mode": "what_if",
            "comparison": None,
            "best_time": None,
            "what_if": {
                "scenario_type": "duration",
                "improvement_expected": improvement,
                "baseline_assumption": baseline_assumption,
                "baseline": self._candidate_from_result(
                    label="baseline",
                    result=baseline_result,
                    basis="baseline_duration",
                    duration_min=baseline_duration,
                ),
                "scenario": self._candidate_from_result(
                    label="scenario",
                    result=scenario_result,
                    basis="adjusted_duration",
                    duration_min=scenario_duration,
                ),
            },
        }
        scenario_result["policy_trace"]["what_if_mode"] = True
        scenario_result["policy_trace"]["what_if_scenario_type"] = "duration"
        scenario_result["policy_trace"]["what_if_improvement_expected"] = improvement
        if baseline_assumption:
            scenario_result["assumptions"] = [baseline_assumption] + list(scenario_result.get("assumptions") or [])
            scenario_result["explanation"]["assumptions"] = [baseline_assumption] + list(
                scenario_result["explanation"].get("assumptions") or []
            )
        return scenario_result

    def _evaluate_timing_scenario(self, decision_input: dict[str, Any]) -> dict[str, Any]:
        baseline_input = deepcopy(decision_input)
        baseline_input["request"]["intent"]["decision_archetype"] = "NOW_CHECK"
        baseline_input["request"]["intent"]["timing_mode"] = "now"
        baseline_input["request"]["intent"]["requested_time"] = "now"
        baseline_result = self.helper.evaluate_single(baseline_input)

        selected_hour = self._select_later_hour(decision_input)
        if not selected_hour:
            return self._fallback_timing_to_baseline(baseline_result)

        scenario_input = self.helper.build_weather_variant(
            decision_input=decision_input,
            selected_hour=selected_hour,
            selection_mode="what_if_window",
            confidence_penalty=0.12,
            decision_archetype="NOW_CHECK",
        )
        scenario_result = self.helper.evaluate_single(scenario_input)
        improvement = scenario_result["decision"]["score"] < baseline_result["decision"]["score"] - 0.03
        display_time = self.helper.display_time(selected_hour.get("time"))
        activity = scenario_result["request"]["intent"]["activity"].replace("_", " ")

        if improvement:
            scenario_result["recommendation"]["message"] = (
                f"If you shift this to around {display_time}, conditions look better than going now for {activity}."
            )
            summary = f"A later what-if window around {display_time} looks better than going now for {activity}."
            lead_reason = f"The later weather-supported window around {display_time} scores better than current conditions."
        else:
            scenario_result["recommendation"]["message"] = (
                f"Shifting this to around {display_time} does not look meaningfully better than going now for {activity}."
            )
            summary = f"A later what-if window around {display_time} does not materially outperform current conditions for {activity}."
            lead_reason = f"The later weather-supported window around {display_time} does not score better than current conditions."

        scenario_result["explanation"]["summary"] = summary
        scenario_result["explanation"]["reasons"] = [lead_reason] + [
            reason for reason in scenario_result["explanation"]["reasons"] if reason != lead_reason
        ]
        scenario_result["mode_result"] = {
            "mode": "what_if",
            "comparison": None,
            "best_time": None,
            "what_if": {
                "scenario_type": "timing",
                "improvement_expected": improvement,
                "baseline_assumption": None,
                "baseline": self._candidate_from_result(
                    label="baseline",
                    result=baseline_result,
                    basis="current",
                    duration_min=baseline_input["request"]["intent"]["duration_min"],
                    display_time="now",
                ),
                "scenario": self._candidate_from_result(
                    label="scenario",
                    result=scenario_result,
                    basis="later_weather_window",
                    duration_min=scenario_input["request"]["intent"]["duration_min"],
                    time=selected_hour.get("time"),
                    display_time=display_time,
                ),
            },
        }
        scenario_result["policy_trace"]["what_if_mode"] = True
        scenario_result["policy_trace"]["what_if_scenario_type"] = "timing"
        scenario_result["policy_trace"]["what_if_improvement_expected"] = improvement
        return scenario_result

    def _build_duration_baseline(self, decision_input: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
        baseline_input = deepcopy(decision_input)
        intent = baseline_input["request"]["intent"]
        reference_duration = intent.get("reference_duration_min")
        if reference_duration is not None:
            baseline_duration = reference_duration
            assumption = None
        else:
            profile = intent.get("activity_profile") or {}
            baseline_duration = profile.get("typical_duration_min") or max(intent["duration_min"] * 2, intent["duration_min"] + 15)
            assumption = (
                f"No explicit original duration was provided, so the baseline was inferred as {baseline_duration} minutes."
            )

        intent["decision_archetype"] = "NOW_CHECK"
        intent["duration_min"] = int(baseline_duration)
        intent["duration_band"] = self._duration_band(int(baseline_duration))
        return baseline_input, assumption

    def _select_later_hour(self, decision_input: dict[str, Any]) -> dict[str, Any] | None:
        environment_state = decision_input["environment_state"]
        time_context = environment_state.get("time_context") or {}
        current_timestamp = time_context.get("snapshot_timestamp_utc")
        forecast_hours = environment_state.get("forecast_hours") or []
        requested_window = decision_input["request"]["intent"].get("time_window")
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

    def _fallback_timing_to_baseline(self, baseline_result: dict[str, Any]) -> dict[str, Any]:
        baseline_result["recommendation"]["message"] = (
            "A later what-if window could not be selected from the available same-day weather forecast, so this is based on current conditions only."
        )
        baseline_result["explanation"]["reasons"] = [
            "A later same-day weather window was not available for this timing simulation."
        ] + baseline_result["explanation"]["reasons"]
        baseline_result["mode_result"] = {
            "mode": "what_if",
            "comparison": None,
            "best_time": None,
            "what_if": None,
        }
        return baseline_result

    @staticmethod
    def _candidate_from_result(
        *,
        label: str,
        result: dict[str, Any],
        basis: str,
        duration_min: int | None,
        time: str | None = None,
        display_time: str | None = None,
    ) -> dict[str, Any]:
        return {
            "label": label,
            "time": time or result["environment_state"]["weather"].get("measured_at_utc"),
            "display_time": display_time,
            "duration_min": duration_min,
            "decision_label": result["decision"]["label"],
            "score": result["decision"]["score"],
            "confidence": result["decision"]["confidence"],
            "basis": basis,
        }

    @staticmethod
    def _duration_band(duration_min: int) -> str:
        if duration_min <= 15:
            return "short"
        if duration_min <= 60:
            return "medium"
        return "long"
