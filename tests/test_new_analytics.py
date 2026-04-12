"""Tests for analytics-upgraded model functions."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.expected_goals import (
    calculate_expected_goals_with_analytics,
    describe_model_upgrade,
)
from src.models.goalie_adjustment import (
    calculate_goalie_adjustment_with_analytics,
    adjusted_xg_with_analytics,
)
from src.models.xg_shot_model import XGShotModel


# ── xG blended model ────────────────────────────────────────────────────────

class _FakeTeam:
    """Minimal stand-in for a TeamStats dataclass."""
    def __init__(self, gf_pg, ga_pg, shots_for_pg=30.0, shots_against_pg=28.0):
        self.goals_for_pg = gf_pg
        self.goals_against_pg = ga_pg
        self.shots_for_pg = shots_for_pg
        self.shots_against_pg = shots_against_pg


HOME = _FakeTeam(gf_pg=3.2, ga_pg=2.6)
AWAY = _FakeTeam(gf_pg=2.8, ga_pg=3.0)

HOME_ANALYTICS = {"xgf": 180.0, "xga": 155.0, "games_played": 55}
AWAY_ANALYTICS = {"xgf": 160.0, "xga": 170.0, "games_played": 55}


def test_blended_xg_returns_two_floats():
    home_xg, away_xg = calculate_expected_goals_with_analytics(
        HOME, AWAY, HOME_ANALYTICS, AWAY_ANALYTICS
    )
    assert isinstance(home_xg, float)
    assert isinstance(away_xg, float)


def test_blended_xg_positive():
    home_xg, away_xg = calculate_expected_goals_with_analytics(
        HOME, AWAY, HOME_ANALYTICS, AWAY_ANALYTICS
    )
    assert home_xg > 0
    assert away_xg > 0


def test_home_team_stronger_analytics_gets_higher_xg():
    """Home team has better xGF/G (3.27) vs away (2.91) → home xG should be higher."""
    home_xg, away_xg = calculate_expected_goals_with_analytics(
        HOME, AWAY, HOME_ANALYTICS, AWAY_ANALYTICS
    )
    assert home_xg > away_xg


def test_analytics_weight_zero_matches_legacy():
    """With analytics_weight=0 the blended function should return the legacy result."""
    from src.models.expected_goals import calculate_expected_goals
    legacy_home, legacy_away = calculate_expected_goals(HOME, AWAY)
    blended_home, blended_away = calculate_expected_goals_with_analytics(
        HOME, AWAY, HOME_ANALYTICS, AWAY_ANALYTICS, analytics_weight=0.0
    )
    assert abs(legacy_home - blended_home) < 0.01
    assert abs(legacy_away - blended_away) < 0.01


def test_analytics_weight_one_uses_only_analytics():
    """With analytics_weight=1.0, only analytics numbers should matter."""
    home_xg, away_xg = calculate_expected_goals_with_analytics(
        HOME, AWAY, HOME_ANALYTICS, AWAY_ANALYTICS, analytics_weight=1.0
    )
    # xGF/G for home = 180/55 = 3.272, with home advantage 1.15 ≈ 3.76
    # xGA/G for away = 170/55 = 3.09
    # Expected home ≈ (3.76 + 3.09) / 2 ≈ 3.42
    assert home_xg > 3.0


def test_missing_analytics_falls_back_to_legacy():
    """None analytics should not crash — falls back to legacy weight."""
    home_xg, away_xg = calculate_expected_goals_with_analytics(
        HOME, AWAY, None, None
    )
    assert home_xg > 0
    assert away_xg > 0


def test_describe_model_upgrade_direction():
    info = describe_model_upgrade(
        legacy_home=2.8, legacy_away=2.5,
        upgraded_home=3.1, upgraded_away=2.3,
    )
    assert info["home_delta"] == pytest.approx(0.3, abs=0.01)
    assert info["away_delta"] == pytest.approx(-0.2, abs=0.01)
    assert "up" in info["home_direction"]
    assert "down" in info["away_direction"]


# ── Goalie adjustment analytics ──────────────────────────────────────────────

def test_goalie_adj_with_all_inputs():
    adj = calculate_goalie_adjustment_with_analytics(
        goalie_name="Test Goalie",
        save_pct=0.920,
        sample_size=40,
        gsaa=8.0,
        hd_save_pct=0.850,
    )
    assert adj is not None
    # Negative adjustment = good goalie reduces the opponent's xG
    assert adj.adjustment < 0
    assert adj.method != "sv_pct"  # should use analytics blend


def test_goalie_adj_no_analytics_uses_legacy():
    adj = calculate_goalie_adjustment_with_analytics(
        goalie_name="Test Goalie",
        save_pct=0.910,
        sample_size=30,
        gsaa=None,
        hd_save_pct=None,
    )
    assert adj.method == "sv_pct"


def test_goalie_adj_below_avg_save_pct_is_negative():
    adj = calculate_goalie_adjustment_with_analytics(
        goalie_name="Bad Goalie",
        save_pct=0.880,
        sample_size=40,
        gsaa=-5.0,
        hd_save_pct=0.780,
    )
    # Positive adjustment = bad goalie increases the opponent's xG
    assert adj.adjustment > 0


def test_adjusted_xg_does_not_go_below_floor():
    # Even a terrible goalie shouldn't produce negative xG for opponent
    result = adjusted_xg_with_analytics(
        base_team_xg=0.6,
        opposing_goalie_sv_pct=0.860,
        opposing_goalie_games=40,
        opposing_goalie_name="Sieve McLetter",
        opposing_goalie_gsaa=-15.0,
        opposing_goalie_hd_sv_pct=0.720,
    )
    assert result >= 0.5  # floor enforced


# ── XGShotModel (fallback coefficients) ─────────────────────────────────────

class TestXGShotModel:
    def setup_method(self):
        self.model = XGShotModel()

    def test_predict_single_returns_probability(self):
        p = self.model.predict_single(distance=20, angle=15)
        assert 0.0 < p < 1.0

    def test_closer_shots_have_higher_xg(self):
        close = self.model.predict_single(distance=10, angle=5)
        far = self.model.predict_single(distance=60, angle=40)
        assert close > far

    def test_tip_in_higher_than_wrist(self):
        tip = self.model.predict_single(distance=20, angle=10, shot_type="tip-in")
        wrist = self.model.predict_single(distance=20, angle=10, shot_type="wrist")
        assert tip > wrist

    def test_rebound_higher_than_clean(self):
        with_rebound = self.model.predict_single(distance=20, angle=10, is_rebound=True)
        without = self.model.predict_single(distance=20, angle=10, is_rebound=False)
        assert with_rebound > without

    def test_rush_higher_than_set_play(self):
        rush = self.model.predict_single(distance=25, angle=15, is_rush=True)
        set_play = self.model.predict_single(distance=25, angle=15, is_rush=False)
        assert rush > set_play

    def test_predict_batch(self):
        shots = [
            {"distance": 20, "angle": 10},
            {"distance": 45, "angle": 30, "shot_type": "slap"},
        ]
        probs = self.model.predict_batch(shots)
        assert len(probs) == 2
        assert all(0.0 < p < 1.0 for p in probs)

    def test_coef_summary(self):
        summary = self.model.get_coef_summary()
        assert "distance" in summary
        assert summary["distance"] < 0  # negative: farther = lower xG
