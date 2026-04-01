from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from contracts.environment_schema import EnvironmentState
from contracts.intent_schema import ActivityLocationContext, ExpectedDurationBand, ExposureLevel, MotionPattern


class CanonicalActivity(str, Enum):
    RUNNING = "running"
    WALKING = "walking"
    CYCLING = "cycling"
    HIKING = "hiking"
    BASKETBALL = "basketball"
    BARBECUE = "barbecue"
    DOG_WALK = "dog_walk"
    BIKE_COMMUTE = "bike_commute"
    COMMUTE = "commute"
    OUTDOOR_ERRAND = "outdoor_errand"
    OPEN_WINDOWS = "open_windows"
    GENERAL_OUTDOOR_ACTIVITY = "general_outdoor_activity"


class ActivityGroup(str, Enum):
    EXERCISE_OUTDOOR = "exercise_outdoor"
    LIGHT_OUTDOOR_ACTIVITY = "light_outdoor_activity"
    BRIEF_OUTDOOR_ACTIVITY = "brief_outdoor_activity"
    COMMUTE_OUTDOOR = "commute_outdoor"
    INDOOR_OUTDOOR_BOUNDARY = "indoor_outdoor_boundary"
    GENERAL_OUTDOOR_ACTIVITY = "general_outdoor_activity"


class ActivityArchetype(str, Enum):
    OUTDOOR_HIGH_EXERTION = "outdoor_high_exertion"
    OUTDOOR_LOW_EXERTION = "outdoor_low_exertion"
    BRIEF_OUTDOOR_EXPOSURE = "brief_outdoor_exposure"
    COMMUTE_ROUTINE = "commute_routine"
    INDOOR_OUTDOOR = "indoor_outdoor"


class DecisionArchetype(str, Enum):
    NOW_CHECK = "NOW_CHECK"
    COMPARE_NOW_LATER = "COMPARE_NOW_LATER"
    BEST_TIME_TODAY = "BEST_TIME_TODAY"
    FUTURE_LOOKAHEAD = "FUTURE_LOOKAHEAD"
    WHAT_IF = "WHAT_IF"


class DurationBand(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class LocationContext(str, Enum):
    OUTDOOR = "outdoor"
    INDOOR = "indoor"
    INDOOR_OUTDOOR_BOUNDARY = "indoor_outdoor_boundary"


class SensitivityLevel(str, Enum):
    UNKNOWN = "unknown"
    NORMAL = "normal"
    SENSITIVE = "sensitive"
    ASTHMA = "asthma"
    CHILD = "child"
    ELDERLY = "elderly"


class AgeGroup(str, Enum):
    UNKNOWN = "unknown"
    CHILD = "child"
    ADULT = "adult"
    SENIOR = "senior"


class RespiratoryCondition(str, Enum):
    UNKNOWN = "unknown"
    NONE = "none"
    ASTHMA = "asthma"
    COPD = "copd"
    OTHER = "other"


class DecisionIntent(BaseModel):
    class ActivityProfilePayload(BaseModel):
        exertion_level: str
        expected_duration_band: ExpectedDurationBand
        exposure_level: ExposureLevel
        location_context: ActivityLocationContext
        motion_pattern: MotionPattern
        typical_duration_min: int | None = Field(default=None, ge=1, le=1440)
        hard_upper_duration_min: int | None = Field(default=None, ge=1, le=1440)

    source_intent: str = "activity_check"
    activity: CanonicalActivity
    activity_profile: ActivityProfilePayload | None = None
    activity_group: ActivityGroup
    activity_archetype: ActivityArchetype
    decision_archetype: DecisionArchetype
    intensity: str
    duration_min: int = Field(ge=1, le=720)
    reference_duration_min: int | None = Field(default=None, ge=1, le=720)
    duration_band: DurationBand
    timing_mode: str
    requested_time: str | None = None
    requested_time_hint: str | None = None
    time_horizon: str = "unspecified"
    time_window: str = "unspecified"
    comparison_target: str | None = None
    adjustment_type: str | None = None
    candidate_modes: list[str] = Field(default_factory=list)
    location_context: LocationContext = LocationContext.OUTDOOR


class DecisionUserContext(BaseModel):
    sensitivity: SensitivityLevel = SensitivityLevel.UNKNOWN
    age_group: AgeGroup = AgeGroup.UNKNOWN
    health_flags: list[str] = Field(default_factory=list)
    sensitive_group: bool = False
    respiratory_condition: RespiratoryCondition = RespiratoryCondition.UNKNOWN


class DecisionRequestEnvelope(BaseModel):
    intent: DecisionIntent
    user_context: DecisionUserContext = Field(default_factory=DecisionUserContext)


class DecisionPayloadTrace(BaseModel):
    stage: str
    decision_archetype: DecisionArchetype
    activity_archetype: ActivityArchetype
    timing_mode: str
    forecast_window_available: bool
    entry_channel: str | None = None


class DecisionInput(BaseModel):
    request: DecisionRequestEnvelope
    environment_state: EnvironmentState
    layer_trace: DecisionPayloadTrace
