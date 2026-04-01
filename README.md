# Aervise

Aervise is a deterministic environmental decision system that turns air quality and weather data into actionable recommendations for outdoor decisions.

This repository is public by design. Keep secrets, runtime logs, traces, and any user-identifiable data out of version control.

This project is an explainable MVP system and not a medical device or emergency-response service.

Instead of exposing raw PM2.5 or temperature alone, the system answers questions like:

- Can I go for a run right now?
- Is it okay to walk outside for 30 minutes?
- Should I modify the plan or avoid it for now?

## Current Architecture

```text
Stage 0: Entry Point
  ->
Stage 1: Intent Recognition
  ->
Stage 2: Context Enrichment
  ->
Stage 3: Decision Payload Builder
  ->
Deterministic Decision Core
  ->
Structured Decision Output
  ->
Rendered User Message
  ->
Logs and Traces
```

## What Exists Today

- FastAPI API and demo/debug UI
- Stage 0 and Stage 1 interaction pipeline from raw user message
- Stage 2 enrichment using OpenAQ plus weather provider fallback
- Stage 3 canonical decision input builder
- Deterministic decision core:
  - Feasibility evaluation
  - Layer 2 factor evaluation
  - Layer 3 policy mapping
  - Layer 4 explanation generation
- Typed contracts for:
  - intent
  - environment
  - decision input
  - decision output
- Rendering layer for stable user-facing messaging
- Route-level observability with structured logs and trace events

## Current Limits

- AQ forecast is not implemented
- `COMPARE_NOW_LATER` is real, but still weather-led
- `BEST_TIME_TODAY` is real, but still weather-led
- `WHAT_IF` is real for timing and duration simulations, but still same-day and weather-led
- stale saved fallback snapshots are now blocked for same-day planning and same-day recommendation flows instead of being treated like current conditions
- same-day timing modes now choose candidate windows by full deterministic score, not by raw temperature alone
- climate-relative comfort thresholds and location-season normalization are not implemented yet and remain MVP 2 scope
- Personalization is minimal
- The UI is an operator/debug surface, not a consumer product UI

## Implemented Structure

```text
aervise/
|-- interfaces/
|   `-- api/
|       |-- main.py
|       |-- routes/
|       |-- static/
|       `-- templates/
|-- pipeline/
|   |-- intent/
|   |-- enrichment/
|   |-- payload_builder/
|   `-- orchestrator.py
|-- core/
|   `-- layers/
|-- contracts/
|   |-- intent_schema.py
|   |-- environment_schema.py
|   |-- decision_input.py
|   `-- decision_output.py
|-- rendering/
|   |-- formatter.py
|   `-- templates.py
|-- observability/
|   |-- logger.py
|   |-- runtime.py
|   `-- trace_schema.py
|-- tests/
|   |-- engine/
|   |-- pipeline/
|   `-- integration/
|-- docs/
|-- logs/
|-- traces/
|-- .env.example
|-- requirements.txt
`-- README.md
```

## Run

```bash
uvicorn interfaces.api.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/
```

## Public Repo Hygiene

- real secrets must never be committed
- use `.env.example` for variable names only
- `logs/` and `traces/` are local runtime artifacts and are intentionally ignored
- see [SECURITY.md](/d:/Users/arnav/Documents/Github_Repos/Aervise/SECURITY.md#L1) for reporting and operational guidance

## Main API Paths

- `POST /interaction/preview`
- `POST /interaction/enrichment-preview`
- `POST /interaction/enrich`
- `POST /interaction/build-payload`
- `POST /decision/evaluate`
- `POST /decision/render`
- `POST /decision/evaluate-rendered`
- `POST /decision/debug/layers`

## Validation

Current verified test pass:

```bash
python -m unittest tests.pipeline.test_window_selector tests.pipeline.test_intent_parser tests.pipeline.test_layer1 tests.engine.test_feasibility tests.engine.test_layer2 tests.engine.test_layer3 tests.engine.test_layer4 tests.integration.test_api tests.integration.test_rendering tests.integration.test_compare_mode tests.integration.test_best_time_mode tests.integration.test_what_if_mode
```

## Documentation

The source-of-truth schema and flow docs are:

- `docs/05_interaction_flow_contract.md`
- `docs/06_intent_schema.md`
- `docs/07_environment_schema.md`
- `docs/08_decision_input_schema.md`
- `docs/09_decision_output_schema.md`
