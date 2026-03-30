# Aervise — Environmental Decision Engine

> **“Can I do this right now?” — answered intelligently.**

Aervise is an AI-powered decision system that transforms environmental data (air quality, weather, exposure) into **actionable, real-time recommendations**.

Instead of showing raw metrics like AQI or temperature, Aervise answers real user questions:

* “Can I go for a run right now?”
* “Is it safe to walk outside for 30 minutes?”
* “Should I wait until evening?”

---

## Core Idea

Most systems provide **data**.

Aervise provides **decisions**.

It combines:

* Air quality (PM2.5, NO2, O3, etc.)
* Weather (temperature, humidity, heat index)
* Duration of activity
* Activity intensity

…into a **decision engine** that outputs:

- Recommendation
- Risk level
- Reasoning

---

## System Architecture (Planned)

```
User Intent → Decision Engine → Output

Where Decision Engine =
    Environmental Data
  + Exposure Modeling
  + Policy Rules
  + Risk Scoring
```

### Layers

1. **Input Layer**

   * Activity (run, walk, etc.)
   * Duration
   * Time (now / later)

2. **Data Layer**

   * Air quality APIs
   * Weather APIs

3. **Factor Evaluation Layer**

   * Air burden calculation
   * Heat index modeling
   * Duration weighting
   * Intensity multipliers

4. **Decision Engine**

   * Risk scoring
   * Policy rules
   * Threshold logic

5. **Output Layer**

   * Decision (Go / Caution / Avoid)
   * Explanation
   * Assumptions

---

## Use Cases

### Real-Time Decisions

* “Can I go for a run now?”
* “Is it safe to walk outside?”

### Controlled Decisions

* “Should I stay indoors or go out?”

### Planning

* “What’s the best time today to go out?”
* “Is evening better than now?”

### Simulation (What-if)

* “What if I go later?”
* “Can I reduce duration and go?”

---

## MVP Scope

### Included

* Real-time decision engine
* Air quality + weather integration
* Basic risk scoring
* Reasoned outputs

### Not Included (Yet)

* Long-term forecasting
* Personalized health profiles
* Indoor air modeling
* Wearable integrations

---

## Tech Stack (Planned)

* **Backend:** Python (FastAPI)
* **Data Processing:** Pandas / NumPy
* **Decision Engine:** Custom logic + scoring system
* **APIs:** Air quality + weather providers
* **Deployment:** TBD (Azure / AWS)

---

## Project Structure

```
aervise/
│
├── interfaces/                 # Entry points (NOT core)
│   ├── api/
│   ├── chat/
│   ├── cli/
│   └── test_harness/
│
├── pipeline/                   # Orchestration layer
│   ├── intent/
│   │   ├── parser.py
│   │   ├── schemas.py
│   │
│   ├── enrichment/
│   │   ├── air_provider.py
│   │   ├── weather_provider.py
│   │   ├── normalization.py
│   │
│   ├── payload_builder/
│   │   ├── builder.py
│   │   ├── validators.py
│   │
│   └── orchestrator.py         # end-to-end flow
│
├── core/                       # 🔥 PURE DECISION ENGINE ONLY
│   ├── layers/
│   │   ├── layer1_intent_env.py
│   │   ├── layer2_factor_eval.py
│   │   ├── layer3_policy.py
│   │   ├── layer4_explanation.py
│   │
│   ├── models/
│   │   ├── risk_models.py
│   │   ├── exposure_models.py
│   │
│   ├── policies/
│   │   ├── thresholds.py
│   │   ├── rules.py
│   │
│   └── engine.py               # main deterministic engine entry
│
├── contracts/                  # 🔥 SCHEMAS (VERY IMPORTANT)
│   ├── intent_schema.py
│   ├── environment_schema.py
│   ├── decision_input.py
│   ├── decision_output.py
│
├── rendering/                  # Output → user message
│   ├── templates.py
│   ├── formatter.py
│
├── observability/
│   ├── logger.py
│   ├── trace_schema.py
│
|── tests/
|   ├── engine/
|   ├── pipeline/
|   └── integration/
├── docs/
│
├── .env.example
├── requirements.txt
└── README.md
```

---

## Design Principles
- Separation of concerns → API vs logic vs data
- Pure core logic → decision engine is testable + reusable
- Service orchestration → scalable workflows
- Future-ready → can evolve into microservices

---

## Evolution Path

| Phase | Architecture |
| ----- | ------------ |
| Phase 1 |	Modular monolith (current) |
| Phase 2 |	Extract services (env / decision) |
| Phase 3 |	Mobile app (iOS + Android) |

---

## Current Status

> Early Stage — System Design Phase

* [x] Use cases defined
* [x] User flows mapped
* [ ] Decision engine design
* [ ] Factor modeling
* [ ] API integration
* [ ] MVP build

---

## Vision

Aervise is not just a project — it’s a step toward:

> **Decision Intelligence Systems**
> where AI answers *“Should I?”*, not just *“What is?”*

---

## Contributing

Currently a solo build, but open to:

* Feedback
* Architecture suggestions
* Collaboration ideas

---

## Contact

**Arnav Ajay**
Toronto, Canada
[LinkedIn](https://linkedin.com/in/arnav-ajay)
[GitHub](https://github.com/Arnav-Ajay)

---

## ⭐ If you like this project

Give it a star ⭐ — it helps a lot!

---