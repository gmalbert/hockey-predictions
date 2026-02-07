# Automatic Bet Recommendation Tracking

## Overview
The performance tracking system automatically evaluates how well the model's betting recommendations perform against actual game results. This is a **completely automated system** - no manual bet entry required.

## How It Works

### 1. Recommendation Generation
When you use the **Value Finder** page, the model analyzes games and identifies betting opportunities with positive expected value (edge). These recommendations are automatically saved to `data_files/recommendations.json`.

### 2. Recommendation Storage
Each recommendation includes:
- **Game details**: Teams, date, game ID
- **Bet type**: Moneyline, Puck Line, or Totals (Over/Under)
- **Specific recommendation**: e.g., "TOR ML", "Over 6.0", "COL -1.5"
- **Odds**: American odds at time of recommendation
- **Edge percentage**: Calculated difference between model probability and implied odds
- **Model probability**: The model's probability for this outcome

### 3. Result Evaluation
After games complete, click the **"Evaluate Recommendations"** button on the Performance page to:
- Match recommendations to actual game results
- Determine which recommendations won/lost
- Calculate profit/loss assuming 1 unit wagered per bet
- Update performance metrics

### 4. Performance Metrics
The system calculates:
- **Win Rate**: Percentage of recommendations that won
- **ROI**: Return on investment (profit/total staked × 100)
- **Total Profit**: Net units won/lost
- **Breakdown by bet type**: Separate metrics for ML, Puck Line, and Totals
- **Monthly trends**: Performance grouped by month

## Using the System

### Value Finder Page
1. Navigate to **💰 Value Finder**
2. Set your minimum edge threshold (e.g., 2%)
3. Select bet types to analyze
4. Choose a date
5. Recommendations with positive edge are automatically saved

### Performance Page
1. Navigate to **📈 Performance Tracker**
2. Click **"Evaluate Recommendations"** to update results
3. View overall performance metrics
4. Examine breakdown by bet type
5. Review recommendation history
6. Analyze monthly trends

## Profit Calculation
- **Win**: Profit = (Odds calculation based on American odds format)
  - Positive odds (+150): Win (150/100) × 1 unit = 1.50 units
  - Negative odds (-150): Win (100/150) × 1 unit = 0.67 units
- **Loss**: Loss = -1 unit
- **Stake**: All calculations assume 1 unit per bet

## Evaluation Logic

### Moneyline
- Recommendation wins if the recommended team wins the game

### Puck Line
- **Team -1.5**: Wins if team wins by 2+ goals
- **Team +1.5**: Wins if team loses by 1 goal or wins

### Totals
- **Over X**: Wins if total goals > X
- **Under X**: Wins if total goals < X

## Data Storage

### Recommendations
- **Location**: `data_files/recommendations.json`
- **Format**: JSON array of recommendation objects
- **Fields**: game_id, date, teams, bet_type, recommendation, odds, edge_percent, model_prob, result, won

### Game Results
- **Location**: `data_files/results/game_results.json`
- **Format**: JSON array of result objects
- **Fields**: game_id, home_goals, away_goals, total_goals, home_won

## Best Practices

1. **Regular Evaluation**: Click "Evaluate Recommendations" daily to keep metrics current
2. **Edge Threshold**: Higher minimum edge (3-5%) = fewer but higher quality recommendations
3. **Sample Size**: Evaluate performance over at least 50-100 recommendations for meaningful insights
4. **Bet Type Analysis**: Compare performance across different bet types to identify strengths
5. **ROI Focus**: Win rate matters, but ROI is the true measure of profitability

## Example Workflow

1. **Morning**: Check Value Finder for today's games
2. **Review**: Model identifies 3 recommendations with 3%+ edge
3. **Automatic**: Recommendations saved automatically
4. **Evening**: Games complete
5. **Evaluate**: Click "Evaluate Recommendations" button
6. **Results**: Performance metrics updated
7. **Repeat**: Continue daily for long-term tracking

## Notes

- Recommendations are saved when you view the Value Finder page
- Game results must be in the system for evaluation to work
- Only evaluated recommendations count toward win rate and ROI
- Pending recommendations are tracked separately
- 1 unit stake assumed for all profit calculations
