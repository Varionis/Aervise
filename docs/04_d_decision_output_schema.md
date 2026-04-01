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
  }
}
```

---

## Design Notes

- this is the stable product-facing structured output
- message rendering should consume this contract, not raw engine internals
- timing guidance is explicitly capability-bound and weather-only for now
- AQ-forecast-based ranking is not part of the current MVP output

---

## Implementation Source

The Stage 5 contract is implemented in:

- [contracts/decision_output.py](/d:/Users/arnav/Documents/Github_Repos/Aervise/contracts/decision_output.py#L1)
- [core/layers/layer3_policy.py](/d:/Users/arnav/Documents/Github_Repos/Aervise/core/layers/layer3_policy.py#L1)
- [core/layers/layer4_explanation.py](/d:/Users/arnav/Documents/Github_Repos/Aervise/core/layers/layer4_explanation.py#L1)
- [interfaces/api/routes/decision.py](/d:/Users/arnav/Documents/Github_Repos/Aervise/interfaces/api/routes/decision.py#L1)
