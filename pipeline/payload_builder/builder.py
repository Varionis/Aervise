from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from contracts.decision_input import (
    ActivityArchetype,
    ActivityGroup,
    CanonicalActivity,
    DecisionArchetype,
    DurationBand,
    LocationContext,
)
from contracts.intent_schema import (
    ActivityLocationContext,
    ActivityType,
    ExpectedDurationBand,
    ExposureLevel,
    IntensityLevel,
    IntentType,
    MotionPattern,
    RequestFieldName,
    TimeContext,
)


ACTIVITY_CATALOG: dict[str, dict[str, str | int]] = {
    ActivityType.RUNNING.value: {
        "canonical_activity": CanonicalActivity.RUNNING.value,
        "default_duration": 45,
    },
    ActivityType.WALKING.value: {
        "canonical_activity": CanonicalActivity.WALKING.value,
        "default_duration": 30,
    },
    ActivityType.DOG_WALK.value: {
        "canonical_activity": CanonicalActivity.DOG_WALK.value,
        "default_duration": 20,
    },
    ActivityType.CYCLING.value: {
        "canonical_activity": CanonicalActivity.CYCLING.value,
        "default_duration": 45,
    },
    ActivityType.HIIT.value: {
        "canonical_activity": CanonicalActivity.GENERAL_OUTDOOR_ACTIVITY.value,
        "default_duration": 30,
    },
    ActivityType.SOCCER.value: {
        "canonical_activity": CanonicalActivity.GENERAL_OUTDOOR_ACTIVITY.value,
        "default_duration": 60,
    },
    ActivityType.BASKETBALL.value: {
        "canonical_activity": CanonicalActivity.BASKETBALL.value,
        "default_duration": 60,
    },
    ActivityType.HIKING.value: {
        "canonical_activity": CanonicalActivity.HIKING.value,
        "default_duration": 120,
    },
    ActivityType.YARD_WORK.value: {
        "canonical_activity": CanonicalActivity.GENERAL_OUTDOOR_ACTIVITY.value,
        "default_duration": 90,
    },
    ActivityType.PARK_VISIT.value: {
        "canonical_activity": CanonicalActivity.GENERAL_OUTDOOR_ACTIVITY.value,
        "default_duration": 60,
    },
    ActivityType.BEACH_DAY.value: {
        "canonical_activity": CanonicalActivity.GENERAL_OUTDOOR_ACTIVITY.value,
        "default_duration": 180,
    },
    ActivityType.FESTIVAL.value: {
        "canonical_activity": CanonicalActivity.GENERAL_OUTDOOR_ACTIVITY.value,
        "default_duration": 180,
    },
    ActivityType.SIGHTSEEING.value: {
        "canonical_activity": CanonicalActivity.GENERAL_OUTDOOR_ACTIVITY.value,
        "default_duration": 90,
    },
    ActivityType.BIKE_COMMUTE.value: {
        "canonical_activity": CanonicalActivity.BIKE_COMMUTE.value,
        "default_duration": 30,
    },
    ActivityType.COMMUTE.value: {
        "canonical_activity": CanonicalActivity.COMMUTE.value,
        "default_duration": 30,
    },
    ActivityType.OUTDOOR_ERRAND.value: {
        "canonical_activity": CanonicalActivity.OUTDOOR_ERRAND.value,
        "default_duration": 20,
    },
    ActivityType.BARBECUE.value: {
        "canonical_activity": CanonicalActivity.BARBECUE.value,
        "default_duration": 180,
    },
    ActivityType.OUTDOOR_GATHERING.value: {
        "canonical_activity": CanonicalActivity.GENERAL_OUTDOOR_ACTIVITY.value,
        "default_duration": 120,
    },
    ActivityType.OPEN_WINDOWS.value: {
        "canonical_activity": CanonicalActivity.OPEN_WINDOWS.value,
        "default_duration": 30,
    },
}


TIMING_ARCHETYPE_MAP = {
    TimeContext.NOW.value: DecisionArchetype.NOW_CHECK.value,
    TimeContext.LATER.value: DecisionArchetype.COMPARE_NOW_LATER.value,
    TimeContext.SPECIFIC_HOUR.value: DecisionArchetype.COMPARE_NOW_LATER.value,
    TimeContext.BEST_TIME_TODAY.value: DecisionArchetype.BEST_TIME_TODAY.value,
    TimeContext.WHAT_IF.value: DecisionArchetype.WHAT_IF.value,
}


