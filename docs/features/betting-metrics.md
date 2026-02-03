# Betting Metrics Reference

## Overview
Key statistics and metrics for NHL sports betting analysis, focused on **moneyline** and **puck line** betting.

---

## Moneyline Betting

### What It Is
Pick the winner. No spread, just who wins (regulation, OT, or shootout).

### Core Metrics

| Metric | Description | Betting Use |
|--------|-------------|-------------|
| **Goal Differential** | Goals For - Goals Against | Overall team strength indicator |
| **Goals Per Game (GF/G)** | Average goals scored | Offensive capability |
| **Goals Against Per Game (GA/G)** | Average goals allowed | Defensive capability |
| **Recent Form (L10)** | Last 10 game record | Current momentum |
| **Home/Away Splits** | Performance by venue | Home advantage sizing |
| **OT Record** | Overtime win percentage | Tight game predictor |
| **1-Goal Game Record** | Performance in close games | Clutch factor |

### Expected Goals (xG)
Expected goals provides a more predictive measure than actual goals.

```python
def calculate_xg(
    team_gf_pg: float,      # Team's goals for per game
    opp_ga_pg: float,       # Opponent's goals against per game
    league_avg: float = 3.0  # League average goals per game
) -> float:
    """
    Calculate expected goals for a team.
    
    Formula: (Team_GF + Opp_GA) / 2
    Adjusted by league average and home/away factor
    """
    raw_xg = (team_gf_pg + opp_ga_pg) / 2
    return raw_xg
```

### Win Probability
Use Poisson distribution for game outcome probabilities.

```python
import math

def poisson_win_prob(home_xg: float, away_xg: float) -> dict:
    """Calculate win probabilities using Poisson model."""
    home_win = 0.0
    away_win = 0.0
    tie = 0.0
    
    for h in range(10):
        for a in range(10):
            prob = (
                (math.exp(-home_xg) * home_xg**h / math.factorial(h)) *
                (math.exp(-away_xg) * away_xg**a / math.factorial(a))
            )
            if h > a:
                home_win += prob
            elif a > h:
                away_win += prob
            else:
                tie += prob
    
    # OT adjustment (roughly 52% home win in OT)
    home_ot_win = tie * 0.52
    away_ot_win = tie * 0.48
    
    return {
        "home_win": home_win + home_ot_win,
        "away_win": away_win + away_ot_win,
        "overtime_prob": tie
    }
```

---

## Puck Line Betting (-1.5 / +1.5)

### What It Is
The NHL's point spread. Favorite must win by 2+ goals (-1.5), underdog can lose by 1 or win (+1.5).

### Why Puck Line Matters
- **Better odds on favorites**: -1.5 on heavy favorites often +120 to +160
- **Underdog value**: +1.5 on underdogs protects against 1-goal losses
- **~30% of NHL games** decided by exactly 1 goal

### Key Metrics for Puck Line
| Metric | Description | Why It Matters |
|--------|-------------|----------------|
| **Win Margin Distribution** | How often team wins by 2+ | Core puck line predictor |
| **Empty Net Goals** | ENGs per game when leading | Inflates margins |
| **3rd Period Scoring** | Goals in final period | Late blowout indicator |
| **Opponent Penalty Rate** | Penalties taken | PP goals pad leads |

### Puck Line Prediction Model
```python
def predict_puck_line_cover(
    home_xg: float,
    away_xg: float,
    home_margin_history: list,  # List of win margins
    away_margin_history: list
) -> dict:
    """
    Predict puck line outcomes.
    
    Returns probability of each puck line outcome.
    """
    import math
    
    # Method 1: Poisson-based
    home_cover = 0.0  # Home -1.5
    away_cover = 0.0  # Away +1.5 (home wins by 0-1 or loses)
    
    for h in range(10):
        for a in range(10):
            prob = (
                (math.exp(-home_xg) * home_xg**h / math.factorial(h)) *
                (math.exp(-away_xg) * away_xg**a / math.factorial(a))
            )
            margin = h - a
            
            if margin >= 2:
                home_cover += prob
            else:  # margin <= 1 (includes ties going to OT)
                away_cover += prob
    
    # Method 2: Historical margin adjustment
    if home_margin_history:
        hist_cover_rate = sum(1 for m in home_margin_history if m >= 2) / len(home_margin_history)
        # Blend with Poisson (60% Poisson, 40% historical)
        home_cover = 0.6 * home_cover + 0.4 * hist_cover_rate
    
    return {
        "home_minus_1_5": round(home_cover, 4),
        "away_plus_1_5": round(away_cover, 4),
        "expected_margin": round(home_xg - away_xg, 2)
    }
```

### Spread Coverage Analysis
```python
def analyze_spread_history(games_df) -> dict:
    """Analyze historical puck line coverage."""
    results = {
        "games": len(games_df),
        "cover_minus_1_5": 0,  # Won by 2+
        "push_minus_1_5": 0,   # Won by exactly 1 (push on some books)
        "fail_minus_1_5": 0,   # Won by 1 or less / lost
    }
    
    for _, game in games_df.iterrows():
        margin = game["team_score"] - game["opponent_score"]
        
        if margin >= 2:
            results["cover_minus_1_5"] += 1
        elif margin == 1:
            results["push_minus_1_5"] += 1
        else:
            results["fail_minus_1_5"] += 1
    
    results["cover_rate"] = results["cover_minus_1_5"] / results["games"]
    return results
```

