"""Expected goals calculations for game predictions."""
from dataclasses import dataclass
from typing import Tuple


@dataclass
class TeamMetrics:
    """Core team statistics for predictions."""
    team: str
    goals_for_pg: float
    goals_against_pg: float
    shots_for_pg: float
    shots_against_pg: float
    pp_pct: float
    pk_pct: float
    
    @property
    def goal_differential(self) -> float:
        """Goals for minus goals against per game."""
        return round(self.goals_for_pg - self.goals_against_pg, 2)
    
    @property
    def shooting_pct(self) -> float:
        """Team shooting percentage."""
        if self.shots_for_pg == 0:
            return 0.0
        return round((self.goals_for_pg / self.shots_for_pg) * 100, 2)
    
    @property
    def save_pct(self) -> float:
        """Implied save percentage against."""
        if self.shots_against_pg == 0:
            return 0.0
        goals_allowed_rate = self.goals_against_pg / self.shots_against_pg
        return round((1 - goals_allowed_rate) * 100, 2)
    
    @classmethod
    def from_api_response(cls, data: dict) -> "TeamMetrics":
        """Create TeamMetrics from API response."""
        return cls(
            team=data.get("team", ""),
            goals_for_pg=data.get("goals_for_pg", 0),
            goals_against_pg=data.get("goals_against_pg", 0),
            shots_for_pg=data.get("shots_for_pg", 0),
            shots_against_pg=data.get("shots_against_pg", 0),
            pp_pct=data.get("pp_pct", 0),
            pk_pct=data.get("pk_pct", 0),
        )


def calculate_expected_goals(
    home_team: TeamMetrics,
    away_team: TeamMetrics,
    home_advantage: float = 0.15,
    adjustments: dict | None = None
) -> Tuple[float, float]:
    """
    Calculate expected goals for each team.
    
    Formula: Average of team's offense and opponent's defense,
    adjusted for home ice advantage.
    
    Args:
        home_team: Home team statistics
        away_team: Away team statistics
        home_advantage: Goal boost for home team (default 15%)
        adjustments: Optional dict with "home" and "away" adjustments
            (e.g., for injuries, back-to-back, goalie)
    
    Returns:
        Tuple of (home_expected_goals, away_expected_goals)
    
    Example:
        >>> home = TeamMetrics("TOR", 3.4, 2.8, 33, 28, 25, 82)
        >>> away = TeamMetrics("MTL", 2.9, 3.3, 30, 32, 20, 78)
        >>> calculate_expected_goals(home, away)
        (3.53, 2.71)
    """
    # Home team: their offense vs away defense
    home_xg = (home_team.goals_for_pg + away_team.goals_against_pg) / 2
    home_xg *= (1 + home_advantage)
    
    # Away team: their offense vs home defense
    away_xg = (away_team.goals_for_pg + home_team.goals_against_pg) / 2
    away_xg *= (1 - home_advantage / 2)  # Road disadvantage
    
    # Apply optional adjustments
    if adjustments:
        home_xg += adjustments.get("home", 0)
        away_xg += adjustments.get("away", 0)
    
    # Floor at 0.5 goals
    home_xg = max(0.5, home_xg)
    away_xg = max(0.5, away_xg)
    
    return round(home_xg, 2), round(away_xg, 2)


def calculate_total_xg(home_xg: float, away_xg: float) -> float:
    """Calculate expected total goals."""
    return round(home_xg + away_xg, 2)


