from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime

from config import Settings
from contracts.intent_schema import (
    ActivityType,
    InputChannel,
    IntentType,
    IntensityLevel,
    ParserStrategy,
    RequestFieldName,
    RequestedTimeHint,
    TimeContext,
)


ACTIVITY_RULES = [
    (ActivityType.RUNNING, ("run", "running", "jog", "jogging")),
    (ActivityType.WALKING, ("walk", "walking", "stroll")),
    (ActivityType.CYCLING, ("cycle", "cycling", "bike", "biking")),
    (ActivityType.DOG_WALK, ("dog walk", "walk my dog")),
    (ActivityType.OUTDOOR_ERRAND, ("errand", "pickup", "grab coffee", "grocery")),
    (ActivityType.OPEN_WINDOWS, ("open windows", "open the windows", "open window")),
]

DEFAULT_INTENSITY = {
    ActivityType.RUNNING: IntensityLevel.HIGH,
    ActivityType.WALKING: IntensityLevel.LOW,
    ActivityType.CYCLING: IntensityLevel.HIGH,
    ActivityType.DOG_WALK: IntensityLevel.LOW,
    ActivityType.OUTDOOR_ERRAND: IntensityLevel.LOW,
    ActivityType.OPEN_WINDOWS: IntensityLevel.LOW,
}


@dataclass
class InteractionService:
    settings: Settings

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
        activity = self._detect_activity(lowered)
        duration = self._detect_duration(lowered)
        timing_mode, requested_time_hint = self._detect_timing(lowered)
        intensity = self._detect_intensity(lowered, activity)

        unresolved_fields = []
        if activity == ActivityType.UNKNOWN:
            unresolved_fields.append(RequestFieldName.ACTIVITY)
        if duration is None:
            unresolved_fields.append(RequestFieldName.DURATION_MINUTES)

        confidence = 0.95
        confidence -= 0.25 * len(unresolved_fields)
        if timing_mode != TimeContext.NOW:
            confidence -= 0.05

        return {
            "intent": IntentType.ACTIVITY_CHECK if activity != ActivityType.UNKNOWN else IntentType.UNKNOWN,
            "activity": activity,
            "intensity": intensity,
            "duration_minutes": duration,
            "time_context": timing_mode,
            "requested_time_hint": requested_time_hint,
            "confidence": round(max(0.0, confidence), 2),
            "unresolved_fields": unresolved_fields,
            "parser": {
                "strategy": ParserStrategy.RULE_BASED_V1,
                "raw_message": message,
            },
        }

    @staticmethod
    def _detect_activity(message: str) -> ActivityType:
        for canonical, variants in ACTIVITY_RULES:
            if any(variant in message for variant in variants):
                return canonical
        return ActivityType.UNKNOWN

    @staticmethod
    def _detect_duration(message: str) -> int | None:
        match = re.search(r"(\d{1,3})\s*(minutes|minute|mins|min)\b", message)
        if match:
            return int(match.group(1))
        if "quick" in message or "brief" in message:
            return 15
        return None

    @staticmethod
    def _detect_timing(message: str) -> tuple[TimeContext, RequestedTimeHint | None]:
        if any(token in message for token in ("right now", "now", "currently")):
            return TimeContext.NOW, None
        if any(token in message for token in ("evening", "tonight", "later", "after")):
            return TimeContext.LATER, RequestedTimeHint.SAME_DAY_RELATIVE_TIME
        if any(token in message for token in ("morning", "afternoon")):
            return TimeContext.SPECIFIC_HOUR, RequestedTimeHint.SAME_DAY_NAMED_PERIOD
        return TimeContext.NOW, None

    @staticmethod
    def _detect_intensity(message: str, activity: ActivityType) -> IntensityLevel:
        if any(token in message for token in ("easy", "light", "slow", "gentle")):
            return IntensityLevel.LOW
        if any(token in message for token in ("moderate",)):
            return IntensityLevel.MODERATE
        if any(token in message for token in ("hard", "intense", "hiit", "sprint", "fast")):
            return IntensityLevel.HIGH
        return DEFAULT_INTENSITY.get(activity, IntensityLevel.MODERATE)