### When to Bet Puck Line
| Scenario | Bet | Rationale |
|----------|-----|-----------|
| Heavy favorite (-200+) vs weak team | Favorite -1.5 | Better value than ML |
| Good team on B2B as underdog | Underdog +1.5 | Insurance on tired legs |
| High-scoring matchup | Favorite -1.5 | More goals = more margin |
| Defensive battle | Underdog +1.5 | Low scores = tight margins |

---

## Total Goals (Over/Under)

### Factors Affecting Totals
| Factor | Effect on Total |
|--------|-----------------|
| Goalie matchup | Elite goalies = lower total |
| Back-to-back | Tired teams = varied |
| Pace of play | High shot teams = higher total |
| Special teams | Strong PP = higher total |

### Total Goals Model
```python
def predict_total(home_xg: float, away_xg: float, line: float = 6.0) -> dict:
    """Predict over/under probabilities."""
    import math
    
    total_xg = home_xg + away_xg
    
    # Cumulative Poisson for under
    under_prob = 0.0
    for goals in range(int(line)):
        prob = (math.exp(-total_xg) * total_xg**goals) / math.factorial(goals)
        under_prob += prob
    
    # Handle exact line (push)
    if line == int(line):
        push_prob = (math.exp(-total_xg) * total_xg**int(line)) / math.factorial(int(line))
    else:
        push_prob = 0.0
    
    over_prob = 1 - under_prob - push_prob
    
    return {
        "expected_total": round(total_xg, 2),
        "over_prob": round(over_prob, 4),
        "under_prob": round(under_prob, 4),
        "push_prob": round(push_prob, 4)
    }
```

---

## Player Props

### Goals Props
| Metric | Description |
|--------|-------------|
| Goals Per Game | Player's scoring rate |
| Shots Per Game | Volume indicator |
| Shooting % | Conversion rate |
| PP Time | Power play opportunity |

```python
def player_goal_probability(
    player_gpg: float,      # Player's goals per game
    opp_ga_pg: float,       # Opponent's GA per game
    league_ga_avg: float,   # League average GA per game
    line: float = 0.5
) -> float:
    """Calculate probability of player scoring at least `line` goals."""
    import math
    
    # Adjust for opponent defense
    defensive_factor = opp_ga_pg / league_ga_avg
    adjusted_xg = player_gpg * defensive_factor
    
    # Poisson probability of 1+ goals
    prob_zero = math.exp(-adjusted_xg)
    return 1 - prob_zero
```

### Shots on Goal Props
- More predictable than goals (higher sample size)
- Consider: ice time, shooting tendencies, opponent shot suppression

### Assists/Points Props
- Combine with linemate analysis
- Power play deployment key factor

---

## Situational Metrics

### Home Ice Advantage
Historical NHL home win rate: ~54%

```python
HOME_ADVANTAGE = 0.15  # 15% goal boost for home team
```

### Back-to-Back Impact
Teams on back-to-back games show:
- ~0.2 fewer goals scored
- ~0.15 more goals allowed

```python
B2B_ADJUSTMENT = {
    "goals_for": -0.20,
    "goals_against": +0.15
}
```

### Rest Days
| Rest | Goal Adjustment |
|------|-----------------|
| 0 days (B2B) | -0.20 |
| 1 day | 0.00 |
| 2 days | +0.05 |
| 3+ days | +0.08 |

---

## Value Betting

### Implied Probability
```python
def american_to_implied(odds: int) -> float:
    """Convert American odds to implied probability."""
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)

# Examples:
# -150 → 60%
# +150 → 40%
# -200 → 66.7%
# +200 → 33.3%
```

### Edge Calculation
```python
def calculate_edge(model_prob: float, book_odds: int) -> float:
    """Calculate betting edge."""
    implied = american_to_implied(book_odds)
    return model_prob - implied

# Example:
# Model says 55% win probability
# Book has +110 (47.6% implied)
# Edge = 55% - 47.6% = 7.4%
```

### Kelly Criterion
Optimal bet sizing based on edge.

```python
def kelly_fraction(prob: float, odds: int) -> float:
    """Calculate Kelly criterion bet fraction."""
    if odds > 0:
        decimal_odds = (odds / 100) + 1
    else:
        decimal_odds = (100 / abs(odds)) + 1
    
    q = 1 - prob
    b = decimal_odds - 1
    
    kelly = (b * prob - q) / b
    return max(0, kelly)  # Never negative

# Example: 55% prob at +110
# kelly_fraction(0.55, 110) = 0.0977 (9.77% of bankroll)
```

---

## Data Quality Indicators

### Minimum Sample Sizes
| Metric | Min Games | Reason |
|--------|-----------|--------|
| Team GF/GA | 20 | Stabilization |
| Player Goals | 30 | Variance reduction |
| Goalie Save % | 15 starts | Statistical significance |
| H2H matchups | 5 | Pattern recognition |

### Recency Weighting
More recent games should carry more weight.

```python
def weighted_average(values: list, decay: float = 0.9) -> float:
    """Calculate recency-weighted average."""
    weights = [decay ** i for i in range(len(values))]
    weights.reverse()  # Most recent = highest weight
    
    weighted_sum = sum(v * w for v, w in zip(values, weights))
    return weighted_sum / sum(weights)
```

---

## Quick Reference

### Betting Edges to Target
| Edge | Recommendation |
|------|----------------|
| < 2% | No bet |
| 2-5% | Small bet (0.5-1 unit) |
| 5-10% | Standard bet (1-2 units) |
| > 10% | Strong bet (2-3 units) |

### Common Pitfalls
1. **Recency bias**: Don't overweight last game
2. **Public bias**: Favorites often overvalued
3. **Ignore rest**: B2B games significant
4. **Goalie neglect**: Starter vs backup matters
5. **Sample size**: Early season stats unreliable
