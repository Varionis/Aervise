# Stage 5 Decision Output Schema

This document locks the structured output contract returned by the deterministic engine.

Stage 5 owns:

- decision label and confidence
- recommendation payload
- factor breakdown
- reasoning and assumptions
- modification guidance
- explanation-ready timing guidance

It must not depend on message rendering.

---

## Canonical Decision Output

```json
{
  "request_feasibility": {
    "status": "within_expected",
    "typical_duration_min": 60,
    "hard_upper_duration_min": 240,
    "requested_duration_min": 30,
    "over_typical_by_min": null,
    "over_hard_upper_by_min": null,
    "reason": null
  },
  "decision": {
    "label": "go_ahead",
    "score": 0.158,
    "confidence": 0.831
  },
  "recommendation": {
    "allowed": true,
    "message": "You can proceed with running under current conditions.",
    "blocked_by_hard_constraints": false
  },
  "factor_breakdown": {
    "air_burden": "low",
    "heat_burden": "low",
    "exposure": "low",
    "confidence": "low"
  },
  "reasoning": [
    "Current air and weather conditions are acceptable for running."
  ],
  "modifications": [],
  "assumptions": [
    "Assessment is based on outdoor conditions only.",
    "No specific respiratory sensitivity was applied."
  ],
  "explanation": {
    "summary": "Current conditions look acceptable for running.",
    "reasons": [
      "Air quality, weather strain, and exposure burden are all currently in a manageable range."
    ],
    "adjustments": [],
    "assumptions": [
      "Assessment is based on outdoor conditions only.",
      "No specific respiratory sensitivity was applied.",
      "No same-day air-quality forecast is available yet."
    ],
    "timing_guidance": {
      "message": null,
      "timing_basis": "weather_only",
      "timing_confidence": "low",
      "alternative_recommendation": null,
      "modification": null,
      "assumption": null
    }
  },
  "mode_result": {
    "mode": "standard",
    "comparison": null,
    "best_time": null,
    "what_if": null
  }
}
```

---

## Design Notes

- this is the stable product-facing structured output
- message rendering should consume this contract, not raw engine internals
- `request_feasibility` is part of the structured output because unrealistic requests are product-relevant, not just internal engine metadata
- `mode_result` is the contract point for distinct decision modes such as `COMPARE_NOW_LATER`
- `mode_result.best_time` is the contract point for `BEST_TIME_TODAY`, including the selected same-day weather window and evaluated candidates
- `mode_result.what_if` is the contract point for `WHAT_IF`, including the simulated scenario and the baseline comparison used for the simulation
- timing guidance is explicitly capability-bound and weather-only for now
- AQ-forecast-based ranking is not part of the current MVP output
- `COMPARE_NOW_LATER` is implemented today as a same-day, weather-led comparison mode
- `BEST_TIME_TODAY` is implemented today as a same-day, weather-led window-ranking mode
- `WHAT_IF` is implemented today for same-day timing shifts and duration-adjustment simulations

---

## Implementation Source

The Stage 5 contract is implemented in:

- [contracts/decision_output.py](/d:/Users/arnav/Documents/Github_Repos/Aervise/contracts/decision_output.py#L1)
- [core/layers/layer3_policy.py](/d:/Users/arnav/Documents/Github_Repos/Aervise/core/layers/layer3_policy.py#L1)
- [core/layers/layer4_explanation.py](/d:/Users/arnav/Documents/Github_Repos/Aervise/core/layers/layer4_explanation.py#L1)
- [interfaces/api/routes/decision.py](/d:/Users/arnav/Documents/Github_Repos/Aervise/interfaces/api/routes/decision.py#L1)
