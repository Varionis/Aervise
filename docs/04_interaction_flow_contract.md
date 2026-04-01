# Aervise Interaction Flow Contract

This document formalizes the current end-to-end flow for Aervise in the structure the backend is now moving toward.

It is based on the high-level 7-stage architecture, but adjusted for:

- deterministic decisioning as the core asset
- limited forecast support today
- chat-style input as one interface, not the product definition
- current backend reality: Stage 0 to Stage 3 pipeline feeding a deterministic core

---

## 1. Architectural Fit

The proposed flow is directionally correct and usable for Aervise.

The main implementation rules are:

1. `Entry Point` is an interface concern, not part of the core engine.
2. `Intent Recognition` is optional for the platform, but required for chat-style entry.
3. `Context Enrichment` owns provider fetch, fallback, and normalization.
4. `Decision Payload Builder` is the canonical contract boundary into the deterministic engine.
5. `Decision Engine` stays deterministic.
6. `Output Structuring` stays deterministic.
7. `Message Rendering` is optional and should start templated.
8. `Logging / Observability` is required from the start.

So the correct framing is:

> A deterministic environmental decision system with optional chat parsing and optional message rendering around a strict engine contract.

---

## 2. Recommended Production Flow

```text
External Request
   ->
Intent Recognition or Structured Input Validation
   ->
Context Enrichment
   ->
Decision Payload Builder
   ->
Deterministic Decision Engine
   ->
Output Structuring
   ->
Message Rendering
   ->
Response Delivery + Observability
```

---

## 3. Canonical Stage Model

### Stage 0. Entry Point

This is the interface boundary.

Possible inputs:

- chat message
- API request
- internal test harness
- debug UI

Example external request:

```json
{
  "user_id": "demo-user",
  "message": "Can I go for a run right now for 30 minutes?",
  "timestamp_utc": "2026-03-29T22:00:00Z",
  "location": {
    "lat": 43.6532,
    "lon": -79.3832
  }
}
```

This is not the engine contract.

---

### Stage 1. Intent Recognition

Purpose:

- convert raw user language into explicit structured intent

Recommended output:

```json
{
  "intent": "activity_check",
  "activity": "running",
  "intensity": "high",
  "duration_minutes": 30,
  "time_context": "now",
  "requested_time_hint": null
}
```

This stage should be explicit and loss-minimized.

No free-text ambiguity should pass beyond this stage.

---

### Stage 2. Context Enrichment

Purpose:

- attach normalized environmental state and source metadata

Inputs:

- structured intent
- location
- timestamp

Required MVP fetches:

- PM2.5
- NO2
- O3
- temperature
- humidity
- wind speed

Optional:

- same-day weather forecast
- same-day AQ forecast later, when supported

Recommended output:

```json
{
  "environment_state": {
    "air_quality": {},
    "weather": {},
    "forecast_hours": [],
    "forecast_capabilities": {
      "supports_air_forecast": false,
      "supports_weather_forecast": true,
      "supports_same_day_timing": "partial"
    }
  }
}
```

This stage owns:

- fallback providers
- unit normalization
- missing-data handling
- source confidence
- forecast capability flags

---

### Stage 3. Decision Payload Builder

Purpose:

- build the strict contract that enters the deterministic engine

No raw chat text should exist beyond this point.

Recommended canonical payload:

```json
{
  "request": {
    "intent": {
      "activity": "running",
      "activity_group": "exercise_outdoor",
      "activity_archetype": "outdoor_high_exertion",
      "decision_archetype": "NOW_CHECK",
      "intensity": "high",
      "duration_min": 30,
      "duration_band": "medium",
      "timing_mode": "now",
      "requested_time": null,
      "requested_time_hint": null,
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
    "stage": "decision_payload_builder"
  }
}
```

This is the canonical engine input contract.

---

### Stage 4. Deterministic Decision Engine

Purpose:

- transform structured input into risk factors, policy outcomes, and explanation-ready signals

Must remain:

- deterministic
- testable
- explainable
- reproducible

Current deterministic core decomposition:

- Layer 2: factor evaluation
- Layer 3: hard constraints + policy mapping
- Layer 4: explanation + modification guidance

Stage 3 payload building now lives outside the core engine.

---

### Stage 5. Output Structuring

Purpose:

- convert engine state into a stable product response contract

This stage should remain deterministic.

---

### Stage 6. Message Rendering

Purpose:

- convert structured output into natural language for chat or UI

MVP guidance:

- use templates first
- add LLM enhancement later only if needed

The product must never depend on an LLM to produce the core decision.

---

### Stage 7. Response Delivery and Observability

Purpose:

- return the result
- persist traces for audit, QA, debugging, and performance monitoring

This is not optional.

---

## 4. Input and Output Assessment

### Does the proposed input make sense?

Yes, with one key adjustment:

- the external request shape is valid for chat or API entry
- it should not be confused with the engine input

So Aervise should maintain two different contracts:

1. external request contract
2. canonical engine input contract

### Does the proposed output make sense?

Yes, with one key adjustment:

- the user-facing output is valid
- it should be derived from a richer structured engine output

So Aervise should maintain two different outputs:

1. engine output contract
2. rendered response contract

---

## 5. Recommended Formal Contracts

These are the schema boundaries that should stay explicit:

1. `04_a_intent_schema.md`
2. `04_b_environment_schema.md`
3. `04_c_decision_input_schema.md`
4. `04_d_decision_output_schema.md`

These should become:

- backend contracts
- test fixtures
- API validation shapes
- observability payloads

---

## 6. MVP Lock-In

For MVP, Aervise should start with:

- rule-based or hybrid intent parsing
- OpenAQ plus one weather provider and fallback
- deterministic decision engine
- template-based message rendering
- full request and decision logging

For MVP, Aervise should not depend on:

- LLM message generation
- personalized health models
- AQ forecast
- open-ended simulations
