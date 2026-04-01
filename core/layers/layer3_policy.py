from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from config import Settings, get_settings


WEIGHTS_BY_ARCHETYPE = {
    "outdoor_high_exertion": {
        "air_burden": 0.34,
        "heat_burden": 0.28,
        "exposure_burden": 0.24,
        "disruption_factor": 0.06,
        "confidence_penalty": 0.08,
    },
    "outdoor_low_exertion": {
        "air_burden": 0.3,
        "heat_burden": 0.22,
        "exposure_burden": 0.2,
        "disruption_factor": 0.08,
        "confidence_penalty": 0.2,
    },
    "brief_outdoor_exposure": {
        "air_burden": 0.25,
        "heat_burden": 0.16,
        "exposure_burden": 0.12,
        "disruption_factor": 0.07,
        "confidence_penalty": 0.4,
    },
    "commute_routine": {
        "air_burden": 0.31,
        "heat_burden": 0.22,
        "exposure_burden": 0.22,
        "disruption_factor": 0.1,
        "confidence_penalty": 0.15,
    },
    "indoor_outdoor": {
        "air_burden": 0.26,
        "heat_burden": 0.14,
        "exposure_burden": 0.08,
        "disruption_factor": 0.02,
        "confidence_penalty": 0.5,
    },
}


