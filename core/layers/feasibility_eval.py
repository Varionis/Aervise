from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RequestFeasibilityEvaluator:
    def evaluate(self, decision_input: dict[str, Any]) -> dict[str, Any]:
        intent = decision_input["request"]["intent"]
        activity = intent["activity"].replace("_", " ")
        requested_duration_min = intent["duration_min"]
        activity_profile = intent.get("activity_profile") or {}
        typical_duration_min = activity_profile.get("typical_duration_min")
        hard_upper_duration_min = activity_profile.get("hard_upper_duration_min")

        status = "within_expected"
        over_typical_by_min = None
        over_hard_upper_by_min = None
        reason = None

        if hard_upper_duration_min is not None and requested_duration_min > hard_upper_duration_min:
            status = "exceeds_hard_upper"
            over_hard_upper_by_min = requested_duration_min - hard_upper_duration_min
            reason = (
                f"The requested {requested_duration_min}-minute duration is well beyond the supported upper range "
                f"for {activity}."
            )
        elif typical_duration_min is not None and requested_duration_min > typical_duration_min:
            status = "exceeds_typical"
            over_typical_by_min = requested_duration_min - typical_duration_min
            reason = (
                f"The requested {requested_duration_min}-minute duration is substantially above the typical range "
                f"for {activity}."
            )

        return {
            **decision_input,
            "request_feasibility": {
                "status": status,
                "typical_duration_min": typical_duration_min,
                "hard_upper_duration_min": hard_upper_duration_min,
                "requested_duration_min": requested_duration_min,
                "over_typical_by_min": over_typical_by_min,
                "over_hard_upper_by_min": over_hard_upper_by_min,
                "reason": reason,
            },
        }
