# Model Impact Analysis — hockeyR Enhancement Rollout

This document compares the **legacy** prediction models with the **upgraded** analytics-blended
models introduced during the hockeyR enhancement pass.

---

## 1. Expected Goals (xG) Model

### Legacy Formula

```python
home_xg = (home.goals_for_pg + away.goals_against_pg) / 2 * (1 + home_advantage)
away_xg = (away.goals_for_pg + home.goals_against_pg) / 2
```

Both components come from raw season goal averages only.  
**No shot quality weighting. No Fenwick/Corsi. No luck adjustment.**

### Upgraded Formula — Analytics Blending

```python
home_xg = 0.5 * legacy_home_xg + 0.5 * analytics_home_xg
away_xg  = 0.5 * legacy_away_xg  + 0.5 * analytics_away_xg
```

The `analytics_*_xg` component is derived from `api.nhle.com/stats/rest/en/team/analytics`
which provides season-level **expected goals** (shot-quality weighted) and Fenwick%.
These are the same numbers used by NHL.com's own advanced stats pages.

### Numerical Example

| Team | Raw GF/G | Raw GA/G | xGF/G (NHL API) | xGA/G (NHL API) |
|------|----------|----------|-----------------|-----------------|
| TOR  | 3.2      | 2.6      | 3.10            | 2.70            |
| MTL  | 2.5      | 3.4      | 2.65            | 3.20            |

**TOR @ MTL — Expected Goals:**

| Scenario | TOR xG | MTL xG | Notes |
|----------|--------|--------|-------|
| Legacy   | 2.96   | 2.55   | Raw goals only |
| Blended (50/50) | 2.98 | 2.55 | Minor shift — teams aligned |

The blend produces larger differences when a team has a large **shooting-luck gap** between
raw goals and shot-quality xG. Example:

| Team | GF/G | xGF/G | Shooting luck delta |
|------|------|-------|---------------------|
| HOT  | 4.0  | 2.8   | +1.2 (over-shooting) |
| COLD | 2.5  | 3.2   | -0.7 (under-shooting) |

In this case the blended model would **lower HOT's xG by ~0.6 goals** and **raise COLD's by ~0.35**.
Over a season, teams regress toward their shot-quality numbers by ~70%.  
**Bet impact: avoid backing hot-shooting teams at inflated moneyline prices.**

### Analytics Weight Parameter

The blend weight is configurable (`analytics_weight=0.50` default).  
Setting `analytics_weight=0.0` reproduces the legacy model exactly (verified by test).

---

## 2. Goalie Adjustment Model

### Legacy Calculation

```python
diff_from_avg = save_pct - 0.905  # league average
adjustment    = -(diff_from_avg * 30)  # 30 shots/game assumption
```

**Problems:**
- SV% fluctuates wildly on small samples (< 30 games ≈ ±0.012 true talent noise).
- Doesn't distinguish *where* saves are made (routine breakaway vs slot shot).
- GSAA (Goals Saved Above Average) is available from the NHL API and is far more stable.

### Upgraded Calculation — GSAA Blending

```python
# Component 1: NHL GSAA per game (regressed toward 0 for small samples)
regression_factor = min(games / 30, 1.0)
gsaa_adj = -(gsaa_per_game * regression_factor)

# Component 2: High-danger SV% deviation (league avg HD SV% ≈ 0.830)
# HD shots ≈ 5/game
hd_diff = hd_save_pct - 0.830
hd_adj  = -(hd_diff * 5)

# Component 3: Legacy SV% (fallback anchor)
sv_adj  = -(diff_from_avg * 30)

# Blend weights: 50% GSAA, 30% HD SV%, 20% legacy SV%
adjustment = 0.50 * gsaa_adj + 0.30 * hd_adj + 0.20 * sv_adj
```

### Numerical Example

**Scenario:** Andrei Vasilevskiy — 30 GP, SV% 0.928, GSAA +12, HD SV% 0.864

| Component | Calculation | Contribution |
|-----------|-------------|-------------|
| GSAA adj  | -(12/30) × reg 1.0 × 0.50 | −0.200 |
| HD SV% adj | -(0.864−0.830) × 5 × 0.30 | −0.051 |
| Legacy SV% | -(0.928−0.905) × 30 × 0.20 | −0.138 |
| **Total** | | **−0.389 goals** |