@dataclass
class DecisionLayer3Policy:
    settings: Settings = field(default_factory=get_settings)

    def evaluate(self, layer2_payload: dict[str, Any]) -> dict[str, Any]:
        intent = layer2_payload["request"]["intent"]
        user_context = layer2_payload["request"]["user_context"]
        environment_state = layer2_payload["environment_state"]
        risk_factors = layer2_payload["risk_factors"]
        request_feasibility = layer2_payload["request_feasibility"]

        stale_snapshot_block = self._stale_fallback_snapshot_constraint(intent=intent, environment_state=environment_state)
        if stale_snapshot_block:
            decision = {"label": "insufficient_confidence", "score": 1.0, "confidence": 0.25}
            payload = {
                **layer2_payload,
                "decision": decision,
                "recommendation": self._recommendation_from_decision(
                    intent=intent,
                    decision=decision["label"],
                    hard_constraints=stale_snapshot_block,
                ),
                "factor_breakdown": self._factor_breakdown(risk_factors),
                "reasoning": [item["reason"] for item in stale_snapshot_block],
                "modifications": [],
                "assumptions": self._assumptions(layer2_payload),
                "policy_trace": {
                    "hard_constraints_triggered": stale_snapshot_block,
                    "score_components": {},
                    "overrides_applied": [],
                },
            }
            return self._apply_intent_behavior(payload)

        future_horizon_block = self._unsupported_future_horizon(intent=intent, environment_state=environment_state)
        if future_horizon_block:
            decision = {"label": "insufficient_confidence", "score": 1.0, "confidence": 0.35}
            payload = {
                **layer2_payload,
                "decision": decision,
                "recommendation": self._recommendation_from_decision(
                    intent=intent,
                    decision=decision["label"],
                    hard_constraints=future_horizon_block,
                ),
                "factor_breakdown": self._factor_breakdown(risk_factors),
                "reasoning": [item["reason"] for item in future_horizon_block],
                "modifications": [],
                "assumptions": self._assumptions(layer2_payload),
                "policy_trace": {
                    "hard_constraints_triggered": future_horizon_block,
                    "score_components": {},
                    "overrides_applied": [],
                },
            }
            return self._apply_intent_behavior(payload)

        feasibility_block = self._feasibility_hard_constraint(request_feasibility=request_feasibility)
        if feasibility_block:
            decision = {"label": "insufficient_confidence", "score": 1.0, "confidence": 0.4}
            payload = {
                **layer2_payload,
                "decision": decision,
                "recommendation": self._recommendation_from_decision(
                    intent=intent,
                    decision=decision["label"],
                    hard_constraints=feasibility_block,
                ),
                "factor_breakdown": self._factor_breakdown(risk_factors),
                "reasoning": [item["reason"] for item in feasibility_block],
                "modifications": [{"type": "duration", "suggestion": f"Use a much shorter duration closer to {request_feasibility['typical_duration_min']} minutes."}] if request_feasibility.get("typical_duration_min") else [],
                "assumptions": self._assumptions(layer2_payload),
                "policy_trace": {
                    "hard_constraints_triggered": feasibility_block,
                    "score_components": {},
                    "overrides_applied": [],
                },
            }
            return self._apply_intent_behavior(payload)

        hard_constraints = self._hard_constraints(intent=intent, user_context=user_context, environment_state=environment_state)
        if hard_constraints:
            decision = self._blocked_decision(hard_constraints)
            recommendation = self._recommendation_from_decision(intent=intent, decision=decision["label"], hard_constraints=hard_constraints)
            payload = {
                **layer2_payload,
                "decision": decision,
                "recommendation": recommendation,
                "factor_breakdown": self._factor_breakdown(risk_factors),
                "reasoning": [item["reason"] for item in hard_constraints],
                "modifications": self._modifications(
                    intent=intent,
                    decision_label=decision["label"],
                    environment_state=environment_state,
                    request_feasibility=request_feasibility,
                ),
                "assumptions": self._assumptions(layer2_payload),
                "policy_trace": {
                    "hard_constraints_triggered": hard_constraints,
                    "score_components": {},
                    "overrides_applied": [],
                },
            }
            return self._apply_intent_behavior(payload)

        weights = WEIGHTS_BY_ARCHETYPE.get(intent["activity_archetype"], WEIGHTS_BY_ARCHETYPE["outdoor_low_exertion"])
        score_components = {
            name: round(weights[name] * risk_factors[name]["score"], 3)
            for name in weights
        }
        weighted_risk_score = round(sum(score_components.values()), 3)

        decision_label = self._map_decision_label(weighted_risk_score)
        overrides = self._apply_overrides(
            decision_label=decision_label,
            weighted_risk_score=weighted_risk_score,
            intent=intent,
            user_context=user_context,
            environment_state=environment_state,
            risk_factors=risk_factors,
            request_feasibility=request_feasibility,
        )
        if overrides:
            decision_label = overrides[-1]["decision_label"]

        decision = {
            "label": decision_label,
            "score": weighted_risk_score,
            "confidence": round(max(0.0, 1.0 - risk_factors["confidence_penalty"]["score"]), 3),
        }

        payload = {
            **layer2_payload,
            "decision": decision,
            "recommendation": self._recommendation_from_decision(intent=intent, decision=decision_label, hard_constraints=[]),
            "factor_breakdown": self._factor_breakdown(risk_factors),
            "reasoning": self._reasoning(intent=intent, risk_factors=risk_factors, request_feasibility=request_feasibility),
            "modifications": self._modifications(
                intent=intent,
                decision_label=decision_label,
                environment_state=environment_state,
                request_feasibility=request_feasibility,
            ),
            "assumptions": self._assumptions(layer2_payload),
            "policy_trace": {
                "hard_constraints_triggered": [],
                "score_components": score_components,
                "overrides_applied": overrides,
                "weights": weights,
            },
        }
        return self._apply_intent_behavior(payload)

    def _hard_constraints(
        self,
        *,
        intent: dict[str, Any],
        user_context: dict[str, Any],
        environment_state: dict[str, Any],
    ) -> list[dict[str, Any]]:
        constraints: list[dict[str, Any]] = []
        pm25 = self._pollutant_value(environment_state, "pm25")
        temperature = environment_state["weather"].get("temperature_c")
        humidity = environment_state["weather"].get("humidity")
        heat_index_c = self._heat_index_celsius(temperature, humidity)
        missing_fields = set(environment_state["data_quality"].get("missing_fields") or [])

        if {"pm25", "temperature_c", "humidity"} & missing_fields:
            constraints.append(
                {
                    "code": "INSUFFICIENT_CORE_INPUTS",
                    "reason": "Core environmental inputs are missing for a safe recommendation.",
                }
            )
        if pm25 is not None and pm25 > 150 and intent["intensity"] == "high":
            constraints.append(
                {
                    "code": "PM25_EXTREME_HIGH_INTENSITY",
                    "reason": "Air pollution is too high for high-intensity outdoor activity.",
                }
            )
        if temperature is not None and temperature > 38:
            constraints.append(
                {
                    "code": "EXTREME_HEAT",
                    "reason": "Outdoor temperature is in the extreme heat range.",
                }
            )
        if heat_index_c is not None and heat_index_c > 35 and intent["intensity"] == "high":
            constraints.append(
                {
                    "code": "HEAT_INDEX_HIGH_EXERTION",
                    "reason": "Heat stress is too high for intense activity.",
                }
            )
        if user_context.get("sensitive_group") and pm25 is not None and pm25 > 80:
            constraints.append(
                {
                    "code": "SENSITIVE_GROUP_PM25",
                    "reason": "PM2.5 is too elevated for a sensitive user group.",
                }
            )
        return constraints

    @staticmethod
    def _unsupported_future_horizon(*, intent: dict[str, Any], environment_state: dict[str, Any]) -> list[dict[str, Any]]:
        if intent.get("time_horizon") not in {"tomorrow", "this_weekend", "future_day"}:
            return []
        if environment_state.get("time_context", {}).get("selected_weather_window_available"):
            return []
        return [
            {
                "code": "FUTURE_HORIZON_NOT_SUPPORTED",
                "reason": "The requested future weather window could not be selected from the available forecast data.",
            }
        ]

    def _stale_fallback_snapshot_constraint(self, *, intent: dict[str, Any], environment_state: dict[str, Any]) -> list[dict[str, Any]]:
        time_context = environment_state.get("time_context") or {}
        if time_context.get("data_origin") != "saved_snapshot_fallback":
            return []
        age_minutes = time_context.get("snapshot_age_minutes")
        if age_minutes is None or age_minutes <= self.settings.max_fallback_snapshot_age_minutes:
            return []

        source_intent = intent.get("source_intent")
        time_horizon = intent.get("time_horizon")
        same_day_or_unspecified = time_horizon in {"now", "later_today", "unspecified"}
        planning_or_current = source_intent in {"activity_check", "best_time_today", "compare_times", "time_shift", "duration_adjustment"}
        if not (same_day_or_unspecified and planning_or_current):
            return []

        return [
            {
                "code": "STALE_FALLBACK_SNAPSHOT",
                "reason": (
                    f"The only available saved fallback snapshot is {round(age_minutes)} minutes old, so this same-day recommendation "
                    "would be misleading."
                ),
            }
        ]

    @staticmethod
    def _feasibility_hard_constraint(*, request_feasibility: dict[str, Any]) -> list[dict[str, Any]]:
        if request_feasibility.get("status") != "exceeds_hard_upper":
            return []
        return [
            {
                "code": "REQUEST_EXCEEDS_HARD_DURATION_UPPER",
                "reason": request_feasibility.get("reason")
                or "The requested duration is beyond the supported range for this activity.",
            }
        ]

    @staticmethod
    def _blocked_decision(hard_constraints: list[dict[str, Any]]) -> dict[str, Any]:
        codes = {item["code"] for item in hard_constraints}
        if "INSUFFICIENT_CORE_INPUTS" in codes:
            return {"label": "insufficient_confidence", "score": 1.0, "confidence": 0.2}
        return {"label": "avoid_for_now", "score": 1.0, "confidence": 0.9}

    @staticmethod
    def _map_decision_label(score: float) -> str:
        if score < 0.25:
            return "go_ahead"
        if score < 0.45:
            return "okay_with_caution"
        if score < 0.68:
            return "shorten_or_modify"
        return "avoid_for_now"

    def _apply_overrides(
        self,
        *,
        decision_label: str,
        weighted_risk_score: float,
        intent: dict[str, Any],
        user_context: dict[str, Any],
        environment_state: dict[str, Any],
        risk_factors: dict[str, Any],
        request_feasibility: dict[str, Any],
    ) -> list[dict[str, Any]]:
        overrides: list[dict[str, Any]] = []
        pm25 = self._pollutant_value(environment_state, "pm25")
        temperature = environment_state["weather"].get("temperature_c")
        humidity = environment_state["weather"].get("humidity")
        heat_index_c = self._heat_index_celsius(temperature, humidity)

        if pm25 is not None and pm25 > 100 and intent["duration_min"] > 60 and decision_label in {"go_ahead", "okay_with_caution"}:
            decision_label = "shorten_or_modify"
            overrides.append({"rule": "PM25_LONG_DURATION", "decision_label": decision_label})

        if heat_index_c is not None and heat_index_c > 35 and intent["intensity"] == "high" and decision_label != "avoid_for_now":
            decision_label = "avoid_for_now"
            overrides.append({"rule": "HEAT_INDEX_HIGH_INTENSITY", "decision_label": decision_label})

        if user_context.get("sensitive_group") and weighted_risk_score >= 0.35 and decision_label == "okay_with_caution":
            decision_label = "shorten_or_modify"
            overrides.append({"rule": "SENSITIVE_GROUP_BORDERLINE", "decision_label": decision_label})

        if risk_factors["confidence_penalty"]["score"] >= 0.5 and decision_label == "go_ahead":
            decision_label = "okay_with_caution"
            overrides.append({"rule": "LOW_CONFIDENCE_DOWNGRADE", "decision_label": decision_label})

        if request_feasibility.get("status") == "exceeds_typical" and decision_label in {"go_ahead", "okay_with_caution"}:
            decision_label = "shorten_or_modify"
            overrides.append({"rule": "REQUEST_DURATION_EXCEEDS_TYPICAL", "decision_label": decision_label})

        return overrides

    @staticmethod
    def _recommendation_from_decision(
        *,
        intent: dict[str, Any],
        decision: str,
        hard_constraints: list[dict[str, Any]],
    ) -> dict[str, Any]:
        messages = {
            "go_ahead": f"You can proceed with {intent['activity']} under current conditions.",
            "okay_with_caution": f"You can proceed with {intent['activity']}, but conditions are not ideal.",
            "shorten_or_modify": f"{intent['activity'].replace('_', ' ').title()} is not ideal as requested; shorten or modify it.",
            "avoid_for_now": f"Avoid {intent['activity'].replace('_', ' ')} under current conditions.",
            "insufficient_confidence": "Conditions cannot be assessed confidently with the available data.",
        }
        if intent.get("time_horizon") in {"tomorrow", "this_weekend", "future_day"}:
            requested_time = intent.get("requested_time") or intent.get("time_horizon", "the requested future window").replace("_", " ")
            messages["insufficient_confidence"] = (
                f"The system cannot yet assess {intent['activity'].replace('_', ' ')} for {requested_time} with enough confidence."
            )
        if decision == "insufficient_confidence" and intent.get("time_horizon") not in {"tomorrow", "this_weekend", "future_day"}:
            feasibility = intent.get("activity_profile") or {}
            if feasibility.get("typical_duration_min"):
                messages["insufficient_confidence"] = (
                    f"The requested duration is outside the supported range for {intent['activity'].replace('_', ' ')}."
                )
        return {
            "allowed": decision in {"go_ahead", "okay_with_caution"},
            "message": messages[decision],
            "blocked_by_hard_constraints": bool(hard_constraints),
        }

    def _apply_intent_behavior(self, payload: dict[str, Any]) -> dict[str, Any]:
        intent = payload["request"]["intent"]
        source_intent = intent.get("source_intent", "activity_check")

        if source_intent == "duration_adjustment":
            payload = self._duration_adjustment_behavior(payload)
        elif source_intent in {"compare_times", "time_shift"}:
            payload = self._comparison_behavior(payload)
        elif source_intent == "best_time_today":
            payload = self._best_time_behavior(payload)
        elif source_intent == "route_mode_choice":
            payload = self._route_mode_behavior(payload)
        elif source_intent == "should_avoid":
            payload = self._should_avoid_behavior(payload)
        return payload

    @staticmethod
    def _duration_adjustment_behavior(payload: dict[str, Any]) -> dict[str, Any]:
        label = payload["decision"]["label"]
        if label == "okay_with_caution":
            payload["decision"]["label"] = "shorten_or_modify"
            payload["recommendation"]["allowed"] = False
            payload["recommendation"]["message"] = "A shorter version of this activity is preferable to the original plan."
            payload["policy_trace"]["overrides_applied"].append(
                {"rule": "DURATION_ADJUSTMENT_PREFERS_MODIFICATION", "decision_label": "shorten_or_modify"}
            )
        return payload

    @staticmethod
    def _comparison_behavior(payload: dict[str, Any]) -> dict[str, Any]:
        payload["recommendation"]["message"] = (
            "This request is being handled as a same-day comparison using current conditions and weather-based timing guidance."
        )
        payload["policy_trace"]["comparison_mode"] = True
        return payload

    @staticmethod
    def _best_time_behavior(payload: dict[str, Any]) -> dict[str, Any]:
        payload["recommendation"]["message"] = (
            "This request is being handled as a best-time-today query using current conditions plus available weather forecast."
        )
        payload["policy_trace"]["best_time_mode"] = True
        return payload

    @staticmethod
    def _route_mode_behavior(payload: dict[str, Any]) -> dict[str, Any]:
        modes = payload["request"]["intent"].get("candidate_modes") or []
        risk = payload["decision"]["score"]
        preferred_mode = None
        if risk >= 0.45:
            for mode in ("drive", "transit"):
                if mode in modes:
                    preferred_mode = mode
                    break
        if preferred_mode is None:
            preferred_mode = modes[0] if modes else None
        if preferred_mode:
            payload["recommendation"]["message"] = f"For current conditions, `{preferred_mode}` is the safer choice among the requested commute modes."
            payload["policy_trace"]["preferred_mode"] = preferred_mode
        return payload

    @staticmethod
    def _should_avoid_behavior(payload: dict[str, Any]) -> dict[str, Any]:
        risk = payload["decision"]["score"]
        air_risk = payload["risk_factors"]["air_burden"]["score"]
        heat_risk = payload["risk_factors"]["heat_burden"]["score"]
        if (risk >= 0.2 or air_risk >= 0.2 or heat_risk >= 0.25) and payload["decision"]["label"] != "avoid_for_now":
            payload["decision"]["label"] = "avoid_for_now"
            payload["decision"]["confidence"] = max(payload["decision"]["confidence"], 0.75)
            payload["recommendation"]["allowed"] = False
            payload["recommendation"]["message"] = "Conditions are elevated enough that avoiding this for now is the safer recommendation."
            payload["policy_trace"]["overrides_applied"].append(
                {"rule": "SHOULD_AVOID_BINARY_TONE", "decision_label": "avoid_for_now"}
            )
        return payload

    @staticmethod
    def _factor_breakdown(risk_factors: dict[str, Any]) -> dict[str, str]:
        return {
            "air_burden": risk_factors["air_burden"]["level"],
            "heat_burden": risk_factors["heat_burden"]["level"],
            "exposure": risk_factors["exposure_burden"]["level"],
            "confidence": risk_factors["confidence_penalty"]["level"],
        }

    @staticmethod
    def _reasoning(*, intent: dict[str, Any], risk_factors: dict[str, Any], request_feasibility: dict[str, Any]) -> list[str]:
        reasoning: list[str] = []
        if risk_factors["air_burden"]["score"] >= 0.25:
            reasoning.append("Air pollution burden is elevated for this activity.")
        if risk_factors["heat_burden"]["score"] >= 0.22:
            reasoning.append("Temperature and humidity add noticeable strain.")
        if risk_factors["exposure_burden"]["score"] >= 0.25:
            reasoning.append("Requested duration increases total exposure.")
        if request_feasibility.get("status") == "exceeds_typical":
            reasoning.append(request_feasibility.get("reason") or "Requested duration is above the typical range for this activity.")
        if not reasoning:
            reasoning.append(f"Current air and weather conditions are acceptable for {intent['activity'].replace('_', ' ')}.")
        return reasoning

    @staticmethod
    def _modifications(
        *,
        intent: dict[str, Any],
        decision_label: str,
        environment_state: dict[str, Any],
        request_feasibility: dict[str, Any],
    ) -> list[dict[str, str]]:
        if decision_label == "go_ahead":
            return []

        modifications: list[dict[str, str]] = []
        if decision_label in {"okay_with_caution", "shorten_or_modify", "avoid_for_now"} and intent["duration_min"] > 15:
            target_duration = request_feasibility.get("typical_duration_min")
            reduced_duration = int(target_duration) if target_duration else max(15, round(intent["duration_min"] * 0.5))
            modifications.append({"type": "duration", "suggestion": f"Reduce duration to around {reduced_duration} minutes."})
        if decision_label in {"shorten_or_modify", "avoid_for_now"} and intent["intensity"] == "high":
            modifications.append({"type": "intensity", "suggestion": "Switch to a lower-intensity outdoor activity."})
        if decision_label in {"shorten_or_modify", "avoid_for_now"} and environment_state["time_context"].get("forecast_window_available"):
            modifications.append({"type": "timing", "suggestion": "Check a later same-day window before going outside."})
        return modifications

    @staticmethod
    def _assumptions(payload: dict[str, Any]) -> list[str]:
        assumptions = ["Assessment is based on outdoor conditions only."]
        user_context = payload["request"]["user_context"]
        if user_context.get("respiratory_condition") == "unknown":
            assumptions.append("No specific respiratory sensitivity was applied.")
        if payload["request"]["intent"]["timing_mode"] == "now":
            assumptions.append("Recommendation is based on current conditions and near-term forecast availability.")
        return assumptions

    @staticmethod
    def _pollutant_value(environment_state: dict[str, Any], key: str) -> float | None:
        pollutant = environment_state["air_quality"].get(key)
        if not pollutant:
            return None
        return pollutant.get("value")

    @staticmethod
    def _heat_index_celsius(temperature_c: float | None, humidity: float | None) -> float | None:
        if temperature_c is None or humidity is None:
            return None
        return temperature_c + (0.1 * humidity)
