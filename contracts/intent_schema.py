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
    UNKNOWN = "unknown"


class ActivityType(str, Enum):
    RUNNING = "running"
    WALKING = "walking"
    CYCLING = "cycling"
    DOG_WALK = "dog_walk"
    OUTDOOR_ERRAND = "outdoor_errand"
    OPEN_WINDOWS = "open_windows"
    UNKNOWN = "unknown"


class IntensityLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class TimeContext(str, Enum):
    NOW = "now"
    LATER = "later"
    SPECIFIC_HOUR = "specific_hour"
    BEST_TIME_TODAY = "best_time_today"
    WHAT_IF = "what_if"


class RequestedTimeHint(str, Enum):
    SAME_DAY_RELATIVE_TIME = "same_day_relative_time"
    SAME_DAY_NAMED_PERIOD = "same_day_named_period"


class RequestFieldName(str, Enum):
    ACTIVITY = "activity"
    DURATION_MINUTES = "duration_minutes"
    LOCATION = "location"


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


class IntentRecognitionResult(BaseModel):
    intent: IntentType
    activity: ActivityType
    intensity: IntensityLevel
    duration_minutes: int | None = Field(default=None, ge=1, le=720)
    time_context: TimeContext
    requested_time_hint: RequestedTimeHint | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    unresolved_fields: list[RequestFieldName] = Field(default_factory=list)
    parser: ParserMetadata


class InteractionPreviewResponse(BaseModel):
    entry_point: EntryPointEnvelope
    intent_recognition: IntentRecognitionResult
