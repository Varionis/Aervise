from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class InputChannel(str, Enum):
    API = "api"
    CHAT = "chat"
    CLI = "cli"
    TEST_HARNESS = "test_harness"
    DEMO_UI = "demo_ui"


class IntentType(str, Enum):
    ACTIVITY_CHECK = "activity_check"
    BEST_TIME_TODAY = "best_time_today"
    COMPARE_TIMES = "compare_times"
    DURATION_ADJUSTMENT = "duration_adjustment"
    TIME_SHIFT = "time_shift"
    ROUTE_MODE_CHOICE = "route_mode_choice"
    SHOULD_AVOID = "should_avoid"
    UNKNOWN = "unknown"


class ActivityType(str, Enum):
    RUNNING = "running"
    WALKING = "walking"
    CYCLING = "cycling"
    HIIT = "hiit"
    SOCCER = "soccer"
    BASKETBALL = "basketball"
    HIKING = "hiking"
    YARD_WORK = "yard_work"
    PARK_VISIT = "park_visit"
    BEACH_DAY = "beach_day"
    FESTIVAL = "festival"
    SIGHTSEEING = "sightseeing"
    COMMUTE = "commute"
    BIKE_COMMUTE = "bike_commute"
    DOG_WALK = "dog_walk"
    OUTDOOR_ERRAND = "outdoor_errand"
    BARBECUE = "barbecue"
    OUTDOOR_GATHERING = "outdoor_gathering"
    OPEN_WINDOWS = "open_windows"
    UNKNOWN = "unknown"


class IntensityLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class ExpectedDurationBand(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class ExposureLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class ActivityLocationContext(str, Enum):
    OUTDOOR = "outdoor"
    INDOOR_OUTDOOR_BOUNDARY = "indoor_outdoor_boundary"


class MotionPattern(str, Enum):
    STATIONARY = "stationary"
    INTERMITTENT = "intermittent"
    CONTINUOUS = "continuous"


class TimeContext(str, Enum):
    NOW = "now"
    LATER = "later"
    SPECIFIC_HOUR = "specific_hour"
    BEST_TIME_TODAY = "best_time_today"
    WHAT_IF = "what_if"


class TimeHorizon(str, Enum):
    NOW = "now"
    LATER_TODAY = "later_today"
    TOMORROW = "tomorrow"
    THIS_WEEKEND = "this_weekend"
    FUTURE_DAY = "future_day"
    UNSPECIFIED = "unspecified"


class TimeWindow(str, Enum):
    UNSPECIFIED = "unspecified"
    EARLY_MORNING = "early_morning"
    MORNING = "morning"
    MIDDAY = "midday"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"
    RUSH_HOUR = "rush_hour"


class RequestedTimeHint(str, Enum):
    SAME_DAY_RELATIVE_TIME = "same_day_relative_time"
    SAME_DAY_NAMED_PERIOD = "same_day_named_period"
    FUTURE_DAY = "future_day"
    WEEKEND = "weekend"
    RUSH_HOUR = "rush_hour"


class ComparisonTarget(str, Enum):
    NOW_VS_LATER = "now_vs_later"
    MORNING_VS_AFTERNOON = "morning_vs_afternoon"
    BEFORE_AFTER_RUSH_HOUR = "before_after_rush_hour"


class AdjustmentType(str, Enum):
    DURATION = "duration"
    TIMING = "timing"


class TransportMode(str, Enum):
    WALK = "walk"
    BIKE = "bike"
    SCOOTER = "scooter"
    TRANSIT = "transit"
    DRIVE = "drive"
    JOG = "jog"


class RequestFieldName(str, Enum):
    ACTIVITY = "activity"
    DURATION_MINUTES = "duration_minutes"
    LOCATION = "location"
    COMPARISON_TARGET = "comparison_target"
    MODE_OPTIONS = "mode_options"
    TIME_HORIZON = "time_horizon"


class ParserStrategy(str, Enum):
    RULE_BASED_V1 = "rule_based_v1"


class InteractionLocation(BaseModel):
    lat: float | None = None
    lon: float | None = None


class UserMessageRequest(BaseModel):
    user_id: str | None = Field(default="demo-user")
    message: str = Field(min_length=1)
    timestamp_utc: str | None = None
    location: InteractionLocation | None = None
    channel: InputChannel = InputChannel.DEMO_UI


class EntryPointEnvelope(BaseModel):
    user_id: str
    message: str
    timestamp_utc: str
    location: InteractionLocation
    channel: InputChannel


class ParserMetadata(BaseModel):
    strategy: ParserStrategy
    raw_message: str


class ActivityProfile(BaseModel):
    exertion_level: IntensityLevel
    expected_duration_band: ExpectedDurationBand
    exposure_level: ExposureLevel
    location_context: ActivityLocationContext = ActivityLocationContext.OUTDOOR
    motion_pattern: MotionPattern = MotionPattern.CONTINUOUS
    typical_duration_min: int | None = Field(default=None, ge=1, le=1440)
    hard_upper_duration_min: int | None = Field(default=None, ge=1, le=1440)


class IntentRecognitionResult(BaseModel):
    intent: IntentType
    activity: ActivityType
    activity_profile: ActivityProfile | None = None
    intensity: IntensityLevel
    duration_minutes: int | None = Field(default=None, ge=1, le=720)
    time_context: TimeContext
    time_horizon: TimeHorizon = TimeHorizon.UNSPECIFIED
    time_window: TimeWindow = TimeWindow.UNSPECIFIED
    requested_time_hint: RequestedTimeHint | None = None
    comparison_target: ComparisonTarget | None = None
    adjustment_type: AdjustmentType | None = None
    candidate_modes: list[TransportMode] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    unresolved_fields: list[RequestFieldName] = Field(default_factory=list)
    parser: ParserMetadata


class InteractionPreviewResponse(BaseModel):
    entry_point: EntryPointEnvelope
    intent_recognition: IntentRecognitionResult
