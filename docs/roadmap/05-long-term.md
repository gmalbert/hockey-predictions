# Long-Term Roadmap

## Overview
Advanced features and scaling improvements for months 2-6 and beyond.

---

## Phase 1: Enhanced Predictions (Month 2)

### Situational Modeling
Adjust predictions based on context.

**Status**: ❌ Not implemented - File `src/models/situational.py` does not exist

### Goalie Impact Model
**Status**: ✅ COMPLETED - Implemented as `src/models/goalie_adjustment.py` and `src/models/goalie_matchup.py`
- Goalie performance adjustments integrated into predictions
- Goalie matchup analysis available

---

## Phase 2: Advanced Analytics (Month 3)

### Head-to-Head Analysis
**Status**: ❌ Not implemented - File `src/models/head_to_head.py` does not exist

### Player Props Engine
**Status**: ✅ COMPLETED - Full player props analysis implemented in Page 5
- Poisson distribution-based predictions
- Over/under line analysis with edge calculations
- Player search and filtering
- Integration with injury data and team stats

---

## Phase 3: Machine Learning (Month 4-5)

### Feature Engineering
**Status**: ❌ Not implemented - File `src/models/features.py` does not exist

### Model Training Pipeline
**Status**: ❌ Not implemented - File `src/models/training.py` does not exist

**However**: ✅ Basic ML prediction exists in `src/models/ml_predictor.py`

---

## Phase 4: Production Features (Month 6+)

### Line Movement Tracking
**Status**: ✅ COMPLETED - Implemented in `src/models/line_movement.py`
- Historical odds tracking with GitHub Actions
- Line movement analysis and alerts
- Odds snapshots stored in `data_files/odds/`

### Real-Time Updates
**Status**: ❌ Not implemented - No WebSocket or real-time features

### Notification System
**Status**: ❌ Not implemented - File `src/utils/notifications.py` does not exist

---

## Infrastructure Improvements

### Caching Strategy
**Status**: ✅ COMPLETED - File-based caching implemented
- TTL-based caching for API responses
- Cache stored in `data_files/cache/`
- 5-minute TTL for live data

### Database
**Status**: ✅ COMPLETED - JSON-based storage implemented
- Historical games in `data_files/historical/`
- Team stats and predictions cached
- No SQL database needed for current scale

### Deployment
**Status**: ✅ COMPLETED - GitHub Actions CI/CD implemented
- Automated odds capture workflow
- Fixed workflow issues for missing directories
- Ready for cloud deployment

---

## Infrastructure Improvements

### API Rate Limiting
**Status**: ❌ Not implemented - File `src/api/rate_limiter.py` does not exist

---

## Feature Wishlist

| Feature | Priority | Effort | Impact | Status |
|---------|----------|--------|--------|--------|
| Goalie-adjusted predictions | High | Medium | High | ✅ COMPLETED |
| Player props engine | High | High | High | ✅ COMPLETED |
| Historical backtesting UI | Medium | Medium | Medium | ✅ COMPLETED (Page 11) |
| Line movement alerts | Medium | Low | Medium | ✅ COMPLETED |
| ML-based predictions | Medium | High | High | ✅ PARTIALLY (Basic ML exists) |
| Mobile-responsive UI | Low | Medium | Low | ❌ Not implemented |
| Discord/email alerts | Low | Low | Medium | ❌ Not implemented |
| Multiple sportsbook odds | Low | High | High | ❌ Not implemented |

---

## Success Metrics

- **Model accuracy**: Target 55%+ on moneyline picks
- **ROI**: Target positive ROI over 100+ bets
- **User engagement**: Track page views, feature usage
- **Prediction calibration**: Predicted probabilities match actual outcomes
## Phase 2: Advanced Analytics (Month 3)

### Head-to-Head Analysis
**Status**: ❌ Not implemented - File `src/models/head_to_head.py` does not exist