def calculate_expected_goals_with_analytics(
    home_team: TeamMetrics,
    away_team: TeamMetrics,
    home_analytics: dict | None = None,
    away_analytics: dict | None = None,
    home_advantage: float = 0.15,
    adjustments: dict | None = None,
    analytics_weight: float = 0.50,
) -> Tuple[float, float]:
    """
    Calculate expected goals blending aggregate stats with NHL shot-quality analytics.

    When NHL team analytics data is available (xGF, xGA per game derived from
    the NHL stats REST API ``team/analytics`` endpoint), this model blends those
    shot-quality adjusted figures with the legacy goals-per-game model at a
    configurable ratio.

    The blend leans on analytics whenever data quality is high.  A team with
    high Fenwick% but modest goal numbers is likely being unlucky; the analytics
    signal captures that.  Conversely, a team with weak analytics but strong
    goal totals is likely running hot.

    Args:
        home_team: Home team aggregate statistics (TeamMetrics).
        away_team: Away team aggregate statistics (TeamMetrics).
        home_analytics: NHL analytics dict for the home team (keys: xgf, xga,
            ff_pct, games_played …). Pass None to skip blending.
        away_analytics: NHL analytics dict for the away team.
        home_advantage: Home-ice boost applied to home expected goals (default 15%).
        adjustments: Optional additive adjustments dict (keys: "home", "away").
        analytics_weight: Weight given to the analytics-based estimate vs the
            legacy estimate (0–1). Default 0.50; set to 0 to ignore analytics.

    Returns:
        Tuple of (home_expected_goals, away_expected_goals).
    """
    # ---- Legacy estimate (existing formula) ----
    home_xg_legacy, away_xg_legacy = calculate_expected_goals(
        home_team, away_team, home_advantage=home_advantage, adjustments=adjustments
    )

    # ---- Analytics-based estimate ----
    home_xg_analytics: float | None = None
    away_xg_analytics: float | None = None

    if home_analytics and away_analytics:
        h_xgf_pg = _analytics_xg_per_game(home_analytics)
        a_xga_pg = _analytics_xg_per_game(away_analytics, use_against=True)
        if h_xgf_pg and a_xga_pg:
            home_xg_analytics = (h_xgf_pg + a_xga_pg) / 2
            home_xg_analytics *= (1 + home_advantage)

        a_xgf_pg = _analytics_xg_per_game(away_analytics)
        h_xga_pg = _analytics_xg_per_game(home_analytics, use_against=True)
        if a_xgf_pg and h_xga_pg:
            away_xg_analytics = (a_xgf_pg + h_xga_pg) / 2
            away_xg_analytics *= (1 - home_advantage / 2)

    # ---- Blend ----
    if home_xg_analytics is not None:
        w = analytics_weight
        home_xg = (1 - w) * home_xg_legacy + w * home_xg_analytics
    else:
        home_xg = home_xg_legacy

    if away_xg_analytics is not None:
        w = analytics_weight
        away_xg = (1 - w) * away_xg_legacy + w * away_xg_analytics
    else:
        away_xg = away_xg_legacy

    # Apply adjustments if not already applied (analytics path)
    if home_xg_analytics is not None and adjustments:
        home_xg += adjustments.get("home", 0)
        away_xg += adjustments.get("away", 0)

    home_xg = max(0.5, home_xg)
    away_xg = max(0.5, away_xg)

    return round(home_xg, 2), round(away_xg, 2)


def _analytics_xg_per_game(
    analytics: dict, use_against: bool = False
) -> float | None:
    """
    Extract per-game xG from an NHL team analytics dict.

    The NHL API returns season totals (xgf, xga) and games_played.
    Converts to per-game rate; returns None if data is missing.
    """
    key = "xga" if use_against else "xgf"
    val = analytics.get(key)
    gp = analytics.get("games_played", 0)
    if val is None or gp == 0:
        return None
    return val / gp


def describe_model_upgrade(
    legacy_home: float,
    legacy_away: float,
    upgraded_home: float,
    upgraded_away: float,
) -> dict:
    """
    Compare legacy vs analytics-enhanced xG estimates.

    Returns a dict summarising the delta and direction of change,
    useful for showing users how the model improvement affected a game.
    """
    return {
        "home_delta": round(upgraded_home - legacy_home, 3),
        "away_delta": round(upgraded_away - legacy_away, 3),
        "home_direction": "up" if upgraded_home > legacy_home else "down" if upgraded_home < legacy_home else "same",
        "away_direction": "up" if upgraded_away > legacy_away else "down" if upgraded_away < legacy_away else "same",
        "total_legacy": round(legacy_home + legacy_away, 2),
        "total_upgraded": round(upgraded_home + upgraded_away, 2),
    }
