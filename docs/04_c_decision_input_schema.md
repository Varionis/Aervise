# Stage 3 Decision Input Schema

This document locks the canonical payload-builder contract that enters the deterministic engine.

Stage 3 owns:

- intent normalization from Stage 1 output
- user-context normalization
- strict assembly of the engine entry payload
- rejection of unresolved Stage 1 inputs

It must not perform:

- text parsing
- provider fetch
- environment normalization
- policy logic

---

## Canonical Decision Input

```json
{
  "request": {
    "intent": {
      "source_intent": "activity_check",
      "activity": "running",
      "activity_profile": {
        "exertion_level": "high",
        "expected_duration_band": "medium",
        "exposure_level": "high",
        "location_context": "outdoor",
        "motion_pattern": "continuous"
      },
      "activity_group": "exercise_outdoor",
      "activity_archetype": "outdoor_high_exertion",
      "decision_archetype": "NOW_CHECK",
      "intensity": "high",
      "duration_min": 30,
      "duration_band": "medium",
      "timing_mode": "now",
      "requested_time": null,
      "requested_time_hint": null,
      "time_horizon": "now",
      "time_window": "unspecified",
      "location_context": "outdoor"
    },
    "user_context": {
      "sensitivity": "unknown",
      "age_group": "unknown",
      "health_flags": [],
      "sensitive_group": false,
      "respiratory_condition": "unknown"
    }
  },
  "environment_state": {},
  "layer_trace": {
    "stage": "decision_payload_builder",
    "decision_archetype": "NOW_CHECK",
    "activity_archetype": "outdoor_high_exertion",
    "timing_mode": "now",
    "forecast_window_available": true
  }
}
```

---

## Design Notes

- `request.intent` is built from Stage 1 output, not from raw user text
- `activity_profile` is carried forward so Stage 3 can derive defaults and engine archetypes from exertion/exposure semantics, not only from hardcoded labels
- `environment_state` must arrive already normalized from Stage 2
- unresolved Stage 1 inputs such as unknown activity must block Stage 3
- missing duration should only block Stage 3 for intents that truly require explicit duration, such as `duration_adjustment`
- this is the only contract the deterministic engine should accept

---

## Implementation Source

The Stage 3 contract is implemented in:

- [contracts/decision_input.py](/d:/Users/arnav/Documents/Github_Repos/Aervise/contracts/decision_input.py#L1)
- [pipeline/payload_builder/builder.py](/d:/Users/arnav/Documents/Github_Repos/Aervise/pipeline/payload_builder/builder.py#L1)
- [pipeline/orchestrator.py](/d:/Users/arnav/Documents/Github_Repos/Aervise/pipeline/orchestrator.py#L1)

The API/debug boundary for this stage is:

- `POST /interaction/build-payload`