### Player Props Engine
**Status**: ✅ COMPLETED - Full player props analysis implemented in Page 5
- Poisson distribution-based predictions
- Over/under line analysis with edge calculations
- Player search and filtering
- Integration with injury data and team stats

---

## Phase 3: Machine Learning (Month 4-5)

### Feature Engineering
**Status**: ❌ Not implemented - File `src/models/features.py` does not exist

### Model Training Pipeline
**Status**: ❌ Not implemented - File `src/models/training.py` does not exist

**However**: ✅ Basic ML prediction exists in `src/models/ml_predictor.py`

---

## Phase 4: Production Features (Month 6+)

### Line Movement Tracking
**Status**: ✅ COMPLETED - Implemented in `src/models/line_movement.py`
- Historical odds tracking with GitHub Actions
- Line movement analysis and alerts
- Odds snapshots stored in `data_files/odds/`

### Real-Time Updates
**Status**: ❌ Not implemented - No WebSocket or real-time features

### Notification System
**Status**: ❌ Not implemented - File `src/utils/notifications.py` does not exist

---

## Infrastructure Improvements

### Caching Strategy
**Status**: ✅ COMPLETED - File-based caching implemented
- TTL-based caching for API responses
- Cache stored in `data_files/cache/`
- 5-minute TTL for live data

### Database
**Status**: ✅ COMPLETED - JSON-based storage implemented
- Historical games in `data_files/historical/`
- Team stats and predictions cached
- No SQL database needed for current scale

### Deployment
**Status**: ✅ COMPLETED - GitHub Actions CI/CD implemented
- Automated odds capture workflow
- Fixed workflow issues for missing directories
- Ready for cloud deployment

---

## Infrastructure Improvements

### API Rate Limiting
**Status**: ❌ Not implemented - File `src/api/rate_limiter.py` does not exist

---

## Feature Wishlist

| Feature | Priority | Effort | Impact | Status |
|---------|----------|--------|--------|--------|
| Goalie-adjusted predictions | High | Medium | High | ✅ COMPLETED |
| Player props engine | High | High | High | ✅ COMPLETED |
| Historical backtesting UI | Medium | Medium | Medium | ✅ COMPLETED (Page 11) |
| Line movement alerts | Medium | Low | Medium | ✅ COMPLETED |
| ML-based predictions | Medium | High | High | ✅ PARTIALLY (Basic ML exists) |
| Mobile-responsive UI | Low | Medium | Low | ❌ Not implemented |
| Discord/email alerts | Low | Low | Medium | ❌ Not implemented |
| Multiple sportsbook odds | Low | High | High | ❌ Not implemented |

---

## Success Metrics

- **Model accuracy**: Target 55%+ on moneyline picks
- **ROI**: Target positive ROI over 100+ bets
- **User engagement**: Track page views, feature usage
- **Prediction calibration**: Predicted probabilities match actual outcomes
class PropPrediction:
    """Player prop prediction."""
    player_id: int
    player_name: str
    prop_type: str  # "goals", "assists", "points", "shots"
    line: float
    over_probability: float
    under_probability: float
    expected_value: float

def predict_player_goals(
    player_stats: dict,
    opponent_stats: dict,
    line: float = 0.5
) -> PropPrediction:
    """
    Predict probability of a player going over/under goals line.
    
    Uses player's goals per game vs opponent's goals against per game.
    """
    import math
    
    # Player's scoring rate
    player_gpg = player_stats.get("goals", 0) / max(player_stats.get("games", 1), 1)
    
    # Adjust for opponent defense
    opp_ga_pg = opponent_stats.get("goals_against_pg", 3.0)
    league_avg_goals = 3.0
    
    # Adjusted expected goals
    defensive_factor = opp_ga_pg / league_avg_goals
    expected_goals = player_gpg * defensive_factor
    
    # Poisson probability of scoring at least 'line' goals
    over_prob = 0.0
    for goals in range(int(line) + 1, 8):  # Cap at 7 goals
        prob = (math.exp(-expected_goals) * (expected_goals ** goals)) / math.factorial(goals)
        over_prob += prob
    
    return PropPrediction(
        player_id=player_stats.get("player_id", 0),
        player_name=player_stats.get("name", "Unknown"),
        prop_type="goals",
        line=line,
        over_probability=round(over_prob, 4),
        under_probability=round(1 - over_prob, 4),
        expected_value=round(expected_goals, 3)
    )
