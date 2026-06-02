# NHL Hockey Predictions — Model Suggested Enhancements

## Priority 1: xG Model (Target: MAE < 1.2)

### Analytics-Blend Calibration
- Current blend: 50% legacy Poisson / 50% NHL analytics xG. Backtest to find the optimal weight (try 30/70, 40/60, 60/40).
- Run season-by-season MAE comparison across blend ratios.

### Corsi and Fenwick Integration
- Add `cf_pct` (Corsi For %) and `ff_pct` (Fenwick For %) as features from `get_team_analytics()`.
- These possession proxies are proven predictors of sustainable team quality.

### Score State Adjustment
- Teams trailing by 2+ goals play more aggressively; this inflates their shot metrics late in games.
- Use `close_game_cf_pct` (only score within 1 goal) for a less biased possession measure.

## Priority 2: Goalie Model

### GSAA Normalisation
- Current `calculate_goalie_adjustment_with_analytics()` uses raw GSAA. Normalise by games played so partial-season starters are comparable.

### High-Danger Save %
- `hd_save_pct` is already integrated. Increase its weight from 30% to 40%: it's the most predictive single goalie metric.

### Backup Flag
- When a goalie is a confirmed backup starter (starter news), add a `goalie_is_backup` binary flag that applies a fixed probability penalty.

## Priority 3: New Features

### Power Play / Penalty Kill
- `pp_pct` and `pk_pct` from NHL analytics. Teams with top-5 PP and bottom-5 PK show significant scoring margin differences.

### Back-to-Back Fatigue
- Second night of a back-to-back shows roughly a 3–5% win rate decline in historical data. Add `is_b2b_home` and `is_b2b_away` flags.

### Momentum Score
- Rolling 5-game points percentage: `(pts_last_5 / 10)`. Simple but captures hot/cold streaks.

## Priority 4: Calibration

- Add calibration curve to Model Performance page.
- Apply isotonic regression to win probability outputs.
- Track Brier score monthly through the season.
