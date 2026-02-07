"""Injury tracking data models."""
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional, List

class InjuryStatus(Enum):
    """Player injury status."""
    HEALTHY = "healthy"
    DAY_TO_DAY = "day-to-day"
    WEEK_TO_WEEK = "week-to-week"
    IR = "ir"
    LTIR = "ltir"
    OUT = "out"
    QUESTIONABLE = "questionable"
    PROBABLE = "probable"

class PlayerTier(Enum):
    """Player importance tier."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class Injury:
    """Individual injury record."""
    player_id: int
    player_name: str
    team: str
    position: str
    status: InjuryStatus
    injury_type: str  # "lower-body", "upper-body", "illness", etc.
    injury_date: Optional[date] = None
    expected_return: Optional[date] = None
    player_tier: PlayerTier = PlayerTier.MEDIUM
    
    @property
    def days_out(self) -> Optional[int]:
        """Days since injury."""
        if self.injury_date:
            return (date.today() - self.injury_date).days
        return None
    
    @property
    def is_game_time_decision(self) -> bool:
        """Player might play but uncertain."""
        return self.status in [
            InjuryStatus.DAY_TO_DAY,
            InjuryStatus.QUESTIONABLE,
            InjuryStatus.PROBABLE
        ]

@dataclass
class TeamInjuryReport:
    """All injuries for a team."""
    team: str
    injuries: List[Injury] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    
    @property
    def critical_injuries(self) -> List[Injury]:
        return [i for i in self.injuries if i.player_tier == PlayerTier.CRITICAL]
    
    @property
    def total_impact(self) -> float:
        """Estimate total goal impact from injuries."""
        impact_map = {
            PlayerTier.CRITICAL: 0.4,
            PlayerTier.HIGH: 0.2,
            PlayerTier.MEDIUM: 0.1,
            PlayerTier.LOW: 0.03
        }
        return sum(impact_map.get(i.player_tier, 0) for i in self.injuries)
