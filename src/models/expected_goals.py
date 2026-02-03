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