```

---

## Phase 3: Machine Learning (Month 4-5)

### Feature Engineering
**Status**: ❌ Not implemented - File `src/models/features.py` does not exist

### Model Training Pipeline
**Status**: ❌ Not implemented - File `src/models/training.py` does not exist

---

## Phase 4: Production Features (Month 6+)

### Line Movement Tracking
**Status**: ✅ COMPLETED - Implemented in `src/models/line_movement.py`
- Historical odds tracking with GitHub Actions
- Line movement analysis and alerts
- Odds snapshots stored in `data_files/odds/`

### Real-Time Updates
**Status**: ❌ Not implemented - No WebSocket or real-time features

### Notification System
**Status**: ❌ Not implemented - File `src/utils/notifications.py` does not exist

---

## Infrastructure Improvements

### Caching Strategy
**Status**: ✅ COMPLETED - File-based caching implemented
- TTL-based caching for API responses
- Cache stored in `data_files/cache/`
- 5-minute TTL for live data

### Database
**Status**: ✅ COMPLETED - JSON-based storage implemented
- Historical games in `data_files/historical/`
- Team stats and predictions cached
- No SQL database needed for current scale

### Deployment
**Status**: ✅ COMPLETED - GitHub Actions CI/CD implemented
- Automated odds capture workflow
- Fixed workflow issues for missing directories
- Ready for cloud deployment

---

## Infrastructure Improvements

### API Rate Limiting
**Status**: ❌ Not implemented - File `src/api/rate_limiter.py` does not exist

---

## Feature Wishlist

| Feature | Priority | Effort | Impact | Status |
|---------|----------|--------|--------|--------|
| Goalie-adjusted predictions | High | Medium | High | ✅ COMPLETED |
| Player props engine | High | High | High | ✅ COMPLETED |
| Historical backtesting UI | Medium | Medium | Medium | ✅ COMPLETED (Page 11) |
| Line movement alerts | Medium | Low | Medium | ✅ COMPLETED |
| ML-based predictions | Medium | High | High | ✅ PARTIALLY (Basic ML exists) |
| Mobile-responsive UI | Low | Medium | Low | ❌ Not implemented |
| Discord/email alerts | Low | Low | Medium | ❌ Not implemented |
| Multiple sportsbook odds | Low | High | High | ❌ Not implemented |

---

## Success Metrics

- **Model accuracy**: Target 55%+ on moneyline picks
- **ROI**: Target positive ROI over 100+ bets
- **User engagement**: Track page views, feature usage
- **Prediction calibration**: Predicted probabilities match actual outcomes
        return 0.5
    wins = (recent_games["result"] == "W").sum()
    return wins / len(recent_games)
```

### Model Training Pipeline
**Status**: ❌ Not implemented - File `src/models/training.py` does not exist

---

## Phase 4: Production Features (Month 6+)

### Line Movement Tracking
**Status**: ✅ COMPLETED - Implemented in `src/models/line_movement.py`
- Historical odds tracking with GitHub Actions
- Line movement analysis and alerts
- Odds snapshots stored in `data_files/odds/`

### Real-Time Updates
**Status**: ❌ Not implemented - No WebSocket or real-time features

### Notification System
**Status**: ❌ Not implemented - File `src/utils/notifications.py` does not exist

---

## Infrastructure Improvements

### Caching Strategy
**Status**: ✅ COMPLETED - File-based caching implemented
- TTL-based caching for API responses
- Cache stored in `data_files/cache/`
- 5-minute TTL for live data

