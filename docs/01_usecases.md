# Aervise Usecases

## A. Outdoor Decisions (CORE)

### 1. Exercise (Moderate–High Intensity)

**Goal:** Elevated breathing → higher pollutant intake → higher risk sensitivity

1. Can I go for a run right now (45 min)?
2. Is it safe to do an outdoor HIIT workout for 30 minutes?
3. Can I play a full soccer match (~60–90 min)?
4. Is it okay to go cycling at high intensity for an hour?
5. Can I do hill sprints outside today?
6. Should I go for a long-distance run (10K+) right now?
7. Is it safe to train for a marathon outdoors today?
8. Can I do outdoor CrossFit training for 45 minutes?
9. Should I play basketball outside for an hour?
10. Can I go rollerblading at a fast pace for 40 minutes?

**Insight:**

These are the **highest-risk scenarios** → strongest need for Aervise decision engine.

---

### 2. Short Exposure

**Goal:** Low duration → lower risk, but still situational (AQ spikes, weather extremes)

1. Is it okay to walk outside for 15 minutes?
2. Can I step out to grab coffee nearby (10–15 min)?
3. Is it safe to take a short walk after dinner (~20 min)?
4. Can I walk my dog quickly around the block?
5. Is it okay to step outside for a quick phone call?
6. Can I wait outside for an Uber for 10 minutes?
7. Is it safe to walk to the grocery store nearby?
8. Can I go outside to get some fresh air briefly?
9. Is it okay to drop off mail at the mailbox?
10. Can I stand outside for 15 minutes during a break?

**Insight:**

These are **high-frequency, low-friction queries** → ideal for daily engagement + notifications.

---

### 3. Extended Exposure

**Goal:** Long duration → cumulative exposure risk → weather + AQ both matter heavily

1. Can I stay outside for 2–3 hours?
2. Is it safe to spend the afternoon at a park?
3. Can I attend an outdoor festival today (3–5 hours)?
4. Is it okay to go hiking for a few hours?
5. Can I spend the day at the beach?
6. Is it safe to do yard work for 2–4 hours?
7. Can I take my kids to play outside for the afternoon?
8. Is it okay to go fishing for several hours?
9. Can I work remotely from a patio today?
10. Is it safe to go sightseeing outdoors for half a day?

**Insight:**

These are **planning-heavy decisions** → strong opportunity for **forecast + simulation layer**.

---

### 4. Commute (Routine)

**Goal:** Repeated daily exposure → optimization + habit formation

1. Should I bike to work (~30 min)?
2. Is it safe to walk to work today (~25 min)?
3. Should I take public transit or avoid it due to air quality?
4. Can I scooter to work this morning?
5. Is it okay to jog to work today?
6. Should I drive instead of biking due to conditions?
7. Can I take my usual walking route to work?
8. Is it safe to cycle during rush hour today?
9. Should I delay my commute due to poor conditions?
10. Is it okay to take a longer scenic route today?

**Insight:**

These unlock **habit loops + personalization** → Aervise becomes a **daily decision assistant**, not a one-time tool.

---

## B. Planning / Optimization

### 5. Best Time Today

1. What’s the best time to go for a run today?
2. When is air quality safest for outdoor exercise today?
3. What time should I walk my dog today?
4. When should I go cycling to avoid poor air quality?
5. What’s the best window to be outside today?
6. When is it safest to take kids to the park?
7. What time is best for outdoor workouts today?
8. When should I plan my outdoor errands?
9. What’s the least risky time to be outside today?
10. When is pollution expected to be lowest today?

**What this requires:**

- Hourly forecast (AQ + weather)
- Ranking/scoring system

---

### 6. Same-Day Comparison

1. Is evening better than now?
2. Will conditions improve later today?
3. Is it safer to go out in the morning or afternoon?
4. Should I go now or wait until later?
5. Is air quality expected to worsen this evening?
6. Is it better to run now or tonight?
7. Will it be safer after sunset?
8. Is afternoon worse than early morning today?
9. Should I delay my outdoor plans?
10. Is it better to go out before or after rush hour?

**Product Shift:**

- From **single decision → comparative reasoning**
- Requires:
    - delta analysis
    - explanation (“because PM2.5 drops by X%”)

---

##  C. Simulation (BOUNDED)

### 7. Duration Adjustment

1. Can I go if I reduce my time?
2. Is it safe if I only stay outside for 20 minutes instead of an hour?
3. Can I still go for a run if I shorten it?
4. Is a quick workout safer than a long one right now?
5. Can I limit exposure and still go outside?
6. Would reducing my walk duration make it safe?
7. Is 15 minutes okay even if 45 minutes isn’t?
8. Can I step out briefly instead of staying long?
9. Is partial outdoor activity safe today?
10. Can I split my time into shorter sessions?

**Core logic:**

- Exposure = **intensity × duration**
- This is your first **quantitative reasoning layer**

---

### 8. Time Shift (What-if lite)

1. What if I go later?
2. Will it be safer in a few hours?
3. Should I wait before going outside?
4. What happens if I delay my run by 2 hours?
5. Will conditions improve if I go in the evening?
6. Is it better to wait until tonight?
7. What if I go early morning instead?
8. Should I postpone my outdoor activity?
9. Will air quality drop later today?
10. Is it worth waiting before stepping out?

**Important Constraint (as you noted):**

- Same-day only
- No multi-day forecasting
- No complex simulations

---

## What This Gives (Product Insight)

**8 strong intent clusters**:

| Category | Frequency | Risk | Product Value |
| --- | --- | --- | --- |
| Exercise | Medium | High | Core differentiation (high-stakes decisions) |
| Short Exposure | Very High | Low–Medium | Daily engagement + notifications |
| Extended Exposure | Medium | High | Planning + forecast-driven decisions |
| Commute | Very High | Medium | Retention + habit formation + personalization |
| Best Time Today | Medium | Medium–High | Optimization layer (forecast → ranked recommendations) |
| Same-Day Comparison | Medium | Medium | Comparative intelligence (delta-based reasoning) |
| Duration Adjustment | Low–Medium | Medium | Quantitative reasoning (exposure control) |
| Time Shift | Medium | Medium | What-if intelligence (temporal decision support) |

### Insight

These are **not just user queries** — they define the **latent decision model your system must infer and compute.**

Each category introduces a **distinct reasoning requirement:**

#### 1. Exposure Modeling

- intensity (breathing rate proxy)
- duration (cumulative exposure)
- activity type (exercise vs passive)

#### 2. Temporal Intelligence

- current vs future conditions
- intra-day variation (rush hour, weather shifts)
- forecast confidence

#### 3. Comparative Reasoning

- “now vs later”
- “short vs long duration”
- “option A vs option B”

#### 4. Constraint Handling

- same-day limits (no long-range forecasting)
- bounded simulation (no open-ended what-if trees)
- assumption handling (indoor air unknown)

#### 5. Personalization (Future Layer)

- sensitivity (e.g., asthma, fitness level)
- routine patterns (commute, habits)

---

### Specific capability layer

| Capability | Triggered By |
| --- | --- |
| Risk Scoring | Exercise, Extended Exposure |
| Engagement Loop | Short Exposure, Commute |
| Forecast Optimization | Best Time, Comparison |
| Simulation Engine | Duration, Time Shift |
| Trust Layer | Indoor vs Outdoor (assumptions) |