from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core import RequestFeasibilityEvaluator, DecisionLayer2Evaluator, DecisionLayer3Policy, DecisionLayer4Explainer
from pipeline.payload_builder.builder import DecisionPayloadBuilder


@dataclass
class DecisionService:
    def evaluate(self, decision_input: dict[str, Any]) -> dict[str, Any]:
        feasibility = RequestFeasibilityEvaluator().evaluate(decision_input)
        layer2 = DecisionLayer2Evaluator().evaluate(feasibility)
        layer3 = DecisionLayer3Policy().evaluate(layer2)
        layer4 = DecisionLayer4Explainer().explain(layer3)
        return layer4

    def debug_from_decision_input(self, decision_input: dict[str, Any]) -> dict[str, Any]:
        feasibility = RequestFeasibilityEvaluator().evaluate(decision_input)
        layer2 = DecisionLayer2Evaluator().evaluate(feasibility)
        layer3 = DecisionLayer3Policy().evaluate(layer2)
        layer4 = DecisionLayer4Explainer().explain(layer3)

        return {
            "decision_input": decision_input,
            "feasibility": layer2["request_feasibility"],
            "layer2": {
                "risk_factors": layer2["risk_factors"],
                "factor_model": layer2["layer_trace"].get("factor_model"),
            },
            "layer3": {
                "decision": layer3["decision"],
                "recommendation": layer3["recommendation"],
                "factor_breakdown": layer3["factor_breakdown"],
                "reasoning": layer3["reasoning"],
                "modifications": layer3["modifications"],
                "assumptions": layer3["assumptions"],
                "policy_trace": layer3["policy_trace"],
            },
            "layer4": {
                "explanation": layer4["explanation"],
                "modifications": layer4["modifications"],
                "safe_alternative_available": layer4["safe_alternative_available"],
                "alternative_recommendation": layer4["alternative_recommendation"],
            },
        }


@dataclass
class PipelineOrchestrator:
    payload_builder: DecisionPayloadBuilder = field(default_factory=DecisionPayloadBuilder)

    def build_decision_input(
        self,
        *,
        entry_point: dict[str, Any],
        intent_recognition: dict[str, Any],
        environment_state: dict[str, Any],
        user_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.payload_builder.build(
            entry_point=entry_point,
            intent_recognition=intent_recognition,
            environment_state=environment_state,
            user_context=user_context,
        )
