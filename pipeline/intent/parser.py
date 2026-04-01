from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

from config import Settings
from contracts.intent_schema import (
    ActivityProfile,
    ActivityType,
    AdjustmentType,
    ComparisonTarget,
    InputChannel,
    IntentType,
    IntensityLevel,
    ParserStrategy,
    RequestFieldName,
    RequestedTimeHint,
    TimeContext,
    TimeHorizon,
    TimeWindow,
    TransportMode,
)
from pipeline.intent.activity_normalizer import ActivityNormalizer

MODE_RULES = [
    (TransportMode.WALK, ("walk", "walking route")),
    (TransportMode.BIKE, ("bike", "biking", "cycle", "cycling")),
    (TransportMode.SCOOTER, ("scooter",)),
    (TransportMode.TRANSIT, ("public transit", "transit", "subway", "bus")),
    (TransportMode.DRIVE, ("drive", "driving", "car")),
    (TransportMode.JOG, ("jog", "jogging")),
]

@dataclass
class InteractionService:
    settings: Settings
    activity_normalizer: ActivityNormalizer = field(default_factory=ActivityNormalizer)

    def preview(self, payload: dict) -> dict:
        entry_point = self._normalize_entry_point(payload)
        intent_recognition = self._recognize_intent(entry_point["message"])

        return {
            "entry_point": entry_point,
            "intent_recognition": intent_recognition,
        }

    def _normalize_entry_point(self, payload: dict) -> dict:
        location = payload.get("location") or {}
        return {
            "user_id": payload.get("user_id") or "demo-user",
            "message": str(payload.get("message") or "").strip(),
            "timestamp_utc": payload.get("timestamp_utc") or datetime.now(UTC).isoformat(),
            "location": {
                "lat": location.get("lat", self.settings.default_lat),
                "lon": location.get("lon", self.settings.default_lon),
            },
            "channel": payload.get("channel") or InputChannel.DEMO_UI,
        }

    def _recognize_intent(self, message: str) -> dict:
        lowered = message.lower()
        intent = self._detect_intent(lowered)
        activity, activity_profile = self._detect_activity(lowered)
        duration, reference_duration = self._detect_duration_fields(lowered, intent)
        time_horizon, time_window, timing_mode, requested_time_hint = self._detect_timing(lowered, intent)
        intensity = self._detect_intensity(lowered, activity_profile)
        comparison_target = self._detect_comparison_target(lowered, intent)
        adjustment_type = self._detect_adjustment_type(lowered, intent)
        candidate_modes = self._detect_candidate_modes(lowered, intent)

        unresolved_fields = self._unresolved_fields(
            intent=intent,
            activity=activity,
            duration=duration,
            comparison_target=comparison_target,
            candidate_modes=candidate_modes,
        )
        confidence = self._confidence(intent=intent, unresolved_fields=unresolved_fields, timing_mode=timing_mode)

        return {
            "intent": intent,
            "activity": activity,
            "activity_profile": activity_profile.model_dump(mode="json") if activity_profile is not None else None,
            "intensity": intensity,
            "duration_minutes": duration,
            "reference_duration_minutes": reference_duration,
            "time_context": timing_mode,
            "time_horizon": time_horizon,
            "time_window": time_window,
            "requested_time_hint": requested_time_hint,
            "comparison_target": comparison_target,
            "adjustment_type": adjustment_type,
            "candidate_modes": candidate_modes,
            "confidence": confidence,
            "unresolved_fields": unresolved_fields,
            "parser": {
                "strategy": ParserStrategy.RULE_BASED_V1,
                "raw_message": message,
            },
        }

    @staticmethod
    def _detect_intent(message: str) -> IntentType:
        if any(token in message for token in ("best time", "best window", "least risky time", "good time to", "when is a good time", "when should i")):
            return IntentType.BEST_TIME_TODAY
        if any(token in message for token in ("better than now", "go now or wait", "morning or afternoon", "before or after")):
            return IntentType.COMPARE_TIMES
        if any(token in message for token in ("if i reduce", "shorten", "instead of an hour", "only stay outside")):
            return IntentType.DURATION_ADJUSTMENT
        if any(token in message for token in ("what if i go later", "will it be safer in a few hours", "should i wait", "postpone")):
            return IntentType.TIME_SHIFT
        if any(token in message for token in ("transit or", "drive instead", "bike to work", "walk to work", "usual route", "rush hour")):
            return IntentType.ROUTE_MODE_CHOICE
        if any(token in message for token in ("should i avoid", "avoid going outside", "stay indoors")):
            return IntentType.SHOULD_AVOID
        if any(token in message for token in ("tomorrow", "this weekend", "weekend", "next week")) and any(
            token in message for token in ("weather", "look like", "good day", "good time", "safe")
        ):
            return IntentType.ACTIVITY_CHECK
        if "?" in message or any(token in message for token in ("can i", "is it safe", "is it okay", "should i")):
            return IntentType.ACTIVITY_CHECK
        return IntentType.UNKNOWN

    def _detect_activity(self, message: str) -> tuple[ActivityType, ActivityProfile | None]:
        return self.activity_normalizer.normalize(message)

    @staticmethod
    def _detect_duration_fields(message: str, intent: IntentType) -> tuple[int | None, int | None]:
        durations = InteractionService._extract_duration_candidates(message)
        if intent == IntentType.DURATION_ADJUSTMENT:
            scenario_duration = durations[0] if durations else None
            reference_duration = durations[1] if len(durations) > 1 else None
            return scenario_duration, reference_duration
        return (durations[0], None) if durations else (None, None)

    @staticmethod
    def _extract_duration_candidates(message: str) -> list[int]:
        durations: list[int] = []
        for match in re.finditer(r"(\d{1,3})\s*(minutes|minute|mins|min|hours|hour|hrs|hr)\b", message):
            value = int(match.group(1))
            unit = match.group(2)
            durations.append(value * 60 if unit.startswith(("hour", "hr")) else value)

        article_patterns = [
            (r"\bhalf\s+an?\s+hour\b", 30),
            (r"\bone\s+hour\b", 60),
            (r"\ban?\s+hour\b", 60),
            (r"\bhalf\s+day\b", 180),
        ]
        for pattern, minutes in article_patterns:
            if re.search(pattern, message):
                durations.append(minutes)

        if not durations:
            if re.search(r"\b(\d{1,2})k\+\b", message):
                durations.append(75)
            elif "quick" in message or "brief" in message:
                durations.append(15)
            elif "afternoon" in message or "half a day" in message:
                durations.append(180)
        return durations

    @staticmethod
    def _detect_timing(
        message: str,
        intent: IntentType,
    ) -> tuple[TimeHorizon, TimeWindow, TimeContext, RequestedTimeHint | None]:
        time_horizon = InteractionService._detect_time_horizon(message)
        time_window = InteractionService._detect_time_window(message)
        requested_time_hint = InteractionService._detect_requested_time_hint(time_horizon, time_window)

        if intent == IntentType.BEST_TIME_TODAY:
            return TimeHorizon.LATER_TODAY, time_window, TimeContext.BEST_TIME_TODAY, RequestedTimeHint.SAME_DAY_NAMED_PERIOD
        if intent == IntentType.TIME_SHIFT:
            return time_horizon, time_window, TimeContext.WHAT_IF, requested_time_hint
        if time_horizon == TimeHorizon.NOW and time_window == TimeWindow.UNSPECIFIED:
            return time_horizon, time_window, TimeContext.NOW, requested_time_hint
        if time_window not in {TimeWindow.UNSPECIFIED, TimeWindow.RUSH_HOUR}:
            return time_horizon, time_window, TimeContext.SPECIFIC_HOUR, requested_time_hint
        return time_horizon, time_window, TimeContext.LATER, requested_time_hint

    @staticmethod
    def _detect_time_horizon(message: str) -> TimeHorizon:
        if any(token in message for token in ("right now", "now", "currently")):
            return TimeHorizon.NOW
        if "tomorrow" in message:
            return TimeHorizon.TOMORROW
        if "weekend" in message or "this weekend" in message:
            return TimeHorizon.THIS_WEEKEND
        if any(token in message for token in ("next week", "friday", "saturday", "sunday", "monday", "tuesday", "wednesday", "thursday")):
            return TimeHorizon.FUTURE_DAY
        if any(token in message for token in ("later", "tonight", "this evening", "this afternoon", "after work", "in a few hours")):
            return TimeHorizon.LATER_TODAY
        return TimeHorizon.UNSPECIFIED

    @staticmethod
    def _detect_time_window(message: str) -> TimeWindow:
        if "rush hour" in message:
            return TimeWindow.RUSH_HOUR
        if re.search(r"\bafter\s+[5-9](?::\d{2})?\s*(pm)?\b", message) or "after work" in message:
            return TimeWindow.EVENING
        if any(token in message for token in ("early morning", "at dawn", "sunrise")):
            return TimeWindow.EARLY_MORNING
        if "morning" in message:
            return TimeWindow.MORNING
        if any(token in message for token in ("noon", "midday", "lunch")):
            return TimeWindow.MIDDAY
        if "afternoon" in message:
            return TimeWindow.AFTERNOON
        if any(token in message for token in ("evening", "tonight", "after sunset")):
            return TimeWindow.EVENING
        if any(token in message for token in ("night", "late night")):
            return TimeWindow.NIGHT
        return TimeWindow.UNSPECIFIED

    @staticmethod
    def _detect_requested_time_hint(
        time_horizon: TimeHorizon,
        time_window: TimeWindow,
    ) -> RequestedTimeHint | None:
        if time_window == TimeWindow.RUSH_HOUR:
            return RequestedTimeHint.RUSH_HOUR
        if time_horizon in {TimeHorizon.TOMORROW, TimeHorizon.FUTURE_DAY}:
            return RequestedTimeHint.FUTURE_DAY
        if time_horizon == TimeHorizon.THIS_WEEKEND:
            return RequestedTimeHint.WEEKEND
        if time_window != TimeWindow.UNSPECIFIED:
            return RequestedTimeHint.SAME_DAY_NAMED_PERIOD
        if time_horizon == TimeHorizon.LATER_TODAY:
            return RequestedTimeHint.SAME_DAY_RELATIVE_TIME
        return None

    @staticmethod
    def _detect_intensity(message: str, activity_profile: ActivityProfile | None) -> IntensityLevel:
        if any(token in message for token in ("easy", "light", "slow", "gentle")):
            return IntensityLevel.LOW
        if any(token in message for token in ("moderate",)):
            return IntensityLevel.MODERATE
        if any(token in message for token in ("hard", "intense", "hiit", "sprint", "fast", "marathon")):
            return IntensityLevel.HIGH
        if activity_profile is not None:
            return activity_profile.exertion_level
        return IntensityLevel.MODERATE

    @staticmethod
    def _detect_comparison_target(message: str, intent: IntentType) -> ComparisonTarget | None:
        if intent != IntentType.COMPARE_TIMES:
            return None
        if "morning or afternoon" in message or "afternoon worse than early morning" in message:
            return ComparisonTarget.MORNING_VS_AFTERNOON
        if "before or after rush hour" in message or "rush hour" in message:
            return ComparisonTarget.BEFORE_AFTER_RUSH_HOUR
        return ComparisonTarget.NOW_VS_LATER

    @staticmethod
    def _detect_adjustment_type(message: str, intent: IntentType) -> AdjustmentType | None:
        if intent == IntentType.DURATION_ADJUSTMENT:
            return AdjustmentType.DURATION
        if intent == IntentType.TIME_SHIFT:
            return AdjustmentType.TIMING
        if "reduce my time" in message or "shorten" in message:
            return AdjustmentType.DURATION
        if "go later" in message or "wait" in message or "delay" in message:
            return AdjustmentType.TIMING
        return None

    @staticmethod
    def _detect_candidate_modes(message: str, intent: IntentType) -> list[TransportMode]:
        if intent != IntentType.ROUTE_MODE_CHOICE:
            return []
        modes: list[TransportMode] = []
        for mode, variants in MODE_RULES:
            if any(variant in message for variant in variants):
                modes.append(mode)
        seen = []
        for mode in modes:
            if mode not in seen:
                seen.append(mode)
        return seen

    @staticmethod
    def _unresolved_fields(
        *,
        intent: IntentType,
        activity: ActivityType,
        duration: int | None,
        comparison_target: ComparisonTarget | None,
        candidate_modes: list[TransportMode],
    ) -> list[RequestFieldName]:
        unresolved_fields: list[RequestFieldName] = []
        if intent in {
            IntentType.ACTIVITY_CHECK,
            IntentType.BEST_TIME_TODAY,
            IntentType.DURATION_ADJUSTMENT,
            IntentType.TIME_SHIFT,
            IntentType.SHOULD_AVOID,
        } and activity == ActivityType.UNKNOWN:
            unresolved_fields.append(RequestFieldName.ACTIVITY)
        if intent == IntentType.DURATION_ADJUSTMENT and duration is None:
            unresolved_fields.append(RequestFieldName.DURATION_MINUTES)
        if intent == IntentType.COMPARE_TIMES and comparison_target is None:
            unresolved_fields.append(RequestFieldName.COMPARISON_TARGET)
        if intent == IntentType.ROUTE_MODE_CHOICE and len(candidate_modes) < 1:
            unresolved_fields.append(RequestFieldName.MODE_OPTIONS)
        return unresolved_fields

    @staticmethod
    def _confidence(
        *,
        intent: IntentType,
        unresolved_fields: list[RequestFieldName],
        timing_mode: TimeContext,
    ) -> float:
        confidence = 0.96
        confidence -= 0.2 * len(unresolved_fields)
        if intent in {IntentType.COMPARE_TIMES, IntentType.BEST_TIME_TODAY, IntentType.TIME_SHIFT, IntentType.ROUTE_MODE_CHOICE}:
            confidence -= 0.06
        if timing_mode != TimeContext.NOW:
            confidence -= 0.04
        return round(max(0.0, confidence), 2)
