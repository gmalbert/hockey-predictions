"""Backtesting framework for model validation."""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class BacktestConfig:
    """Backtesting configuration."""
    start_date: str
    end_date: str
    initial_bankroll: float = 1000.0
    unit_size: float = 10.0  # $10 per unit
    min_edge: float = 0.02  # 2% minimum edge to bet
    max_kelly_fraction: float = 0.25  # Max 25% Kelly
    bet_types: List[str] = field(default_factory=lambda: ["moneyline"])

@dataclass
class BetResult:
    """Single bet outcome."""
    game_id: str
    date: str
    bet_type: str  # "home_ml", "away_ml", "home_pl", "away_pl", "over", "under"
    odds: int
    stake: float
    model_prob: float
    edge: float
    won: Optional[bool] = None
    profit: Optional[float] = None

@dataclass
class BacktestResults:
    """Aggregated backtesting results."""
    config: BacktestConfig
    bets: List[BetResult] = field(default_factory=list)
    
    @property
    def total_bets(self) -> int:
        return len([b for b in self.bets if b.won is not None])
    
    @property
    def wins(self) -> int:
        return sum(1 for b in self.bets if b.won is True)
    
    @property
    def losses(self) -> int:
        return sum(1 for b in self.bets if b.won is False)
    
    @property
    def win_rate(self) -> float:
        if self.total_bets == 0:
            return 0.0
        return self.wins / self.total_bets
    
    @property
    def total_staked(self) -> float:
        return sum(b.stake for b in self.bets if b.won is not None)
    
    @property
    def total_profit(self) -> float:
        return sum(b.profit for b in self.bets if b.profit is not None)
    
    @property
    def roi(self) -> float:
        if self.total_staked == 0:
            return 0.0
        return (self.total_profit / self.total_staked) * 100
    
    @property
    def units_profit(self) -> float:
        if self.config.unit_size == 0:
            return 0.0
        return self.total_profit / self.config.unit_size
    
    def max_drawdown(self) -> float:
        """Calculate maximum drawdown."""
        cumulative = 0.0
        peak = 0.0
        max_dd = 0.0
        
        for bet in self.bets:
            if bet.profit is not None:
                cumulative += bet.profit
                peak = max(peak, cumulative)
                drawdown = peak - cumulative
                max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def longest_losing_streak(self) -> int:
        """Find longest consecutive losing streak."""
        max_streak = 0
        current_streak = 0
        
        for bet in self.bets:
            if bet.won is False:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            elif bet.won is True:
                current_streak = 0
        
        return max_streak
    
    def summary(self) -> str:
        """Return formatted summary."""
        return f"""
Backtest Results: {self.config.start_date} to {self.config.end_date}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Bets:        {self.total_bets}
Record:            {self.wins}-{self.losses} ({self.win_rate:.1%})
Total Staked:      ${self.total_staked:,.2f}
Total Profit:      ${self.total_profit:+,.2f}
ROI:               {self.roi:+.2f}%
Units:             {self.units_profit:+.1f}u
Max Drawdown:      ${self.max_drawdown():,.2f}
Longest Losing:    {self.longest_losing_streak()} bets
"""
    
    def add_bet(self, bet: BetResult) -> None:
        """Add a bet to results."""
        self.bets.append(bet)


class BacktestEngine:
    """Run backtests against historical data."""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.results = BacktestResults(config=config)
    
    def evaluate_bet(
        self,
        game_id: str,
        date: str,
        bet_type: str,
        model_prob: float,
        odds: int,
        actual_result: bool
    ) -> None:
        """
        Evaluate a single betting opportunity.
        
        Args:
            game_id: Unique game identifier
            date: Date of game
            bet_type: Type of bet (home_ml, away_ml, etc.)
            model_prob: Model's probability for this outcome
            odds: American odds for this bet
            actual_result: True if bet won, False if lost
        """
        from src.utils.odds import american_to_implied, calculate_edge
        
        # Calculate edge
        edge_info = calculate_edge(model_prob, odds)
        edge = edge_info["edge_pct"] / 100
        
        # Only bet if edge exceeds minimum
        if edge < self.config.min_edge:
            return
        
        # Calculate stake using Kelly criterion (with fraction limit)
        kelly = edge_info.get("kelly_fraction", 0)
        fraction = min(kelly, self.config.max_kelly_fraction)
        stake = self.config.unit_size * fraction / 0.01  # Scale to units
        stake = max(stake, self.config.unit_size)  # Minimum 1 unit
        
        # Calculate profit
        if actual_result:
            if odds > 0:
                profit = stake * (odds / 100)
            else:
                profit = stake * (100 / abs(odds))
        else:
            profit = -stake
        
        # Record bet
        bet = BetResult(
            game_id=game_id,
            date=date,
            bet_type=bet_type,
            odds=odds,
            stake=stake,
            model_prob=model_prob,
            edge=edge,
            won=actual_result,
            profit=profit
        )
        
        self.results.add_bet(bet)
    
    def get_results(self) -> BacktestResults:
        """Return backtest results."""
        return self.results
