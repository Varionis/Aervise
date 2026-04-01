# Stage 0 and Stage 1 Schema

This document locks the formal schema for:

- Stage 0: Entry Point
- Stage 1: Intent Recognition

These are the contracts for the interaction boundary before context enrichment and before the deterministic engine.

---

## 1. Stage 0: Entry Point Contract

### Purpose

Represent the raw external request in a stable, typed form.

### Canonical model

```json
{
  "user_id": "demo-user",
  "message": "Can I go for a run right now for 30 minutes?",
  "timestamp_utc": "2026-03-29T22:00:00Z",
  "location": {
    "lat": 43.6532,
    "lon": -79.3832
  },
  "channel": "demo_ui"
}
```

---

## 2. Stage 1: Intent Recognition Contract

### Purpose

Convert raw text into explicit structured intent for the outer pipeline.

### Canonical model

```json
{
  "intent": "compare_times",
  "activity": "running",
  "activity_profile": {
    "exertion_level": "high",
    "expected_duration_band": "medium",
    "exposure_level": "high",
    "location_context": "outdoor",
    "motion_pattern": "continuous"
  },
  "intensity": "high",
  "duration_minutes": null,
  "reference_duration_minutes": null,
  "time_context": "specific_hour",
  "time_horizon": "tomorrow",
  "time_window": "evening",
  "requested_time_hint": "future_day",
  "comparison_target": "now_vs_later",
  "adjustment_type": null,
  "candidate_modes": [],
  "confidence": 0.86,
  "unresolved_fields": [],
  "parser": {
    "strategy": "rule_based_v1",
    "raw_message": "Is evening better than now for a run?"
  }
}
```

### Attributes

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `intent` | enum | yes | Top-level recognized intent family |
| `activity` | enum | yes | Canonical activity type |
| `activity_profile` | object or `null` | yes | Semantic profile used for downstream defaults and archetypes |
| `intensity` | enum | yes | Explicit or inferred |
| `duration_minutes` | `int \| null` | yes | Optional; null is valid for open-ended checks |
| `reference_duration_minutes` | `int \| null` | no | Optional baseline duration for duration-adjustment requests like `20 minutes instead of an hour` |
| `time_context` | enum | yes | Decision-timing mode used by downstream flow |
| `time_horizon` | enum | yes | Calendar-oriented horizon like `tomorrow` or `this_weekend` |
| `time_window` | enum | yes | General purpose daypart window like `morning` or `evening` |
| `requested_time_hint` | enum or `null` | no | Coarse hint for same-day, future-day, or weekend phrasing |
| `comparison_target` | enum or `null` | no | Filled for compare-style requests |
| `adjustment_type` | enum or `null` | no | Filled for duration/time-shift requests |
| `candidate_modes` | enum list | yes | Filled for commute/mode-choice requests |
| `confidence` | `float` | yes | `0.0` to `1.0` |
| `unresolved_fields` | enum list | yes | Missing fields blocking certainty |
| `parser.strategy` | enum | yes | Parser version |
| `parser.raw_message` | `str` | yes | Original text for traceability |

---

## 3. Enums

### `intent`

- `activity_check`
- `best_time_today`
- `compare_times`
- `duration_adjustment`
- `time_shift`
- `route_mode_choice`
- `should_avoid`
- `unknown`

### `activity`

- `running`
- `walking`
- `cycling`
- `hiit`
- `soccer`
- `basketball`
- `hiking`
- `yard_work`
- `park_visit`
- `beach_day`
- `festival`
- `sightseeing`
- `commute`
- `bike_commute`
- `dog_walk`
- `outdoor_errand`
- `barbecue`
- `outdoor_gathering`
- `open_windows`
- `unknown`

### `intensity`

- `low`
- `moderate`
- `high`

### `activity_profile.exertion_level`

- `low`
- `moderate`
- `high`

### `activity_profile.expected_duration_band`

- `short`
- `medium`
- `long`

### `activity_profile.exposure_level`

- `low`
- `moderate`
- `high`

### `activity_profile.location_context`

- `outdoor`
- `indoor_outdoor_boundary`

### `activity_profile.motion_pattern`

- `stationary`
- `intermittent`
- `continuous`

### `time_context`

- `now`
- `later`
- `specific_hour`
- `best_time_today`
- `what_if`

### `requested_time_hint`

- `same_day_relative_time`
- `same_day_named_period`
- `future_day`
- `weekend`
- `rush_hour`

### `time_horizon`

- `now`
- `later_today`
- `tomorrow`
- `this_weekend`
- `future_day`
- `unspecified`

### `time_window`

- `unspecified`
- `early_morning`
- `morning`
- `midday`
- `afternoon`
- `evening`
- `night`
- `rush_hour`

### `comparison_target`

- `now_vs_later`
- `morning_vs_afternoon`
- `before_after_rush_hour`

### `adjustment_type`

- `duration`
- `timing`

### `candidate_modes`

- `walk`
- `bike`
- `scooter`
- `transit`
- `drive`
- `jog`

### `unresolved_fields`

- `activity`
- `duration_minutes`
- `location`
- `comparison_target`
- `mode_options`

### `parser.strategy`

- `rule_based_v1`

---

## 4. Current Stage 1 Coverage

Current parser behavior supports these use-case families:

- immediate activity checks
- open-ended activity checks without duration
- best-time-today requests
- same-day time comparison
- future-day activity/weather checks
- duration-adjustment requests
- time-shift / wait-later requests
- commute / route-mode choice
- should-avoid phrasing

It also now normalizes temporal phrasing in two dimensions:

- `time_horizon` for when the request applies on the calendar
- `time_window` for the broad part of day

And it separates:

- `activity` as the readable canonical label
- `activity_profile` as the semantic exertion/exposure profile that downstream stages use for defaults and policy mapping

This is intentionally broader than the original parser and avoids forcing phrases like `tomorrow after 5 pm` into the old `now` / `later` split.

This is still rule-based and MVP-grade, but it now matches the documented use-case surface much better than the original single-intent parser.

For duration-adjustment requests, Stage 1 now preserves both:

- `duration_minutes` for the simulated scenario
- `reference_duration_minutes` for the baseline plan when the user explicitly provides one

---

## 5. Implementation Source

The schema is implemented in:

- [contracts/intent_schema.py](/d:/Users/arnav/Documents/Github_Repos/Aervise/contracts/intent_schema.py#L1)
- [pipeline/intent/schemas.py](/d:/Users/arnav/Documents/Github_Repos/Aervise/pipeline/intent/schemas.py#L1)
- [pipeline/intent/parser.py](/d:/Users/arnav/Documents/Github_Repos/Aervise/pipeline/intent/parser.py#L1)

These should now be treated as the source of truth for Stage 0 and Stage 1.
