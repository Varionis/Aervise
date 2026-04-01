# Policy Rules

This is the **heart of the engine**.

We split into 4 layers:

---

## A. Hard Safety Rules (Non-negotiable)

```yaml
- condition: pm25 > 150 AND activity_intensity = high
  action: BLOCK
  reason: "Air pollution too high for intense activity"

- condition: temperature > 38
  action: BLOCK
  reason: "Extreme heat risk"

- condition: aqi > 200
  action: STRONGLY_AVOID
```

---

## B. Factor Scoring

Each factor produces a **burden score (0–1)**

### 1. Air Burden

- Based on:
    - PM2.5
    - O3
    - duration
    - intensity

---

### 2. Heat Burden

- Temperature + humidity (feels-like)
- Duration-weighted

---

### 3. Exposure Burden

- Duration × intensity × pollutant load

---

### 4. Disruption Factor

- Rain
- Wind
- UV

---

### 5. Confidence Penalty

- Low data confidence
- Missing pollutants
- Sparse station coverage

---

## C. Weighted Decision Score

```
total_risk_score =
    w1 * air_burden +
    w2 * heat_burden +
    w3 * exposure_burden +
    w4 * disruption +
    w5 * confidence_penalty
```

---

## D. Decision Mapping

```yaml
0.0 – 0.3 → GOOD
0.3 – 0.6 → MODERATE
0.6 – 0.8 → CAUTION
0.8 – 1.0 → AVOID
```

---

## E. Override Logic

Even if score is moderate:

```yaml
IF (pm25 > 100 AND duration > 60):
    escalate → CAUTION

IF (high_intensity AND heat_index > 35):
    escalate → CAUTION

IF (sensitive_user AND AQI > 80):
    escalate → AVOID
```

---

## F. Timing Mode Ranking (Current MVP)

For timing-oriented modes:

- `COMPARE_NOW_LATER`
- `BEST_TIME_TODAY`
- `WHAT_IF` with timing adjustment

candidate forecast windows should be ranked by the full deterministic score for that simulated window, not by a single raw weather field such as temperature.

That means current MVP ranking already reflects:

- heat burden
- wind disruption
- confidence penalty
- duration and intensity effects

This is still weather-led today because AQ forecast is not available.

---

## G. MVP 2 Scope

The following is intentionally deferred:

- climate-relative comfort thresholds by location and season
- “unusually hot for Toronto in April” style normalization
- activity-specific comfort targets derived from local climate history

Those enhancements should modify how weather burden is normalized, but they should not replace the deterministic score-based ranking structure.