@dataclass
class DecisionPayloadBuilder:
    def build(
        self,
        *,
        entry_point: dict[str, Any],
        intent_recognition: dict[str, Any],
        environment_state: dict[str, Any],
        user_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        intent = self._normalize_intent(intent_recognition)

        return {
            "request": {
                "intent": intent,
                "user_context": self._normalize_user_context(user_context or {}),
            },
            "environment_state": environment_state,
            "layer_trace": {
                "stage": "decision_payload_builder",
                "decision_archetype": intent["decision_archetype"],
                "activity_archetype": intent["activity_archetype"],
                "timing_mode": intent["timing_mode"],
                "forecast_window_available": environment_state["time_context"]["forecast_window_available"],
                "entry_channel": entry_point.get("channel"),
            },
        }

    def _normalize_intent(self, payload: dict[str, Any]) -> dict[str, Any]:
        unresolved = {self._value(value) for value in (payload.get("unresolved_fields") or [])}
        activity_value = self._value(payload.get("activity"))
        source_intent = self._value(payload.get("intent")) or IntentType.ACTIVITY_CHECK.value
        requires_activity = source_intent not in {IntentType.ROUTE_MODE_CHOICE.value}
        requires_duration = source_intent in {IntentType.DURATION_ADJUSTMENT.value}
        if requires_activity and (RequestFieldName.ACTIVITY.value in unresolved or activity_value == ActivityType.UNKNOWN.value):
            raise ValueError("Stage 3 requires a resolved activity before building decision input")
        if requires_duration and (RequestFieldName.DURATION_MINUTES.value in unresolved or payload.get("duration_minutes") is None):
            raise ValueError("Stage 3 requires duration_minutes before building decision input")

        activity_key = str(activity_value or "").strip().lower()
        activity_profile = ACTIVITY_CATALOG.get(activity_key)
        if not activity_profile:
            activity_profile = {
                "canonical_activity": CanonicalActivity.GENERAL_OUTDOOR_ACTIVITY.value,
                "default_duration": 45,
            }

        normalized_profile = self._normalize_activity_profile(payload.get("activity_profile"))
        duration_min = int(payload.get("duration_minutes") or self._default_duration_for(source_intent, activity_profile, normalized_profile))
        reference_duration_min = payload.get("reference_duration_minutes")
        timing_mode = str(self._value(payload.get("time_context")) or TimeContext.NOW.value).strip().lower()
        time_horizon = str(self._value(payload.get("time_horizon")) or "unspecified").strip().lower()
        time_window = str(self._value(payload.get("time_window")) or "unspecified").strip().lower()
        intensity = str(
            self._value(payload.get("intensity"))
            or normalized_profile["exertion_level"]
            or IntensityLevel.MODERATE.value
        ).strip().lower()
        decision_archetype = self._decision_archetype(
            source_intent=source_intent,
            timing_mode=timing_mode,
            time_horizon=time_horizon,
        )

        return {
            "source_intent": source_intent,
            "activity": activity_profile["canonical_activity"],
            "activity_profile": normalized_profile,
            "activity_group": self._activity_group(activity_key, normalized_profile),
            "activity_archetype": self._activity_archetype(activity_key, normalized_profile),
            "decision_archetype": decision_archetype,
            "intensity": intensity,
            "duration_min": duration_min,
            "reference_duration_min": int(reference_duration_min) if reference_duration_min is not None else None,
            "duration_band": self._duration_band(duration_min),
            "timing_mode": timing_mode,
            "requested_time": self._requested_time_label(time_horizon=time_horizon, time_window=time_window),
            "requested_time_hint": self._value(payload.get("requested_time_hint")),
            "time_horizon": time_horizon,
            "time_window": time_window,
            "comparison_target": self._value(payload.get("comparison_target")),
            "adjustment_type": self._value(payload.get("adjustment_type")),
            "candidate_modes": [self._value(mode) for mode in (payload.get("candidate_modes") or [])],
            "location_context": self._location_context(normalized_profile),
        }

    @staticmethod
    def _duration_band(duration_min: int) -> str:
        if duration_min <= 15:
            return DurationBand.SHORT.value
        if duration_min <= 60:
            return DurationBand.MEDIUM.value
        return DurationBand.LONG.value

    @staticmethod
    def _normalize_user_context(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "sensitivity": str(payload.get("sensitivity") or "unknown").lower(),
            "age_group": str(payload.get("age_group") or "unknown").lower(),
            "health_flags": payload.get("health_flags") or [],
            "sensitive_group": bool(payload.get("sensitive_group", False)),
            "respiratory_condition": str(payload.get("respiratory_condition") or "unknown").lower(),
        }

    @staticmethod
    def _default_duration_for(
        source_intent: str,
        activity_profile: dict[str, Any],
        normalized_profile: dict[str, Any],
    ) -> int:
        if source_intent == IntentType.BEST_TIME_TODAY.value:
            return 45
        if source_intent == IntentType.COMPARE_TIMES.value:
            return 45
        if source_intent == IntentType.TIME_SHIFT.value:
            return 45
        if source_intent == IntentType.ROUTE_MODE_CHOICE.value:
            return 30
        band_defaults = {
            ExpectedDurationBand.SHORT.value: 20,
            ExpectedDurationBand.MEDIUM.value: 45,
            ExpectedDurationBand.LONG.value: 120,
        }
        if normalized_profile.get("expected_duration_band") in band_defaults:
            return band_defaults[normalized_profile["expected_duration_band"]]
        return int(activity_profile.get("default_duration") or 45)

    @staticmethod
    def _decision_archetype(*, source_intent: str, timing_mode: str, time_horizon: str) -> str:
        if time_horizon in {"tomorrow", "this_weekend", "future_day"}:
            return DecisionArchetype.FUTURE_LOOKAHEAD.value
        if source_intent == IntentType.COMPARE_TIMES.value:
            return DecisionArchetype.COMPARE_NOW_LATER.value
        if source_intent == IntentType.BEST_TIME_TODAY.value:
            return DecisionArchetype.BEST_TIME_TODAY.value
        if source_intent == IntentType.DURATION_ADJUSTMENT.value:
            return DecisionArchetype.WHAT_IF.value
        if source_intent == IntentType.TIME_SHIFT.value:
            return DecisionArchetype.WHAT_IF.value
        return TIMING_ARCHETYPE_MAP.get(timing_mode, DecisionArchetype.NOW_CHECK.value)

    @staticmethod
    def _requested_time_label(*, time_horizon: str, time_window: str) -> str | None:
        parts = [part.replace("_", " ") for part in (time_horizon, time_window) if part and part != "unspecified"]
        if not parts:
            return None
        return " ".join(parts)

    @staticmethod
    def _normalize_activity_profile(value: Any) -> dict[str, Any]:
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json")
        if isinstance(value, dict):
            return dict(value)
        return {
            "exertion_level": IntensityLevel.MODERATE.value,
            "expected_duration_band": ExpectedDurationBand.MEDIUM.value,
            "exposure_level": ExposureLevel.MODERATE.value,
            "location_context": ActivityLocationContext.OUTDOOR.value,
            "motion_pattern": MotionPattern.CONTINUOUS.value,
        }

    @staticmethod
    def _activity_group(activity_key: str, profile: dict[str, Any]) -> str:
        if activity_key in {ActivityType.BIKE_COMMUTE.value, ActivityType.COMMUTE.value}:
            return ActivityGroup.COMMUTE_OUTDOOR.value
        if profile.get("location_context") == ActivityLocationContext.INDOOR_OUTDOOR_BOUNDARY.value:
            return ActivityGroup.INDOOR_OUTDOOR_BOUNDARY.value
        if profile.get("expected_duration_band") == ExpectedDurationBand.SHORT.value and profile.get("exposure_level") == ExposureLevel.LOW.value:
            return ActivityGroup.BRIEF_OUTDOOR_ACTIVITY.value
        if profile.get("exertion_level") == IntensityLevel.HIGH.value:
            return ActivityGroup.EXERCISE_OUTDOOR.value
        if profile.get("expected_duration_band") == ExpectedDurationBand.SHORT.value:
            return ActivityGroup.BRIEF_OUTDOOR_ACTIVITY.value
        if profile.get("exertion_level") == IntensityLevel.LOW.value:
            return ActivityGroup.LIGHT_OUTDOOR_ACTIVITY.value
        return ActivityGroup.GENERAL_OUTDOOR_ACTIVITY.value

    @staticmethod
    def _activity_archetype(activity_key: str, profile: dict[str, Any]) -> str:
        if activity_key in {ActivityType.BIKE_COMMUTE.value, ActivityType.COMMUTE.value}:
            return ActivityArchetype.COMMUTE_ROUTINE.value
        if profile.get("location_context") == ActivityLocationContext.INDOOR_OUTDOOR_BOUNDARY.value:
            return ActivityArchetype.INDOOR_OUTDOOR.value
        if profile.get("exertion_level") == IntensityLevel.HIGH.value:
            return ActivityArchetype.OUTDOOR_HIGH_EXERTION.value
        if profile.get("expected_duration_band") == ExpectedDurationBand.SHORT.value and profile.get("exposure_level") == ExposureLevel.LOW.value:
            return ActivityArchetype.BRIEF_OUTDOOR_EXPOSURE.value
        if profile.get("motion_pattern") == MotionPattern.STATIONARY.value and profile.get("exposure_level") == ExposureLevel.HIGH.value:
            return ActivityArchetype.BRIEF_OUTDOOR_EXPOSURE.value
        return ActivityArchetype.OUTDOOR_LOW_EXERTION.value

    @staticmethod
    def _location_context(profile: dict[str, Any]) -> str:
        if profile.get("location_context") == ActivityLocationContext.INDOOR_OUTDOOR_BOUNDARY.value:
            return LocationContext.INDOOR_OUTDOOR_BOUNDARY.value
        return LocationContext.OUTDOOR.value

    @staticmethod
    def _value(value: Any) -> Any:
        if hasattr(value, "value"):
            return value.value
        return value
