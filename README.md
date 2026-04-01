# Aervise

Aervise is a deterministic environmental decision system that turns air quality and weather data into actionable recommendations for outdoor decisions.

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
- Timing guidance is weather-only
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
python -m unittest tests.pipeline.test_intent_parser tests.pipeline.test_layer1 tests.engine.test_layer2 tests.engine.test_layer3 tests.engine.test_layer4 tests.integration.test_api tests.integration.test_rendering
```

## Documentation

The source-of-truth schema and flow docs are:

- `docs/04_interaction_flow_contract.md`
- `docs/04_a_intent_schema.md`
- `docs/04_b_environment_schema.md`
- `docs/04_c_decision_input_schema.md`
- `docs/04_d_decision_output_schema.md`
