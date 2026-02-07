"""Odds and line movement data models."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class OddsFormat(Enum):
    AMERICAN = "american"
    DECIMAL = "decimal"
    
@dataclass
class OddsSnapshot:
    """Point-in-time odds capture."""
    timestamp: datetime
    home_ml: int
    away_ml: int
    home_puck_line: float  # Usually -1.5
    home_pl_odds: int
    away_puck_line: float  # Usually +1.5
    away_pl_odds: int
    total: float
    over_odds: int
    under_odds: int
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "home_ml": self.home_ml,
            "away_ml": self.away_ml,
            "home_pl": self.home_puck_line,
            "home_pl_odds": self.home_pl_odds,
            "away_pl": self.away_puck_line,
            "away_pl_odds": self.away_pl_odds,
            "total": self.total,
            "over": self.over_odds,
            "under": self.under_odds
        }

@dataclass
class GameOdds:
    """All odds snapshots for a game."""
    game_id: str
    home_team: str
    away_team: str
    game_time: datetime
    snapshots: List[OddsSnapshot] = field(default_factory=list)
    
    @property
    def opening_odds(self) -> Optional[OddsSnapshot]:
        """First recorded odds."""
        return self.snapshots[0] if self.snapshots else None
    
    @property
    def current_odds(self) -> Optional[OddsSnapshot]:
        """Most recent odds."""
        return self.snapshots[-1] if self.snapshots else None
    
    @property
    def moneyline_movement(self) -> Optional[int]:
        """Change in home ML from open to current."""
        if self.opening_odds and self.current_odds:
            return self.current_odds.home_ml - self.opening_odds.home_ml
        return None
    
    @property
    def total_movement(self) -> Optional[float]:
        """Change in total from open to current."""
        if self.opening_odds and self.current_odds:
            return self.current_odds.total - self.opening_odds.total
        return None
