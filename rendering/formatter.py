from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from contracts.decision_output import DecisionOutput
from rendering.templates import HEADLINE_TEMPLATES, MESSAGE_PREFIX_TEMPLATES, SAFETY_NOTE_TEMPLATES


class RenderMetadata(BaseModel):
    decision_label: str
    render_strategy: str = "template_v1"
    confidence_band: str


class RenderedDecision(BaseModel):
    headline: str
    message: str
    reason_bullets: list[str] = Field(default_factory=list)
    adjustment_bullets: list[str] = Field(default_factory=list)
    timing_note: str | None = None
    safety_note: str | None = None
    metadata: RenderMetadata


class RenderedDecisionEnvelope(BaseModel):
    structured: DecisionOutput
    rendered: RenderedDecision


@dataclass
class DecisionMessageFormatter:
    def render(self, decision_output: dict[str, Any] | DecisionOutput) -> RenderedDecision:
        structured = decision_output if isinstance(decision_output, DecisionOutput) else DecisionOutput(**decision_output)
        label = structured.decision.label.value
        reasons = structured.explanation.reasons or structured.reasoning
        adjustments = [item.suggestion for item in structured.modifications]
        timing_note = structured.explanation.timing_guidance.message

        message_parts = [MESSAGE_PREFIX_TEMPLATES[label], structured.recommendation.message]
        if reasons:
            message_parts.append(reasons[0])
        if timing_note and label in {"okay_with_caution", "shorten_or_modify", "avoid_for_now"}:
            message_parts.append(timing_note)

        return RenderedDecision(
            headline=HEADLINE_TEMPLATES[label],
            message=" ".join(part.strip() for part in message_parts if part),
            reason_bullets=reasons[:3],
            adjustment_bullets=adjustments[:3],
            timing_note=timing_note,
            safety_note=SAFETY_NOTE_TEMPLATES[label],
            metadata=RenderMetadata(
                decision_label=label,
                confidence_band=self._confidence_band(structured.decision.confidence),
            ),
        )

    @staticmethod
    def _confidence_band(confidence: float) -> str:
        if confidence >= 0.85:
            return "high"
        if confidence >= 0.6:
            return "medium"
        return "low"