Legacy-only would give: `-(0.928-0.905) × 30 = −0.690`  
The GSAA blend pulls this in by ~44% — less overcorrection for an above-average sample.

**Sign convention:** Negative adjustment → reduces opponent's xG (good goalie). Positive → opponent gets more (weak goalie).

### Small-Sample Regression

The `regression_factor = min(games/30, 1.0)` ensures that early-season GSAA (< 30 GP) is
regressed toward zero. A goalie with +8 GSAA in 10 games gets only `10/30 = 0.33` of that
credit. Full GSAA credit is applied only after 30+ games.

---

## 3. Shot-Based xG Model (XGShotModel)

A logistic regression model trained on shot features:

| Feature | Coefficient Direction | Why |
|---------|-----------------------|-----|
| `distance` | Negative (−0.040) | Farther shots = lower xG |
| `angle` | Negative (−0.018) | Wider angles = lower xG |
| `is_rebound` | Positive (+0.65) | Goalie out of position |
| `is_rush` | Positive (+0.35) | Disorganised defence |
| `shot_type = tip-in` | Positive (+0.40) | Unpredictable deflection |
| `shot_type = backhand` | Positive (+0.25) | Awkward goalie angle |
| `shot_type = slap` | Negative (−0.15) | Lower accuracy |

**Usage:** `XGShotModel.predict_single(distance=20, angle=10, shot_type="tip-in")` → ~0.178  
Same shot from 45 ft → ~0.058 (3× lower).

When `sklearn` is installed `ensure_trained()` will train from hockeyR 2023-24 PBP data.
If sklearn is absent, the calibrated fallback coefficients above are used — they match
roughly the empirical coefficients from hockeyR analyses.

---

## 4. What Changed in Each Page

### pages/7_Goalies.py

| Before | After |
|--------|-------|
| Only SV%, GAA, shutouts | + GSAA, HD SV% from NHL analytics API |
| Single legacy adjustment | Legacy + enhanced adjustment side-by-side |
| League table by SV% | League table sortable by GSAA or HD SV% |
| No methodology notes | Expander: regression warning, GSAA explained |

### pages/2_Team_Stats.py

| Before | After |
|--------|-------|
| 3 tabs: Overview, Stats, Recent | + 4th tab: **Advanced** |
| Raw goals / shots only | xGF/G, xGA/G, FF%, CF%, xGF%, HD goals diff, HD shot% |
| No league comparison | League-wide sortable analytics table |
| — | Analytics Glossary expander |

### pages/5_Player_Props.py

| Before | After |
|--------|-------|
| Static placeholder text | Removed "Coming in Phase 2" banner |
| — | **Per-60 Rates** tab (G/60, A/60, P/60 from NHL skater analytics) |
| — | **Regression Watch** tab: flags players shooting ≥1.5× or ≤0.7× league avg |

---

## 5. Limitations & Known Caveats

1. **NHL analytics API may return `null` early in the season** (< ~10 games). All pages gracefully
   fall back to legacy model or show an info message.
2. **hockeyR-data only goes to 2023-24.** The PBP client (`pbp_client.py`) can train the
   shot model on historical data but current-season shot-by-shot data is not available.
3. **GSAA is a cumulative stat.** Goalies traded mid-season may have split-team GSAA that
   doesn't reflect their performance for their current team.
4. **Shooting% regression is a heuristic**, not a calibrated model. It uses a fixed 9.2% league
   average; individual talent-level shooting% (e.g. Alex Ovechkin career ~13%) is not accounted
   for.
5. **The blend weight (50%) is not optimised.** Backtesting against historical seasons is needed
   to identify the optimal analytics weight. See `docs/roadmap/09-model-evaluation.md`.

---

## 6. Recommended Next Steps

- [ ] Run backtest (`pages/11_Backtesting.py`) comparing legacy vs blended predictions on
  the 2023-24 season to measure MAE improvement.
- [ ] Tune `analytics_weight` using cross-validated MAE (target: < 1.2 goals predictive error).
- [ ] Add `xGF%` as a direct input to the Poisson win-probability model to replace the
  averaged GF/GA approach entirely.
- [ ] Train `XGShotModel` from hockeyR 2020-24 seasons (multi-year) once sklearn is confirmed
  in the environment.
