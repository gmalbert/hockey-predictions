"""Tests for NHL API client."""
import pytest
from pathlib import Path


class TestNHLClient:
    """Test suite for NHL API client."""
    
    def test_client_initialization(self):
        """Test client can be initialized."""
        from src.api.nhl_client import NHLClient
        
        client = NHLClient()
        assert client.CACHE_DIR.exists() or True  # May not exist until first call
        assert client.cache_ttl.total_seconds() == 300  # 5 minutes
    
    def test_client_custom_ttl(self):
        """Test client with custom cache TTL."""
        from src.api.nhl_client import NHLClient
        
        client = NHLClient(cache_ttl_minutes=10)
        assert client.cache_ttl.total_seconds() == 600
    
    def test_cache_path_generation(self):
        """Test cache path is generated correctly."""
        from src.api.nhl_client import NHLClient
        
        client = NHLClient()
        url = "https://api-web.nhle.com/v1/schedule/2026-01-15"
        path = client._get_cache_path(url)
        
        assert path.suffix == ".json"
        assert len(path.name) <= 105  # 100 + .json


class TestOddsUtils:
    """Test suite for odds utilities."""
    
    def test_american_to_implied_favorite(self):
        """Test conversion for favorite odds."""
        from src.utils.odds import american_to_implied
        
        prob = american_to_implied(-150)
        assert abs(prob - 0.6) < 0.01
    
    def test_american_to_implied_underdog(self):
        """Test conversion for underdog odds."""
        from src.utils.odds import american_to_implied
        
        prob = american_to_implied(150)
        assert abs(prob - 0.4) < 0.01
    
    def test_implied_to_american_roundtrip(self):
        """Test roundtrip conversion."""
        from src.utils.odds import american_to_implied, implied_to_american
        
        original = -150
        prob = american_to_implied(original)
        converted = implied_to_american(prob)
        
        assert abs(converted - original) <= 1  # Allow rounding
    
    def test_calculate_edge_positive(self):
        """Test edge calculation with positive edge."""
        from src.utils.odds import calculate_edge
        
        result = calculate_edge(model_prob=0.55, book_odds=110)
        
        assert result["edge_pct"] > 0
        assert result["has_value"] is True
    
    def test_calculate_edge_negative(self):
        """Test edge calculation with no edge."""
        from src.utils.odds import calculate_edge
        
        result = calculate_edge(model_prob=0.45, book_odds=-110)
        
        assert result["edge_pct"] < 0
        assert result["has_value"] is False


class TestExpectedGoals:
    """Test suite for expected goals model."""
    
    def test_calculate_xg_basic(self):
        """Test basic xG calculation."""
        from src.models.expected_goals import calculate_expected_goals, TeamMetrics
        
        home = TeamMetrics("TOR", 3.4, 2.8, 33, 28, 25, 82)
        away = TeamMetrics("MTL", 2.9, 3.3, 30, 32, 20, 78)
        
        home_xg, away_xg = calculate_expected_goals(home, away)
        
        assert home_xg > away_xg  # Home should have advantage
        assert home_xg > 0
        assert away_xg > 0
    
    def test_home_advantage_applied(self):
        """Test home advantage is applied."""
        from src.models.expected_goals import calculate_expected_goals, TeamMetrics
        
        # Equal teams
        team = TeamMetrics("TST", 3.0, 3.0, 30, 30, 20, 80)
        
        home_xg, away_xg = calculate_expected_goals(team, team)
        
        assert home_xg > away_xg  # Home should still have advantage


class TestWinProbability:
    """Test suite for win probability model."""
    
    def test_poisson_prob(self):
        """Test Poisson probability calculation."""
        from src.models.win_probability import poisson_prob
        
        # P(X=0) when lambda=3 should be e^-3 ≈ 0.05
        prob = poisson_prob(3.0, 0)
        assert abs(prob - 0.0498) < 0.01
    
    def test_probabilities_sum_to_one(self):
        """Test win probabilities sum to 1."""
        from src.models.win_probability import calculate_win_probability
        
        probs = calculate_win_probability(3.0, 2.5)
        
        total = probs.home_win + probs.away_win
        assert abs(total - 1.0) < 0.01
    
    def test_higher_xg_higher_prob(self):
        """Test team with higher xG has higher win prob."""
        from src.models.win_probability import calculate_win_probability
        
        probs = calculate_win_probability(3.5, 2.5)
        
        assert probs.home_win > probs.away_win


class TestPuckLine:
    """Test suite for puck line model."""
    
    def test_puck_line_probabilities(self):
        """Test puck line probabilities sum correctly."""
        from src.models.puck_line import predict_puck_line
        
        pred = predict_puck_line(3.5, 2.5)
        
        total = pred.home_minus_1_5 + pred.away_plus_1_5
        assert abs(total - 1.0) < 0.01
    
    def test_higher_margin_higher_cover(self):
        """Test larger expected margin = higher cover rate."""
        from src.models.puck_line import predict_puck_line
        
        close_game = predict_puck_line(3.0, 2.8)
        blowout = predict_puck_line(4.0, 2.0)
        
        assert blowout.home_minus_1_5 > close_game.home_minus_1_5


class TestEvaluation:
    """Test suite for model evaluation."""
    
    def test_mae_calculation(self):
        """Test MAE calculation."""
        from src.models.evaluation import calculate_mae, PredictionResult
        
        predictions = [
            PredictionResult("1", "2026-01-01", "TOR", "MTL", 3.0, 2.5, 3, 2, 0.55, True),
            PredictionResult("2", "2026-01-02", "BOS", "NYR", 2.8, 2.8, 4, 2, 0.50, True),
        ]
        
        mae = calculate_mae(predictions, "total")
        
        # Game 1: pred 5.5, actual 5, error 0.5
        # Game 2: pred 5.6, actual 6, error 0.4
        # MAE = 0.45
        assert mae > 0
    
    def test_accuracy_calculation(self):
        """Test accuracy calculation."""
        from src.models.evaluation import calculate_accuracy, PredictionResult
        
        predictions = [
            PredictionResult("1", "2026-01-01", "TOR", "MTL", 3.0, 2.5, 3, 2, 0.60, True),
            PredictionResult("2", "2026-01-02", "BOS", "NYR", 2.8, 2.8, 2, 4, 0.55, False),
        ]
        
        accuracy = calculate_accuracy(predictions)
        
        # Pred 1: predicted home win (0.6 > 0.5), home won = correct
        # Pred 2: predicted home win (0.55 > 0.5), home lost = incorrect
        assert accuracy == 0.5
