# NHL Hockey Predictions — Next 5 Features to Implement

> **Based on:** Codebase gap analysis as of July 2025

---

## Feature 1: Best Bets JSON Export for Sports-Picks-Grid

**Why:** `hockey-predictions` is listed in the sports-picks-grid aggregator's REPOS mapping, but the `data_files/best_bets_today.json` file needs to be written consistently with the unified schema. The value finder model already computes edges — this is a packaging step.

**How:**
1. Add `scripts/export_best_bets.py` that reads today's value bets from the Value Finder page
2. Filter to bets with edge ≥ 2% (Strong tier and above)
3. Write `data_files/best_bets_today.json` per the unified schema (`meta` + `bets` array with game_date, game, bet_type, pick, confidence, edge, odds, tier)
4. Add this export step to GitHub Actions nightly pipeline
5. Validate schema against sports-picks-grid `docs/02-unified-schema.md`

**Complexity:** Low

---

## Feature 2: Power Play / Penalty Kill Rate Features

**Why:** PP% and PK% are highly predictive advanced stats for NHL game outcomes. They are available in `api.nhle.com/stats/rest` team stats and can be computed from the same endpoint as xGF/xGA. These features would add meaningful signal beyond the current 50/50 Elo blend.

**How:**
1. Extend `NHLClient` in `src/api/nhl_client.py` to fetch `powerPlayPct` and `penaltyKillPct` per team per season
2. Add `home_pp_pct`, `away_pp_pct`, `home_pk_pct`, `away_pk_pct` as features in `src/models/expected_goals.py`
3. The analytics-blended path in `calculate_expected_goals_with_analytics()` should incorporate PP/PK advantage
4. Display PP and PK rates on each game card in `pages/1_Todays_Games.py`

**Complexity:** Low

---

## Feature 3: Goalie Starts Confirmation Feed

**Why:** Goalie starts are announced ~1.5 hours before puck drop. The current model uses season aggregate goalie stats but does not know which goalie is actually starting tonight. An uncertain goalie start is one of the biggest model blind spots.

**How:**
1. Add `auto_fetch_games.py` (the file already exists in the repo) or extend it to pull starting goalie from the NHL edge API (`api-web.nhle.com/v1/gamecenter/{gameId}/boxscore`) once rosters are released
2. If starting goalie differs from team's #1 goalie (backup starting), apply an adjustment factor using the backup's GSAA from `get_goalie_analytics()`
3. Display a "✅ Confirmed" or "⚠ TBD" badge on each game card

**Complexity:** Medium

---

## Feature 4: Puck Line Probability Model

**Why:** The current model outputs win probability (moneyline) but does not have a dedicated puck-line (+1.5 / -1.5) model. The puck line model needs to estimate the probability of winning by 2+ goals (favorite) or losing by ≤1 goal (underdog). This requires a goal-differential distribution, which Poisson provides.

**How:**
1. In `src/models/expected_goals.py`, compute a Poisson distribution for each team's expected goals
2. From the distribution, compute: `P(home wins by 2+)` and `P(away covers +1.5)`
3. Display puck line probabilities alongside moneyline on `pages/4_Value_Finder.py`
4. Add to `best_bets_today.json` export as `bet_type: "puck_line"`

**Complexity:** Medium

---

## Feature 5: Backtesting Page (ATS and ML Historical Accuracy)

**Why:** `pages/11_Backtesting.py` exists but may be incomplete. A walk-forward historical backtest of model predictions vs actual outcomes would prove (or disprove) the model's edge and identify in which game contexts it outperforms the market.

**How:**
1. Load historical game results from `api-web.nhle.com/v1/schedule/` for past seasons
2. Re-run the xG model for each historical matchup using the corresponding season's team analytics
3. Compute: predicted win% vs actual win% per confidence bucket (0–55%, 55–65%, 65%+)
4. Display calibration chart + ATS ROI by confidence tier
5. Segment analysis: home vs away, back-to-back games, post-shutout, etc.

**Complexity:** High