### Database
**Status**: ✅ COMPLETED - JSON-based storage implemented
- Historical games in `data_files/historical/`
- Team stats and predictions cached
- No SQL database needed for current scale

### Deployment
**Status**: ✅ COMPLETED - GitHub Actions CI/CD implemented
- Automated odds capture workflow
- Fixed workflow issues for missing directories
- Ready for cloud deployment

---

## Infrastructure Improvements

### API Rate Limiting
**Status**: ❌ Not implemented - File `src/api/rate_limiter.py` does not exist

---

## Feature Wishlist

| Feature | Priority | Effort | Impact | Status |
|---------|----------|--------|--------|--------|
| Goalie-adjusted predictions | High | Medium | High | ✅ COMPLETED |
| Player props engine | High | High | High | ✅ COMPLETED |
| Historical backtesting UI | Medium | Medium | Medium | ✅ COMPLETED (Page 11) |
| Line movement alerts | Medium | Low | Medium | ✅ COMPLETED |
| ML-based predictions | Medium | High | High | ✅ PARTIALLY (Basic ML exists) |
| Mobile-responsive UI | Low | Medium | Low | ❌ Not implemented |
| Discord/email alerts | Low | Low | Medium | ❌ Not implemented |
| Multiple sportsbook odds | Low | High | High | ❌ Not implemented |

---

## Success Metrics

- **Model accuracy**: Target 55%+ on moneyline picks
- **ROI**: Target positive ROI over 100+ bets
- **User engagement**: Track page views, feature usage
- **Prediction calibration**: Predicted probabilities match actual outcomes
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

def create_value_alert(
    game: dict,
    bet_type: str,
    edge: float,
    model_prob: float,
    odds: int
) -> BetAlert:
    """Create alert for value betting opportunity."""
    home = game.get("home_team", "HOME")
    away = game.get("away_team", "AWAY")
    
    return BetAlert(
        game_id=game.get("game_id", ""),
        alert_type="value_bet",
        message=f"Value: {away}@{home} - {bet_type} at {odds} (edge: {edge:.1f}%)",
        edge=edge
    )
```

### API Rate Limiting
**Status**: ❌ Not implemented - File `src/api/rate_limiter.py` does not exist

---

## Infrastructure Improvements

### Caching Strategy
**Status**: ✅ COMPLETED - File-based caching implemented
- TTL-based caching for API responses
- Cache stored in `data_files/cache/`
- 5-minute TTL for live data

### Database
**Status**: ✅ COMPLETED - JSON-based storage implemented
- Historical games in `data_files/historical/`
- Team stats and predictions cached
- No SQL database needed for current scale

### Deployment
**Status**: ✅ COMPLETED - GitHub Actions CI/CD implemented
- Automated odds capture workflow
- Fixed workflow issues for missing directories
- Ready for cloud deployment

---

## Feature Wishlist

| Feature | Priority | Effort | Impact | Status |
|---------|----------|--------|--------|--------|
| Goalie-adjusted predictions | High | Medium | High | ✅ COMPLETED |
| Player props engine | High | High | High | ✅ COMPLETED |
| Historical backtesting UI | Medium | Medium | Medium | ✅ COMPLETED (Page 11) |
| Line movement alerts | Medium | Low | Medium | ✅ COMPLETED |
| ML-based predictions | Medium | High | High | ✅ PARTIALLY (Basic ML exists) |
| Mobile-responsive UI | Low | Medium | Low | ❌ Not implemented |
| Discord/email alerts | Low | Low | Medium | ❌ Not implemented |
| Multiple sportsbook odds | Low | High | High | ❌ Not implemented |

---

## Success Metrics

- **Model accuracy**: Target 55%+ on moneyline picks
- **ROI**: Target positive ROI over 100+ bets
- **User engagement**: Track page views, feature usage
- **Prediction calibration**: Predicted probabilities match actual outcomes
