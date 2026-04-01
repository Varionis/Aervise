# **Decision Archetypes**

---

These define **what kind of decision the engine is solving**.

Think of them as **execution modes**.

---

## A. Immediate Decision (`NOW_CHECK`)

> “Can I do this right now?”
> 

**Characteristics:**

- Uses **current conditions only**
- Fast, deterministic
- No forecasting

**Examples:**

- Run now
- Walk dog now
- Open windows now

---

## B. Comparative Decision (`COMPARE_NOW_LATER`)

> “Is later better than now?”
> 

**Characteristics:**

- Uses **current + short-term forecast**
- Compares **2–3 time slots**
- Returns relative recommendation
- In the current MVP, candidate slots are ranked by the full deterministic score, not by temperature-only heuristics

---

## C. Optimization Decision (`BEST_TIME_TODAY`)

> “When is the best time today?”
> 

**Characteristics:**

- Scans **time windows (e.g., hourly)**
- Scores each window
- Returns ranked options
- In the current MVP, the ranking is still weather-led because AQ forecast is not available
- Location-relative comfort normalization is explicitly deferred to MVP 2

---

## D. Constraint Simulation (`WHAT_IF`)

> “What if I reduce duration / go later?”
> 

**Characteristics:**

- Adjusts **one variable**
- Keeps others constant
- Lightweight simulation
- For timing simulations, the current MVP chooses the best same-day candidate by full deterministic score
- Climate-relative “too cold / too hot for this place and season” modeling is deferred to MVP 2

---

## E. Binary Advisory (`SHOULD_AVOID`)

> “Should I avoid going outside?”
> 

**Characteristics:**

- No optimization
- Focus on **risk threshold breach**
- Strong yes/no tone

---

## F. Assumption-Based (`INDOOR_OUTDOOR`)

> “Stay inside or go out?”
> 

**Characteristics:**

- Requires **explicit assumptions**
- Lower confidence
- Must explain uncertainty
