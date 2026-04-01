from __future__ import annotations

from contracts.decision_output import DecisionLabel


HEADLINE_TEMPLATES = {
    DecisionLabel.GO_AHEAD.value: "Conditions are acceptable",
    DecisionLabel.OKAY_WITH_CAUTION.value: "Proceed, but keep it conservative",
    DecisionLabel.SHORTEN_OR_MODIFY.value: "Modify the plan before going out",
    DecisionLabel.AVOID_FOR_NOW.value: "Avoid this right now",
    DecisionLabel.INSUFFICIENT_CONFIDENCE.value: "Data is not strong enough yet",
}


MESSAGE_PREFIX_TEMPLATES = {
    DecisionLabel.GO_AHEAD.value: "Current conditions support the requested plan.",
    DecisionLabel.OKAY_WITH_CAUTION.value: "The activity looks feasible, but conditions are not ideal.",
    DecisionLabel.SHORTEN_OR_MODIFY.value: "The requested plan is not ideal as-is.",
    DecisionLabel.AVOID_FOR_NOW.value: "Current conditions make this a poor choice right now.",
    DecisionLabel.INSUFFICIENT_CONFIDENCE.value: "The system cannot make a strong recommendation from the available inputs.",
}


SAFETY_NOTE_TEMPLATES = {
    DecisionLabel.GO_AHEAD.value: "Recheck if conditions change or timing shifts.",
    DecisionLabel.OKAY_WITH_CAUTION.value: "Keep effort and exposure conservative.",
    DecisionLabel.SHORTEN_OR_MODIFY.value: "Use the suggested modifications rather than the original plan.",
    DecisionLabel.AVOID_FOR_NOW.value: "Choose an indoor or lower-exposure alternative for now.",
    DecisionLabel.INSUFFICIENT_CONFIDENCE.value: "Treat this as a hold, not as a green light.",
}
