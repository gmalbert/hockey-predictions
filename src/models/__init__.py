"""Prediction models package."""
from .expected_goals import (
    calculate_expected_goals,
    calculate_expected_goals_with_analytics,
    describe_model_upgrade,
    TeamMetrics,
)
from .win_probability import calculate_win_probability, GameProbabilities
from .puck_line import predict_puck_line
from .goalie_adjustment import (
    calculate_goalie_adjustment,
    calculate_goalie_adjustment_with_analytics,
    adjusted_xg_with_analytics,
    GoalieAdjustment,
)

__all__ = [
    "calculate_expected_goals",
    "calculate_expected_goals_with_analytics",
    "describe_model_upgrade",
    "TeamMetrics",
    "calculate_win_probability",
    "GameProbabilities",
    "predict_puck_line",
    "calculate_goalie_adjustment",
    "calculate_goalie_adjustment_with_analytics",
    "adjusted_xg_with_analytics",
    "GoalieAdjustment",
]
