from __future__ import annotations

from dataclasses import dataclass
from typing import Any


INTENSITY_MULTIPLIERS = {
    "low": 0.8,
    "moderate": 1.0,
    "high": 1.3,
}

ACTIVITY_AMPLIFIERS = {
    "outdoor_high_exertion": {"air": 1.15, "heat": 1.15, "exposure": 1.2},
    "outdoor_low_exertion": {"air": 1.0, "heat": 1.0, "exposure": 1.0},
    "brief_outdoor_exposure": {"air": 0.75, "heat": 0.85, "exposure": 0.65},
    "commute_routine": {"air": 1.05, "heat": 1.0, "exposure": 1.05},
    "indoor_outdoor": {"air": 0.6, "heat": 0.7, "exposure": 0.4},
}


@dataclass
class DecisionLayer2Evaluator:
    def evaluate(self, decision_input: dict[str, Any]) -> dict[str, Any]:
        intent = decision_input["request"]["intent"]
        user_context = decision_input["request"]["user_context"]
        environment_state = decision_input["environment_state"]
        request_feasibility = decision_input["request_feasibility"]

        pm25 = self._pollutant_value(environment_state, "pm25")
        no2 = self._pollutant_value(environment_state, "no2")
        o3 = self._pollutant_value(environment_state, "o3")
        temperature = environment_state["weather"].get("temperature_c")
        humidity = environment_state["weather"].get("humidity")
        wind_speed = environment_state["weather"].get("wind_speed")

        duration_factor = self._duration_factor(intent["duration_min"])
        intensity_factor = INTENSITY_MULTIPLIERS.get(intent["intensity"], 1.0)
        activity_amplifiers = ACTIVITY_AMPLIFIERS.get(
            intent["activity_archetype"],
            {"air": 1.0, "heat": 1.0, "exposure": 1.0},
        )

        pm25_severity = self._pm25_severity(pm25)
        no2_severity = self._no2_severity(no2)
        o3_severity = self._o3_severity(o3)
        pollutant_base = self._clamp((0.55 * pm25_severity) + (0.2 * no2_severity) + (0.25 * o3_severity))

        air_burden = self._clamp(
            pollutant_base * intensity_factor * duration_factor * activity_amplifiers["air"] * self._sensitivity_factor(user_context)
        )

        heat_index_c = self._heat_index_celsius(temperature, humidity)
        heat_severity = self._heat_severity(heat_index_c)
        heat_burden = self._clamp(
            heat_severity * intensity_factor * self._heat_duration_factor(intent["duration_min"]) * activity_amplifiers["heat"]
        )

        exposure_burden = self._clamp(
            pollutant_base * duration_factor * intensity_factor * activity_amplifiers["exposure"]
        )

        wind_disruption = self._wind_disruption(wind_speed)
        confidence_penalty = self._confidence_penalty(environment_state)

        risk_factors = {
            "air_burden": self._factor_payload(
                score=air_burden,
                level=self._severity_label(air_burden),
                drivers={
                    "pm25": pm25,
                    "no2": no2,
                    "o3": o3,
                    "pollutant_base": round(pollutant_base, 3),
                    "intensity_factor": intensity_factor,
                    "duration_factor": duration_factor,
                    "activity_multiplier": activity_amplifiers["air"],
                },
            ),
            "heat_burden": self._factor_payload(
                score=heat_burden,
                level=self._severity_label(heat_burden),
                drivers={
                    "temperature_c": temperature,
                    "humidity": humidity,
                    "heat_index_c": round(heat_index_c, 2) if heat_index_c is not None else None,
                    "heat_severity": round(heat_severity, 3),
                    "intensity_factor": intensity_factor,
                    "activity_multiplier": activity_amplifiers["heat"],
                },
            ),
            "exposure_burden": self._factor_payload(
                score=exposure_burden,
                level=self._severity_label(exposure_burden),
                drivers={
                    "duration_min": intent["duration_min"],
                    "duration_factor": duration_factor,
                    "intensity_factor": intensity_factor,
                    "pollutant_base": round(pollutant_base, 3),
                    "activity_multiplier": activity_amplifiers["exposure"],
                },
            ),
            "disruption_factor": self._factor_payload(
                score=wind_disruption,
                level=self._severity_label(wind_disruption),
                drivers={
                    "wind_speed": wind_speed,
                },
            ),
            "confidence_penalty": self._factor_payload(
                score=confidence_penalty,
                level=self._severity_label(confidence_penalty),
                drivers={
                    "overall_confidence": environment_state["data_quality"].get("overall_confidence"),
                    "aq_source_confidence": environment_state["data_quality"].get("aq_source_confidence"),
                    "weather_source_confidence": environment_state["data_quality"].get("weather_source_confidence"),
                    "missing_fields": environment_state["data_quality"].get("missing_fields"),
                },
            ),
        }

        return {
            **decision_input,
            "risk_factors": risk_factors,
            "request_feasibility": request_feasibility,
            "layer_trace": {
                **decision_input["layer_trace"],
                "factor_model": {
                    "duration_factor": duration_factor,
                    "intensity_factor": intensity_factor,
                    "activity_amplifiers": activity_amplifiers,
                    "request_feasibility": request_feasibility,
                },
            },
        }

    @staticmethod
    def _pollutant_value(environment_state: dict[str, Any], key: str) -> float | None:
        pollutant = environment_state["air_quality"].get(key)
        if not pollutant:
            return None
        return pollutant.get("value")

    @staticmethod
    def _duration_factor(duration_min: int) -> float:
        if duration_min <= 15:
            return 0.55
        if duration_min <= 30:
            return 0.8
        if duration_min <= 60:
            return 1.0
        if duration_min <= 120:
            return 1.2
        return 1.35

    @staticmethod
    def _heat_duration_factor(duration_min: int) -> float:
        if duration_min <= 15:
            return 0.7
        if duration_min <= 45:
            return 1.0
        if duration_min <= 90:
            return 1.15
        return 1.3

    @staticmethod
    def _pm25_severity(value: float | None) -> float:
        if value is None:
            return 0.5
        if value <= 12:
            return 0.1
        if value <= 35:
            return 0.35
        if value <= 55:
            return 0.55
        if value <= 100:
            return 0.75
        if value <= 150:
            return 0.9
        return 1.0

    @staticmethod
    def _no2_severity(value: float | None) -> float:
        if value is None:
            return 0.3
        if value <= 0.03:
            return 0.1
        if value <= 0.06:
            return 0.35
        if value <= 0.1:
            return 0.6
        return 0.85

    @staticmethod
    def _o3_severity(value: float | None) -> float:
        if value is None:
            return 0.3
        if value <= 0.05:
            return 0.12
        if value <= 0.07:
            return 0.35
        if value <= 0.09:
            return 0.6
        return 0.85

    @staticmethod
    def _heat_index_celsius(temperature_c: float | None, humidity: float | None) -> float | None:
        if temperature_c is None or humidity is None:
            return None
        return temperature_c + (0.1 * humidity)

    @staticmethod
    def _heat_severity(heat_index_c: float | None) -> float:
        if heat_index_c is None:
            return 0.2
        if heat_index_c <= 10:
            return 0.05
        if heat_index_c <= 20:
            return 0.15
        if heat_index_c <= 27:
            return 0.3
        if heat_index_c <= 32:
            return 0.5
        if heat_index_c <= 38:
            return 0.75
        return 1.0

    @staticmethod
    def _wind_disruption(wind_speed: float | None) -> float:
        if wind_speed is None:
            return 0.15
        if wind_speed <= 3:
            return 0.05
        if wind_speed <= 7:
            return 0.1
        if wind_speed <= 12:
            return 0.2
        return 0.35

    @staticmethod
    def _confidence_penalty(environment_state: dict[str, Any]) -> float:
        data_quality = environment_state["data_quality"]
        overall = data_quality.get("overall_confidence")
        if overall is None:
            base_penalty = 0.35
        else:
            base_penalty = max(0.0, 1.0 - overall)
        missing_fields = data_quality.get("missing_fields") or []
        missing_penalty = min(0.25, 0.08 * len(missing_fields))
        future_window_penalty = 0.0
        time_context = environment_state.get("time_context") or {}
        if time_context.get("weather_selection_mode") == "forecast_window":
            future_window_penalty = 0.18
        return DecisionLayer2Evaluator._clamp(base_penalty + missing_penalty + future_window_penalty)

    @staticmethod
    def _sensitivity_factor(user_context: dict[str, Any]) -> float:
        if user_context.get("sensitive_group"):
            return 1.15
        if user_context.get("respiratory_condition") not in {None, "", "unknown"}:
            return 1.15
        sensitivity = user_context.get("sensitivity")
        if sensitivity in {"asthma", "child", "elderly", "sensitive"}:
            return 1.15
        return 1.0

    @staticmethod
    def _severity_label(score: float) -> str:
        if score < 0.2:
            return "low"
        if score < 0.45:
            return "moderate"
        if score < 0.7:
            return "moderate_high"
        if score < 0.85:
            return "high"
        return "very_high"

    @staticmethod
    def _factor_payload(*, score: float, level: str, drivers: dict[str, Any]) -> dict[str, Any]:
        return {
            "score": round(score, 3),
            "level": level,
            "drivers": drivers,
        }

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, value))
