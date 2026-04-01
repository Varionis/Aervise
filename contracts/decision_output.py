from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from contracts.decision_input import DecisionRequestEnvelope
from contracts.environment_schema import EnvironmentState


class FactorSeverity(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    MODERATE_HIGH = "moderate_high"
    HIGH = "high"
    VERY_HIGH = "very_high"


class FeasibilityStatus(str, Enum):
    WITHIN_EXPECTED = "within_expected"
    EXCEEDS_TYPICAL = "exceeds_typical"
    EXCEEDS_HARD_UPPER = "exceeds_hard_upper"


class DecisionLabel(str, Enum):
    GO_AHEAD = "go_ahead"
    OKAY_WITH_CAUTION = "okay_with_caution"
    SHORTEN_OR_MODIFY = "shorten_or_modify"
    AVOID_FOR_NOW = "avoid_for_now"
    INSUFFICIENT_CONFIDENCE = "insufficient_confidence"


class ModificationType(str, Enum):
    DURATION = "duration"
    INTENSITY = "intensity"
    TIMING = "timing"


class TimingBasis(str, Enum):
    NONE = "none"
    WEATHER_ONLY = "weather_only"


class TimingConfidence(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FactorPayload(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    level: FactorSeverity
    drivers: dict[str, Any]


class RiskFactorSet(BaseModel):
    air_burden: FactorPayload
    heat_burden: FactorPayload
    exposure_burden: FactorPayload
    disruption_factor: FactorPayload
    confidence_penalty: FactorPayload


class FeasibilityAssessment(BaseModel):
    status: FeasibilityStatus
    typical_duration_min: int | None = None
    hard_upper_duration_min: int | None = None
    requested_duration_min: int
    over_typical_by_min: int | None = None
    over_hard_upper_by_min: int | None = None
    reason: str | None = None


class DecisionOutcome(BaseModel):
    label: DecisionLabel
    score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)


class Recommendation(BaseModel):
    allowed: bool
    message: str
    blocked_by_hard_constraints: bool


class FactorBreakdown(BaseModel):
    air_burden: FactorSeverity
    heat_burden: FactorSeverity
    exposure: FactorSeverity
    confidence: FactorSeverity


class ModificationSuggestion(BaseModel):
    type: ModificationType
    suggestion: str


class HardConstraint(BaseModel):
    code: str
    reason: str


class PolicyOverride(BaseModel):
    rule: str
    decision_label: DecisionLabel


class PolicyTrace(BaseModel):
    hard_constraints_triggered: list[HardConstraint] = Field(default_factory=list)
    score_components: dict[str, float] = Field(default_factory=dict)
    overrides_applied: list[PolicyOverride] = Field(default_factory=list)
    weights: dict[str, float] = Field(default_factory=dict)


class TimingAlternative(BaseModel):
    time: str | None = None
    display_time: str | None = None
    basis: TimingBasis
    confidence: TimingConfidence
    reason: str | None = None


class TimingGuidance(BaseModel):
    message: str | None = None
    timing_basis: TimingBasis
    timing_confidence: TimingConfidence
    alternative_recommendation: TimingAlternative | None = None
    modification: ModificationSuggestion | None = None
    assumption: str | None = None


class Explanation(BaseModel):
    summary: str
    reasons: list[str]
    adjustments: list[str]
    assumptions: list[str]
    timing_guidance: TimingGuidance


class LayerTrace(BaseModel):
    stage: str
    decision_archetype: str
    activity_archetype: str
    timing_mode: str
    forecast_window_available: bool
    entry_channel: str | None = None
    factor_model: dict[str, Any] | None = None


class DecisionOutput(BaseModel):
    request: DecisionRequestEnvelope
    environment_state: EnvironmentState
    layer_trace: LayerTrace
    risk_factors: RiskFactorSet
    request_feasibility: FeasibilityAssessment
    decision: DecisionOutcome
    recommendation: Recommendation
    factor_breakdown: FactorBreakdown
    reasoning: list[str]
    modifications: list[ModificationSuggestion]
    assumptions: list[str]
    policy_trace: PolicyTrace
    explanation: Explanation
    safe_alternative_available: bool
    alternative_recommendation: TimingAlternative | None = None
