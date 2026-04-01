# Aervise Core User Flow Template

Note: the current MVP starts from Stage 0 raw message input, then Stage 1 intent recognition, then Stage 2 enrichment. Forecast-heavy flows in this document are target-state only until same-day AQ forecast exists.

This applies to *every* use case.

## Step-by-step flow

```
User Input
   ↓
Intent Parsing
   ↓
Context Enrichment (location, time, user profile)
   ↓
Environmental Data Fetch (AQ + weather + forecast)
   ↓
Exposure Modeling
   ↓
Decision Engine
   ↓
Response Generation (with reasoning + assumptions)
```

---

## Core Data Contract

### Input (from user)

```json
{
  "activity": "running",
  "duration_minutes": 45,
  "intensity": "high",
  "time_context": "now" | "later" | "specific_hour",
  "location": "lat/lon OR inferred",
  "user_profile": {
    "sensitivity": "normal | asthma | child | elderly",
    "preferences": {}
  }
}
```

---

### System Enriched Data

```json
{
  "timestamp": "current time",
  "hourly_forecast": [...],
  "current_conditions": {
    "AQI": 85,
    "PM2_5": 35,
    "temperature": 28,
    "humidity": 70,
    "wind_speed": 10
  }
}
```

---

### Output (standardized)

```json
{
  "decision": "yes | no | caution",
  "confidence": 0.82,
  "reasoning": [
    "Air quality is moderate",
    "High-intensity activity increases exposure"
  ],
  "risk_level": "low | medium | high",
  "recommendations": [
    "Reduce duration to 30 minutes",
    "Avoid peak traffic areas"
  ],
  "assumptions": [
    "User has no respiratory conditions"
  ],
  "alternatives": [
    "Consider indoor workout"
  ]
}
```

---

## User Flow Mapping by Category

### A. Exercise (High Value / Core Engine)

Example:
“Can I go for a run right now (45 min)?”

#### Flow

```
User → activity=run, duration=45, intensity=high
     → time=now
```

#### Additional Derived Variables

* breathing_rate_multiplier = HIGH ⚠️
* exposure_score = f(AQI × duration × intensity)

#### Required Data

* Real-time AQ (PM2.5 critical)
* Temperature (heat stress)
* Humidity (breathing discomfort)
* Wind (pollutant dispersion)

#### Decision Logic

```
IF AQI > threshold AND intensity=high
   → NO

IF AQI moderate
   → CAUTION (reduce duration)

ELSE → YES
```

#### Output Add-ons

* “High-intensity exercise increases pollutant intake by ~2–4x”
* Suggest duration reduction

---

### B. Short Exposure (High Frequency)

Example:
“Can I step out for 10 minutes?”

#### Flow Simpler

* intensity = LOW
* duration = SHORT

#### Key Insight

> Risk is mostly threshold-based, not cumulative

#### Decision Logic

```
IF AQI extremely high → NO
ELSE → YES
```

#### Data Priority

* Current AQ (no heavy need for forecast)

---

### C. Extended Exposure (Planning-heavy)

Example:
“Can I stay outside for 3 hours?”

#### Flow

```
duration = LONG
→ must use hourly forecast
```

#### Required Data

* Hourly AQ forecast
* Weather trend (heat, UV)

#### Derived

```
cumulative_exposure =
   Σ (AQI_hour × exposure_weight)
```

#### Decision Logic

* Weighted risk over time (not just current AQ)

#### Output

* “Conditions worsen after 2 PM”
* “Safe window: 9 AM – 11 AM”

---

### D. Commute (Optimization Layer)

Example:
“Should I bike to work?”

#### Flow

* route duration
* repeated exposure (daily pattern)

##### Additional Inputs (future scope)

* route AQ variation
* traffic pollution

#### Decision Logic

* Compare options:

```
bike vs drive vs transit
```

#### Output

* “Biking now exposes you to 2x pollution vs driving”
* “Delay by 1 hour for better conditions”

---

### E. Planning / Optimization

#### 1. Best Time Today

Example:
“When should I go?”

##### Flow

```
for each hour:
   compute risk_score(hour)

return best window
```

##### Output

```json
{
  "best_time": "7–9 AM",
  "why": "Lowest PM2.5 levels"
}
```

---

#### 2. Same-Day Comparison

Example:
“Is evening better than now?”

##### Flow

```
risk_now vs risk_later
→ compare delta
```

##### Output

* “Evening is 35% safer due to lower PM2.5”

---

### F. Simulation Layer (Differentiator)

#### 1. Duration Adjustment

Example:
📌 “What if I reduce time?”

##### Core Formula

```
exposure ∝ intensity × duration × AQ
```

##### Flow

```
simulate(duration=45)
simulate(duration=20)
compare
```

##### Output

* “45 min = high risk, 20 min = acceptable”

---

#### 2. Time Shift

📌 “What if I go later?”

##### Flow

```
simulate(now)
simulate(+2 hours)
compare
```
