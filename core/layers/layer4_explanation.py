from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class DecisionLayer4Explainer:
    def explain(self, layer3_payload: dict[str, Any]) -> dict[str, Any]:
        intent = layer3_payload["request"]["intent"]
        environment_state = layer3_payload["environment_state"]
        decision = layer3_payload["decision"]
        risk_factors = layer3_payload["risk_factors"]
        request_feasibility = layer3_payload["request_feasibility"]

        timing_guidance = self._timing_guidance(layer3_payload)
        modifications = list(layer3_payload.get("modifications") or [])
        if timing_guidance.get("modification"):
            modifications.append(timing_guidance["modification"])

        explanation = {
            "summary": self._summary(
                intent=intent,
                decision_label=decision["label"],
                timing_guidance=timing_guidance,
                request_feasibility=request_feasibility,
            ),
            "reasons": self._reasons(
                intent=intent,
                risk_factors=risk_factors,
                decision_label=decision["label"],
                request_feasibility=request_feasibility,
            ),
            "adjustments": [item["suggestion"] for item in modifications],
            "assumptions": self._assumptions(layer3_payload, timing_guidance),
            "timing_guidance": timing_guidance,
        }

        return {
            **layer3_payload,
            "modifications": modifications,
            "explanation": explanation,
            "safe_alternative_available": timing_guidance["alternative_recommendation"] is not None,
            "alternative_recommendation": timing_guidance["alternative_recommendation"],
        }

    def _summary(
        self,
        *,
        intent: dict[str, Any],
        decision_label: str,
        timing_guidance: dict[str, Any],
        request_feasibility: dict[str, Any],
    ) -> str:
        activity = intent["activity"].replace("_", " ")
        source_intent = intent.get("source_intent", "activity_check")
        future_horizon = intent.get("time_horizon") in {"tomorrow", "this_weekend", "future_day"}
        summaries = {
            "go_ahead": f"Current conditions look acceptable for {activity}.",
            "okay_with_caution": f"{activity.title()} looks feasible, but conditions are not ideal.",
            "shorten_or_modify": f"{activity.title()} is not ideal as requested right now.",
            "avoid_for_now": f"It is better to avoid {activity} right now.",
            "insufficient_confidence": "The available data is not strong enough for a confident recommendation.",
        }
        summary = summaries[decision_label]
        if request_feasibility.get("status") == "exceeds_typical":
            summary = f"The requested duration for {activity} is longer than the typical supported range."
        elif request_feasibility.get("status") == "exceeds_hard_upper":
            summary = f"The requested duration for {activity} is outside the supported range."
        if future_horizon:
            requested_time = intent.get("requested_time") or intent.get("time_horizon", "the requested future window").replace("_", " ")
            if decision_label == "insufficient_confidence":
                summary = f"This is a future-window request for {activity} ({requested_time}), but the current system cannot assess it confidently yet."
            else:
                summary = f"This is a future-window assessment for {activity} ({requested_time})."
        if source_intent == "best_time_today":
            summary = f"This is a best-time-today assessment for {activity}."
        elif source_intent in {"compare_times", "time_shift"}:
            summary = f"This is a same-day comparison for {activity}."
        elif source_intent == "route_mode_choice":
            summary = "This is a route or mode choice recommendation under current conditions."
        elif source_intent == "duration_adjustment":
            summary = f"This is a shortened-plan assessment for {activity}."
        elif source_intent == "should_avoid":
            summary = f"This is a binary avoid-or-proceed assessment for {activity}."
        if timing_guidance["message"] and decision_label in {"shorten_or_modify", "avoid_for_now"}:
            summary = f"{summary} {timing_guidance['message']}"
        return summary

    def _reasons(
        self,
        *,
        intent: dict[str, Any],
        risk_factors: dict[str, Any],
        decision_label: str,
        request_feasibility: dict[str, Any],
    ) -> list[str]:
        source_intent = intent.get("source_intent", "activity_check")
        reasons: list[str] = []
        if request_feasibility.get("reason"):
            reasons.append(request_feasibility["reason"])
        if intent.get("time_horizon") in {"tomorrow", "this_weekend", "future_day"}:
            reasons.append("Future-day requests are currently limited because the system does not yet have air-quality forecast support.")
        if source_intent == "best_time_today":
            reasons.append("Best-time requests are currently ranked with weather forecast support only.")
        if source_intent in {"compare_times", "time_shift"}:
            reasons.append("Same-day comparison requests are currently limited to weather-supported timing differences.")
        if source_intent == "route_mode_choice" and intent.get("candidate_modes"):
            reasons.append(f"Requested commute modes considered: {', '.join(intent['candidate_modes'])}.")
        if risk_factors["air_burden"]["score"] >= 0.2:
            reasons.append(
                f"Air pollution adds a {risk_factors['air_burden']['level'].replace('_', ' ')} respiratory burden for this activity."
            )
        if risk_factors["heat_burden"]["score"] >= 0.18:
            reasons.append("Temperature and humidity add noticeable physical strain.")
        if risk_factors["exposure_burden"]["score"] >= 0.18:
            reasons.append(f"A {intent['duration_min']}-minute session increases cumulative exposure.")
        if risk_factors["confidence_penalty"]["score"] >= 0.25:
            reasons.append("The recommendation carries extra uncertainty because source confidence is limited.")
        if not reasons and decision_label == "go_ahead":
            reasons.append("Air quality, weather strain, and exposure burden are all currently in a manageable range.")
        return reasons

    def _timing_guidance(self, payload: dict[str, Any]) -> dict[str, Any]:
        capabilities = payload["environment_state"]["forecast_capabilities"]
        decision_label = payload["decision"]["label"]
        source_intent = payload["request"]["intent"].get("source_intent", "activity_check")
        current_weather = payload["environment_state"]["weather"]
        forecast_hours = payload["environment_state"]["forecast_hours"]
        time_horizon = payload["request"]["intent"].get("time_horizon")

        if not capabilities.get("supports_weather_forecast"):
            return {
                "message": None,
                "timing_basis": "none",
                "timing_confidence": "none",
                "alternative_recommendation": None,
                "modification": None,
            }

        if time_horizon in {"tomorrow", "this_weekend", "future_day"}:
            return {
                "message": None,
                "timing_basis": "none",
                "timing_confidence": "none",
                "alternative_recommendation": None,
                "modification": None,
                "assumption": "Future-day timing guidance is disabled because the current forecast support is limited to same-day weather guidance.",
            }

        if decision_label not in {"shorten_or_modify", "avoid_for_now", "okay_with_caution"} and source_intent not in {
            "best_time_today",
            "compare_times",
            "time_shift",
        }:
            return {
                "message": None,
                "timing_basis": "weather_only",
                "timing_confidence": "low",
                "alternative_recommendation": None,
                "modification": None,
            }

        current_temp = current_weather.get("temperature_c")
        best_hour = self._best_weather_hour(forecast_hours, current_temp)
        if not best_hour:
            return {
                "message": None,
                "timing_basis": "weather_only",
                "timing_confidence": "low",
                "alternative_recommendation": None,
                "modification": None,
            }

        message = (
            f"Weather may improve later around {best_hour['display_time']} because temperature drops to "
            f"{best_hour['temperature_c']}\u00b0C."
        )
        if source_intent == "best_time_today":
            message = f"The best weather-supported window today looks closest to {best_hour['display_time']}."
        elif source_intent in {"compare_times", "time_shift"}:
            message = f"Later today may look better around {best_hour['display_time']} based on the available weather forecast."
        assumption = "This timing suggestion is weather-based only because same-day air-quality forecast is not available yet."
        alternative = {
            "time": best_hour["time"],
            "display_time": best_hour["display_time"],
            "basis": "weather_only",
            "confidence": "low",
            "reason": assumption,
        }
        modification = {
            "type": "timing",
            "suggestion": f"Consider a later window around {best_hour['display_time']} if cooler weather would help.",
        }
        return {
            "message": message,
            "timing_basis": "weather_only",
            "timing_confidence": "low",
            "alternative_recommendation": alternative,
            "modification": modification,
            "assumption": assumption,
        }

    @staticmethod
    def _best_weather_hour(forecast_hours: list[dict[str, Any]], current_temp: float | None) -> dict[str, Any] | None:
        candidates = []
        for hour in forecast_hours:
            temp = hour.get("temperature_c")
            timestamp = hour.get("time")
            if temp is None or not timestamp:
                continue
            if current_temp is not None and temp >= current_temp:
                continue
            candidates.append(
                {
                    "time": timestamp,
                    "display_time": DecisionLayer4Explainer._display_time(timestamp),
                    "temperature_c": temp,
                    "humidity": hour.get("humidity"),
                    "wind_speed": hour.get("wind_speed"),
                }
            )
        if not candidates:
            return None
        return min(candidates, key=lambda item: item["temperature_c"])

    @staticmethod
    def _display_time(timestamp: str) -> str:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return parsed.strftime("%I %p").lstrip("0")

    @staticmethod
    def _assumptions(payload: dict[str, Any], timing_guidance: dict[str, Any]) -> list[str]:
        assumptions = list(payload.get("assumptions") or [])
        capabilities = payload["environment_state"]["forecast_capabilities"]
        if not capabilities.get("supports_air_forecast"):
            assumptions.append("No same-day air-quality forecast is available yet.")
        if timing_guidance.get("assumption"):
            assumptions.append(timing_guidance["assumption"])
        return assumptions
