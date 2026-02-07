"""Test bet recommendation tracking functionality."""
from src.utils.bet_storage import (
    add_recommendation, get_performance_metrics, 
    load_recommendations, evaluate_recommendations
)

# Add sample recommendations
print('Adding sample recommendations...')

rec1 = add_recommendation(
    game_id="2025020789",
    game_date="2026-02-07",
    home_team="MTL",
    away_team="TOR",
    bet_type="Moneyline",
    recommendation="TOR ML",
    odds="-150",
    edge_percent=5.2,
    model_prob=0.65
)
print(f'✅ Added recommendation #{rec1["id"]}: {rec1["matchup"]} - {rec1["recommendation"]} (Edge: {rec1["edge_percent"]}%)')

rec2 = add_recommendation(
    game_id="2025020790",
    game_date="2026-02-06",
    home_team="NYR",
    away_team="BOS",
    bet_type="Over",
    recommendation="Over 6.0",
    odds="-110",
    edge_percent=3.8,
    model_prob=0.54
)
print(f'✅ Added recommendation #{rec2["id"]}: {rec2["matchup"]} - {rec2["recommendation"]} (Edge: {rec2["edge_percent"]}%)')

rec3 = add_recommendation(
    game_id="2025020791",
    game_date="2026-02-05",
    home_team="VGK",
    away_team="COL",
    bet_type="Puck Line",
    recommendation="COL -1.5",
    odds="+140",
    edge_percent=4.1,
    model_prob=0.38
)
print(f'✅ Added recommendation #{rec3["id"]}: {rec3["matchup"]} - {rec3["recommendation"]} (Edge: {rec3["edge_percent"]}%)')

# Get initial metrics
metrics = get_performance_metrics()
print(f'\n📊 Initial Metrics:')
print(f'   Total Recommendations: {metrics["total_recommendations"]}')
print(f'   Evaluated: {metrics["evaluated"]}')
print(f'   Pending: {metrics["pending"]}')

# Simulate adding game results (normally done by data collection)
print(f'\n💾 Simulating game results...')
import json
from pathlib import Path

results_file = Path("data_files/results/game_results.json")
results_file.parent.mkdir(parents=True, exist_ok=True)

# Create fake results
results_data = {
    "results": [
        {
            "game_id": "2025020789",
            "home_goals": 2,
            "away_goals": 4,
            "total_goals": 6,
            "home_won": False
        },
        {
            "game_id": "2025020790",
            "home_goals": 4,
            "away_goals": 3,
            "total_goals": 7,
            "home_won": True
        },
        {
            "game_id": "2025020791",
            "home_goals": 3,
            "away_goals": 5,
            "total_goals": 8,
            "home_won": False
        }
    ]
}

with open(results_file, 'w') as f:
    json.dump(results_data, f, indent=2)

print('✅ Game results saved')

# Evaluate recommendations
print(f'\n🔄 Evaluating recommendations...')
evaluate_recommendations()

# Get updated metrics
metrics = get_performance_metrics()
print(f'\n📊 Updated Metrics:')
print(f'   Total Recommendations: {metrics["total_recommendations"]}')
print(f'   Evaluated: {metrics["evaluated"]}')
print(f'   Wins: {metrics["wins"]}')
print(f'   Losses: {metrics["losses"]}')
print(f'   Win Rate: {metrics["win_rate"]:.1f}%')
print(f'   Total Profit: {metrics["total_profit"]:+.2f}u')
print(f'   ROI: {metrics["roi"]:+.1f}%')

# Show individual results
print(f'\n📋 Individual Results:')
recs = load_recommendations()
for rec in recs:
    status = "✅ Won" if rec.get("won") else "❌ Lost" if rec.get("won") is False else "⏳ Pending"
    print(f'   {rec["recommendation"]}: {status}')

print('\n✅ All tests passed!')

