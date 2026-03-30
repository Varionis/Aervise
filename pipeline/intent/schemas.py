from contracts.intent_schema import (
    ActivityType,
    EntryPointEnvelope,
    InputChannel,
    InteractionLocation,
    InteractionPreviewResponse,
    IntentRecognitionResult,
    IntentType,
    IntensityLevel,
    ParserMetadata,
    ParserStrategy,
    RequestFieldName,
    RequestedTimeHint,
    TimeContext,
    UserMessageRequest,
)

InteractionRequest = UserMessageRequest
InteractionResponse = InteractionPreviewResponse

__all__ = [
    "ActivityType",
    "EntryPointEnvelope",
    "InputChannel",
    "InteractionLocation",
    "InteractionRequest",
    "InteractionResponse",
    "IntentRecognitionResult",
    "IntentType",
    "IntensityLevel",
    "ParserMetadata",
    "ParserStrategy",
    "RequestFieldName",
    "RequestedTimeHint",
    "TimeContext",
    "UserMessageRequest",
]
