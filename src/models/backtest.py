"""Backtesting framework for model validation."""
from dataclasses import dataclass, field
from typing import List

@dataclass
class BetResult:
    """Single bet outcome."""
    game_id: str
    prediction: str  # "home", "away", "over", "under"
    odds: int
    stake: float
    won: bool
    profit: float

@dataclass
class BacktestResults:
    """Aggregated backtesting results."""
    total_bets: int = 0
    wins: int = 0
    losses: int = 0
    total_staked: float = 0.0
    total_profit: float = 0.0
    bets: List[BetResult] = field(default_factory=list)
    
    @property
    def win_rate(self) -> float:
        if self.total_bets == 0:
            return 0.0
        return self.wins / self.total_bets
    
    @property
    def roi(self) -> float:
        if self.total_staked == 0:
            return 0.0
        return (self.total_profit / self.total_staked) * 100
    
    def add_bet(self, bet: BetResult) -> None:
        self.bets.append(bet)
        self.total_bets += 1
        self.total_staked += bet.stake
        self.total_profit += bet.profit
        if bet.won:
            self.wins += 1
        else:
            self.losses += 1
